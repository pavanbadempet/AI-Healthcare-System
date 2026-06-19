import logging
import os  # noqa: F401 — tests patch backend.prediction.os.path.exists
from typing import Any, Dict, Optional

import joblib  # noqa: F401 — tests patch backend.prediction.joblib.load
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

# --- Custom Modules ---
from . import audit, database, explainability, schemas
from . import features as _features
from .clinical_indices import (
    calculate_egfr_ckd_epi,
    calculate_fib4_index,
    calculate_framingham_risk,
)
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


def _get_imputer_and_conformal(model_name: str, current_model_obj: Any):
    """
    Helper to retrieve the MICE imputer and conformal prediction threshold
    associated with the given model name, maintaining compatibility with tests.
    """
    entry = model_service._entries.get(model_name)
    if entry and entry.model is current_model_obj:
        return entry.imputer, entry.conformal_q
    return None, None


def _calculate_conformal_prediction(proba_positive: float, conformal_q: Any):
    """
    Calculates the conformal prediction set at 95% confidence and the uncertainty status.
    Supports both a float (marginal threshold) and a dictionary (class-conditional thresholds).
    """
    p0 = 1.0 - proba_positive
    p1 = proba_positive
    
    prediction_set = []
    if isinstance(conformal_q, dict):
        q0 = conformal_q.get(0, conformal_q.get("0", 0.0))
        q1 = conformal_q.get(1, conformal_q.get("1", 0.0))
        if p0 >= 1.0 - q0:
            prediction_set.append(0)
        if p1 >= 1.0 - q1:
            prediction_set.append(1)
    else:
        threshold = 1.0 - (conformal_q or 0.0)
        if p0 >= threshold:
            prediction_set.append(0)
        if p1 >= threshold:
            prediction_set.append(1)
        
    if len(prediction_set) == 1:
        uncertainty_status = "Low Uncertainty"
    elif len(prediction_set) > 1:
        uncertainty_status = "High Uncertainty (Ambiguous Case)"
    else:
        uncertainty_status = "High Uncertainty (Out-of-Distribution Case)"
        
    return {
        "conformal_prediction_set": prediction_set,
        "significance_level": 0.05,
        "uncertainty_status": uncertainty_status
    }


def _get_triage_recommendation(prediction_val: int, conformal_set: list) -> str:
    """
    Translates conformal prediction sets and raw predictions into actionable clinician guidance.
    """
    if conformal_set == [1]:
        return "Urgent Action: Patient exhibits strong canonical markers. Initiate standard treatment protocols."
    elif conformal_set == [0]:
        return "Routine Monitoring: Patient is within normal parameters. Re-evaluate at next routine visit."
    elif len(conformal_set) > 1:
        return "Clinical Triage: Borderline case. Schedule a follow-up test or refer to a specialist."
    else:  # empty set
        return "Secondary Review: Patient presents with unusual clinical features not well-represented in training. Perform manual chart review."


def _get_top_risk_factors(model: Any, imputed_list: list, feature_names: list) -> list:
    """
    Returns a sorted list of top clinical risk factors based on local SHAP feature contributions.
    """
    try:
        import shap
    except ImportError:
        return []
        
    try:
        # Strategy: Unwrap model to find a tree-based estimator for fast TreeExplainer
        target_estimator = model
        if hasattr(model, 'estimators_'):
            # First member is XGBoost / Calibrated XGBoost in our train pipelines
            target_estimator = model.estimators_[0]
            
        if hasattr(target_estimator, 'calibrated_classifiers_') and len(target_estimator.calibrated_classifiers_) > 0:
            target_estimator = target_estimator.calibrated_classifiers_[0].estimator
        elif hasattr(target_estimator, 'estimator'):
            target_estimator = target_estimator.estimator
            
        # Bypass deep learning model TabPFN since it doesn't support TreeExplainer
        if "TabPFNClassifier" in str(type(target_estimator)):
            return ["Deep Attention Model: Tabular transformer predictions are computed via in-context attention over similar patients."]
            
        input_vector = np.array([imputed_list])
        explainer = shap.TreeExplainer(target_estimator)
        shap_values = explainer.shap_values(input_vector)
        
        # Handle different SHAP version output shapes
        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif len(shap_values.shape) == 3:  # (nsamples, nfeatures, nclasses)
            sv = shap_values[0, :, 1]
        elif len(shap_values.shape) == 2:
            sv = shap_values[0]
        else:
            sv = shap_values
            
        # Create list of (feature_name, shap_value)
        contributions = []
        for feat, val in zip(feature_names, sv):
            contributions.append((feat, float(val)))
            
        # Sort by absolute SHAP value descending (largest impact first)
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # Format as readable strings
        top_factors = []
        for feat, val in contributions[:3]:
            direction = "increases risk" if val > 0 else "decreases risk"
            display_name = feat.replace('_', ' ').title()
            top_factors.append(f"{display_name} ({direction})")
            
        return top_factors
    except Exception:
        return []


