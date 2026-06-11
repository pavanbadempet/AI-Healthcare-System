import logging
import os  # noqa: F401 — tests patch backend.prediction.os.path.exists
from typing import Any, Dict

import joblib  # noqa: F401 — tests patch backend.prediction.joblib.load
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

# --- Custom Modules ---
from . import audit, database, explainability, schemas
from . import features as _features
from .facility_scope import users_share_facility_context
from .model_service import (  # noqa: F401 — re-exported for backward compat & tests
    MEDICAL_DISCLAIMER,
    PREDICTION_FAILURE_DETAIL,
    _extract_confidence,
    get_age_bucket,
    model_service,
)

# --- Logging Configuration ---
logger = logging.getLogger(__name__)

# --- Router Definition ---
router = APIRouter()

# --- Backward-compatible re-export ---
# External modules that import initialize_models from prediction.py
# will continue to work. The canonical source is model_service.
def initialize_models():
    """Delegates to model_service.initialize() and syncs module-level model attrs."""
    global diabetes_model, heart_model, liver_model, kidney_model, lungs_model
    global liver_scaler, kidney_scaler, lungs_scaler
    model_service.initialize()
    # Sync module-level attributes so legacy code and tests can access them
    diabetes_model = model_service._entries["diabetes"].model
    heart_model = model_service._entries["heart"].model
    liver_model = model_service._entries["liver"].model
    kidney_model = model_service._entries["kidney"].model
    lungs_model = model_service._entries["lungs"].model
    liver_scaler = model_service._entries["liver"].scaler
    kidney_scaler = model_service._entries["kidney"].scaler
    lungs_scaler = model_service._entries["lungs"].scaler


def load_pkl(filenames):
    """Backward-compatible pickle loader used by legacy tests and scripts."""
    model_dir = os.path.dirname(os.path.abspath(__file__))
    for f_name in filenames:
        path = os.path.join(model_dir, f_name)
        if os.path.exists(path):
            try:
                with open(path, "rb") as handle:
                    return joblib.load(handle)
            except Exception:
                logger.error("Failed to load model file %s", f_name)
                return None
    logger.warning("Could not find any of: %s in %s", filenames, model_dir)
    return None


def _get_confidence(model, input_data):
    """Backward-compatible confidence helper."""
    return _extract_confidence(model, input_data)


# Module-level model attributes — populated by initialize_models().
# Tests patch these directly (e.g. patch("backend.prediction.diabetes_model", mock)).
# Routes check these attributes so patches affect route behaviour.
diabetes_model = None
heart_model = None
liver_model = None
kidney_model = None
lungs_model = None
liver_scaler = None
kidney_scaler = None
lungs_scaler = None

from fastapi import Depends

from . import auth
from . import models as db_models


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
    import backend.prediction as _pred
    if _pred.kidney_model is None:
        raise HTTPException(status_code=503, detail="Kidney Model not trained/loaded.")
    try:
        import pandas as pd

        from . import features as _features
        from .model_service import _extract_confidence, _normalize_prediction
        feature_names = _features.KIDNEY_FEATURES
        input_list = [
            data.age, data.bp, data.sg, data.al, data.su,
            data.rbc, data.pc, data.pcc, data.ba,
            data.bgr, data.bu, data.sc, data.sod, data.pot, data.hemo,
            data.pcv, data.wc, data.rc,
            data.htn, data.dm, data.cad, data.appet, data.pe, data.ane
        ]
        df = pd.DataFrame([input_list], columns=feature_names)
        if _pred.kidney_scaler is not None:
            X = _pred.kidney_scaler.transform(df)
        else:
            X = df.values
        raw_pred = _pred.kidney_model.predict(X)
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.kidney_model, X)
        prediction = "Chronic Kidney Disease Detected" if raw == 1 else "Healthy Kidney"
        return {"prediction": prediction, "raw": raw, "confidence": confidence,
                "risk_level": risk_level, "disclaimer": MEDICAL_DISCLAIMER}
    except Exception:
        logger.error("Kidney prediction error")
        _raise_prediction_failure("Kidney")

@router.post("/predict/lungs", response_model=Dict[str, Any])
def predict_lungs(
    data: schemas.LungInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    import backend.prediction as _pred
    if _pred.lungs_model is None:
        raise HTTPException(status_code=503, detail="Lung Model not trained/loaded.")
    try:
        import pandas as pd

        from . import features as _features
        from .model_service import _extract_confidence, _normalize_prediction
        feature_names = _features.LUNG_FEATURES
        input_list = [
            data.gender, data.age, data.smoking, data.yellow_fingers,
            data.anxiety, data.peer_pressure, data.chronic_disease, data.fatigue,
            data.allergy, data.wheezing, data.alcohol, data.coughing,
            data.shortness_of_breath, data.swallowing_difficulty, data.chest_pain
        ]
        df = pd.DataFrame([input_list], columns=feature_names)
        if _pred.lungs_scaler is not None:
            X = _pred.lungs_scaler.transform(df)
        else:
            X = df.values
        raw_pred = _pred.lungs_model.predict(X)
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.lungs_model, X)
        prediction = "Respiratory Issue Detected" if raw == 1 else "Healthy Lungs"
        return {"prediction": prediction, "raw": raw, "confidence": confidence,
                "risk_level": risk_level, "disclaimer": MEDICAL_DISCLAIMER}
    except Exception:
        logger.error("Lung prediction error")
        _raise_prediction_failure("Lung")

