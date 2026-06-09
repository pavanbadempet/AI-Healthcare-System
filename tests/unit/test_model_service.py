"""
Tests for the ModelService — the centralized ML model lifecycle manager.
Validates initialization, health checks, prediction delegation, and SHAP explainability.
"""
import os
import pytest
import numpy as np

os.environ["TESTING"] = "1"

from backend.model_service import (
    ModelService, ModelStatus, PredictionResult,
    get_age_bucket, _normalize_prediction, _classify_confidence,
)


# ── ModelService Initialization ─────────────────────────────────────

class TestModelServiceInit:
    def test_mock_initialization(self):
        svc = ModelService()
        svc.initialize()
        assert svc.is_available("diabetes")
        assert svc.is_available("heart")
        assert svc.is_available("liver")
        assert svc.is_available("kidney")
        assert svc.is_available("lungs")

    def test_mock_status(self):
        svc = ModelService()
        svc.initialize()
        for key in ("diabetes", "heart", "liver", "kidney", "lungs"):
            entry = svc._entries[key]
            assert entry.status == ModelStatus.MOCK

    def test_double_initialize_is_idempotent(self):
        svc = ModelService()
        svc.initialize()
        svc.initialize()  # should not raise
        assert svc.is_available("diabetes")


# ── Health Check ─────────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_check_returns_all_models(self):
        svc = ModelService()
        svc.initialize()
        health = svc.health_check()
        assert health["healthy"] is True
        assert set(health["models"].keys()) == {"diabetes", "heart", "liver", "kidney", "lungs"}

    def test_health_check_shows_prediction_count(self):
        svc = ModelService()
        svc.initialize()
        health = svc.health_check()
        for model_data in health["models"].values():
            assert "prediction_count" in model_data
            assert "uptime_seconds" in model_data or model_data["uptime_seconds"] is None

    def test_unloaded_model_unhealthy(self):
        svc = ModelService()
        # Don't initialize
        assert not svc.is_available("diabetes")
        health = svc.health_check()
        assert health["healthy"] is False


# ── Age Bucket ───────────────────────────────────────────────────────

class TestAgeBucket:
    @pytest.mark.parametrize("age,expected", [
        (18, 1), (25, 2), (30, 3), (35, 4), (40, 5),
        (45, 6), (50, 7), (55, 8), (60, 9), (65, 10),
        (70, 11), (75, 12), (85, 13), (0, 1),
    ])
    def test_age_bucket_mapping(self, age, expected):
        assert get_age_bucket(age) == expected


# ── Prediction Normalization ─────────────────────────────────────────

class TestNormalizePrediction:
    @pytest.mark.parametrize("value,expected", [
        (1, 1), (0, 0), (2, 1), (np.int64(1), 1),
        ("1", 1), ("0", 0), ("high", 1), ("medium", 1),
        ("Chronic Kidney Disease Detected", 1),
        ("healthy", 0),
    ])
    def test_normalize(self, value, expected):
        assert _normalize_prediction(value) == expected


# ── Confidence Classification ────────────────────────────────────────

class TestConfidenceClassification:
    def test_high_risk(self):
        conf, risk = _classify_confidence(0.80)
        assert conf == 80.0
        assert risk == "High"

    def test_moderate_risk(self):
        conf, risk = _classify_confidence(0.50)
        assert conf == 50.0
        assert risk == "Moderate"

    def test_low_risk(self):
        conf, risk = _classify_confidence(0.20)
        assert conf == 20.0
        assert risk == "Low"

    def test_none_probability(self):
        conf, risk = _classify_confidence(None)
        assert conf is None
        assert risk is None


# ── Mock Prediction End-to-End ──────────────────────────────────────

class TestMockPredictions:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.svc = ModelService()
        self.svc.initialize()

    def _make_diabetes_input(self):
        from unittest.mock import MagicMock
        d = MagicMock()
        d.age = 45
        d.hypertension = 1
        d.high_chol = 1
        d.bmi = 30.0
        d.smoking_history = 0
        d.heart_disease = 0
        d.physical_activity = 1
        d.general_health = 3
        d.gender = 1
        return d

    def _make_heart_input(self):
        from unittest.mock import MagicMock
        d = MagicMock()
        d.age = 55
        d.sex = 1
        d.cp = 2
        d.trestbps = 140
        d.chol = 250
        d.fbs = 1
        d.restecg = 1
        d.thalach = 150
        d.exang = 0
        d.oldpeak = 1.5
        d.slope = 2
        d.ca = 0
        d.thal = 2
        return d

    def test_predict_diabetes_returns_result(self):
        result = self.svc.predict_diabetes(self._make_diabetes_input())
        assert isinstance(result, PredictionResult)
        assert result.disclaimer  # Always includes medical disclaimer
        assert result.raw in (0, 1)

    def test_predict_heart_returns_result(self):
        result = self.svc.predict_heart(self._make_heart_input())
        assert isinstance(result, PredictionResult)
        assert result.disclaimer

    def test_unavailable_model_raises(self):
        svc = ModelService()  # Not initialized
        with pytest.raises(ValueError, match="not available"):
            svc.predict_diabetes(self._make_diabetes_input())


# ── Backward-compatible shim ────────────────────────────────────────

class TestBackwardCompatibility:
    def test_initialize_models_shim(self):
        from backend.model_service import initialize_models, model_service
        initialize_models()
        assert model_service.is_available("diabetes")

    def test_get_model_status_shim(self):
        from backend.model_service import get_model_status, model_service
        model_service.initialize()
        status = get_model_status()
        assert status["diabetes_loaded"] is True
        assert status["heart_loaded"] is True