def _get_model_metadata(model_name: str, current_model_obj: Any) -> dict:
    """
    Helper to retrieve model provenance metadata (version, training timestamp, model card id)
    associated with the given model, maintaining compatibility and safety.
    """
    entry = model_service._entries.get(model_name)
    version = "2.1.0-extratrees"
    timestamp = "2026-06-18T00:00:00"
    model_card_id = f"card-{model_name}-v2"
    
    if entry and entry.model is current_model_obj:
        version = getattr(entry, "model_version", version)
        timestamp = getattr(entry, "training_timestamp", timestamp)
        model_card_id = getattr(entry, "model_card_id", model_card_id)
        
    return {
        "model_version": version,
        "training_timestamp": timestamp,
        "model_card_id": model_card_id
    }


def _calculate_clinical_recourse(
    model_name: str,
    model_obj: Any,
    imputed_list: list,
    current_prob: float,
    scaler: Any = None
) -> Optional[str]:
    """
    Simulates a counterfactual 'what-if' patient profile by searching combinations of 
    controllable lifestyle features to find the optimal risk reduction path.
    """
    try:
        if current_prob < 0.5:
            # Recourse is only relevant for high-risk patients
            return None
            
        import itertools
        import pandas as pd
        import numpy as np

        # Define candidate modifications per model: (index, check_fn, target_value, description)
        candidates = {
            "diabetes": [
                (0, lambda val: val == 1.0, 0.0, "managing hypertension"),
                (3, lambda val: val == 1.0, 0.0, "smoking cessation"),
                (5, lambda val: val == 0.0, 1.0, "increasing physical activity"),
            ],
            "heart": [
                (5, lambda val: val == 1.0, 0.0, "managing blood sugar"),
                (10, lambda val: val == 1.0, 0.0, "abstaining from heavy alcohol"),
                (7, lambda val: val is not None and val < 120.0, 150.0, "increasing physical activity"),
            ],
            "kidney": [
                (1, lambda val: val is not None and val > 120.0, 120.0, "controlling blood pressure to 120 mmHg"),
                (18, lambda val: val == 1, 0, "managing hypertension"),
                (19, lambda val: val == 1, 0, "managing diabetes"),
            ],
            "lungs": [
                (2, lambda val: val == 2.0, 1.0, "smoking cessation"),
                (10, lambda val: val == 2.0, 1.0, "abstaining from alcohol"),
            ],
            "liver": []  # Lab values are not lifestyle controllable
        }.get(model_name, [])

        applicable = []
        for index, check_fn, target_val, desc in candidates:
            if index < len(imputed_list) and check_fn(imputed_list[index]):
                applicable.append((index, target_val, desc))

        if not applicable:
            return "Patient has no standard controllable lifestyle risk factors to modify."

        best_combination = None
        best_proba = current_prob
        best_reduction = 0.0
        successful_combinations = []

        # Evaluate all subsets of combinations
        for r in range(1, len(applicable) + 1):
            for comb in itertools.combinations(applicable, r):
                test_profile = list(imputed_list)
                for index, target_val, desc in comb:
                    test_profile[index] = target_val
                
                if model_name in ("kidney", "liver", "lungs"):
                    from . import features as _feat
                    feat_names = {
                        "kidney": _feat.KIDNEY_FEATURES,
                        "liver": _feat.LIVER_FEATURES,
                        "lungs": _feat.LUNG_FEATURES
                    }[model_name]
                    df_rec = pd.DataFrame([test_profile], columns=feat_names)
                    if scaler is not None:
                        X_rec = scaler.transform(df_rec)
                    else:
                        X_rec = df_rec.values
                else:
                    X_rec = [test_profile]

                proba_rec = model_obj.predict_proba(X_rec)[0]
                prob_pos_rec = float(proba_rec[1]) if len(proba_rec) > 1 else float(proba_rec[0])
                reduction = current_prob - prob_pos_rec

                if reduction > best_reduction:
                    best_reduction = reduction
                    best_proba = prob_pos_rec
                    best_combination = comb

                if prob_pos_rec < 0.5:
                    successful_combinations.append((comb, prob_pos_rec, reduction))

        if best_reduction <= 0.01:
            return "Lifestyle modifications alone show minimal expected risk reduction for this patient's profile."

        # If some combinations successfully bring predicted risk below 50%:
        # Pick the smallest combination (fewest lifestyle changes required).
        # In case of ties, pick the one with the highest risk reduction.
        if successful_combinations:
            successful_combinations.sort(key=lambda x: (len(x[0]), -x[2]))
            optimal_comb, optimal_proba, optimal_reduction = successful_combinations[0]
            descs = [item[2] for item in optimal_comb]
            actions = ", ".join(descs[:-1]) + " and " + descs[-1] if len(descs) > 1 else descs[0]
            return f"Managing risk through {actions} could potentially reduce risk probability by {optimal_reduction * 100:.1f}%, bringing predicted risk below the threshold to {optimal_proba * 100:.1f}%."
        else:
            descs = [item[2] for item in best_combination]
            actions = ", ".join(descs[:-1]) + " and " + descs[-1] if len(descs) > 1 else descs[0]
            return f"Although additional clinical intervention may be required, adopting {actions} could potentially reduce risk probability by {best_reduction * 100:.1f}% (predicted risk: {best_proba * 100:.1f}%)."
    except Exception as e:
        logger.warning("Recourse calculation failed: %s", e)
        return None


