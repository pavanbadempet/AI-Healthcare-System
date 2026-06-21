"""
Longitudinal (temporal) prediction service.

Provides API endpoints that accept a *sequence* of patient visits and use the
ClinicalTemporalLSTM model to predict disease risk while exposing per-visit
attention weights for clinical interpretability.

The service supports diabetes, heart, liver, and kidney domains.  Models are
loaded lazily on first request and cached in memory.
"""

import logging
import os
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
from fastapi import APIRouter, Depends, HTTPException

from . import auth, models
from .model_service import MEDICAL_DISCLAIMER
from .schemas.longitudinal import (
    LongitudinalDiabetesRequest,
    LongitudinalHeartRequest,
    LongitudinalKidneyRequest,
    LongitudinalLiverRequest,
    LongitudinalPredictionResponse,
    VisitAttention,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict/longitudinal", tags=["Longitudinal Predictions"])

# ---------------------------------------------------------------------------
# Model cache
# ---------------------------------------------------------------------------
_longitudinal_models: Dict[str, Any] = {}

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_longitudinal_model(condition: str):
    """Load a trained ClinicalTemporalLSTM from disk, if available."""
    if condition in _longitudinal_models:
        return _longitudinal_models[condition]

    pkl_name = f"longitudinal_{condition}_model.pkl"
    pkl_path = os.path.join(MODEL_DIR, pkl_name)

    if not os.path.exists(pkl_path):
        logger.info(
            "No longitudinal model found for '%s' at %s — "
            "will use synthetic/demo mode.",
            condition,
            pkl_path,
        )
        return None

    try:
        model = joblib.load(pkl_path)
        _longitudinal_models[condition] = model
        logger.info("Loaded longitudinal model for '%s' from %s", condition, pkl_path)
        return model
    except Exception as exc:
        logger.error("Failed to load longitudinal model for '%s': %s", condition, exc)
        return None


# ---------------------------------------------------------------------------
# Feature extraction helpers
# ---------------------------------------------------------------------------

# Canonical feature orderings per domain (must match training order)
DIABETES_FEATURES = [
    "hypertension", "high_chol", "bmi", "smoking_history",
    "heart_disease", "physical_activity", "general_health", "gender", "age",
]

HEART_FEATURES = [
    "age", "sex", "cp", "trestbps", "chol", "fbs",
    "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal",
]

LIVER_FEATURES = [
    "age", "gender", "total_bilirubin", "direct_bilirubin",
    "alkaline_phosphotase", "alamine_aminotransferase",
    "aspartate_aminotransferase", "total_proteins", "albumin",
    "albumin_globulin_ratio",
]

KIDNEY_FEATURES = [
    "age", "blood_pressure", "specific_gravity", "albumin", "sugar",
    "blood_glucose_random", "blood_urea", "serum_creatinine", "sodium",
    "potassium", "hemoglobin", "packed_cell_volume",
    "white_blood_cell_count", "red_blood_cell_count",
    "hypertension", "diabetes_mellitus", "appetite",
    "pedal_edema", "anemia",
]

FEATURE_MAPS = {
    "diabetes": DIABETES_FEATURES,
    "heart": HEART_FEATURES,
    "liver": LIVER_FEATURES,
    "kidney": KIDNEY_FEATURES,
}


def _visits_to_array(
    visits: list,
    feature_names: List[str],
) -> np.ndarray:
    """
    Convert a list of Pydantic visit objects into a 3-D numpy array
    of shape (1, n_visits, n_features).  Missing values are forward-filled
    from the previous visit, then back-filled, then filled with 0.
    """
    n_visits = len(visits)
    n_features = len(feature_names)
    arr = np.full((n_visits, n_features), np.nan, dtype=np.float32)

    for t, visit in enumerate(visits):
        visit_dict = visit.model_dump()
        for j, feat in enumerate(feature_names):
            val = visit_dict.get(feat)
            if val is not None:
                arr[t, j] = float(val)

    # Forward fill → backward fill → zero fill
    for j in range(n_features):
        col = arr[:, j]
        # Forward fill
        for t in range(1, n_visits):
            if np.isnan(col[t]) and not np.isnan(col[t - 1]):
                col[t] = col[t - 1]
        # Backward fill
        for t in range(n_visits - 2, -1, -1):
            if np.isnan(col[t]) and not np.isnan(col[t + 1]):
                col[t] = col[t + 1]
    # Zero fill remaining
    arr = np.nan_to_num(arr, nan=0.0)

    return arr[np.newaxis, :, :]  # (1, T, F)


# ---------------------------------------------------------------------------
# Risk classification helpers
# ---------------------------------------------------------------------------

def _classify_risk(prob: float) -> str:
    """Map probability to a clinical risk label."""
    if prob < 0.20:
        return "LOW"
    elif prob < 0.45:
        return "MODERATE"
    elif prob < 0.70:
        return "HIGH"
    else:
        return "VERY HIGH"


def _assess_trend(visit_array: np.ndarray) -> str:
    """
    Assess whether the patient's feature trajectory is improving, stable,
    or worsening using a simple linear slope of the mean feature values
    across visits.
    """
    # Mean feature value per visit → (T,)
    visit_means = visit_array.mean(axis=-1).squeeze()  # (T,)
    if len(visit_means) < 2:
        return "STABLE"

    # Simple linear regression slope
    x = np.arange(len(visit_means), dtype=np.float32)
    slope = np.polyfit(x, visit_means, 1)[0]

    if slope > 0.05:
        return "WORSENING"
    elif slope < -0.05:
        return "IMPROVING"
    else:
        return "STABLE"


def _build_response(
    condition: str,
    prob: float,
    attn_weights: np.ndarray,
    visit_array: np.ndarray,
    n_visits: int,
) -> LongitudinalPredictionResponse:
    """Build the standardised response object."""
    attention_list = [
        VisitAttention(visit_index=i, weight=round(float(w), 4))
        for i, w in enumerate(attn_weights.squeeze())
    ]
    return LongitudinalPredictionResponse(
        condition=condition,
        risk_probability=round(float(prob), 4),
        risk_label=_classify_risk(prob),
        trend=_assess_trend(visit_array),
        num_visits=n_visits,
        visit_attention=attention_list,
        medical_disclaimer=MEDICAL_DISCLAIMER,
    )


# ---------------------------------------------------------------------------
# Heuristic fallback (when no trained model is available)
# ---------------------------------------------------------------------------

def _heuristic_predict(
    visit_array: np.ndarray,
) -> Tuple[float, np.ndarray]:
    """
    Simple heuristic prediction when no trained longitudinal model exists.
    Uses the mean feature magnitude of the latest visit relative to the
    sequence range to estimate risk.  Returns uniform attention weights.
    """
    seq = visit_array.squeeze(0)  # (T, F)
    n_visits = seq.shape[0]

    # Normalise features to 0-1 range across the sequence
    mins = seq.min(axis=0)
    maxs = seq.max(axis=0)
    ranges = maxs - mins
    ranges[ranges == 0] = 1.0
    normed = (seq - mins) / ranges

    # Risk = mean of normalised latest visit features (higher = riskier)
    latest_risk = float(normed[-1].mean())
    prob = np.clip(latest_risk, 0.05, 0.95)

    # Linearly increasing attention (recent visits weighted more)
    weights = np.arange(1, n_visits + 1, dtype=np.float32)
    weights /= weights.sum()

    return prob, weights[np.newaxis, :]  # (1, T)


# ---------------------------------------------------------------------------
# Generic prediction pipeline
# ---------------------------------------------------------------------------

def _predict_longitudinal(
    condition: str,
    visits: list,
    feature_names: List[str],
) -> LongitudinalPredictionResponse:
    """Run longitudinal prediction for any supported condition."""
    if len(visits) < 2:
        raise HTTPException(
            status_code=422,
            detail="Longitudinal prediction requires at least 2 visits.",
        )

    visit_array = _visits_to_array(visits, feature_names)  # (1, T, F)

    model = _load_longitudinal_model(condition)

    if model is not None:
        probs, attn_weights = model.predict_with_attention(visit_array)
        prob = float(probs[0])
    else:
        # Fallback heuristic when no trained model exists
        logger.info(
            "Using heuristic fallback for longitudinal %s prediction "
            "(no trained model available).",
            condition,
        )
        prob, attn_weights = _heuristic_predict(visit_array)

    return _build_response(
        condition=condition,
        prob=prob,
        attn_weights=attn_weights,
        visit_array=visit_array,
        n_visits=len(visits),
    )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


def _validate_patient_context(patient_id: int | None, current_user: models.User) -> None:
    if patient_id is not None and patient_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Patient context does not match the authenticated user",
        )


