"""Tests for the longitudinal (time-series) prediction endpoints and models."""

import importlib.util
import numpy as np
import pytest

has_torch = importlib.util.find_spec("torch") is not None


def _auth_headers(client, username="longitudinal_user"):
    signup = client.post("/v1/signup", json={
        "username": username,
        "password": "Password123!",
        "email": f"{username}@example.com",
        "full_name": "Longitudinal Test User",
        "dob": "1990-01-01",
    })
    assert signup.status_code == 200
    token = client.post(
        "/v1/token",
        data={"username": username, "password": "Password123!"},
    )
    assert token.status_code == 200
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Unit: ClinicalTemporalLSTM model
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not has_torch, reason="PyTorch is required for LSTM models")
class TestClinicalTemporalLSTM:
    """Test the sklearn-compliant LSTM wrapper."""

    def test_fit_predict_3d(self):
        """Fit on synthetic 3-D sequences and verify output shapes."""
        from backend.ml.longitudinal_models import ClinicalTemporalLSTM

        rng = np.random.RandomState(42)
        n_samples, seq_len, n_features = 60, 5, 4
        X = rng.randn(n_samples, seq_len, n_features).astype(np.float32)
        y = (X[:, -1, 0] > 0).astype(int)  # label from latest visit

        model = ClinicalTemporalLSTM(
            hidden_dim=16, num_layers=1, epochs=5, batch_size=16, patience=3,
        )
        model.fit(X, y)

        proba = model.predict_proba(X)
        assert proba.shape == (n_samples, 2), f"Expected (60,2), got {proba.shape}"
        assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-5)

        preds = model.predict(X)
        assert preds.shape == (n_samples,)
        assert set(preds).issubset({0, 1})

    def test_predict_with_attention(self):
        """Verify attention weights shape and normalisation."""
        from backend.ml.longitudinal_models import ClinicalTemporalLSTM

        rng = np.random.RandomState(7)
        n, t, f = 20, 4, 3
        X = rng.randn(n, t, f).astype(np.float32)
        y = np.random.randint(0, 2, n)

        model = ClinicalTemporalLSTM(
            hidden_dim=8, num_layers=1, epochs=3, batch_size=10,
        )
        model.fit(X, y)

        probs, attn = model.predict_with_attention(X)
        assert probs.shape == (n,)
        assert attn.shape == (n, t)
        # Attention weights should sum to ~1 per sample
        assert np.allclose(attn.sum(axis=1), 1.0, atol=1e-5)

    def test_2d_fallback(self):
        """2-D input should be treated as single-step sequences."""
        from backend.ml.longitudinal_models import ClinicalTemporalLSTM

        rng = np.random.RandomState(99)
        X = rng.randn(30, 5).astype(np.float32)
        y = np.random.randint(0, 2, 30)

        model = ClinicalTemporalLSTM(
            hidden_dim=8, num_layers=1, epochs=2, batch_size=16,
        )
        model.fit(X, y)
        preds = model.predict(X)
        assert preds.shape == (30,)

    def test_pickle_roundtrip(self):
        """Verify model survives pickle serialisation."""
        import pickle

        from backend.ml.longitudinal_models import ClinicalTemporalLSTM

        rng = np.random.RandomState(1)
        X = rng.randn(40, 3, 4).astype(np.float32)
        y = np.random.randint(0, 2, 40)

        model = ClinicalTemporalLSTM(
            hidden_dim=8, num_layers=1, epochs=3, batch_size=16,
        )
        model.fit(X, y)
        p_before = model.predict_proba(X[:5])

        data = pickle.dumps(model)
        restored = pickle.loads(data)
        p_after = restored.predict_proba(X[:5])

        np.testing.assert_allclose(p_before, p_after, atol=1e-5)


# ---------------------------------------------------------------------------
# Integration: API endpoint tests (heuristic fallback — no trained model)
# ---------------------------------------------------------------------------

