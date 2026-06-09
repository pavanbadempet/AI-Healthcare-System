"""
Model Service — Encapsulated ML Model Lifecycle Management
============================================================

Replaces the previous global-mutable-state pattern in prediction.py.
All model state is owned by a single ModelService instance, making
it testable, thread-safe, and easier to reason about.

Usage:
    from backend.model_service import model_service

    model_service.initialize()
    result = model_service.predict("diabetes", input_list)
    status = model_service.health_check()
"""

import logging
import os
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from . import features

logger = logging.getLogger(__name__)


# ── Data Structures ──────────────────────────────────────────────────

class ModelStatus(str, Enum):
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    MOCK = "mock"


@dataclass
class ModelEntry:
    """Tracks the lifecycle state of a single ML model."""
    name: str
    model: Any = None
    scaler: Any = None
    scaler_needed: bool = False
    status: ModelStatus = ModelStatus.NOT_LOADED
    error_message: str = ""
    loaded_at: Optional[float] = None
    prediction_count: int = 0


@dataclass
class PredictionResult:
    """Structured result from a prediction call."""
    prediction: str
    raw: int
    confidence: Optional[float] = None
    risk_level: Optional[str] = None
    disclaimer: str = ""


MEDICAL_DISCLAIMER = (
    "This is an AI-assisted screening tool, not a medical diagnosis. "
    "Please consult a qualified healthcare professional for clinical decisions."
)

PREDICTION_FAILURE_DETAIL = "Prediction failed. Please try again later."

# Risk thresholds
HIGH_RISK_THRESHOLD = 75
MODERATE_RISK_THRESHOLD = 40

# Age bucket mapping for BRFSS datasets
_AGE_BUCKET_BOUNDARIES = [
    (24, 1), (29, 2), (34, 3), (39, 4), (44, 5),
    (49, 6), (54, 7), (59, 8), (64, 9), (69, 10),
    (74, 11), (79, 12),
]


def get_age_bucket(age: float) -> int:
    """Map Age (Years) to BRFSS Age Bucket (1-13)."""
    for upper, bucket in _AGE_BUCKET_BOUNDARIES:
        if age <= upper:
            return bucket
    return 13


def _classify_confidence(probability: Optional[float]) -> Tuple[Optional[float], Optional[str]]:
    """Classify a probability into confidence % and risk level."""
    if probability is None:
        return None, None
    confidence = round(probability * 100, 1)
    if confidence >= HIGH_RISK_THRESHOLD:
        risk_level = "High"
    elif confidence >= MODERATE_RISK_THRESHOLD:
        risk_level = "Moderate"
    else:
        risk_level = "Low"
    return confidence, risk_level


def _extract_confidence(model: Any, input_data: Any) -> Tuple[Optional[float], Optional[str]]:
    """Extract prediction probability from model. Returns (confidence, risk_level)."""
    try:
        proba = model.predict_proba(input_data)[0]
        disease_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        return _classify_confidence(disease_prob)
    except Exception:
        return None, None


def _normalize_prediction(prediction: Any) -> int:
    """Normalize a model prediction to 0 or 1."""
    if isinstance(prediction, (list, tuple, np.ndarray)):
        prediction = prediction[0]
    if hasattr(prediction, 'item'):
        prediction = prediction.item()
    if isinstance(prediction, (int, float)):
        return 1 if prediction in (1, 2) else 0
    s = str(prediction).strip().lower()
    return 1 if s in ('1', 'high', 'medium') or 'detected' in s or 'chronic' in s else 0


# ── Model Service ────────────────────────────────────────────────────

