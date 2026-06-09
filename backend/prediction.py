import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
import logging
from typing import Dict, Any

# --- Custom Modules ---
from . import audit, database, explainability, schemas, features
from .facility_scope import users_share_facility_context
from .model_service import model_service, MEDICAL_DISCLAIMER, PREDICTION_FAILURE_DETAIL, get_age_bucket
from sqlalchemy.orm import Session

# --- Logging Configuration ---
logger = logging.getLogger(__name__)

# --- Router Definition ---
router = APIRouter()

# --- Backward-compatible re-export ---
# External modules that import initialize_models from prediction.py
# will continue to work. The canonical source is model_service.
def initialize_models():
    """Delegates to model_service.initialize()."""
    model_service.initialize()

from . import auth, models as db_models
from fastapi import Depends

@router.post("/admin/reload_models")
def reload_models(current_user: db_models.User = Depends(auth.get_current_user)):
    """Force reload of all models from disk (Zero-Downtime Update). Admin only."""
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    status = model_service.reload()
    return {"status": "Models Reloaded", **{f"{k}_loaded": v["loaded"] for k, v in status["models"].items()}}


@router.get("/admin/models/health")
def models_health_check(current_user: db_models.User = Depends(auth.get_current_user)):
    """Detailed health check for all ML models. Admin only."""
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return model_service.health_check()


PREDICTION_REVIEW_DECISIONS = {"accepted", "overridden", "ignored"}
PREDICTION_REVIEW_TYPES = {"diabetes", "heart", "liver", "kidney", "lungs"}
PREDICTION_REVIEW_CATEGORIES = {
    "administrative",
    "patient_education",
    "clinician_review",
    "clinical_decision_support",
}


