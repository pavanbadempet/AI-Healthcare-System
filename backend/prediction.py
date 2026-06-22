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


def _calculate_adaptive_conformal_prediction(
    proba_positive: float,
    conformal_q: Any,
    input_list: list,
    raw_pred: int,
    risk_level: str = None
) -> dict:
    """
    Calculates the conformal prediction set and dynamically adjusts the threshold (q)
    based on feature missingness (imputation rate) and patient clinical severity.
    """
    missing_count = sum(1 for x in input_list if x is None)
    total_features = len(input_list) if input_list else 1
    missingness_ratio = missing_count / total_features

    # Adjust significance level: more missingness -> higher q (smaller 1-q threshold) -> wider prediction sets
    # We also increase q slightly if the patient is high risk to be more cautious.
    cautious_boost = 0.1 if (raw_pred == 1 and risk_level == "High Risk") else 0.0
    adjustment_factor = min(1.0, missingness_ratio * 0.5 + cautious_boost)

    def adjust_q_val(q: float) -> float:
        return q + (1.0 - q) * adjustment_factor

    adjusted_q = None
    if isinstance(conformal_q, dict):
        adjusted_q = {}
        for k, v in conformal_q.items():
            adjusted_q[int(k)] = adjust_q_val(float(v))
    elif conformal_q is not None:
        adjusted_q = adjust_q_val(float(conformal_q))

    # Calculate standard conformal prediction using adjusted_q
    p0 = 1.0 - proba_positive
    p1 = proba_positive

    prediction_set = []
    if isinstance(adjusted_q, dict):
        q0 = adjusted_q.get(0, 0.0)
        q1 = adjusted_q.get(1, 0.0)
        if p0 >= 1.0 - q0:
            prediction_set.append(0)
        if p1 >= 1.0 - q1:
            prediction_set.append(1)
        significance_level = float(np.round(1.0 - (q0 + q1)/2.0, 4))
    else:
        q = adjusted_q or 0.0
        threshold = 1.0 - q
        if p0 >= threshold:
            prediction_set.append(0)
        if p1 >= threshold:
            prediction_set.append(1)
        significance_level = float(np.round(1.0 - q, 4))

    if len(prediction_set) == 1:
        uncertainty_status = "Low Uncertainty"
    elif len(prediction_set) > 1:
        uncertainty_status = "High Uncertainty (Ambiguous Case)"
    else:
        uncertainty_status = "High Uncertainty (Out-of-Distribution Case)"

    return {
        "conformal_prediction_set": prediction_set,
        "significance_level": significance_level,
        "uncertainty_status": uncertainty_status,
        "missingness_ratio": float(np.round(missingness_ratio, 4)),
        "adjusted_thresholds": adjusted_q
    }


def _log_feature_attributions(
    db: Session,
    model_name: str,
    model_version: str,
    imputed_list: list,
    feature_names: list,
    raw_pred: int,
    model: Any
) -> Optional[dict]:
    """
    Calculates SHAP values for the prediction and logs them to the feature_attribution_logs table
    for population-level drift monitoring. Returns the calculated attributions_dict.
    """
    try:
        import shap
    except ImportError:
        return None

    try:
        # Unwrap model to get tree estimator
        target_estimator = model
        if hasattr(model, 'estimators_'):
            target_estimator = model.estimators_[0]
        if hasattr(target_estimator, 'calibrated_classifiers_') and len(target_estimator.calibrated_classifiers_) > 0:
            target_estimator = target_estimator.calibrated_classifiers_[0].estimator
        elif hasattr(target_estimator, 'estimator'):
            target_estimator = target_estimator.estimator

        if "TabPFNClassifier" in str(type(target_estimator)):
            return None

        input_vector = np.array([imputed_list])
        explainer = shap.TreeExplainer(target_estimator)
        shap_values = explainer.shap_values(input_vector)

        # Handle different SHAP shapes
        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif len(shap_values.shape) == 3:
            sv = shap_values[0, :, 1]
        elif len(shap_values.shape) == 2:
            sv = shap_values[0]
        else:
            sv = shap_values

        features_dict = {feat: float(val) for feat, val in zip(feature_names, imputed_list)}
        attributions_dict = {feat: float(val) for feat, val in zip(feature_names, sv)}

        from .models import DbFeatureAttributionLog
        log_entry = DbFeatureAttributionLog(
            model_name=model_name,
            model_version=model_version,
            features=features_dict,
            attributions=attributions_dict,
            prediction_value=int(raw_pred)
        )
        db.add(log_entry)
        db.commit()
        return attributions_dict
    except Exception as e:
        logger.warning("Failed to log feature attributions for %s: %s", model_name, e)
        return None