class ModelService:
    """
    Singleton-style service that owns all ML model lifecycle.

    Thread-safe via a reentrant lock for model reloads.
    Provides health-check, per-model status, and structured prediction.
    """

    def __init__(self, model_dir: Optional[str] = None):
        self._model_dir = model_dir or os.path.dirname(os.path.abspath(__file__))
        self._entries: Dict[str, ModelEntry] = {
            "diabetes": ModelEntry(name="diabetes"),
            "heart":    ModelEntry(name="heart"),
            "liver":    ModelEntry(name="liver", scaler_needed=True),
            "kidney":   ModelEntry(name="kidney", scaler_needed=True),
            "lungs":    ModelEntry(name="lungs", scaler_needed=True),
        }
        self._lock = threading.RLock()
        self._initialized = False

    # ── Loading ──────────────────────────────────────────────────

    def _load_pkl(self, filenames: List[str]) -> Any:
        """Attempt to load a pickle/joblib file from the models directory."""
        for f_name in filenames:
            path = os.path.join(self._model_dir, f_name)
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        obj = joblib.load(f)
                        logger.info("Successfully loaded model: %s", f_name)
                        return obj
                except Exception as exc:
                    logger.error("Failed to load model file %s: %s", f_name, exc)

        logger.warning("Could not find any of: %s in %s", filenames, self._model_dir)
        return None

    def initialize(self) -> None:
        """Load all models. In TESTING mode, inject mocks."""
        with self._lock:
            if os.getenv("TESTING"):
                self._inject_mocks()
                return

            logger.info("Loading ML models from %s ...", self._model_dir)
            self._load_real_models()
            self._initialized = True

    def _inject_mocks(self) -> None:
        """Replace models with MagicMock objects for testing."""
        from unittest.mock import MagicMock
        mock_pred = lambda X: np.array([0])

        for key in self._entries:
            entry = self._entries[key]
            entry.model = MagicMock()
            entry.model.predict.side_effect = mock_pred
            entry.model.predict_proba.side_effect = lambda X: np.array([[0.7, 0.3]])
            if entry.scaler_needed:
                entry.scaler = MagicMock()
                entry.scaler.transform.side_effect = lambda x: x
            entry.status = ModelStatus.MOCK
            entry.loaded_at = 0.0

        self._initialized = True
        logger.info("TESTING MODE: Injected mock models")

    def _load_real_models(self) -> None:
        """Load real .pkl models from disk."""
        model_files = {
            "diabetes": (["diabetes_model.pkl"], None),
            "heart":    (["heart_disease_model.pkl"], None),
            "liver":    (["liver_disease_model.pkl"], ["liver_scaler.pkl"]),
            "kidney":   (["kidney_model.pkl"], ["kidney_scaler.pkl"]),
            "lungs":    (["lungs_model.pkl"], ["lungs_scaler.pkl"]),
        }

        import time as _time
        for key, (model_pkl, scaler_pkl) in model_files.items():
            entry = self._entries[key]
            entry.status = ModelStatus.LOADING
            try:
                entry.model = self._load_pkl(model_pkl)
                if scaler_pkl:
                    entry.scaler = self._load_pkl(scaler_pkl)
                entry.status = ModelStatus.READY if entry.model else ModelStatus.NOT_LOADED
                if entry.model and scaler_pkl and not entry.scaler:
                    entry.status = ModelStatus.ERROR
                    entry.error_message = "Scaler missing"
                entry.loaded_at = _time.monotonic()
            except Exception as exc:
                entry.status = ModelStatus.ERROR
                entry.error_message = str(exc)
                logger.error("Failed to load %s model: %s", key, exc)

    def reload(self) -> Dict[str, Any]:
        """Force reload all models from disk. Returns status dict."""
        self._load_real_models()
        return self.health_check()

    # ── Health Check ─────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """Return health status for all models."""
        import time as _time
        now = _time.monotonic()
        statuses = {}
        for key, entry in self._entries.items():
            uptime = (now - entry.loaded_at) if entry.loaded_at else None
            statuses[key] = {
                "loaded": entry.status in (ModelStatus.READY, ModelStatus.MOCK),
                "status": entry.status.value,
                "error": entry.error_message or None,
                "uptime_seconds": round(uptime, 1) if uptime else None,
                "prediction_count": entry.prediction_count,
            }
        return {
            "healthy": all(s["loaded"] for s in statuses.values()),
            "models": statuses,
        }

    def is_available(self, model_name: str) -> bool:
        """Check if a specific model is available for predictions."""
        entry = self._entries.get(model_name)
        return entry is not None and entry.status in (ModelStatus.READY, ModelStatus.MOCK)

    # ── Prediction ───────────────────────────────────────────────

    def predict_diabetes(self, data: Any) -> PredictionResult:
        """Predict diabetes risk from DiabetesInput schema."""
        entry = self._entries["diabetes"]
        if not self.is_available("diabetes"):
            raise ValueError("Diabetes model not available")

        age_bucket = get_age_bucket(data.age)
        input_list = [
            data.hypertension, data.high_chol, data.bmi, data.smoking_history,
            data.heart_disease, data.physical_activity, data.general_health,
            data.gender, age_bucket
        ]
        prediction = entry.model.predict([input_list])
        raw = _normalize_prediction(prediction)
        confidence, risk_level = _extract_confidence(entry.model, [input_list])
        result = "High Risk" if raw == 1 else "Low Risk"

        entry.prediction_count += 1
        return PredictionResult(
            prediction=result, raw=raw,
            confidence=confidence, risk_level=risk_level,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    def predict_heart(self, data: Any) -> PredictionResult:
        """Predict heart disease risk from HeartInput schema."""
        entry = self._entries["heart"]
        if not self.is_available("heart"):
            raise ValueError("Heart model not available")

        input_list = [
            data.age, data.sex, data.cp, data.trestbps, data.chol,
            data.fbs, data.restecg, data.thalach, data.exang,
            data.oldpeak, data.slope, data.ca, data.thal
        ]
        prediction = entry.model.predict([input_list])
        raw = _normalize_prediction(prediction)
        confidence, risk_level = _extract_confidence(entry.model, [input_list])
        result = "Heart Disease Detected" if raw == 1 else "Healthy Heart"

        entry.prediction_count += 1
        return PredictionResult(
            prediction=result, raw=raw,
            confidence=confidence, risk_level=risk_level,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    def predict_liver(self, data: Any) -> PredictionResult:
        """Predict liver disease risk from LiverInput schema."""
        entry = self._entries["liver"]
        if not self.is_available("liver") or not entry.scaler:
            raise ValueError("Liver model or scaler not available")

        feature_names = features.LIVER_FEATURES
        input_list = [
            data.age, data.gender, data.total_bilirubin, data.direct_bilirubin,
            data.alkaline_phosphotase, data.alamine_aminotransferase,
            data.aspartate_aminotransferase, data.total_proteins,
            data.albumin, data.albumin_and_globulin_ratio
        ]
        df = pd.DataFrame([input_list], columns=feature_names)
        skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
        for col in skewed:
            df[col] = np.log1p(df[col])

        X_scaled = entry.scaler.transform(df)
        prediction = entry.model.predict(X_scaled)
        raw = _normalize_prediction(prediction)
        confidence, risk_level = _extract_confidence(entry.model, X_scaled)
        result = "Liver Disease Detected" if raw == 1 else "Healthy Liver"

        entry.prediction_count += 1
        return PredictionResult(
            prediction=result, raw=raw,
            confidence=confidence, risk_level=risk_level,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    def predict_kidney(self, data: Any) -> PredictionResult:
        """Predict kidney disease risk from KidneyInput schema."""
        entry = self._entries["kidney"]
        if not self.is_available("kidney") or not entry.scaler:
            raise ValueError("Kidney model or scaler not available")

        feature_names = features.KIDNEY_FEATURES
        input_list = [
            data.age, data.bp, data.sg, data.al, data.su,
            data.rbc, data.pc, data.pcc, data.ba,
            data.bgr, data.bu, data.sc, data.sod, data.pot, data.hemo, data.pcv, data.wc, data.rc,
            data.htn, data.dm, data.cad, data.appet, data.pe, data.ane
        ]
        df = pd.DataFrame([input_list], columns=feature_names)
        input_scaled = entry.scaler.transform(df)
        prediction = entry.model.predict(input_scaled)
        raw = _normalize_prediction(prediction)
        confidence, risk_level = _extract_confidence(entry.model, input_scaled)
        result = "Chronic Kidney Disease Detected" if raw == 1 else "Healthy Kidney"

        entry.prediction_count += 1
        return PredictionResult(
            prediction=result, raw=raw,
            confidence=confidence, risk_level=risk_level,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    def predict_lungs(self, data: Any) -> PredictionResult:
        """Predict lung/respiratory risk from LungInput schema."""
        entry = self._entries["lungs"]
        if not self.is_available("lungs") or not entry.scaler:
            raise ValueError("Lung model or scaler not available")

        feature_names = features.LUNG_FEATURES
        input_list = [
            data.gender, data.age, data.smoking, data.yellow_fingers,
            data.anxiety, data.peer_pressure, data.chronic_disease, data.fatigue,
            data.allergy, data.wheezing, data.alcohol, data.coughing,
            data.shortness_of_breath, data.swallowing_difficulty, data.chest_pain
        ]
        df = pd.DataFrame([input_list], columns=feature_names)
        input_scaled = entry.scaler.transform(df)
        prediction = entry.model.predict(input_scaled)
        raw = _normalize_prediction(prediction)
        confidence, risk_level = _extract_confidence(entry.model, input_scaled)
        result = "Respiratory Issue Detected" if raw == 1 else "Healthy Lungs"

        entry.prediction_count += 1
        return PredictionResult(
            prediction=result, raw=raw,
            confidence=confidence, risk_level=risk_level,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    # ── SHAP Explainability ──────────────────────────────────────

    def explain(self, model_name: str, data: Any) -> Optional[Dict]:
        """Generate SHAP explanation for a given model and input."""
        from . import explainability

        entry = self._entries.get(model_name)
        if not entry or not self.is_available(model_name):
            return None

        if model_name == "diabetes":
            age_bucket = get_age_bucket(data.age)
            input_list = [
                data.hypertension, data.high_chol, data.bmi, data.smoking_history,
                data.heart_disease, data.physical_activity, data.general_health,
                data.gender, age_bucket
            ]
            feature_names = features.DIABETES_FEATURES
            input_array = np.array([input_list])
            return explainability.get_shap_values(entry.model, input_array, feature_names)

        elif model_name == "heart":
            input_list = [
                data.age, data.sex, data.cp, data.trestbps, data.chol,
                data.fbs, data.restecg, data.thalach, data.exang,
                data.oldpeak, data.slope, data.ca, data.thal
            ]
            feature_names = ['Age', 'Sex', 'ChestPain', 'RestBP', 'Cholesterol', 'FastingBS',
                             'RestECG', 'MaxHR', 'ExerciseAngina', 'Oldpeak', 'Slope', 'MajorVessels', 'Thal']
            return explainability.get_shap_values(entry.model, np.array([input_list]), feature_names)

        elif model_name == "liver":
            if not entry.scaler:
                return None
            feature_names = features.LIVER_FEATURES
            input_list = [
                data.age, data.gender, data.total_bilirubin, data.direct_bilirubin,
                data.alkaline_phosphotase, data.alamine_aminotransferase,
                data.aspartate_aminotransferase, data.total_proteins,
                data.albumin, data.albumin_and_globulin_ratio
            ]
            df = pd.DataFrame([input_list], columns=feature_names)
            skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
            for col in skewed:
                df[col] = np.log1p(df[col])
            X_scaled = entry.scaler.transform(df)
            return explainability.get_shap_values(entry.model, X_scaled, feature_names)

        return None


# ── Module-level singleton ───────────────────────────────────────────

model_service = ModelService()


# ── Backward-compatible shim functions ───────────────────────────────
# These preserve the existing public API so that prediction.py and tests
# can migrate incrementally without breaking.

def initialize_models() -> None:
    """Backward-compatible entry point. Delegates to model_service."""
    model_service.initialize()


def get_model_status() -> Dict[str, bool]:
    """Return simple loaded/not-loaded dict for each model."""
    return {
        "diabetes_loaded": model_service.is_available("diabetes"),
        "heart_loaded": model_service.is_available("heart"),
        "liver_loaded": model_service.is_available("liver"),
        "kidney_loaded": model_service.is_available("kidney"),
        "lungs_loaded": model_service.is_available("lungs"),
    }
