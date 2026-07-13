"""Real-time vitals monitoring and deterministic review signals."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import audit, auth, database, models, schemas
from .facility_scope import users_share_facility_context

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

OPEN_SIGNAL_STATUSES = ("open", "acknowledged")
MONITORING_FACILITY_MISMATCH_DETAIL = "Monitoring resources must belong to the same facility"
MONITORING_FACILITY_ACCESS_DETAIL = "Monitoring resource is outside the user's facility"
VITAL_MEASUREMENT_FIELDS = (
    "heart_rate",
    "systolic_bp",
    "diastolic_bp",
    "spo2",
    "temperature_c",
    "respiratory_rate",
)
VITAL_CAPTURE_RANGES = {
    "heart_rate": (20, 250),
    "systolic_bp": (50, 260),
    "diastolic_bp": (30, 160),
    "spo2": (0, 100),
    "temperature_c": (30, 45),
    "respiratory_rate": (5, 80),
}


def _require_admin(current_user: models.User) -> None:
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")


def _doctor_assigned_to_patient(db: Session, doctor_id: int, patient_id: int) -> bool:
    if not users_share_facility_context(db, doctor_id, patient_id):
        return False

    encounter = db.query(models.Encounter).filter(
        models.Encounter.patient_id == patient_id,
        models.Encounter.doctor_id == doctor_id,
    ).first()
    if encounter:
        return True

    admission = db.query(models.Admission).filter(
        models.Admission.patient_id == patient_id,
        models.Admission.doctor_id == doctor_id,
        models.Admission.status == "active",
    ).first()
    if admission:
        return True

    appointment = db.query(models.Appointment).filter(
        models.Appointment.user_id == patient_id,
        models.Appointment.doctor_id == doctor_id,
    ).first()
    return appointment is not None


def _ensure_patient_access(db: Session, current_user: models.User, patient_id: int) -> None:
    if auth.is_admin(current_user):
        patient = _get_patient(db, patient_id)
        _ensure_facility_access(current_user, patient.facility_id)
        return
    if current_user.role == "patient":
        if current_user.id != patient_id:
            raise HTTPException(status_code=403, detail="Patients can submit only their own vitals")
        return
    if current_user.role == "doctor":
        if not _doctor_assigned_to_patient(db, current_user.id, patient_id):
            raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")
        return
    raise HTTPException(status_code=403, detail="Not authorized")


def _ensure_doctor_review_access(db: Session, current_user: models.User, patient_id: int) -> None:
    if auth.is_admin(current_user):
        patient = _get_patient(db, patient_id)
        _ensure_facility_access(current_user, patient.facility_id)
        return
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")
    if not _doctor_assigned_to_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")


def _get_patient(db: Session, patient_id: int) -> models.User:
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _get_signal(db: Session, signal_id: int) -> models.MonitoringSignal:
    signal = db.query(models.MonitoringSignal).filter(models.MonitoringSignal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Monitoring signal not found")
    return signal


def _resolve_monitoring_facility_id(*entities: object | None) -> int | None:
    facility_ids = {
        getattr(entity, "facility_id", None)
        for entity in entities
        if entity is not None and getattr(entity, "facility_id", None) is not None
    }
    if len(facility_ids) > 1:
        raise HTTPException(status_code=400, detail=MONITORING_FACILITY_MISMATCH_DETAIL)
    return next(iter(facility_ids), None)


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(or_(facility_column == current_user.facility_id, facility_column.is_(None)))


def _ensure_facility_access(current_user: models.User, facility_id: int | None) -> None:
    if current_user.facility_id is None or facility_id is None:
        return
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=MONITORING_FACILITY_ACCESS_DETAIL)


def _validate_context(
    db: Session,
    vital: schemas.VitalObservationCreate,
) -> tuple[models.Encounter | None, models.Department | None]:
    encounter = None
    department = None
    encounter_department_id = None
    if vital.encounter_id is not None:
        encounter = db.query(models.Encounter).filter(models.Encounter.id == vital.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        if encounter.patient_id != vital.patient_id:
            raise HTTPException(status_code=400, detail="Encounter patient must match vital patient")
        encounter_department_id = encounter.department_id
    if vital.department_id is not None:
        department = db.query(models.Department).filter(models.Department.id == vital.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        if encounter_department_id is not None and encounter_department_id != vital.department_id:
            raise HTTPException(status_code=400, detail="Encounter department must match vital department")
    return encounter, department


def _validate_vital_measurements(vital: schemas.VitalObservationCreate) -> None:
    values = {
        field: getattr(vital, field)
        for field in VITAL_MEASUREMENT_FIELDS
    }
    if all(value is None for value in values.values()):
        raise HTTPException(status_code=400, detail="At least one vital measurement is required")
    for field, value in values.items():
        if value is None:
            continue
        lower, upper = VITAL_CAPTURE_RANGES[field]
        if value < lower or value > upper:
            raise HTTPException(status_code=400, detail="Vital measurement is outside accepted capture range")


def _add_signal(
    db: Session,
    signals: list[models.MonitoringSignal],
    *,
    vital: models.VitalObservation,
    signal_type: str,
    severity: str,
    title: str,
    summary: str,
) -> None:
    signal = models.MonitoringSignal(
        facility_id=vital.facility_id,
        patient_id=vital.patient_id,
        vital_observation_id=vital.id,
        encounter_id=vital.encounter_id,
        department_id=vital.department_id,
        signal_type=signal_type,
        severity=severity,
        title=title,
        summary=summary,
        status="open",
    )
    db.add(signal)
    signals.append(signal)


def _generate_signals(db: Session, vital: models.VitalObservation) -> list[models.MonitoringSignal]:
    signals: list[models.MonitoringSignal] = []
    import math

    from sqlalchemy import desc

    # 1. Rolling Z-Score Anomaly Detection
    past_vitals = (
        db.query(models.VitalObservation)
        .filter(
            models.VitalObservation.patient_id == vital.patient_id,
            models.VitalObservation.id != vital.id
        )
        .order_by(desc(models.VitalObservation.observed_at))
        .limit(10)
        .all()
    )

    if len(past_vitals) >= 3:
        for metric in ["heart_rate", "systolic_bp", "spo2"]:
            current_val = getattr(vital, metric, None)
            if current_val is None:
                continue

            past_vals = [getattr(pv, metric) for pv in past_vitals if getattr(pv, metric, None) is not None]
            if len(past_vals) >= 3:
                mean = sum(past_vals) / len(past_vals)
                variance = sum((x - mean) ** 2 for x in past_vals) / len(past_vals)
                std_dev = math.sqrt(variance)

                min_std = 2.0 if metric != "spo2" else 0.5
                effective_std = max(std_dev, min_std)

                z_score = abs(current_val - mean) / effective_std
                if z_score > 2.5:
                    _add_signal(
                        db,
                        signals,
                        vital=vital,
                        signal_type=f"anomaly_{metric}",
                        severity="warning",
                        title=f"Anomaly detected in {metric.replace('_', ' ').title()}",
                        summary=(
                            f"Recent {metric.replace('_', ' ')} value ({current_val:.1f}) is statistically anomalous "
                            f"relative to the patient's rolling baseline (Mean: {mean:.1f}, Z-Score: {z_score:.2f})."
                        )
                    )

    # 2. Deterministic alerts
    if vital.spo2 is not None and vital.spo2 < 94:
        _add_signal(
            db,
            signals,
            vital=vital,
            signal_type="oxygen_saturation",
            severity="critical" if vital.spo2 < 90 else "warning",
            title="Oxygen saturation needs review",
            summary="Recent oxygen saturation is outside the review range and needs clinician review.",
        )

    if (
        vital.systolic_bp is not None
        and vital.diastolic_bp is not None
        and (vital.systolic_bp >= 140 or vital.diastolic_bp >= 90)
    ):
        _add_signal(
            db,
            signals,
            vital=vital,
            signal_type="blood_pressure",
            severity="critical" if vital.systolic_bp >= 180 or vital.diastolic_bp >= 120 else "warning",
            title="Blood pressure needs review",
            summary="Recent blood pressure is outside the review range and needs clinician review.",
        )

    if vital.heart_rate is not None and (vital.heart_rate < 50 or vital.heart_rate > 120):
        _add_signal(
            db,
            signals,
            vital=vital,
            signal_type="heart_rate",
            severity="critical" if vital.heart_rate < 40 or vital.heart_rate > 140 else "warning",
            title="Heart rate needs review",
            summary="Recent heart rate is outside the review range and needs clinician review.",
        )

    if vital.temperature_c is not None and (vital.temperature_c < 35 or vital.temperature_c >= 38):
        _add_signal(
            db,
            signals,
            vital=vital,
            signal_type="temperature",
            severity="critical" if vital.temperature_c < 35 or vital.temperature_c >= 39 else "warning",
            title="Temperature needs review",
            summary="Recent temperature is outside the review range and needs clinician review.",
        )

    if vital.respiratory_rate is not None and (vital.respiratory_rate < 10 or vital.respiratory_rate > 24):
        _add_signal(
            db,
            signals,
            vital=vital,
            signal_type="respiratory_rate",
            severity="warning",
            title="Respiratory rate needs review",
            summary="Recent respiratory rate is outside the review range and needs clinician review.",
        )
    return signals


def _record_care_event(
    db: Session,
    *,
    vital: models.VitalObservation,
    actor_user_id: int,
    event_type: str,
    title: str,
    summary: str,
    severity: str = "info",
) -> None:
    db.add(models.CareEvent(
        facility_id=vital.facility_id,
        patient_id=vital.patient_id,
        actor_user_id=actor_user_id,
        encounter_id=vital.encounter_id,
        department_id=vital.department_id,
        event_type=event_type,
        title=title,
        summary=summary,
        severity=severity,
    ))


def _vital_to_dict(vital: models.VitalObservation) -> dict[str, Any]:
    return schemas.VitalObservationResponse.model_validate(vital).model_dump(mode="json")


def _signal_to_dict(signal: models.MonitoringSignal) -> dict[str, Any]:
    return schemas.MonitoringSignalResponse.model_validate(signal).model_dump(mode="json")


@router.post("/vitals", response_model=schemas.VitalSubmissionResponse)
def submit_vitals(
    vital: schemas.VitalObservationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    patient = _get_patient(db, vital.patient_id)
    _ensure_facility_access(current_user, patient.facility_id)
    _ensure_patient_access(db, current_user, vital.patient_id)
    encounter, department = _validate_context(db, vital)
    _validate_vital_measurements(vital)
    facility_id = _resolve_monitoring_facility_id(current_user, patient, encounter, department)

    db_vital = models.VitalObservation(
        facility_id=facility_id,
        patient_id=vital.patient_id,
        recorded_by_id=current_user.id,
        encounter_id=vital.encounter_id,
        department_id=vital.department_id,
        source=vital.source or "manual",
        heart_rate=vital.heart_rate,
        systolic_bp=vital.systolic_bp,
        diastolic_bp=vital.diastolic_bp,
        spo2=vital.spo2,
        temperature_c=vital.temperature_c,
        respiratory_rate=vital.respiratory_rate,
        observed_at=vital.observed_at or datetime.now(timezone.utc),
    )
    db.add(db_vital)
    db.flush()
    _record_care_event(
        db,
        vital=db_vital,
        actor_user_id=current_user.id,
        event_type="VITALS_RECORDED",
        title="Vitals recorded",
        summary="New vitals were recorded for clinician review.",
    )
    signals = _generate_signals(db, db_vital)
    for signal in signals:
        _record_care_event(
            db,
            vital=db_vital,
            actor_user_id=current_user.id,
            event_type="MONITORING_SIGNAL",
            title=signal.title,
            summary=signal.summary,
            severity=signal.severity,
        )
    db.commit()
    db.refresh(db_vital)
    for signal in signals:
        db.refresh(signal)

    # Publish VITALS_RECORDED event via BackgroundTasks
    from .event_bus import event_bus
    payload = {
        "patient_id": db_vital.patient_id,
        "heart_rate": db_vital.heart_rate,
        "systolic_bp": db_vital.systolic_bp,
        "diastolic_bp": db_vital.diastolic_bp,
        "spo2": db_vital.spo2,
        "temperature_c": db_vital.temperature_c,
        "respiratory_rate": db_vital.respiratory_rate,
    }
    background_tasks.add_task(event_bus.publish, "VITALS_RECORDED", payload)

    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=vital.patient_id,
        action="RECORD_VITALS",
        details={
            "resource_type": "vital_observation",
            "resource_id": db_vital.id,
            "signal_count": len(signals),
        },
    )
    return {"vital": db_vital, "signals": signals}


@router.get("/patient/vitals", response_model=list[schemas.VitalObservationResponse])
def get_patient_vitals(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    return db.query(models.VitalObservation).filter(
        models.VitalObservation.patient_id == current_user.id
    ).order_by(models.VitalObservation.observed_at.desc()).limit(100).all()


@router.get("/doctor/patients/{patient_id}/signals")
def get_patient_signals_for_doctor(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _get_patient(db, patient_id)
    _ensure_doctor_review_access(db, current_user, patient_id)
    latest_vitals = db.query(models.VitalObservation).filter(
        models.VitalObservation.patient_id == patient_id
    ).order_by(models.VitalObservation.observed_at.desc()).limit(10).all()
    open_signals = db.query(models.MonitoringSignal).filter(
        models.MonitoringSignal.patient_id == patient_id,
        models.MonitoringSignal.status.in_(OPEN_SIGNAL_STATUSES),
    ).order_by(models.MonitoringSignal.created_at.desc()).all()
    return {
        "patient_id": patient_id,
        "latest_vitals": [_vital_to_dict(vital) for vital in latest_vitals],
        "open_signals": [_signal_to_dict(signal) for signal in open_signals],
        "clinical_safety_note": "Signals highlight patterns for clinician review and are not final clinical conclusions.",
    }


@router.put("/signals/{signal_id}/resolve", response_model=schemas.MonitoringSignalResponse)
def resolve_monitoring_signal(
    signal_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    signal = _get_signal(db, signal_id)
    _ensure_facility_access(current_user, signal.facility_id)
    _ensure_doctor_review_access(db, current_user, signal.patient_id)
    if signal.status == "resolved":
        raise HTTPException(status_code=409, detail="Monitoring signal is already resolved")

    signal.status = "resolved"
    db.add(models.CareEvent(
        facility_id=signal.facility_id,
        patient_id=signal.patient_id,
        actor_user_id=current_user.id,
        encounter_id=signal.encounter_id,
        department_id=signal.department_id,
        event_type="MONITORING_SIGNAL_RESOLVED",
        title="Monitoring signal resolved",
        summary="Clinician reviewed and resolved a monitoring signal.",
        severity="info",
    ))
    db.commit()
    db.refresh(signal)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=signal.patient_id,
        action="RESOLVE_MONITORING_SIGNAL",
        details={"resource_type": "monitoring_signal", "resource_id": signal.id},
    )
    return signal


@router.get("/doctor/patterns")
def get_doctor_patterns(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    if current_user.role != "doctor" and not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")

    patient_ids_query = db.query(models.Encounter.patient_id)
    if current_user.role == "doctor":
        patient_ids_query = patient_ids_query.filter(models.Encounter.doctor_id == current_user.id)
    patient_ids = {row[0] for row in patient_ids_query.all()}
    signal_query = db.query(models.MonitoringSignal)
    vital_query = db.query(models.VitalObservation)
    if patient_ids:
        signal_query = signal_query.filter(models.MonitoringSignal.patient_id.in_(patient_ids))
        vital_query = vital_query.filter(models.VitalObservation.patient_id.in_(patient_ids))
    elif current_user.role == "doctor":
        return {
            "assigned_patient_count": 0,
            "total_vital_observations": 0,
            "open_signals": 0,
            "clinical_safety_note": "No assigned monitoring data available.",
        }
    return {
        "assigned_patient_count": len(patient_ids),
        "total_vital_observations": vital_query.count(),
        "open_signals": signal_query.filter(models.MonitoringSignal.status.in_(OPEN_SIGNAL_STATUSES)).count(),
        "clinical_safety_note": "Pattern summaries support clinician review and are not diagnoses.",
    }


@router.get("/admin/patterns")
def get_admin_patterns(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    signal_query = _scope_query_to_user_facility(
        db.query(models.MonitoringSignal),
        models.MonitoringSignal.facility_id,
        current_user,
    )
    vital_query = _scope_query_to_user_facility(
        db.query(models.VitalObservation),
        models.VitalObservation.facility_id,
        current_user,
    )
    signals = signal_query.all()
    signals_by_type: dict[str, int] = {}
    signals_by_severity: dict[str, int] = {}
    signals_by_department: dict[int | str, int] = {}
    for signal in signals:
        signals_by_type[signal.signal_type] = signals_by_type.get(signal.signal_type, 0) + 1
        signals_by_severity[signal.severity] = signals_by_severity.get(signal.severity, 0) + 1
        department_key: int | str = signal.department_id if signal.department_id is not None else "unassigned"
        signals_by_department[department_key] = signals_by_department.get(department_key, 0) + 1

    from backend.models.clinical import SparkStreamingMetrics
    latest_metric = db.query(SparkStreamingMetrics).order_by(SparkStreamingMetrics.timestamp.desc()).first()
    spark_info = None
    if latest_metric:
        spark_info = {
            "spark_batch_id": latest_metric.batch_id,
            "spark_latency_ms": latest_metric.processing_time_ms,
            "spark_ml_latency_ms": latest_metric.ml_latency_ms,
            "spark_records_processed": latest_metric.records_processed,
            "spark_timestamp": latest_metric.timestamp.isoformat()
        }

    return {
        "total_vital_observations": vital_query.count(),
        "open_signals": signal_query.filter(
            models.MonitoringSignal.status.in_(OPEN_SIGNAL_STATUSES)
        ).count(),
        "signals_by_type": signals_by_type,
        "signals_by_severity": signals_by_severity,
        "signals_by_department": signals_by_department,
        "spark_info": spark_info,
        "clinical_safety_note": "Monitoring patterns support clinician and administrator review; clinicians make care decisions.",
    }
