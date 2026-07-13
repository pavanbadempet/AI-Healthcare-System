"""Clinical Intelligence Layer — real-time alerting, AI insights, and explainable AI."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from . import auth, database, models, schemas
from .core_ai import generate
from .event_bus import event_bus

router = APIRouter(prefix="/intelligence", tags=["Clinical Intelligence"])

MEDICAL_DISCLAIMER = (
    "This AI-generated insight is for informational purposes only. Always "
    "consult a qualified clinician for diagnosis, treatment, or emergencies."
)


# ------------------------------------------------------------------
# Real-Time Alert Engine (Event Bus Subscriptions)
# ------------------------------------------------------------------
async def handle_vitals_recorded(payload: dict[str, Any]) -> None:
    """Callback triggered whenever new patient vitals are recorded."""
    patient_id = payload.get("patient_id")
    if not patient_id:
        return

    # Extract vitals
    hr = payload.get("heart_rate")
    sys_bp = payload.get("systolic_bp")
    dia_bp = payload.get("diastolic_bp")
    spo2 = payload.get("spo2")

    alerts_to_create = []

    # Check SpO2 (Critical < 90%)
    if spo2 is not None and spo2 < 90.0:
        alerts_to_create.append({
            "alert_type": "Hypoxia Alert",
            "severity": "CRITICAL",
            "message": f"Critical blood oxygen saturation level detected: {spo2}% (threshold: < 90%)",
        })

    # Check Heart Rate (Warning < 50 bpm or > 120 bpm)
    if hr is not None:
        if hr > 120.0:
            alerts_to_create.append({
                "alert_type": "Tachycardia Alert",
                "severity": "WARNING",
                "message": f"Elevated heart rate detected: {hr} bpm (threshold: > 120 bpm)",
            })
        elif hr < 50.0:
            alerts_to_create.append({
                "alert_type": "Bradycardia Alert",
                "severity": "WARNING",
                "message": f"Low heart rate detected: {hr} bpm (threshold: < 50 bpm)",
            })

    # Check Blood Pressure (Critical Systolic > 180 or Diastolic > 120)
    if sys_bp is not None or dia_bp is not None:
        is_crisis = False
        bp_str = ""
        if sys_bp is not None and sys_bp > 180.0:
            is_crisis = True
            bp_str += f"Systolic BP {sys_bp} mmHg "
        if dia_bp is not None and dia_bp > 120.0:
            is_crisis = True
            bp_str += f"Diastolic BP {dia_bp} mmHg"

        if is_crisis:
            alerts_to_create.append({
                "alert_type": "Hypertensive Crisis Alert",
                "severity": "CRITICAL",
                "message": f"Hypertensive crisis range detected: {bp_str.strip()}",
            })

    # Persist alerts to DB and publish alerts
    if alerts_to_create:
        from .database import get_db_context
        with get_db_context() as db:
            for alert_info in alerts_to_create:
                db_alert = models.ClinicalAlert(
                    patient_id=patient_id,
                    alert_type=alert_info["alert_type"],
                    severity=alert_info["severity"],
                    message=alert_info["message"],
                    is_acknowledged=False,
                )
                db.add(db_alert)
                db.commit()
                db.refresh(db_alert)

                # Publish DIAGNOSTIC_ALERT to event bus
                await event_bus.publish("DIAGNOSTIC_ALERT", {
                    "alert_id": db_alert.id,
                    "patient_id": patient_id,
                    "alert_type": db_alert.alert_type,
                    "severity": db_alert.severity,
                    "message": db_alert.message,
                })


def register_intelligence_event_handlers() -> None:
    """Subscribe intelligence engine callbacks to the event bus."""
    event_bus.subscribe("VITALS_RECORDED", handle_vitals_recorded)


# ------------------------------------------------------------------
# REST Endpoints
# ------------------------------------------------------------------
@router.get("/alerts", response_model=list[schemas.ClinicalAlertResponse])
def list_clinical_alerts(
    severity: Optional[str] = Query(None, description="Filter by CRITICAL | WARNING | INFO"),
    patient_id: Optional[int] = Query(None, description="Filter by specific patient ID"),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[models.ClinicalAlert]:
    """List active clinical alerts, ordered by created_at desc (limit 50)."""
    query = db.query(models.ClinicalAlert)

    # Scoping: patients can only see their own alerts
    if current_user.role == "patient":
        query = query.filter(models.ClinicalAlert.patient_id == current_user.id)
    elif patient_id is not None:
        query = query.filter(models.ClinicalAlert.patient_id == patient_id)

    if severity:
        query = query.filter(models.ClinicalAlert.severity == severity.upper())

    return (
        query.order_by(models.ClinicalAlert.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, str]:
    """Acknowledge a clinical alert (clinicians and admins only)."""
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinicians or admins can acknowledge alerts",
        )

    alert = db.query(models.ClinicalAlert).filter(models.ClinicalAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    alert.is_acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "acknowledged"}


@router.get("/insights/{patient_id}", response_model=schemas.PatientInsightResponse)
async def generate_patient_insights(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.PatientInsight:
    """Generate or retrieve AI-powered clinical insights for a patient."""
    # Safety Check: Patients cannot access other patient's insights
    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to other patient's records",
        )

    # Verify patient exists
    patient = (
        db.query(models.User)
        .filter(models.User.id == patient_id, models.User.role == "patient")
        .first()
    )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Retrieve most recent vitals
    vitals = (
        db.query(models.VitalObservation)
        .filter(models.VitalObservation.patient_id == patient_id)
        .order_by(models.VitalObservation.observed_at.desc())
        .first()
    )

    # Construct clinical context for LLM
    vitals_summary = "No recent vitals available."
    if vitals:
        vitals_summary = (
            f"Heart Rate: {vitals.heart_rate or 'N/A'} bpm, "
            f"Blood Pressure: {vitals.systolic_bp or 'N/A'}/{vitals.diastolic_bp or 'N/A'} mmHg, "
            f"SpO2: {vitals.spo2 or 'N/A'}%, "
            f"Temp: {vitals.temperature_c or 'N/A'} C"
        )

    prompt = (
        f"Generate a clinical risk summary for patient '{patient.full_name}'.\n"
        f"Recent Vital Signs: {vitals_summary}\n\n"
        "Provide a concise, professional risk summary dashboard outlining "
        "potential concerns, suggested monitoring protocols, and lifestyle recommendations."
    )

    system_prompt = (
        "You are an expert clinical intelligence AI. "
        "Your task is to analyze patient vitals and write a professional, "
        "highly-structured risk summary for a clinician. Keep it brief. "
        "Always adhere to clinical accuracy."
    )

    # Call core_ai.generate to get LLM response
    ai_response = await generate(prompt=prompt, system=system_prompt)

    insight_content = {
        "summary": ai_response,
        "vital_summary": vitals_summary,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save insight record
    db_insight = models.PatientInsight(
        patient_id=patient_id,
        insight_type="risk_summary",
        content=json.dumps(insight_content),
        model_version="clinos-intelligence-v1",
    )
    db.add(db_insight)
    db.commit()
    db.refresh(db_insight)

    # Set temporary disclaimer attribute for the response model
    db_insight.disclaimer = MEDICAL_DISCLAIMER
    return db_insight


@router.get("/explainability/{prediction_id}", response_model=schemas.ExplainabilityResponse)
def get_prediction_explainability(
    prediction_id: int,
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    """Get SHAP-style feature importances explaining a model prediction."""
    # SHAP feature importance mock for cardiovascular / general clinical risk
    feature_importances = {
        "systolic_bp": 0.28,
        "heart_rate": 0.22,
        "cholesterol": 0.18,
        "age": 0.14,
        "bmi": 0.10,
        "spo2": 0.08,
    }

    explanation_text = (
        "Systolic Blood Pressure (28%) and Heart Rate (22%) are the primary driving "
        "features for this prediction. High BP and tachycardia indicate heightened "
        "cardiac strain."
    )

    return {
        "prediction_id": prediction_id,
        "model_name": "heart_disease_risk",
        "feature_importances": feature_importances,
        "explanation_text": explanation_text,
    }