async def _generate_patient_explanation(
    model_name: str,
    prediction: str,
    confidence: float,
    risk_level: str,
    attributions: dict
) -> str:
    """
    Generates an empathetic, patient-friendly explanation translating the prediction
    result and SHAP feature attributions into layperson language.
    """
    if not attributions:
        return "Patient-friendly explanation is currently unavailable as feature attributions could not be calculated."
    try:
        from .core_ai import generate
        from .prompt_registry import get_prompt

        # Clean/format the attributions for the prompt
        formatted_attributions = []
        for feat, val in attributions.items():
            formatted_attributions.append(f"- {feat}: SHAP Impact = {val:+.4f}")
        attributions_str = "\n".join(formatted_attributions)

        template = get_prompt("patient_xai_explanation")
        prompt = template.format(
            disease=model_name.upper(),
            prediction=prediction,
            confidence=f"{confidence:.1f}" if isinstance(confidence, (int, float)) else str(confidence),
            risk_level=risk_level,
            feature_attributions=attributions_str
        )
        explanation = await generate(
            prompt=prompt,
            system="You are an empathetic, patient-friendly medical AI assistant. Output only the layperson explanation."
        )
        return explanation.strip()
    except Exception as e:
        logger.warning("Failed to generate patient explanation for %s: %s", model_name, e)
        return "Patient explanation could not be generated due to an internal system error."


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
    Simulates a counterfactual 'what-if' patient profile by performing step-wise boundary
    searches on controllable lifestyle features to find the optimal risk reduction path.
    """
    try:
        if current_prob < 0.5:
            # Recourse is only relevant for high-risk patients
            return None

        import itertools

        import numpy as np
        import pandas as pd

        # Schema: (index, check_fn, target_val, description, is_continuous)
        candidates = {
            "diabetes": [
                (0, lambda val: val == 1.0, 0.0, "managing hypertension", False),
                (3, lambda val: val == 1.0, 0.0, "smoking cessation", False),
                (5, lambda val: val == 0.0, 1.0, "increasing physical activity", False),
                (2, lambda val: val is not None and val > 25.0, 25.0, "reducing BMI", True),
            ],
            "heart": [
                (5, lambda val: val == 1.0, 0.0, "managing blood sugar", False),
                (10, lambda val: val == 1.0, 0.0, "abstaining from heavy alcohol", False),
                (3, lambda val: val is not None and val > 120.0, 120.0, "reducing resting blood pressure", True),
            ],
            "kidney": [
                (1, lambda val: val is not None and val > 120.0, 120.0, "controlling blood pressure", True),
                (18, lambda val: val == 1, 0, "managing hypertension", False),
                (19, lambda val: val == 1, 0, "managing diabetes", False),
            ],
            "lungs": [
                (2, lambda val: val == 2.0, 1.0, "smoking cessation", False),
                (10, lambda val: val == 2.0, 1.0, "abstaining from alcohol", False),
            ],
            "liver": []
        }.get(model_name, [])

        applicable = []
        for index, check_fn, target_val, desc, is_cont in candidates:
            if index < len(imputed_list) and check_fn(imputed_list[index]):
                applicable.append((index, target_val, desc, is_cont))

        if not applicable:
            return "Patient has no standard controllable lifestyle risk factors to modify."

        def _predict_profile(profile):
            if model_name in ("kidney", "liver", "lungs"):
                from . import features as _feat
                feat_names = {
                    "kidney": _feat.KIDNEY_FEATURES,
                    "liver": _feat.LIVER_FEATURES,
                    "lungs": _feat.LUNG_FEATURES
                }[model_name]
                df_rec = pd.DataFrame([profile], columns=feat_names)
                if scaler is not None:
                    X_rec = scaler.transform(df_rec)
                else:
                    X_rec = df_rec.values
            else:
                X_rec = [profile]
            proba_rec = model_obj.predict_proba(X_rec)[0]
            return float(proba_rec[1]) if len(proba_rec) > 1 else float(proba_rec[0])

        best_combination = None
        best_proba = current_prob
        best_reduction = 0.0
        successful_combinations = []

        # Evaluate all subsets of combinations
        for r in range(1, len(applicable) + 1):
            for comb in itertools.combinations(applicable, r):
                test_profile = list(imputed_list)
                comb_descs = []
                for index, target_val, desc, is_cont in comb:
                    if is_cont:
                        current_val = test_profile[index]
                        best_val = target_val
                        best_val_proba = current_prob
                        # Step-wise boundary search (binary/grid search)
                        for step_val in np.linspace(current_val, target_val, 6):
                            temp_profile = list(test_profile)
                            temp_profile[index] = step_val
                            prob_pos_step = _predict_profile(temp_profile)
                            if prob_pos_step < 0.5:
                                best_val = step_val
                                best_val_proba = prob_pos_step
                                break
                            if prob_pos_step < best_val_proba:
                                best_val = step_val
                                best_val_proba = prob_pos_step
                        test_profile[index] = best_val
                        comb_descs.append(f"{desc} to {float(best_val):.1f}")
                    else:
                        test_profile[index] = target_val
                        comb_descs.append(desc)

                prob_pos_rec = _predict_profile(test_profile)
                reduction = current_prob - prob_pos_rec

                if reduction > best_reduction:
                    best_reduction = reduction
                    best_proba = prob_pos_rec
                    best_combination = (comb, comb_descs)

                if prob_pos_rec < 0.5:
                    successful_combinations.append((comb, comb_descs, prob_pos_rec, reduction))

        if best_reduction <= 0.01:
            return "Lifestyle modifications alone show minimal expected risk reduction for this patient's profile."

        if successful_combinations:
            successful_combinations.sort(key=lambda x: (len(x[0]), -x[3]))
            optimal_comb, optimal_descs, optimal_proba, optimal_reduction = successful_combinations[0]
            actions = ", ".join(optimal_descs[:-1]) + " and " + optimal_descs[-1] if len(optimal_descs) > 1 else optimal_descs[0]
            return f"Managing risk through {actions} could potentially reduce risk probability by {optimal_reduction * 100:.1f}%, bringing predicted risk below the threshold to {optimal_proba * 100:.1f}%."
        else:
            best_comb, best_descs = best_combination
            actions = ", ".join(best_descs[:-1]) + " and " + best_descs[-1] if len(best_descs) > 1 else best_descs[0]
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
    db: Session = Depends(database.get_db),
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
                    conformal_metrics = _calculate_adaptive_conformal_prediction(
                        proba_pos, conformal_q, input_list, raw, risk_level
                    )

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

        # Log feature attributions for drift monitoring
        attributions = _log_feature_attributions(
            db, "kidney", getattr(model_service._entries["kidney"], "model_version", "1.0.0"),
            imputed_list, feature_names, raw, _pred.kidney_model
        )

        model_metadata = _get_model_metadata("kidney", _pred.kidney_model)
        narrative = await _generate_clinical_narrative(
            "kidney", prediction, confidence, risk_level, clinical_indices
        )
        patient_explanation = await _generate_patient_explanation(
            "kidney", prediction, confidence, risk_level, attributions or {}
        )
        return {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative,
            "attributions": attributions or {},
            "patient_explanation": patient_explanation
        }
    except Exception:
        logger.error("Kidney prediction error")
        _raise_prediction_failure("Kidney")

@router.post("/predict/lungs", response_model=Dict[str, Any])
async def predict_lungs(
    data: schemas.LungInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
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
                    conformal_metrics = _calculate_adaptive_conformal_prediction(
                        proba_pos, conformal_q, input_list, raw, risk_level
                    )

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

        # Log feature attributions for drift monitoring
        attributions = _log_feature_attributions(
            db, "lungs", getattr(model_service._entries["lungs"], "model_version", "1.0.0"),
            imputed_list, feature_names, raw, _pred.lungs_model
        )

        model_metadata = _get_model_metadata("lungs", _pred.lungs_model)
        narrative = await _generate_clinical_narrative(
            "lungs", prediction, confidence, risk_level, clinical_indices
        )
        patient_explanation = await _generate_patient_explanation(
            "lungs", prediction, confidence, risk_level, attributions or {}
        )
        res = {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative,
            "attributions": attributions or {},
            "patient_explanation": patient_explanation
        }
        return res
    except Exception:
        logger.error("Lung prediction error")
        _raise_prediction_failure("Lung")

@router.post("/predict/diabetes", response_model=Dict[str, Any])
async def predict_diabetes(
    data: schemas.DiabetesInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
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
                    conformal_metrics = _calculate_adaptive_conformal_prediction(
                        proba_pos, conformal_q, imputed_list, raw, risk_level
                    )

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

        # Log feature attributions for drift monitoring
        attributions = _log_feature_attributions(
            db, "diabetes", getattr(model_service._entries["diabetes"], "model_version", "1.0.0"),
            imputed_list, _features.DIABETES_FEATURES, raw, _pred.diabetes_model
        )

        model_metadata = _get_model_metadata("diabetes", _pred.diabetes_model)
        narrative = await _generate_clinical_narrative(
            "diabetes", prediction, confidence, risk_level, clinical_indices
        )
        patient_explanation = await _generate_patient_explanation(
            "diabetes", prediction, confidence, risk_level, attributions or {}
        )
        res = {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative,
            "attributions": attributions or {},
            "patient_explanation": patient_explanation
        }
        return res
    except Exception:
        logger.error("Diabetes prediction error")
        _raise_prediction_failure("Diabetes")

@router.post("/predict/heart", response_model=Dict[str, Any])
async def predict_heart(
    data: schemas.HeartInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
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
                    conformal_metrics = _calculate_adaptive_conformal_prediction(
                        proba_pos, conformal_q, imputed_list, raw, risk_level
                    )

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

        # Log feature attributions for drift monitoring
        attributions = _log_feature_attributions(
            db, "heart", getattr(model_service._entries["heart"], "model_version", "1.0.0"),
            imputed_list, _features.HEART_FEATURES, raw, _pred.heart_model
        )

        model_metadata = _get_model_metadata("heart", _pred.heart_model)
        narrative = await _generate_clinical_narrative(
            "heart", prediction, confidence, risk_level, clinical_indices
        )
        patient_explanation = await _generate_patient_explanation(
            "heart", prediction, confidence, risk_level, attributions or {}
        )
        return {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative,
            "attributions": attributions or {},
            "patient_explanation": patient_explanation
        }
    except Exception:
        logger.error("Heart prediction error")
        _raise_prediction_failure("Heart")

@router.post("/predict/liver", response_model=Dict[str, Any])
async def predict_liver(
    data: schemas.LiverInput,
    _current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
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
                    conformal_metrics = _calculate_adaptive_conformal_prediction(
                        proba_pos, conformal_q, input_list, raw, risk_level
                    )

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

        # Log feature attributions for drift monitoring
        attributions = _log_feature_attributions(
            db, "liver", getattr(model_service._entries["liver"], "model_version", "1.0.0"),
            imputed_list, feature_names, raw, _pred.liver_model
        )

        model_metadata = _get_model_metadata("liver", _pred.liver_model)
        narrative = await _generate_clinical_narrative(
            "liver", prediction, confidence, risk_level, clinical_indices
        )
        patient_explanation = await _generate_patient_explanation(
            "liver", prediction, confidence, risk_level, attributions or {}
        )
        return {
            "prediction": prediction,
            "raw": raw,
            "confidence": confidence,
            "risk_level": risk_level,
            "disclaimer": MEDICAL_DISCLAIMER,
            "clinical_indices": clinical_indices,
            "model_metadata": model_metadata,
            "clinical_narrative": narrative,
            "attributions": attributions or {},
            "patient_explanation": patient_explanation
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


@router.get("/predict/advisory-board/{patient_id}", response_model=Dict[str, Any])
async def get_advisory_board(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: db_models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    """Execute the multi-agent clinical advisory board sequential consultation debate."""
    from backend.agents.advisory_board import ClinicalAdvisoryBoard

    # 1. Enforce access control
    _ensure_prediction_review_access(db, current_user, patient_id)

    # 2. Instantiate and run
    board = ClinicalAdvisoryBoard(db)
    result = await board.execute_board(patient_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


async def handle_vitals_recorded(payload: dict) -> None:
    """Auto-run heart/diabetes classifiers when new vitals arrive.
    If risk probability > 0.6, commit a DIAGNOSTIC_ALERT CareEvent to the DB.
    """
    patient_id = payload.get("patient_id")
    if not patient_id:
        return

    # Extract vitals from payload
    sys_bp = payload.get("systolic_bp")
    hr = payload.get("heart_rate")

    import backend.models as db_models
    import backend.prediction as _pred
    from backend.database import get_db_context

    with get_db_context() as db:
        # Fetch patient
        patient = db.query(db_models.User).filter(db_models.User.id == patient_id, db_models.User.role == "patient").first()
        if not patient:
            return

        # 1. Check Diabetes Model
        if _pred.diabetes_model is not None:
            hypertension = 1.0 if (sys_bp is not None and sys_bp > 140.0) else 0.0
            high_chol = 0.0
            bmi = 25.0
            smoking_history = 0.0
            heart_disease = 0.0
            physical_activity = 1.0
            general_health = 3.0
            gender_val = 1.0
            age_bucket = 7.0  # age 50-54

            input_list_db = [hypertension, high_chol, bmi, smoking_history, heart_disease, physical_activity, general_health, gender_val, age_bucket]

            imputer, conformal_q = _pred._get_imputer_and_conformal("diabetes", _pred.diabetes_model)
            if imputer is not None:
                imputed_arr = imputer.transform([input_list_db])
                imputed_list = imputed_arr[0].tolist()
            else:
                imputed_list = [0.0 if x is None else x for x in input_list_db]

            try:
                proba = _pred.diabetes_model.predict_proba([imputed_list])[0]
                diabetes_risk = float(proba[1]) if len(proba) > 1 else float(proba[0])
            except Exception:
                diabetes_risk = 0.0

            if diabetes_risk > 0.6:
                db.add(db_models.CareEvent(
                    facility_id=patient.facility_id,
                    patient_id=patient_id,
                    event_type="DIAGNOSTIC_ALERT",
                    title="Diabetes Risk Flagged",
                    summary=f"Automated ClinOS intelligence flagged high diabetes risk ({round(diabetes_risk * 100, 1)}%) based on recent vital logs.",
                    severity="warning",
                ))
                db.commit()

        # 2. Check Heart Model
        if _pred.heart_model is not None:
            trestbps = sys_bp if sys_bp is not None else 120.0
            thalach = hr if hr is not None else 72.0
            age_val = 50.0
            sex = 1.0
            cp = 0.0
            chol = 200.0
            fbs = 0.0
            restecg = 0.0
            exang = 0.0
            oldpeak = 0.0
            slope = 1.0
            ca = 0.0
            thal = 2.0

            input_list_hr = [age_val, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]

            imputer, conformal_q = _pred._get_imputer_and_conformal("heart", _pred.heart_model)
            if imputer is not None:
                imputed_arr = imputer.transform([input_list_hr])
                imputed_list = imputed_arr[0].tolist()
            else:
                imputed_list = [0.0 if x is None else x for x in input_list_hr]

            try:
                proba = _pred.heart_model.predict_proba([imputed_list])[0]
                heart_risk = float(proba[1]) if len(proba) > 1 else float(proba[0])
            except Exception:
                heart_risk = 0.0

            if heart_risk > 0.6:
                db.add(db_models.CareEvent(
                    facility_id=patient.facility_id,
                    patient_id=patient_id,
                    event_type="DIAGNOSTIC_ALERT",
                    title="Cardiovascular Risk Flagged",
                    summary=f"Automated ClinOS intelligence flagged high cardiovascular risk ({round(heart_risk * 100, 1)}%) based on recent vital logs.",
                    severity="critical",
                ))
                db.commit()


# --- Phase 10 API Routes & Schemas ---
from pydantic import BaseModel as PydanticBaseModel


class ScribeRequest(PydanticBaseModel):
    transcript: str

class ScribeCommitItem(PydanticBaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    quantity_prescribed: float

class ScribeCommitRequest(PydanticBaseModel):
    patient_id: int
    subjective: str
    objective: str
    assessment: str
    plan: str
    icd10_codes: list[str]
    billing_codes: list[str]
    prescriptions: list[ScribeCommitItem]
    billing_items: list[dict]

class CounterfactualRequest(PydanticBaseModel):
    target_model: str  # "diabetes" or "heart"
    features: dict[str, float]


@router.post("/predict/scribe/commit")
async def commit_scribe_soap(
    req: ScribeCommitRequest,
    current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    import json
    patient = db.query(db_models.User).filter(db_models.User.id == req.patient_id, db_models.User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    facility_id = patient.facility_id

    # 1. Log CareEvent
    summary_data = {
        "subjective": req.subjective,
        "objective": req.objective,
        "assessment": req.assessment,
        "plan": req.plan,
        "icd10_codes": req.icd10_codes,
        "billing_codes": req.billing_codes,
    }
    care_event = db_models.CareEvent(
        facility_id=facility_id,
        patient_id=req.patient_id,
        actor_user_id=current_user.id,
        event_type="ambient_scribe_note",
        title="Ambient Clinical SOAP Note",
        summary=json.dumps(summary_data),
        severity="info",
    )
    db.add(care_event)

    # 2. Add prescriptions if present
    if req.prescriptions:
        prescription = db_models.Prescription(
            facility_id=facility_id,
            patient_id=req.patient_id,
            doctor_id=current_user.id if current_user.role == "doctor" else None,
            diagnosis_context=", ".join(req.icd10_codes),
            status="active",
        )
        db.add(prescription)
        db.flush()

        for item in req.prescriptions:
            db.add(db_models.PrescriptionItem(
                prescription_id=prescription.id,
                medication_name=item.medication_name,
                dosage=item.dosage,
                frequency=item.frequency,
                duration=item.duration,
                quantity_prescribed=item.quantity_prescribed,
                quantity_dispensed=0.0,
                status="pending",
            ))

    # 3. Add billing Invoice if items present
    if req.billing_items:
        subtotal = sum(float(item.get("amount", 0)) for item in req.billing_items)
        invoice = db_models.Invoice(
            facility_id=facility_id,
            patient_id=req.patient_id,
            created_by_id=current_user.id,
            status="issued",
            subtotal=subtotal,
            total_amount=subtotal,
            balance_amount=subtotal,
            currency="INR",
        )
        db.add(invoice)
        db.flush()

        for item in req.billing_items:
            db.add(db_models.InvoiceLineItem(
                invoice_id=invoice.id,
                description=item.get("description", "Service"),
                quantity=1.0,
                unit_price=float(item.get("amount", 0)),
                line_total=float(item.get("amount", 0)),
            ))

    db.commit()
    return {"status": "success", "message": "Clinical SOAP note, prescriptions, and invoice committed to EHR successfully."}


@router.post("/predict/scribe/{patient_id}")
async def generate_scribe_soap(
    patient_id: int,
    req: ScribeRequest,
    current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    _ensure_prediction_review_access(db, current_user, patient_id)
    from backend.agents.scribe_agent import ClinicalScribeAgent
    agent = ClinicalScribeAgent(db)
    result = await agent.generate_soap_note(patient_id, req.transcript)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/predict/clinical-trials/{patient_id}")
async def match_clinical_trials(
    patient_id: int,
    current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    import json
    from datetime import datetime

    from .prompt_registry import get_prompt
    _ensure_prediction_review_access(db, current_user, patient_id)

    patient = db.query(db_models.User).filter(db_models.User.id == patient_id, db_models.User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    recent_records = db.query(db_models.HealthRecord).filter(
        db_models.HealthRecord.user_id == patient_id
    ).order_by(db_models.HealthRecord.timestamp.desc()).all()

    predictions_summary = []
    for r in recent_records:
        predictions_summary.append(f"{r.record_type.title()}: {r.prediction}")
    ml_risks_str = ", ".join(predictions_summary) if predictions_summary else "No recent ML predictions"

    latest_vital = db.query(db_models.VitalObservation).filter(
        db_models.VitalObservation.patient_id == patient_id
    ).order_by(db_models.VitalObservation.observed_at.desc()).first()

    age = "N/A"
    if patient.dob:
        try:
            dob_dt = datetime.strptime(patient.dob, "%Y-%m-%d") if isinstance(patient.dob, str) else patient.dob
            age = datetime.now().year - dob_dt.year
        except Exception:
            pass

    patient_context = (
        f"Patient: {patient.full_name or patient.username}\n"
        f"Age: {age}\n"
        f"Gender: {'Male' if patient.gender == 1 else 'Female' if patient.gender == 0 else 'Other'}\n"
        f"Ailments/Diagnoses: {patient.existing_ailments or 'None'}\n"
        f"Latest Vitals: HR: {latest_vital.heart_rate if latest_vital else 72.0} bpm, "
        f"BP: {latest_vital.systolic_bp if latest_vital else 120.0}/{latest_vital.diastolic_bp if latest_vital else 80.0} mmHg, "
        f"SpO2: {latest_vital.spo2 if latest_vital else 98.0}%\n"
        f"ML Risk Scores: {ml_risks_str}"
    )

    trials_context = (
        "1. Trial ID: NCT04510001\n"
        "   Title: Phase III Trial of Novel SGLT2 Inhibitor in Cardiovascular Outcomes\n"
        "   Focus: Cardiovascular disease and heart health outcomes\n"
        "   Inclusion: Age >= 18, Hypertension, High Risk of cardiovascular events.\n"
        "   Exclusion: Pregnancy, Stage 5 Chronic Kidney Disease.\n\n"
        "2. Trial ID: NCT03920188\n"
        "   Title: Efficacy of Digital Health Coaching vs. Pharmacological Therapy in Pre-Diabetic Patients\n"
        "   Focus: Diabetes prevention and management\n"
        "   Inclusion: Age >= 18, Pre-diabetes or High Risk Diabetes prediction, BMI >= 25.\n"
        "   Exclusion: Type 1 Diabetes, Active insulin treatment.\n\n"
        "3. Trial ID: NCT04983210\n"
        "   Title: A Study of Endothelin Receptor Antagonist in Retarding Diabetic Nephropathy\n"
        "   Focus: Kidney disease and diabetic nephropathy\n"
        "   Inclusion: Estimated GFR between 30 and 75 mL/min/1.73m2, Type 2 Diabetes.\n"
        "   Exclusion: Severe Heart Failure, Active liver failure.\n"
    )

    prompt = get_prompt("clinical_trials_match").format(
        patient_context=patient_context,
        trials_context=trials_context
    )

    from backend.core_ai import generate
    raw_output = await generate(
        prompt=prompt,
        system="You are a clinical trials matching coordinator."
    )

    try:
        clean_str = raw_output.strip()
        if clean_str.startswith("```json"):
            clean_str = clean_str[7:]
        if clean_str.endswith("```"):
            clean_str = clean_str[:-3]
        clean_str = clean_str.strip()

        parsed = json.loads(clean_str)
        return parsed
    except Exception as e:
        logger.warning("Failed to parse trials output: %s", e)
        return {
            "matches": [
                {
                    "trial_id": "NCT04510001",
                    "title": "Phase III Trial of Novel SGLT2 Inhibitor in Cardiovascular Outcomes",
                    "match_percentage": 50.0,
                    "eligible": False,
                    "reasons": ["Could not parse LLM screening details"],
                    "referral_letter": f"Raw output: {raw_output}"
                }
            ]
        }


def _run_diabetes_proba(features: dict) -> float:
    import backend.prediction as _pred

    from .model_service import get_age_bucket

    age_bucket = get_age_bucket(features.get("age", 45))
    input_list = [
        features.get("hypertension", 0.0),
        features.get("high_chol", 0.0),
        features.get("bmi", 25.0),
        features.get("smoking_history", 0.0),
        features.get("heart_disease", 0.0),
        features.get("physical_activity", 1.0),
        features.get("general_health", 3.0),
        features.get("gender", 1.0),
        age_bucket
    ]
    imputer, _ = _pred._get_imputer_and_conformal("diabetes", _pred.diabetes_model)
    if imputer is not None:
        imputed_arr = imputer.transform([input_list])
        imputed_list = imputed_arr[0].tolist()
    else:
        imputed_list = [0.0 if x is None else x for x in input_list]

    try:
        proba = _pred.diabetes_model.predict_proba([imputed_list])[0]
        return float(proba[1]) if len(proba) > 1 else float(proba[0])
    except Exception:
        return 0.0


def _run_heart_proba(features: dict) -> float:
    import backend.prediction as _pred

    input_list = [
        features.get("age", 50.0),
        features.get("sex", 1.0),
        features.get("cp", 0.0),
        features.get("trestbps", 120.0),
        features.get("chol", 200.0),
        features.get("fbs", 0.0),
        features.get("restecg", 0.0),
        features.get("thalach", 150.0),
        features.get("exang", 0.0),
        features.get("oldpeak", 0.0),
        features.get("slope", 1.0),
        features.get("ca", 0.0),
        features.get("thal", 2.0)
    ]
    imputer, _ = _pred._get_imputer_and_conformal("heart", _pred.heart_model)
    if imputer is not None:
        imputed_arr = imputer.transform([input_list])
        imputed_list = imputed_arr[0].tolist()
    else:
        imputed_list = [0.0 if x is None else x for x in input_list]

    try:
        proba = _pred.heart_model.predict_proba([imputed_list])[0]
        return float(proba[1]) if len(proba) > 1 else float(proba[0])
    except Exception:
        return 0.0


@router.post("/predict/counterfactual/{patient_id}")
async def counterfactual_recourse(
    patient_id: int,
    req: CounterfactualRequest,
    current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    _ensure_prediction_review_access(db, current_user, patient_id)

    target = req.target_model.lower()
    features = req.features.copy()

    if target == "diabetes":
        baseline = _run_diabetes_proba(features)
        recourse = features.copy()

        # If risk is already low, return
        if baseline < 0.5:
            return {
                "baseline_risk": baseline,
                "optimized_risk": baseline,
                "recourse_recommendation": recourse,
                "changes_applied": {}
            }

        # Step-wise optimization logic
        # Optimize: BMI, High Chol, Hypertension, Physical Activity, Smoking, Gen Health
        changes = {}

        # 1. Smoking history to 0
        if recourse.get("smoking_history", 0.0) == 1.0:
            recourse["smoking_history"] = 0.0
            changes["smoking_history"] = "Quit smoking"

        # 2. High Chol to 0
        if _run_diabetes_proba(recourse) >= 0.5 and recourse.get("high_chol", 0.0) == 1.0:
            recourse["high_chol"] = 0.0
            changes["high_chol"] = "Control cholesterol (target High Chol to No)"

        # 3. Hypertension to 0
        if _run_diabetes_proba(recourse) >= 0.5 and recourse.get("hypertension", 0.0) == 1.0:
            recourse["hypertension"] = 0.0
            changes["hypertension"] = "Manage hypertension (target Hypertension to No)"

        # 4. Physical Activity to 1
        if _run_diabetes_proba(recourse) >= 0.5 and recourse.get("physical_activity", 1.0) == 0.0:
            recourse["physical_activity"] = 1.0
            changes["physical_activity"] = "Increase physical activity (target to Yes)"

        # 5. General Health to 2 (Good) or 1 (Excellent)
        current_gen_health = recourse.get("general_health", 3.0)
        if _run_diabetes_proba(recourse) >= 0.5 and current_gen_health > 2.0:
            recourse["general_health"] = 2.0
            changes["general_health"] = f"Improve general self-reported health from {int(current_gen_health)} to 2"

        # 6. Reduce BMI progressively
        current_bmi = recourse.get("bmi", 25.0)
        if _run_diabetes_proba(recourse) >= 0.5 and current_bmi > 24.0:
            target_bmi = max(18.5, min(24.0, current_bmi - 5.0))
            recourse["bmi"] = target_bmi
            changes["bmi"] = f"Reduce BMI from {current_bmi:.1f} to {target_bmi:.1f}"

        optimized_risk = _run_diabetes_proba(recourse)
        return {
            "baseline_risk": baseline,
            "optimized_risk": optimized_risk,
            "recourse_recommendation": recourse,
            "changes_applied": changes
        }

    elif target == "heart":
        baseline = _run_heart_proba(features)
        recourse = features.copy()

        if baseline < 0.5:
            return {
                "baseline_risk": baseline,
                "optimized_risk": baseline,
                "recourse_recommendation": recourse,
                "changes_applied": {}
            }

        # Optimize: trestbps (BP), chol (Cholesterol), smoker, thalach (max HR), hyp_treatment
        changes = {}

        # 1. If smoker, stop smoking
        if recourse.get("smoker", 0) == 1:
            recourse["smoker"] = 0
            changes["smoker"] = "Stop smoking"

        # 2. Control Resting Blood Pressure (trestbps)
        current_bp = recourse.get("trestbps", 120.0)
        if _run_heart_proba(recourse) >= 0.5 and current_bp > 120.0:
            recourse["trestbps"] = 120.0
            changes["trestbps"] = f"Reduce resting blood pressure from {int(current_bp)} mmHg to 120 mmHg"

        # 3. Control Cholesterol (chol)
        current_chol = recourse.get("chol", 200.0)
        if _run_heart_proba(recourse) >= 0.5 and current_chol > 200.0:
            recourse["chol"] = 200.0
            changes["chol"] = f"Reduce serum cholesterol from {int(current_chol)} mg/dL to 200 mg/dL"

        # 4. Improve max heart rate achieved (thalach)
        current_hr = recourse.get("thalach", 150.0)
        if _run_heart_proba(recourse) >= 0.5 and current_hr < 160.0:
            recourse["thalach"] = 160.0
            changes["thalach"] = "Improve max heart rate achieved (aerobic capacity) to 160 bpm"

        optimized_risk = _run_heart_proba(recourse)
        return {
            "baseline_risk": baseline,
            "optimized_risk": optimized_risk,
            "recourse_recommendation": recourse,
            "changes_applied": changes
        }

    else:
        raise HTTPException(status_code=400, detail=f"Counterfactual recourse not supported for model: {req.target_model}")


@router.get("/predict/consensus/{patient_id}")
async def get_clinical_consensus(
    patient_id: int,
    current_user: db_models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    import json
    _ensure_prediction_review_access(db, current_user, patient_id)

    patient = db.query(db_models.User).filter(db_models.User.id == patient_id, db_models.User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Fetch recent predictions and vitals
    recent_records = db.query(db_models.HealthRecord).filter(
        db_models.HealthRecord.user_id == patient_id
    ).order_by(db_models.HealthRecord.timestamp.desc()).all()

    predictions_summary = {}
    for r in recent_records:
        if r.record_type not in predictions_summary:
            predictions_summary[r.record_type] = r.prediction

    latest_vital = db.query(db_models.VitalObservation).filter(
        db_models.VitalObservation.patient_id == patient_id
    ).order_by(db_models.VitalObservation.observed_at.desc()).first()

    # Identify consensus conflicts
    conflicts = []

    # 1. Diabetes Conflict: High vitals/glucose but low predicted risk
    diabetes_pred = predictions_summary.get("diabetes", "low")
    if latest_vital and latest_vital.blood_glucose is not None and latest_vital.blood_glucose > 140.0 and diabetes_pred == "low":
        conflicts.append("Patient has elevated blood glucose (>140 mg/dL) but the ML classifier predicted Low Diabetes Risk. This warrants closer inspection of HbA1c.")

    # 2. Heart Conflict: High BP or Heart Rate but low predicted risk
    heart_pred = predictions_summary.get("heart", "low")
    if latest_vital and (
        (latest_vital.heart_rate is not None and latest_vital.heart_rate > 100.0) or
        (latest_vital.systolic_bp is not None and latest_vital.systolic_bp > 140.0)
    ) and heart_pred == "low":
        conflicts.append("Patient has resting tachycardia (>100 bpm) or Stage 2 Hypertension (>140 mmHg systolic) but the ML classifier predicted Low Heart Disease Risk.")

    # Build AI prompt for consensus report
    vitals_str = (
        f"HR: {latest_vital.heart_rate if latest_vital else 72.0} bpm, "
        f"BP: {latest_vital.systolic_bp if latest_vital else 120.0}/{latest_vital.diastolic_bp if latest_vital else 80.0} mmHg, "
        f"Blood Glucose: {latest_vital.blood_glucose if latest_vital else 90.0} mg/dL"
    )

    conflict_notes = "\n".join(f"- {c}" for c in conflicts) if conflicts else "None identified."

    prompt = (
        "You are an expert clinical second-opinion consensus agent.\n\n"
        f"Patient Vitals:\n{vitals_str}\n\n"
        f"ML Risk Assessments:\n"
        f"- Diabetes: {diabetes_pred}\n"
        f"- Heart Disease: {heart_pred}\n\n"
        f"Identified Discrepancies/Conflicts:\n{conflict_notes}\n\n"
        "Generate a second opinion diagnostic consensus report. Output your response as a JSON object in this exact format:\n"
        "{\n"
        '  "consensus_level": "agreement | minor_discrepancy | major_conflict",\n'
        '  "summary": "Short 1-sentence consensus summary.",\n'
        '  "detailed_audit": "Detailed clinical reasoning resolving any conflicts.",\n'
        '  "recommended_tests": ["List of recommended labs to resolve discrepancies"]\n'
        "}\n\n"
        "Do not include markdown formatting like ```json."
    )

    from backend.core_ai import generate
    raw_output = await generate(
        prompt=prompt,
        system="You are a clinical diagnostics consensus auditor."
    )

    try:
        clean_str = raw_output.strip()
        if clean_str.startswith("```json"):
            clean_str = clean_str[7:]
        if clean_str.endswith("```"):
            clean_str = clean_str[:-3]
        clean_str = clean_str.strip()

        parsed = json.loads(clean_str)
        return parsed
    except Exception as e:
        logger.warning("Failed to parse consensus output: %s", e)
        return {
            "consensus_level": "minor_discrepancy" if conflicts else "agreement",
            "summary": "AI Clinician Consensus: Vitals and risk predictions are aligned.",
            "detailed_audit": f"Vitals check: {vitals_str}. Discrepancies found: {len(conflicts)}. Review recommended tests to resolve.",
            "recommended_tests": ["HbA1c test" if "glucose" in conflict_notes else "12-Lead ECG"]
        }


def register_prediction_event_handlers() -> None:
    """Subscribe prediction event handlers to the event bus."""
    from backend.event_bus import event_bus
    event_bus.subscribe("VITALS_RECORDED", handle_vitals_recorded)

