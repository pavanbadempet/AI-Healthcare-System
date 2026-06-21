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

import json
import logging
import os
import shutil
import tempfile
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
    imputer: Any = None
    conformal_q: Optional[float] = None
    model_version: str = "2.1.0-extratrees"
    training_timestamp: str = "2026-06-18T00:00:00"
    model_card_id: str = ""
    # ONNX support fields
    onnx_session: Any = None
    scaler_onnx_session: Any = None
    onnx_estimators: Dict[str, Any] = field(default_factory=dict)
    onnx_weights: Optional[List[float]] = None
    is_voting: bool = False


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


def _run_onnx_inference(session: Any, input_data: np.ndarray) -> List[Any]:
    """Helper to run inference on an ONNX session."""
    input_name = session.get_inputs()[0].name
    # Ensure float32 format for standard ONNX conversion
    feed = {input_name: input_data.astype(np.float32)}
    return session.run(None, feed)


def _predict_onnx_probs(entry: ModelEntry, input_data: np.ndarray) -> Tuple[int, float]:
    """
    Run ONNX inference and return (predicted_class, class_1_probability).
    Handles VotingClassifier models and normalizes probability formats.
    """
    if entry.is_voting:
        probs = []
        for name, session in entry.onnx_estimators.items():
            outputs = _run_onnx_inference(session, input_data)
            probabilities = outputs[1]
            if isinstance(probabilities, list) and len(probabilities) > 0 and isinstance(probabilities[0], dict):
                p = probabilities[0].get(1, 0.0)
            elif isinstance(probabilities, np.ndarray):
                p = float(probabilities[0][1]) if probabilities.shape[1] > 1 else float(probabilities[0][0])
            else:
                p = 0.5
            probs.append(p)

        if entry.onnx_weights:
            weights = np.array(entry.onnx_weights)
            avg_prob = np.average(probs, weights=weights)
        else:
            avg_prob = np.mean(probs)

        pred_label = 1 if avg_prob >= 0.5 else 0
        return pred_label, avg_prob
    else:
        outputs = _run_onnx_inference(entry.onnx_session, input_data)
        prediction = outputs[0]
        if isinstance(prediction, np.ndarray):
            pred_label = int(prediction[0])
        else:
            pred_label = int(prediction)

        probabilities = outputs[1]
        if isinstance(probabilities, list) and len(probabilities) > 0 and isinstance(probabilities[0], dict):
            prob = probabilities[0].get(1, 0.0)
        elif isinstance(probabilities, np.ndarray):
            prob = float(probabilities[0][1]) if probabilities.shape[1] > 1 else float(probabilities[0][0])
        else:
            prob = 0.5

        return pred_label, prob


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
        """Attempt to load a pickle/joblib file from the models directory with memory-mapping."""
        for f_name in filenames:
            path = os.path.join(self._model_dir, f_name)
            if os.path.exists(path):
                try:
                    # Use memory mapping to read scikit-learn arrays directly from disk.
                    # This drastically reduces RSS RAM usage and speeds up model loads.
                    obj = joblib.load(path, mmap_mode='r')
                    logger.info("Successfully loaded model via mmap: %s", f_name)
                    return obj
                except Exception as mmap_err:
                    # Fallback to regular file stream loading if memory-mapping fails
                    try:
                        with open(path, 'rb') as f:
                            obj = joblib.load(f)
                            logger.info("Successfully loaded model (fallback): %s", f_name)
                            return obj
                    except Exception:
                        logger.error("Failed to load model file %s: %s", f_name, mmap_err)

        logger.warning("Could not find any of: %s in %s", filenames, self._model_dir)
        return None

    def _download_models_from_hf_if_needed(self) -> None:
        """Download real models from Hugging Face if they are missing or placeholders."""
        hf_token = os.getenv("HF_TOKEN")
        hf_dataset_id = os.getenv("HF_DATASET_ID")
        if not hf_token or not hf_dataset_id:
            logger.info("HF_TOKEN or HF_DATASET_ID not set. Skipping dynamic model download.")
            return

        models_to_check = [
            "diabetes_model.pkl",
            "heart_disease_model.pkl",
            "liver_disease_model.pkl",
            "liver_scaler.pkl",
            "kidney_model.pkl",
            "kidney_scaler.pkl",
            "lungs_model.pkl",
            "lungs_scaler.pkl",
            "longitudinal_diabetes_model.pkl",
            "longitudinal_heart_model.pkl",
            "longitudinal_liver_model.pkl",
            "longitudinal_kidney_model.pkl"
        ]

        needs_download = False
        for filename in models_to_check:
            filepath = os.path.join(self._model_dir, filename)
            # If a model doesn't exist, or is a tiny placeholder (<100KB), we need to download
            if not os.path.exists(filepath) or os.path.getsize(filepath) < 100000:
                if not filename.startswith("longitudinal_") or os.path.exists(filepath):
                    needs_download = True
                    break

        if needs_download or not any(os.path.exists(os.path.join(self._model_dir, f)) for f in models_to_check):
            try:
                logger.info("Real models are missing or placeholders. Attempting to download from Hugging Face private dataset %s...", hf_dataset_id)
                from huggingface_hub import HfApi
                api = HfApi(token=hf_token)
                files = api.list_repo_files(repo_id=hf_dataset_id, repo_type="dataset")
                model_files = [
                    f
                    for f in files
                    if f.startswith("models/") and os.path.basename(f) in models_to_check
                ]

                if not model_files:
                    logger.warning("No files found in 'models/' folder of HF dataset %s", hf_dataset_id)
                    return

                with tempfile.TemporaryDirectory(prefix="healthcare-model-download-") as staging_dir:
                    for file in model_files:
                        filename = os.path.basename(file)
                        logger.info("Downloading %s from HF...", filename)
                        downloaded_path = api.hf_hub_download(
                            repo_id=hf_dataset_id,
                            repo_type="dataset",
                            filename=file,
                            local_dir=staging_dir,
                        )
                        shutil.copy2(downloaded_path, os.path.join(self._model_dir, filename))
                logger.info("Successfully downloaded all models from Hugging Face.")
            except Exception as e:
                logger.error("Failed to download models from Hugging Face: %s", e)

    def initialize(self) -> None:
        """Load all models. In TESTING mode, inject mocks."""
        with self._lock:
            if os.getenv("TESTING"):
                self._inject_mocks()
                return

            # Check and download models from HF if needed
            self._download_models_from_hf_if_needed()

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
        """Load real .pkl models from disk concurrently."""
        model_files = {
            "diabetes": (["diabetes_model.pkl"], None),
            "heart":    (["heart_disease_model.pkl"], None),
            "liver":    (["liver_disease_model.pkl"], ["liver_scaler.pkl"]),
            "kidney":   (["kidney_model.pkl"], ["kidney_scaler.pkl"]),
            "lungs":    (["lungs_model.pkl"], ["lungs_scaler.pkl"]),
        }

        import time as _time
        from concurrent.futures import ThreadPoolExecutor

        def load_single_model(key, model_pkl, scaler_pkl):
            entry = self._entries[key]
            entry.status = ModelStatus.LOADING
            try:
                # Try loading ONNX model first
                try:
                    import onnxruntime as ort
                    onnx_name = model_pkl[0].replace(".pkl", ".onnx")
                    onnx_path = os.path.join(self._model_dir, onnx_name)
                    meta_path = onnx_path.replace(".onnx", ".meta.json")

                    if os.path.exists(onnx_path) or os.path.exists(meta_path):
                        if os.path.exists(meta_path):
                            with open(meta_path, "r") as f_meta:
                                meta = json.load(f_meta)
                            if meta.get("type") == "VotingClassifier":
                                entry.onnx_estimators = {}
                                base_name = onnx_name.replace(".onnx", "")
                                for name in meta["estimators"]:
                                    est_onnx_name = f"{base_name}_{name}.onnx"
                                    est_onnx_path = os.path.join(self._model_dir, est_onnx_name)
                                    entry.onnx_estimators[name] = ort.InferenceSession(est_onnx_path)
                                entry.onnx_weights = meta.get("weights")
                                entry.is_voting = True
                        else:
                            entry.onnx_session = ort.InferenceSession(onnx_path)
                            entry.is_voting = False

                        if scaler_pkl:
                            scaler_onnx_name = scaler_pkl[0].replace(".pkl", ".onnx")
                            scaler_onnx_path = os.path.join(self._model_dir, scaler_onnx_name)
                            if os.path.exists(scaler_onnx_path):
                                entry.scaler_onnx_session = ort.InferenceSession(scaler_onnx_path)

                        entry.model_version = "2.1.0-onnx"
                        entry.training_timestamp = "2026-06-19T00:00:00"
                        entry.model_card_id = f"card-{key}-v2"
                        entry.status = ModelStatus.READY
                        entry.loaded_at = _time.monotonic()
                        logger.info("Successfully loaded ONNX model for %s", key)
                        return
                except Exception as ex_onnx:
                    logger.warning("ONNX load failed for %s, falling back to pickle: %s", key, ex_onnx)

                loaded_obj = self._load_pkl(model_pkl)
                if isinstance(loaded_obj, dict) and "model" in loaded_obj:
                    entry.model = loaded_obj["model"]
                    entry.imputer = loaded_obj.get("imputer")
                    entry.conformal_q = loaded_obj.get("conformal_q")
                    entry.model_version = loaded_obj.get("model_version", "2.1.0-extratrees")
                    entry.training_timestamp = loaded_obj.get("training_timestamp", "2026-06-18T00:00:00")
                    entry.model_card_id = loaded_obj.get("model_card_id", f"card-{key}-v2")
                else:
                    entry.model = loaded_obj
                    entry.imputer = None
                    entry.conformal_q = None
                    entry.model_version = "2.1.0-extratrees"
                    entry.training_timestamp = "2026-06-18T00:00:00"
                    entry.model_card_id = f"card-{key}-v2"

                if scaler_pkl:
                    entry.scaler = self._load_pkl(scaler_pkl)
                entry.status = ModelStatus.READY if entry.model else ModelStatus.NOT_LOADED
                if entry.model and scaler_pkl and not entry.scaler:
                    entry.status = ModelStatus.ERROR
                    entry.error_message = "Scaler missing"
                entry.loaded_at = _time.monotonic()
            except Exception:
                entry.status = ModelStatus.ERROR
                entry.error_message = "Model load failed"
                logger.error("Failed to load %s model", key)

        with ThreadPoolExecutor(max_workers=len(model_files)) as executor:
            futures = [
                executor.submit(load_single_model, key, model_pkl, scaler_pkl)
                for key, (model_pkl, scaler_pkl) in model_files.items()
            ]
            for future in futures:
                future.result()

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

        if entry.onnx_session is not None or entry.is_voting:
            input_array = np.array([input_list], dtype=np.float32)
            raw, prob = _predict_onnx_probs(entry, input_array)
            confidence, risk_level = _classify_confidence(prob)
        else:
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

        if entry.onnx_session is not None or entry.is_voting:
            input_array = np.array([input_list], dtype=np.float32)
            raw, prob = _predict_onnx_probs(entry, input_array)
            confidence, risk_level = _classify_confidence(prob)
        else:
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
        if not self.is_available("liver") or (not entry.scaler and entry.scaler_onnx_session is None):
            raise ValueError("Liver model or scaler not available")

        feature_names = features.LIVER_FEATURES
        input_list = [
            data.age, data.gender, data.total_bilirubin, data.direct_bilirubin,
            data.alkaline_phosphotase, data.alamine_aminotransferase,
            data.aspartate_aminotransferase, data.total_proteins,
            data.albumin, data.albumin_and_globulin_ratio
        ]

        if entry.onnx_session is not None or entry.is_voting:
            df = pd.DataFrame([input_list], columns=feature_names)
            skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
            for col in skewed:
                df[col] = np.log1p(df[col])

            if entry.scaler_onnx_session:
                X_scaled = _run_onnx_inference(entry.scaler_onnx_session, df.to_numpy(dtype=np.float32))[0]
            else:
                X_scaled = entry.scaler.transform(df)

            raw, prob = _predict_onnx_probs(entry, X_scaled)
            confidence, risk_level = _classify_confidence(prob)
        else:
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
        if not self.is_available("kidney") or (not entry.scaler and entry.scaler_onnx_session is None):
            raise ValueError("Kidney model or scaler not available")

        feature_names = features.KIDNEY_FEATURES
        input_list = [
            data.age, data.bp, data.sg, data.al, data.su,
            data.rbc, data.pc, data.pcc, data.ba,
            data.bgr, data.bu, data.sc, data.sod, data.pot, data.hemo, data.pcv, data.wc, data.rc,
            data.htn, data.dm, data.cad, data.appet, data.pe, data.ane
        ]

        if entry.onnx_session is not None or entry.is_voting:
            df = pd.DataFrame([input_list], columns=feature_names)
            if entry.scaler_onnx_session:
                input_scaled = _run_onnx_inference(entry.scaler_onnx_session, df.to_numpy(dtype=np.float32))[0]
            else:
                input_scaled = entry.scaler.transform(df)

            raw, prob = _predict_onnx_probs(entry, input_scaled)
            confidence, risk_level = _classify_confidence(prob)
        else:
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
        if not self.is_available("lungs") or (not entry.scaler and entry.scaler_onnx_session is None):
            raise ValueError("Lung model or scaler not available")

        feature_names = features.LUNG_FEATURES
        input_list = [
            data.gender, data.age, data.smoking, data.yellow_fingers,
            data.anxiety, data.peer_pressure, data.chronic_disease, data.fatigue,
            data.allergy, data.wheezing, data.alcohol, data.coughing,
            data.shortness_of_breath, data.swallowing_difficulty, data.chest_pain
        ]

        if entry.onnx_session is not None or entry.is_voting:
            df = pd.DataFrame([input_list], columns=feature_names)
            if entry.scaler_onnx_session:
                input_scaled = _run_onnx_inference(entry.scaler_onnx_session, df.to_numpy(dtype=np.float32))[0]
            else:
                input_scaled = entry.scaler.transform(df)

            raw, prob = _predict_onnx_probs(entry, input_scaled)
            confidence, risk_level = _classify_confidence(prob)
        else:
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