@router.post("/diabetes", response_model=LongitudinalPredictionResponse)
async def predict_longitudinal_diabetes(
    request: LongitudinalDiabetesRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Predict diabetes risk from a chronological sequence of patient visits.

    Accepts 2+ visit records ordered oldest → newest.  Returns risk probability,
    clinical risk label, trend assessment, and per-visit attention weights
    showing which visits most influenced the prediction.

    **Note**: This is an AI-generated health assessment. Please consult a
    qualified healthcare professional for diagnosis and treatment decisions.
    """
    _validate_patient_context(request.patient_id, current_user)
    return _predict_longitudinal("diabetes", request.visits, DIABETES_FEATURES)


@router.post("/heart", response_model=LongitudinalPredictionResponse)
async def predict_longitudinal_heart(
    request: LongitudinalHeartRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Predict heart disease risk from a chronological sequence of patient visits.

    Accepts 2+ visit records ordered oldest → newest.  Returns risk probability,
    clinical risk label, trend assessment, and per-visit attention weights.
    """
    _validate_patient_context(request.patient_id, current_user)
    return _predict_longitudinal("heart", request.visits, HEART_FEATURES)


@router.post("/liver", response_model=LongitudinalPredictionResponse)
async def predict_longitudinal_liver(
    request: LongitudinalLiverRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Predict liver disease risk from a chronological sequence of patient visits.

    Accepts 2+ visit records ordered oldest → newest.  Returns risk probability,
    clinical risk label, trend assessment, and per-visit attention weights.
    """
    _validate_patient_context(request.patient_id, current_user)
    return _predict_longitudinal("liver", request.visits, LIVER_FEATURES)


@router.post("/kidney", response_model=LongitudinalPredictionResponse)
async def predict_longitudinal_kidney(
    request: LongitudinalKidneyRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Predict kidney disease risk from a chronological sequence of patient visits.

    Accepts 2+ visit records ordered oldest → newest.  Returns risk probability,
    clinical risk label, trend assessment, and per-visit attention weights.
    """
    _validate_patient_context(request.patient_id, current_user)
    return _predict_longitudinal("kidney", request.visits, KIDNEY_FEATURES)