class TestLongitudinalEndpoints:
    """Test the FastAPI longitudinal prediction endpoints."""

    @pytest.mark.parametrize("condition", ["diabetes", "heart", "liver", "kidney"])
    def test_longitudinal_prediction_requires_authentication(self, client, condition):
        response = client.post(
            f"/v1/predict/longitudinal/{condition}",
            json={"visits": [{}, {}]},
        )

        assert response.status_code == 401

    def test_diabetes_longitudinal(self, client):
        headers = _auth_headers(client, "longitudinal_diabetes")
        payload = {
            "visits": [
                {"gender": 1, "age": 45, "bmi": 28.0, "hypertension": 0,
                 "heart_disease": 0, "smoking_history": 0, "high_chol": 0,
                 "physical_activity": 1, "general_health": 2},
                {"gender": 1, "age": 46, "bmi": 30.0, "hypertension": 1,
                 "heart_disease": 0, "smoking_history": 0, "high_chol": 1,
                 "physical_activity": 0, "general_health": 3},
                {"gender": 1, "age": 47, "bmi": 32.5, "hypertension": 1,
                 "heart_disease": 1, "smoking_history": 1, "high_chol": 1,
                 "physical_activity": 0, "general_health": 4},
            ],
        }
        resp = client.post(
            "/v1/predict/longitudinal/diabetes",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["condition"] == "diabetes"
        assert 0.0 <= data["risk_probability"] <= 1.0
        assert data["risk_label"] in ("LOW", "MODERATE", "HIGH", "VERY HIGH")
        assert data["trend"] in ("IMPROVING", "STABLE", "WORSENING")
        assert data["num_visits"] == 3
        assert len(data["visit_attention"]) == 3
        assert "medical_disclaimer" in data

    def test_heart_longitudinal(self, client):
        headers = _auth_headers(client, "longitudinal_heart")
        payload = {
            "visits": [
                {"age": 55, "sex": 1, "cp": 1, "trestbps": 130, "chol": 220,
                 "fbs": 0, "restecg": 0, "thalach": 160, "exang": 0,
                 "oldpeak": 0.5, "slope": 1, "ca": 0, "thal": 2},
                {"age": 56, "sex": 1, "cp": 2, "trestbps": 145, "chol": 250,
                 "fbs": 1, "restecg": 1, "thalach": 140, "exang": 1,
                 "oldpeak": 2.0, "slope": 2, "ca": 1, "thal": 3},
            ],
        }
        resp = client.post(
            "/v1/predict/longitudinal/heart",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["condition"] == "heart"
        assert data["num_visits"] == 2

    def test_too_few_visits_rejected(self, client):
        headers = _auth_headers(client, "longitudinal_validation")
        payload = {
            "visits": [
                {"gender": 1, "age": 50, "bmi": 25.0},
            ],
        }
        resp = client.post(
            "/v1/predict/longitudinal/diabetes",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 422  # Validation error: min_length=2

    def test_kidney_longitudinal(self, client):
        headers = _auth_headers(client, "longitudinal_kidney")
        payload = {
            "visits": [
                {"age": 60, "blood_pressure": 80, "serum_creatinine": 1.2,
                 "hemoglobin": 14.0, "albumin": 4.0},
                {"age": 61, "blood_pressure": 90, "serum_creatinine": 2.1,
                 "hemoglobin": 11.0, "albumin": 3.0},
            ],
        }
        resp = client.post(
            "/v1/predict/longitudinal/kidney",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["condition"] == "kidney"
        assert data["num_visits"] == 2
        # Attention weights should sum close to 1
        total_attn = sum(v["weight"] for v in data["visit_attention"])
        assert abs(total_attn - 1.0) < 0.01

    def test_liver_longitudinal(self, client):
        headers = _auth_headers(client, "longitudinal_liver")
        payload = {
            "visits": [
                {"age": 45, "gender": 1, "total_bilirubin": 0.8,
                 "direct_bilirubin": 0.2, "albumin": 4.5},
                {"age": 46, "gender": 1, "total_bilirubin": 2.5,
                 "direct_bilirubin": 1.1, "albumin": 3.2},
            ],
        }
        resp = client.post(
            "/v1/predict/longitudinal/liver",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["condition"] == "liver"

    def test_longitudinal_prediction_rejects_other_patient_context(self, client):
        headers = _auth_headers(client, "longitudinal_context")
        payload = {
            "patient_id": 999999,
            "visits": [
                {"gender": 1, "age": 45, "bmi": 28.0},
                {"gender": 1, "age": 46, "bmi": 29.0},
            ],
        }

        response = client.post(
            "/v1/predict/longitudinal/diabetes",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 403
