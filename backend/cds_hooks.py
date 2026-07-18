"""HL7 CDS Hooks (Clinical Decision Support) Engine.

Provides standard discovery and evaluation endpoints for clinical alert cards
triggered by clinician workflows (e.g., patient-view hook).
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from backend.models.clinical import VitalObservation

logger = logging.getLogger(__name__)

def get_cds_services_registry() -> Dict[str, Any]:
    """Returns a list of registered clinical decision support services (discovery)."""
    return {
        "services": [
            {
                "id": "cardio-risk-service",
                "hook": "patient-view",
                "title": "Cardiovascular Risk Evaluator",
                "description": "Analyzes vital observations for elevated blood pressure and tachycardia.",
                "prefetch": {
                  "patient": "Patient/{{context.patientId}}"
                }
            }
        ]
    }

def evaluate_cardio_risk_service(request_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Evaluates the cardio-risk CDS Hook request.
    If the patient's systolic blood pressure or heart rate exceeds thresholds,
    returns a warning 'Card' suggesting a cardiology referral.
    """
    context = request_data.get("context", {})
    patient_id_str = context.get("patientId")

    if not patient_id_str:
        return {"cards": []}

    # Extract patient ID integer
    try:
        if "/" in patient_id_str:
            patient_id = int(patient_id_str.split("/")[-1])
        else:
            patient_id = int(patient_id_str)
    except ValueError:
        logger.warning("Invalid patient ID format: %s", patient_id_str)
        return {"cards": []}

    # Fetch latest VitalObservation record for the patient
    latest_obs = (
        db.query(VitalObservation)
        .filter(VitalObservation.patient_id == patient_id)
        .order_by(VitalObservation.observed_at.desc())
        .first()
    )

    if not latest_obs:
        return {"cards": []}

    cards: List[Dict[str, Any]] = []

    # Check for clinical thresholds
    high_bp = latest_obs.systolic_bp and latest_obs.systolic_bp >= 140
    tachycardia = latest_obs.heart_rate and latest_obs.heart_rate >= 100

    if high_bp or tachycardia:
        detail_msg = "Patient vital check triggered warnings: "
        conditions = []
        if high_bp:
            conditions.append(f"Elevated systolic BP ({latest_obs.systolic_bp} mmHg)")
        if tachycardia:
            conditions.append(f"Tachycardia heart rate ({latest_obs.heart_rate} bpm)")
        detail_msg += " and ".join(conditions) + ". Please review cardiovascular metrics immediately."

        # Construct a standardized CDS Hook Card
        card = {
            "summary": "Cardiovascular Risk Flagged",
            "detail": detail_msg,
            "indicator": "warning",
            "source": {
                "label": "AI Healthcare System CDS Risk Analyzer",
                "url": "http://127.0.0.1:8000"
            },
            "suggestions": [
                {
                    "label": "Refer to Cardiology Consult",
                    "actions": [
                        {
                            "type": "create",
                            "description": "Create standard clinical order for cardiologist consult",
                            "resource": {
                                "resourceType": "ServiceRequest",
                                "status": "active",
                                "intent": "order",
                                "code": {
                                    "coding": [
                                        {
                                            "system": "http://snomed.info/sct",
                                            "code": "308292008",
                                            "display": "Referral to cardiology service"
                                        }
                                    ]
                                },
                                "subject": {
                                    "reference": f"Patient/{patient_id}"
                                }
                            }
                        }
                    ]
                }
            ]
        }
        cards.append(card)

    return {"cards": cards}