def _prediction_patient(db: Session, patient_id: int) -> db_models.User:
    patient = db.query(db_models.User).filter(
        db_models.User.id == patient_id,
        db_models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _doctor_assigned_to_prediction_patient(db: Session, doctor_id: int, patient_id: int) -> bool:
    if not users_share_facility_context(db, doctor_id, patient_id):
        return False
    if db.query(db_models.Encounter).filter(
        db_models.Encounter.patient_id == patient_id,
        db_models.Encounter.doctor_id == doctor_id,
    ).first():
        return True
    if db.query(db_models.Admission).filter(
        db_models.Admission.patient_id == patient_id,
        db_models.Admission.doctor_id == doctor_id,
    ).first():
        return True
    if db.query(db_models.ClinicalOrder).filter(
        db_models.ClinicalOrder.patient_id == patient_id,
        db_models.ClinicalOrder.doctor_id == doctor_id,
    ).first():
        return True
    appointment = db.query(db_models.Appointment).filter(
        db_models.Appointment.user_id == patient_id,
        db_models.Appointment.doctor_id == doctor_id,
    ).first()
    return appointment is not None


def _ensure_prediction_review_access(db: Session, current_user: db_models.User, patient_id: int) -> None:
    if auth.is_admin(current_user):
        return
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")
    if not _doctor_assigned_to_prediction_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")


@router.post("/predict/reviews", status_code=201, response_model=Dict[str, Any])
def record_prediction_review(
    payload: schemas.PredictionReviewCreate,
    db: Session = Depends(database.get_db),
    current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    decision = payload.decision.strip().lower()
    prediction_type = payload.prediction_type.strip().lower()
    use_category = (payload.clinical_use_category or "clinician_review").strip().lower()
    if decision not in PREDICTION_REVIEW_DECISIONS:
        raise HTTPException(status_code=400, detail="Unsupported prediction review decision")
    if prediction_type not in PREDICTION_REVIEW_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported prediction review type")
    if use_category not in PREDICTION_REVIEW_CATEGORIES:
        raise HTTPException(status_code=400, detail="Unsupported prediction review category")

    patient = _prediction_patient(db, payload.patient_id)
    _ensure_prediction_review_access(db, current_user, patient.id)
    audit_entry = audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=patient.id,
        action="REVIEW_AI_PREDICTION",
        details={
            "resource_type": "ai_prediction_review",
            "screening_area": prediction_type,
            "decision": decision,
            "use_category": use_category,
            "model_card_id": payload.model_card_id,
            "prediction_reference_id_present": bool(payload.prediction_reference_id),
            "review_text_present": bool(payload.review_note),
        },
    )
    return {
        "status": "recorded",
        "patient_id": patient.id,
        "reviewed_by_id": current_user.id,
        "prediction_type": prediction_type,
        "decision": decision,
        "clinical_use_category": use_category,
        "audit_event_id": audit_entry.id if audit_entry else None,
    }

# --- Helper Functions for Big Data Mapping ---

def _raise_prediction_failure(model_name: str) -> None:
    logger.error("%s prediction failed", model_name)
    raise HTTPException(status_code=500, detail=PREDICTION_FAILURE_DETAIL)

# --- Prediction Endpoints ---

@router.post("/predict/kidney", response_model=Dict[str, Any])
def predict_kidney(
    data: schemas.KidneyInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    if not model_service.is_available("kidney"):
         raise HTTPException(status_code=503, detail="Kidney Model not trained/loaded.")
    try:
        result = model_service.predict_kidney(data)
        return {"prediction": result.prediction, "raw": result.raw, "confidence": result.confidence, "risk_level": result.risk_level, "disclaimer": result.disclaimer}
    except (ValueError, KeyError, AttributeError, RuntimeError) as exc:
        logger.error("Kidney prediction error: %s", exc)
        _raise_prediction_failure("Kidney")

@router.post("/predict/lungs", response_model=Dict[str, Any])
def predict_lungs(
    data: schemas.LungInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    if not model_service.is_available("lungs"):
         raise HTTPException(status_code=503, detail="Lung Model not trained/loaded.")
    try:
        result = model_service.predict_lungs(data)
        return {"prediction": result.prediction, "raw": result.raw, "confidence": result.confidence, "risk_level": result.risk_level, "disclaimer": result.disclaimer}
    except (ValueError, KeyError, AttributeError, RuntimeError) as exc:
        logger.error("Lung prediction error: %s", exc)
        _raise_prediction_failure("Lung")

@router.post("/predict/diabetes", response_model=Dict[str, Any])
def predict_diabetes(
    data: schemas.DiabetesInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    if not model_service.is_available("diabetes"):
        raise HTTPException(status_code=503, detail="Diabetes Model not available")
    try:
        result = model_service.predict_diabetes(data)
        return {"prediction": result.prediction, "raw": result.raw, "confidence": result.confidence, "risk_level": result.risk_level, "disclaimer": result.disclaimer}
    except (ValueError, KeyError, AttributeError, RuntimeError) as exc:
        logger.error("Diabetes prediction error: %s", exc)
        _raise_prediction_failure("Diabetes")

@router.post("/predict/heart", response_model=Dict[str, Any])
def predict_heart(
    data: schemas.HeartInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    if not model_service.is_available("heart"):
        raise HTTPException(status_code=503, detail="Heart Model not available")
    try:
        result = model_service.predict_heart(data)
        return {"prediction": result.prediction, "raw": result.raw, "confidence": result.confidence, "risk_level": result.risk_level, "disclaimer": result.disclaimer}
    except (ValueError, KeyError, AttributeError, RuntimeError) as exc:
        logger.error("Heart prediction error: %s", exc)
        _raise_prediction_failure("Heart")

@router.post("/predict/liver", response_model=Dict[str, Any])
def predict_liver(
    data: schemas.LiverInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    if not model_service.is_available("liver"):
        raise HTTPException(status_code=503, detail="Liver Model or Scaler not available")
    try:
        result = model_service.predict_liver(data)
        return {"prediction": result.prediction, "raw": result.raw, "confidence": result.confidence, "risk_level": result.risk_level, "disclaimer": result.disclaimer}
    except (ValueError, KeyError, AttributeError, RuntimeError) as exc:
        logger.error("Liver prediction error: %s", exc)
        _raise_prediction_failure("Liver")

# --- Explanation Endpoints (SHAP) ---

@router.post("/predict/explain/diabetes")
def explain_diabetes(
    data: schemas.DiabetesInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
):
    if not model_service.is_available("diabetes"):
        raise HTTPException(status_code=503, detail="Model unavailable")
    explanation = model_service.explain("diabetes", data)
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")

@router.post("/predict/explain/heart")
def explain_heart(
    data: schemas.HeartInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
):
    if not model_service.is_available("heart"):
        raise HTTPException(status_code=503, detail="Model unavailable")
    explanation = model_service.explain("heart", data)
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")

@router.post("/predict/explain/liver")
def explain_liver(
    data: schemas.LiverInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
):
    if not model_service.is_available("liver"):
         raise HTTPException(status_code=503, detail="Model unavailable")
    explanation = model_service.explain("liver", data)
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")