async def _generate_clinical_narrative(
    model_name: str,
    prediction: str,
    confidence: float,
    risk_level: str,
    clinical_indices: dict
) -> str:
    """
    Generates a natural-language clinical narrative report summarizing prediction,
    conformal uncertainty, SHAP risk factors, and counterfactual recourse.
    """
    try:
        from .core_ai import generate
        from .prompt_registry import get_prompt
        
        template = get_prompt("clinical_narrative")
        prompt = template.format(
            disease=model_name.upper(),
            prediction=prediction,
            confidence=f"{confidence:.1f}" if isinstance(confidence, (int, float)) else str(confidence),
            risk_level=risk_level,
            uncertainty_status=clinical_indices.get("uncertainty_status", "N/A"),
            conformal_set=str(clinical_indices.get("conformal_prediction_set", [])),
            triage_recommendation=clinical_indices.get("triage_recommendation", "N/A"),
            top_risk_factors=str(clinical_indices.get("top_risk_factors", "N/A")),
            clinical_recourse=clinical_indices.get("clinical_recourse", "N/A")
        )
        narrative = await generate(
            prompt=prompt,
            system="You are an expert clinical artificial intelligence assistant. Output only the requested clinical summary."
        )
        return narrative.strip()
    except Exception as e:
        logger.warning("Failed to generate clinical narrative for %s: %s", model_name, e)
        return "Clinical analysis narrative is currently unavailable."





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
async def predict_kidney(
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
        
        imputer, conformal_q = _get_imputer_and_conformal("kidney", _pred.kidney_model)
        if imputer is not None:
            imputed_arr = imputer.transform([input_list])
            imputed_list = imputed_arr[0].tolist()
        else:
            imputed_list = [0.0 if x is None else x for x in input_list]

        df = pd.DataFrame([imputed_list], columns=feature_names)
        if _pred.kidney_scaler is not None:
            X = _pred.kidney_scaler.transform(df)
        else:
            X = df.values
        raw_pred = _pred.kidney_model.predict(X)
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.kidney_model, X)
        prediction = "Chronic Kidney Disease Detected" if raw == 1 else "Healthy Kidney"

        # Extract imputed values for clinical indices
        imputed_age = imputed_list[0]
        imputed_sc = imputed_list[11]

        # Calculate clinical domain indices
        egfr_data = calculate_egfr_ckd_epi(imputed_age, data.gender or 1, imputed_sc)
        clinical_indices = {"egfr": egfr_data} if egfr_data else {}

        # Calculate Conformal prediction set & Explainability
        proba_pos = None
        try:
            proba = _pred.kidney_model.predict_proba(X)[0]
            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as e:
            logger.warning("Predict proba failed for Kidney: %s", e)

        if proba_pos is not None:
            if conformal_q is not None:
                try:
                    conformal_metrics = _calculate_conformal_prediction(proba_pos, conformal_q)
                    
                    # Add Triage recommendation
                    triage = _get_triage_recommendation(raw, conformal_metrics["conformal_prediction_set"])
                    conformal_metrics["triage_recommendation"] = triage
                    
                    # Add Top Risk Factors
                    top_factors = _get_top_risk_factors(_pred.kidney_model, imputed_list, feature_names)
                    if top_factors:
                        conformal_metrics["top_risk_factors"] = top_factors
                    
                    clinical_indices.update(conformal_metrics)
                except Exception as e:
                    logger.warning("Conformal prediction calculation failed for Kidney: %s", e)

            recourse = _calculate_clinical_recourse(
                "kidney",
                _pred.kidney_model,
                imputed_list,
                proba_pos,
                _pred.kidney_scaler
            )
            if recourse:
                clinical_indices["clinical_recourse"] = recourse

        model_metadata = _get_model_metadata("kidney", _pred.kidney_model)
        narrative = await _generate_clinical_narrative(
            "kidney", prediction, confidence, risk_level, clinical_indices
        )
        return {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative
        }
    except Exception:
        logger.error("Kidney prediction error")
        _raise_prediction_failure("Kidney")