@router.post("/predict/diabetes", response_model=Dict[str, Any])
def predict_diabetes(
    data: schemas.DiabetesInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    import backend.prediction as _pred
    if _pred.diabetes_model is None:
        raise HTTPException(status_code=503, detail="Diabetes Model not available")
    try:
        from .model_service import _extract_confidence, _normalize_prediction
        input_list = [
            data.hypertension, data.high_chol, data.bmi, data.smoking_history,
            data.heart_disease, data.physical_activity, data.general_health,
            data.gender, get_age_bucket(data.age)
        ]
        raw_pred = _pred.diabetes_model.predict([input_list])
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.diabetes_model, [input_list])
        prediction = "High Risk" if raw == 1 else "Low Risk"
        return {"prediction": prediction, "raw": raw, "confidence": confidence,
                "risk_level": risk_level, "disclaimer": MEDICAL_DISCLAIMER}
    except Exception:
        logger.error("Diabetes prediction error")
        _raise_prediction_failure("Diabetes")

@router.post("/predict/heart", response_model=Dict[str, Any])
def predict_heart(
    data: schemas.HeartInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    import backend.prediction as _pred
    if _pred.heart_model is None:
        raise HTTPException(status_code=503, detail="Heart Model not available")
    try:
        from .model_service import _extract_confidence, _normalize_prediction
        input_list = [
            data.age, data.sex, data.cp, data.trestbps, data.chol,
            data.fbs, data.restecg, data.thalach, data.exang,
            data.oldpeak, data.slope, data.ca, data.thal
        ]
        raw_pred = _pred.heart_model.predict([input_list])
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.heart_model, [input_list])
        prediction = "Heart Disease Detected" if raw == 1 else "Healthy Heart"
        return {"prediction": prediction, "raw": raw, "confidence": confidence,
                "risk_level": risk_level, "disclaimer": MEDICAL_DISCLAIMER}
    except Exception:
        logger.error("Heart prediction error")
        _raise_prediction_failure("Heart")

@router.post("/predict/liver", response_model=Dict[str, Any])
def predict_liver(
    data: schemas.LiverInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    import backend.prediction as _pred
    if _pred.liver_model is None:
        raise HTTPException(status_code=503, detail="Liver Model or Scaler not available")
    try:
        import numpy as np
        import pandas as pd

        from . import features as _features
        from .model_service import _extract_confidence, _normalize_prediction
        feature_names = _features.LIVER_FEATURES
        input_list = [
            data.age, data.gender, data.total_bilirubin, data.direct_bilirubin,
            data.alkaline_phosphotase, data.alamine_aminotransferase,
            data.aspartate_aminotransferase, data.total_proteins,
            data.albumin, data.albumin_and_globulin_ratio
        ]
        df = pd.DataFrame([input_list], columns=feature_names)
        for col in ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']:
            df[col] = np.log1p(df[col])
        if _pred.liver_scaler is not None:
            X = _pred.liver_scaler.transform(df)
        else:
            X = df.values
        raw_pred = _pred.liver_model.predict(X)
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.liver_model, X)
        prediction = "Liver Disease Detected" if raw == 1 else "Healthy Liver"
        return {"prediction": prediction, "raw": raw, "confidence": confidence,
                "risk_level": risk_level, "disclaimer": MEDICAL_DISCLAIMER}
    except Exception:
        logger.error("Liver prediction error")
        _raise_prediction_failure("Liver")

# --- Explanation Endpoints (SHAP) ---

@router.post("/predict/explain/diabetes")
def explain_diabetes(
    data: schemas.DiabetesInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
):
    import backend.prediction as _pred
    if _pred.diabetes_model is None:
        raise HTTPException(status_code=503, detail="Model unavailable")
    input_list = [
        data.hypertension, data.high_chol, data.bmi, data.smoking_history,
        data.heart_disease, data.physical_activity, data.general_health,
        data.gender, get_age_bucket(data.age)
    ]
    explanation = explainability.get_shap_values(
        _pred.diabetes_model,
        np.array([input_list]),
        _features.DIABETES_FEATURES,
    )
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")

@router.post("/predict/explain/heart")
def explain_heart(
    data: schemas.HeartInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
):
    import backend.prediction as _pred
    if _pred.heart_model is None:
        raise HTTPException(status_code=503, detail="Model unavailable")
    input_list = [
        data.age, data.sex, data.cp, data.trestbps, data.chol,
        data.fbs, data.restecg, data.thalach, data.exang,
        data.oldpeak, data.slope, data.ca, data.thal
    ]
    explanation = explainability.get_shap_values(
        _pred.heart_model,
        np.array([input_list]),
        ['Age', 'Sex', 'ChestPain', 'RestBP', 'Cholesterol', 'FastingBS',
         'RestECG', 'MaxHR', 'ExerciseAngina', 'Oldpeak', 'Slope', 'MajorVessels', 'Thal'],
    )
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")

@router.post("/predict/explain/liver")
def explain_liver(
    data: schemas.LiverInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
):
    import backend.prediction as _pred
    if _pred.liver_model is None or _pred.liver_scaler is None:
        raise HTTPException(status_code=503, detail="Model unavailable")
    input_list = [
        data.age, data.gender, data.total_bilirubin, data.direct_bilirubin,
        data.alkaline_phosphotase, data.alamine_aminotransferase,
        data.aspartate_aminotransferase, data.total_proteins,
        data.albumin, data.albumin_and_globulin_ratio
    ]
    df = pd.DataFrame([input_list], columns=_features.LIVER_FEATURES)
    for col in ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']:
        df[col] = np.log1p(df[col])
    explanation = explainability.get_shap_values(
        _pred.liver_model,
        _pred.liver_scaler.transform(df),
        _features.LIVER_FEATURES,
    )
    if explanation: return explanation
    raise HTTPException(status_code=500, detail="Explanation Generation Failed")