@router.post("/predict/lungs", response_model=Dict[str, Any])
async def predict_lungs(
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
        
        imputer, conformal_q = _get_imputer_and_conformal("lungs", _pred.lungs_model)
        if imputer is not None:
            imputed_arr = imputer.transform([input_list])
            imputed_list = imputed_arr[0].tolist()
        else:
            imputed_list = [0.0 if x is None else x for x in input_list]

        df = pd.DataFrame([imputed_list], columns=feature_names)
        if _pred.lungs_scaler is not None:
            X = _pred.lungs_scaler.transform(df)
        else:
            X = df.values
        raw_pred = _pred.lungs_model.predict(X)
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.lungs_model, X)
        prediction = "Respiratory Issue Detected" if raw == 1 else "Healthy Lungs"
        
        clinical_indices = {}
        proba_pos = None
        try:
            proba = _pred.lungs_model.predict_proba(X)[0]
            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as e:
            logger.warning("Predict proba failed for Lungs: %s", e)

        if proba_pos is not None:
            if conformal_q is not None:
                try:
                    conformal_metrics = _calculate_conformal_prediction(proba_pos, conformal_q)
                    
                    # Add Triage recommendation
                    triage = _get_triage_recommendation(raw, conformal_metrics["conformal_prediction_set"])
                    conformal_metrics["triage_recommendation"] = triage
                    
                    # Add Top Risk Factors
                    top_factors = _get_top_risk_factors(_pred.lungs_model, imputed_list, feature_names)
                    if top_factors:
                        conformal_metrics["top_risk_factors"] = top_factors
                    
                    clinical_indices.update(conformal_metrics)
                except Exception as e:
                    logger.warning("Conformal prediction calculation failed for Lungs: %s", e)

            recourse = _calculate_clinical_recourse(
                "lungs",
                _pred.lungs_model,
                imputed_list,
                proba_pos,
                _pred.lungs_scaler
            )
            if recourse:
                clinical_indices["clinical_recourse"] = recourse

        model_metadata = _get_model_metadata("lungs", _pred.lungs_model)
        narrative = await _generate_clinical_narrative(
            "lungs", prediction, confidence, risk_level, clinical_indices
        )
        res = {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative
        }
        return res
    except Exception:
        logger.error("Lung prediction error")
        _raise_prediction_failure("Lung")

@router.post("/predict/diabetes", response_model=Dict[str, Any])
async def predict_diabetes(
    data: schemas.DiabetesInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    import backend.prediction as _pred
    if _pred.diabetes_model is None:
        raise HTTPException(status_code=503, detail="Diabetes Model not available")
    try:
        from .model_service import _extract_confidence, _normalize_prediction
        
        age_bucket = get_age_bucket(data.age) if data.age is not None else None
        input_list = [
            data.hypertension, data.high_chol, data.bmi, data.smoking_history,
            data.heart_disease, data.physical_activity, data.general_health,
            data.gender, age_bucket
        ]
        
        imputer, conformal_q = _get_imputer_and_conformal("diabetes", _pred.diabetes_model)
        if imputer is not None:
            imputed_arr = imputer.transform([input_list])
            imputed_list = imputed_arr[0].tolist()
        else:
            imputed_list = [0.0 if x is None else x for x in input_list]

        raw_pred = _pred.diabetes_model.predict([imputed_list])
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.diabetes_model, [imputed_list])
        prediction = "High Risk" if raw == 1 else "Low Risk"
        
        clinical_indices = {}
        proba_pos = None
        try:
            proba = _pred.diabetes_model.predict_proba([imputed_list])[0]
            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as e:
            logger.warning("Predict proba failed for Diabetes: %s", e)

        if proba_pos is not None:
            if conformal_q is not None:
                try:
                    conformal_metrics = _calculate_conformal_prediction(proba_pos, conformal_q)
                    
                    # Add Triage recommendation
                    triage = _get_triage_recommendation(raw, conformal_metrics["conformal_prediction_set"])
                    conformal_metrics["triage_recommendation"] = triage
                    
                    # Add Top Risk Factors
                    top_factors = _get_top_risk_factors(_pred.diabetes_model, imputed_list, _features.DIABETES_FEATURES)
                    if top_factors:
                        conformal_metrics["top_risk_factors"] = top_factors
                    
                    clinical_indices.update(conformal_metrics)
                except Exception as e:
                    logger.warning("Conformal prediction calculation failed for Diabetes: %s", e)

            recourse = _calculate_clinical_recourse(
                "diabetes",
                _pred.diabetes_model,
                imputed_list,
                proba_pos,
                None
            )
            if recourse:
                clinical_indices["clinical_recourse"] = recourse

        model_metadata = _get_model_metadata("diabetes", _pred.diabetes_model)
        narrative = await _generate_clinical_narrative(
            "diabetes", prediction, confidence, risk_level, clinical_indices
        )
        res = {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative
        }
        return res
    except Exception:
        logger.error("Diabetes prediction error")
        _raise_prediction_failure("Diabetes")

@router.post("/predict/heart", response_model=Dict[str, Any])
async def predict_heart(
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
        
        imputer, conformal_q = _get_imputer_and_conformal("heart", _pred.heart_model)
        if imputer is not None:
            imputed_arr = imputer.transform([input_list])
            imputed_list = imputed_arr[0].tolist()
        else:
            imputed_list = [0.0 if x is None else x for x in input_list]

        raw_pred = _pred.heart_model.predict([imputed_list])
        raw = _normalize_prediction(raw_pred)
        confidence, risk_level = _extract_confidence(_pred.heart_model, [imputed_list])
        prediction = "Heart Disease Detected" if raw == 1 else "Healthy Heart"

        # Extract imputed values for clinical indices
        imputed_age = imputed_list[0]
        imputed_sex = imputed_list[1]
        imputed_chol = imputed_list[4]
        imputed_fbs = imputed_list[5]
        imputed_trestbps = imputed_list[3]

        # Calculate clinical domain indices
        framingham_data = calculate_framingham_risk(
            age=imputed_age,
            gender=imputed_sex,
            total_chol=imputed_chol,
            hdl_chol=data.hdl if data.hdl is not None else 50.0,
            sbp=imputed_trestbps,
            smoker=data.smoker if data.smoker is not None else 0,
            diabetes=int(imputed_fbs),
            hyp_treatment=data.hyp_treatment if data.hyp_treatment is not None else 0
        )
        clinical_indices = {"framingham_risk": framingham_data} if framingham_data else {}

        proba_pos = None
        try:
            proba = _pred.heart_model.predict_proba([imputed_list])[0]
            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as e:
            logger.warning("Predict proba failed for Heart: %s", e)

        if proba_pos is not None:
            if conformal_q is not None:
                try:
                    conformal_metrics = _calculate_conformal_prediction(proba_pos, conformal_q)
                    
                    # Add Triage recommendation
                    triage = _get_triage_recommendation(raw, conformal_metrics["conformal_prediction_set"])
                    conformal_metrics["triage_recommendation"] = triage
                    
                    # Add Top Risk Factors
                    top_factors = _get_top_risk_factors(_pred.heart_model, imputed_list, _features.HEART_FEATURES)
                    if top_factors:
                        conformal_metrics["top_risk_factors"] = top_factors
                    
                    clinical_indices.update(conformal_metrics)
                except Exception as e:
                    logger.warning("Conformal prediction calculation failed for Heart: %s", e)

            recourse = _calculate_clinical_recourse(
                "heart",
                _pred.heart_model,
                imputed_list,
                proba_pos,
                None
            )
            if recourse:
                clinical_indices["clinical_recourse"] = recourse

        model_metadata = _get_model_metadata("heart", _pred.heart_model)
        narrative = await _generate_clinical_narrative(
            "heart", prediction, confidence, risk_level, clinical_indices
        )
        return {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative
        }
    except Exception:
        logger.error("Heart prediction error")
        _raise_prediction_failure("Heart")

@router.post("/predict/liver", response_model=Dict[str, Any])
async def predict_liver(
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
        
        imputer, conformal_q = _get_imputer_and_conformal("liver", _pred.liver_model)
        if imputer is not None:
            imputed_arr = imputer.transform([input_list])
            imputed_list = imputed_arr[0].tolist()
        else:
            imputed_list = [0.0 if x is None else x for x in input_list]

        df = pd.DataFrame([imputed_list], columns=feature_names)
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

        # Extract imputed values for clinical indices
        imputed_age = imputed_list[0]
        imputed_ast = imputed_list[6]
        imputed_alt = imputed_list[5]

        # Calculate clinical domain indices
        fib4_data = calculate_fib4_index(
            age=imputed_age,
            ast=imputed_ast,
            alt=imputed_alt,
            platelets=data.platelets if data.platelets is not None else 250.0
        )
        clinical_indices = {"fib4": fib4_data} if fib4_data else {}

        proba_pos = None
        try:
            proba = _pred.liver_model.predict_proba(X)[0]
            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as e:
            logger.warning("Predict proba failed for Liver: %s", e)

        if proba_pos is not None:
            if conformal_q is not None:
                try:
                    conformal_metrics = _calculate_conformal_prediction(proba_pos, conformal_q)
                    
                    # Add Triage recommendation
                    triage = _get_triage_recommendation(raw, conformal_metrics["conformal_prediction_set"])
                    conformal_metrics["triage_recommendation"] = triage
                    
                    # Add Top Risk Factors
                    top_factors = _get_top_risk_factors(_pred.liver_model, imputed_list, feature_names)
                    if top_factors:
                        conformal_metrics["top_risk_factors"] = top_factors
                    
                    clinical_indices.update(conformal_metrics)
                except Exception as e:
                    logger.warning("Conformal prediction calculation failed for Liver: %s", e)

            recourse = _calculate_clinical_recourse(
                "liver",
                _pred.liver_model,
                imputed_list,
                proba_pos,
                _pred.liver_scaler
            )
            if recourse:
                clinical_indices["clinical_recourse"] = recourse

        model_metadata = _get_model_metadata("liver", _pred.liver_model)
        narrative = await _generate_clinical_narrative(
            "liver", prediction, confidence, risk_level, clinical_indices
        )
        return {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative
        }
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


@router.get("/predict/organ_health/{patient_id}", response_model=Dict[str, Any])
async def predict_organ_health(
    patient_id: int,
    db: Session = Depends(database.get_db),
    _current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    """Calculate a patient's Unified Multi-Organ Health Index based on their vitals and demographics."""
    from datetime import datetime

    import numpy as np
    import pandas as pd

    import backend.prediction as _pred

    from . import features as _features

    # 1. Fetch patient
    patient = db.query(db_models.User).filter(db_models.User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 2. Get vitals
    latest_vital = (
        db.query(db_models.VitalObservation)
        .filter(db_models.VitalObservation.patient_id == patient_id)
        .order_by(db_models.VitalObservation.observed_at.desc())
        .first()
    )

    vitals_source = "latest_observation" if latest_vital else "baseline_fallback"
    heart_rate = float(latest_vital.heart_rate) if latest_vital and latest_vital.heart_rate is not None else 72.0
    systolic_bp = float(latest_vital.systolic_bp) if latest_vital and latest_vital.systolic_bp is not None else 120.0
    diastolic_bp = float(latest_vital.diastolic_bp) if latest_vital and latest_vital.diastolic_bp is not None else 80.0
    spo2 = float(latest_vital.spo2) if latest_vital and latest_vital.spo2 is not None else 98.0
    temp = float(latest_vital.temperature_c) if latest_vital and latest_vital.temperature_c is not None else 36.8
    resp_rate = float(latest_vital.respiratory_rate) if latest_vital and latest_vital.respiratory_rate is not None else 14.0

    # 2.5 Get laboratory results from patient clinical history
    import re
    labs = db.query(db_models.DiagnosticResult).filter(db_models.DiagnosticResult.patient_id == patient_id).all()

    # Default laboratory values
    serum_creatinine = 1.0
    blood_urea = 40.0
    total_bilirubin = 1.0
    direct_bilirubin = 0.3
    alt_val = 30.0
    ast_val = 30.0
    labs_extracted = False

    def extract_lab_value(text, pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    for lab in labs:
        combined_text = f"{lab.title or ''} {lab.summary or ''}"

        c_val = extract_lab_value(combined_text, r'creatinine\s*[:=]\s*([0-9.]+)')
        if c_val is not None:
            serum_creatinine = c_val
            labs_extracted = True

        bu_val = extract_lab_value(combined_text, r'(?:blood urea(?: nitrogen)?|bun)\s*[:=]\s*([0-9.]+)')
        if bu_val is not None:
            blood_urea = bu_val
            labs_extracted = True

        tb_val = extract_lab_value(combined_text, r'total bilirubin\s*[:=]\s*([0-9.]+)')
        if tb_val is not None:
            total_bilirubin = tb_val
            labs_extracted = True

        db_val = extract_lab_value(combined_text, r'direct bilirubin\s*[:=]\s*([0-9.]+)')
        if db_val is not None:
            direct_bilirubin = db_val
            labs_extracted = True

        alt_e = extract_lab_value(combined_text, r'(?:alt|alamine aminotransferase)\s*[:=]\s*([0-9.]+)')
        if alt_e is not None:
            alt_val = alt_e
            labs_extracted = True

        ast_e = extract_lab_value(combined_text, r'(?:ast|aspartate aminotransferase)\s*[:=]\s*([0-9.]+)')
        if ast_e is not None:
            ast_val = ast_e
            labs_extracted = True

    labs_source = "clinical_history" if labs_extracted else "baseline_fallback"

    # 3. Demographics & Lifestyle
    gender_str = (patient.gender or "female").strip().lower()
    is_male_num = 1 if gender_str in ["male", "m"] else 0

    # Calculate age
    age = 45
    dob_str = patient.dob
    if dob_str:
        try:
            birth_date = datetime.fromisoformat(dob_str)
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            age = max(1, min(120, age))
        except Exception:
            try:
                age = datetime.now().year - int(dob_str[:4])
                age = max(1, min(120, age))
            except Exception:
                pass

    # 4. Predict Organ Risks

    # --- Heart Risk ---
    if _pred.heart_model is not None:
        try:
            # heart features: [age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]
            heart_input = [float(age), float(is_male_num), 0.0, float(systolic_bp), 200.0, 0.0, 0.0, float(heart_rate), 0.0, 0.0, 1.0, 0.0, 2.0]
            if hasattr(_pred.heart_model, "predict_proba"):
                heart_prob = float(_pred.heart_model.predict_proba([heart_input])[0][1])
            else:
                raw_pred = _pred.heart_model.predict([heart_input])[0]
                heart_prob = 0.85 if raw_pred == 1 else 0.15
        except Exception:
            heart_prob = 0.15
    else:
        # fallback heuristic
        heart_prob = 0.12
        if heart_rate > 100: heart_prob += 0.25
        if systolic_bp > 140: heart_prob += 0.20

    # --- Lungs Risk ---
    if _pred.lungs_model is not None:
        try:
            # lungs features: gender, age, smoking, yellow_fingers, anxiety, peer_pressure, chronic_disease, fatigue,
            # allergy, wheezing, alcohol, coughing, shortness_of_breath, swallowing_difficulty, chest_pain
            # mapped: 2 for YES / 1 for NO
            fatigue_val = 2 if spo2 < 95.0 else 1
            wheezing_val = 2 if resp_rate > 20.0 else 1
            coughing_val = 2 if resp_rate > 18.0 else 1
            sob_val = 2 if spo2 < 94.0 or resp_rate > 22.0 else 1
            chest_pain_val = 2 if spo2 < 92.0 else 1

            lungs_input = [
                is_male_num, age, 1, 1, 1, 1, 1, fatigue_val, 1, wheezing_val, 1, coughing_val, sob_val, 1, chest_pain_val
            ]
            df_lungs = pd.DataFrame([lungs_input], columns=_features.LUNG_FEATURES)
            if _pred.lungs_scaler is not None:
                X_lungs = _pred.lungs_scaler.transform(df_lungs)
            else:
                X_lungs = df_lungs.values

            if hasattr(_pred.lungs_model, "predict_proba"):
                lungs_prob = float(_pred.lungs_model.predict_proba(X_lungs)[0][1])
            else:
                raw_pred = _pred.lungs_model.predict(X_lungs)[0]
                lungs_prob = 0.85 if raw_pred == 1 else 0.15
        except Exception:
            lungs_prob = 0.15
    else:
        # fallback heuristic
        lungs_prob = 0.08
        if spo2 < 95.0: lungs_prob += 0.35
        if resp_rate > 20.0: lungs_prob += 0.20

    # --- Kidney Risk ---
    if _pred.kidney_model is not None:
        try:
            # kidney features: age, bp, sg, al, su, rbc, pc, pcc, ba, bgr, bu, sc, sod, pot, hemo, pcv, wc, rc, htn, dm, cad, appet, pe, ane
            htn_val = 1 if systolic_bp > 140.0 else 0
            kidney_input = [
                float(age), float(systolic_bp), 1.020, 0.0, 0.0,
                1.0, 1.0, 0.0, 0.0,  # rbc=normal, pc=normal, pcc=notpresent, ba=notpresent
                120.0, float(blood_urea), float(serum_creatinine), 138.0, 4.0, 15.0,  # bgr, bu, sc, sod, pot, hemo
                44.0, 8000.0, 5.2,  # pcv, wc, rc
                float(htn_val), 0.0, 0.0, 0.0, 0.0, 0.0  # htn, dm, cad, appet=good, pe, ane
            ]
            df_kidney = pd.DataFrame([kidney_input], columns=_features.KIDNEY_FEATURES)
            if _pred.kidney_scaler is not None:
                X_kidney = _pred.kidney_scaler.transform(df_kidney)
            else:
                X_kidney = df_kidney.values

            if hasattr(_pred.kidney_model, "predict_proba"):
                kidney_prob = float(_pred.kidney_model.predict_proba(X_kidney)[0][1])
            else:
                raw_pred = _pred.kidney_model.predict(X_kidney)[0]
                kidney_prob = 0.85 if raw_pred == 1 else 0.15
        except Exception:
            kidney_prob = 0.10
    else:
        # fallback
        kidney_prob = 0.05
        if systolic_bp > 150.0: kidney_prob += 0.20

    # --- Diabetes Risk ---
    if _pred.diabetes_model is not None:
        try:
            # diabetes features: [hypertension, high_chol, bmi, smoking_history, heart_disease, physical_activity, general_health, gender, age_bucket]
            htn_val = 1 if systolic_bp > 140.0 or diastolic_bp > 90.0 else 0
            bmi_val = 24.5
            if patient.height and patient.weight:
                try:
                    bmi_val = float(patient.weight) / ((float(patient.height) / 100.0) ** 2)
                except Exception:
                    pass
            active_val = 1 if patient.activity_level and "active" in str(patient.activity_level).lower() else 0

            diabetes_input = [
                float(htn_val), 0.0, float(bmi_val), 0.0,
                0.0, float(active_val), 4.0, float(is_male_num), float(get_age_bucket(age))
            ]
            if hasattr(_pred.diabetes_model, "predict_proba"):
                diabetes_prob = float(_pred.diabetes_model.predict_proba([diabetes_input])[0][1])
            else:
                raw_pred = _pred.diabetes_model.predict([diabetes_input])[0]
                diabetes_prob = 0.85 if raw_pred == 1 else 0.15
        except Exception:
            diabetes_prob = 0.15
    else:
        # fallback
        diabetes_prob = 0.10
        if patient.weight and patient.height:
            try:
                bmi = float(patient.weight) / ((float(patient.height) / 100.0) ** 2)
                if bmi > 28: diabetes_prob += 0.25
            except Exception:
                pass

    # --- Liver Risk ---
    if _pred.liver_model is not None:
        try:
            # liver features: age, gender, total_bilirubin, direct_bilirubin, alkaline_phosphotase, alamine_aminotransferase, aspartate_aminotransferase, total_proteins, albumin, albumin_and_globulin_ratio
            liver_input = [
                float(age), float(is_male_num), float(total_bilirubin), float(direct_bilirubin),
                180.0, float(alt_val), float(ast_val), 6.5,
                3.5, 1.1
            ]
            df_liver = pd.DataFrame([liver_input], columns=_features.LIVER_FEATURES)
            for col in ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']:
                df_liver[col] = np.log1p(df_liver[col])
            if _pred.liver_scaler is not None:
                X_liver = _pred.liver_scaler.transform(df_liver)
            else:
                X_liver = df_liver.values

            if hasattr(_pred.liver_model, "predict_proba"):
                liver_prob = float(_pred.liver_model.predict_proba(X_liver)[0][1])
            else:
                raw_pred = _pred.liver_model.predict(X_liver)[0]
                liver_prob = 0.85 if raw_pred == 1 else 0.15
        except Exception:
            liver_prob = 0.10
    else:
        # fallback
        liver_prob = 0.08

    # Ensure all risk values are clipped between 0.01 and 0.99
    heart_prob = max(0.01, min(0.99, heart_prob))
    lungs_prob = max(0.01, min(0.99, lungs_prob))
    kidney_prob = max(0.01, min(0.99, kidney_prob))
    diabetes_prob = max(0.01, min(0.99, diabetes_prob))
    liver_prob = max(0.01, min(0.99, liver_prob))

    # Calculate Unified Health Index: 100 minus weighted risk
    health_index = 100.0 - (
        0.25 * heart_prob +
        0.20 * lungs_prob +
        0.20 * kidney_prob +
        0.15 * diabetes_prob +
        0.20 * liver_prob
    ) * 100.0
    health_index = max(1.0, min(100.0, health_index))

    # Determine status matching
    def get_risk_status(prob):
        if prob > 0.65: return "Critical"
        if prob > 0.40: return "Guarded"
        if prob > 0.20: return "Elevated"
        return "Stable"

    # Generate Recommended Clinical Orders based on risks
    recommended_orders = []
    if heart_prob > 0.40:
        recommended_orders.append({
            "order_type": "lab",
            "title": "Serum Troponin and CK-MB Panel",
            "reason": "Elevated cardiovascular risk profile detected."
        })
        recommended_orders.append({
            "order_type": "diagnostic",
            "title": "12-Lead Electrocardiogram (ECG)",
            "reason": "Rule out active arrhythmia or ischemia."
        })
    if lungs_prob > 0.40:
        recommended_orders.append({
            "order_type": "radiology",
            "title": "Chest X-Ray (PA & Lateral)",
            "reason": "Elevated respiratory risk."
        })
    if kidney_prob > 0.40:
        recommended_orders.append({
            "order_type": "lab",
            "title": "Renal Function Panel (BUN/Creatinine)",
            "reason": "Elevated renal risk."
        })
    if liver_prob > 0.40:
        recommended_orders.append({
            "order_type": "lab",
            "title": "Liver Function Test (LFT) Panel",
            "reason": "Elevated hepatic risk profile detected."
        })
    if diabetes_prob > 0.40:
        recommended_orders.append({
            "order_type": "lab",
            "title": "Hemoglobin A1c (HbA1c) Screening",
            "reason": "Elevated metabolic risk profile detected."
        })

    # Generate AI Clinical Synthesis
    try:
        from . import core_ai
        prompt = f"""
Analyze this patient screening profile:
- Age: {age}, Gender: {gender_str}
- Health Index: {health_index:.1f}/100
- Risks: Heart={heart_prob*100:.1f}%, Lungs={lungs_prob*100:.1f}%, Kidney={kidney_prob*100:.1f}%, Diabetes={diabetes_prob*100:.1f}%, Liver={liver_prob*100:.1f}%
- Ingested Labs: Creatinine={serum_creatinine} mg/dL, BUN={blood_urea} mg/dL, Bilirubin={total_bilirubin} mg/dL, ALT={alt_val} U/L, AST={ast_val} U/L
- Vitals: HR={heart_rate} bpm, BP={systolic_bp}/{diastolic_bp} mmHg, SpO2={spo2}%

Write a highly concise clinical summary (exactly 2 sentences) explaining key systemic risks and recommending immediate steps.
"""
        ai_synthesis = await core_ai.generate(
            prompt=prompt,
            system="You are an expert clinical consultant. Keep summaries under 30 words, clinical, and objective."
        )
    except Exception as e:
        logger.warning(f"AI synthesis failed: {e}")
        criticals = [org.upper() for org, p in [("heart", heart_prob), ("lungs", lungs_prob), ("kidney", kidney_prob), ("diabetes", diabetes_prob), ("liver", liver_prob)] if p > 0.40]
        ai_synthesis = (
            f"CLINICAL INSIGHT: Patient presents with a Unified Health Index of {health_index:.1f}/100. "
            f"Primary systemic risk factors observed in: {', '.join(criticals) or 'none'}. "
            "Verification and follow-up lab orders recommended."
        )

    return {
        "patient_id": patient.id,
        "patient_name": patient.full_name or patient.username,
        "age": age,
        "gender": gender_str,
        "vitals_source": vitals_source,
        "vitals": {
            "heart_rate": heart_rate,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp,
            "spo2": spo2,
            "temperature_c": temp,
            "respiratory_rate": resp_rate
        },
        "health_index": round(health_index, 1),
        "organ_risks": {
            "heart": { "risk_probability": round(heart_prob, 3), "status": get_risk_status(heart_prob) },
            "lungs": { "risk_probability": round(lungs_prob, 3), "status": get_risk_status(lungs_prob) },
            "kidney": { "risk_probability": round(kidney_prob, 3), "status": get_risk_status(kidney_prob) },
            "diabetes": { "risk_probability": round(diabetes_prob, 3), "status": get_risk_status(diabetes_prob) },
            "liver": { "risk_probability": round(liver_prob, 3), "status": get_risk_status(liver_prob) }
        },
        "labs_source": labs_source,
        "labs": {
            "serum_creatinine": round(serum_creatinine, 2),
            "blood_urea": round(blood_urea, 2),
            "total_bilirubin": round(total_bilirubin, 2),
            "direct_bilirubin": round(direct_bilirubin, 2),
            "alt": round(alt_val, 2),
            "ast": round(ast_val, 2)
        },
        "recommended_orders": recommended_orders,
        "ai_clinical_synthesis": ai_synthesis,
        "disclaimer": MEDICAL_DISCLAIMER
    }
