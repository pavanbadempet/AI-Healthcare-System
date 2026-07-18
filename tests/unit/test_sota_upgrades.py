from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sklearn.impute import SimpleImputer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.model_service import model_service
from backend.prediction import initialize_models

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def mock_core_ai_generate(monkeypatch):
    async def mock_generate(*args, **kwargs):
        return "Clinical analysis mock response: This is a mocked clinical narrative."
    monkeypatch.setattr("backend.core_ai.generate", mock_generate)
    try:
        monkeypatch.setattr("backend.prediction.generate", mock_generate)
    except AttributeError:
        pass

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = override_get_db
    initialize_models()
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c
    app.dependency_overrides.clear()

def test_kidney_endpoint_with_imputer_and_conformal(client, db_session):
    # 1. Create a user and log in to get token
    client.post("/signup", json={
        "username": "sotatest",
        "password": "SotaPassword123!",
        "email": "sotatest@test.com",
        "full_name": "SOTA Test",
        "dob": "1990-01-01",
    })
    r = client.post("/token", data={"username": "sotatest", "password": "SotaPassword123!"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # 2. Inject dummy imputer and conformal_q
    from backend import prediction as _pred

    dummy_imputer = SimpleImputer()
    dummy_imputer.fit(np.random.rand(5, 24))

    # Mock the model's predict_proba to return dummy probabilities
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0])
    mock_model.predict_proba.return_value = np.array([[0.8, 0.2]]) # 80% Healthy, 20% Disease

    # Set model service attributes
    model_service._entries["kidney"].model = mock_model
    model_service._entries["kidney"].imputer = dummy_imputer
    model_service._entries["kidney"].conformal_q = 0.7  # 1-q = 0.3 threshold

    # Sync global prediction module model
    _pred.kidney_model = mock_model

    # 3. Call endpoint with missing features (some set to None)
    payload = {
        "age": 45.0,
        "bp": 80.0,
        "sg": 1.020,
        "al": 1.0,
        "su": 0.0,
        "rbc": None, # missing
        "pc": 1,
        "pcc": 0,
        "ba": 0,
        "bgr": 120.0,
        "bu": None, # missing
        "sc": 1.2,
        "sod": 138.0,
        "pot": 4.5,
        "hemo": 15.0,
        "pcv": None, # missing
        "wc": 8000.0,
        "rc": 5.0,
        "htn": 0,
        "dm": 0,
        "cad": 0,
        "appet": 0,
        "pe": 0,
        "ane": 0,
        "gender": 1
    }

    response = client.post("/predict/kidney", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "prediction" in data
    assert "clinical_indices" in data
    clinical = data["clinical_indices"]

    # Conformal checks:
    # Threshold = 1 - 0.7 = 0.3
    # proba for class 0 = 0.8 >= 0.3 -> Included
    # proba for class 1 = 0.2 < 0.3 -> Excluded
    # prediction_set should be [0], uncertainty_status should be "Low Uncertainty"
    assert "conformal_prediction_set" in clinical
    assert clinical["conformal_prediction_set"] == [0]
    assert clinical["uncertainty_status"] == "Low Uncertainty"
    assert clinical["significance_level"] == pytest.approx(0.2812, abs=1e-3)
    assert "triage_recommendation" in clinical
    assert "Routine Monitoring" in clinical["triage_recommendation"]

    # 4. Try high uncertainty (ambiguous case)
    # Both class probabilities >= 1-q (0.3)
    mock_model.predict_proba.return_value = np.array([[0.5, 0.5]])
    response = client.post("/predict/kidney", json=payload, headers=headers)
    clinical = response.json()["clinical_indices"]
    assert clinical["conformal_prediction_set"] == [0, 1]
    assert clinical["uncertainty_status"] == "High Uncertainty (Ambiguous Case)"
    assert "Clinical Triage" in clinical["triage_recommendation"]

    # 5. Try high uncertainty (out-of-distribution case)
    # Neither class probability >= 1-q (0.8)
    model_service._entries["kidney"].conformal_q = 0.2  # 1-q = 0.8
    mock_model.predict_proba.return_value = np.array([[0.5, 0.5]])
    response = client.post("/predict/kidney", json=payload, headers=headers)
    clinical = response.json()["clinical_indices"]
    assert clinical["conformal_prediction_set"] == []
    assert clinical["uncertainty_status"] == "High Uncertainty (Out-of-Distribution Case)"
    assert "Secondary Review" in clinical["triage_recommendation"]


def test_kidney_endpoint_with_class_conditional_conformal(client, db_session):
    # 1. Create a user and log in to get token
    client.post("/signup", json={
        "username": "sotatest2",
        "password": "SotaPassword123!",
        "email": "sotatest2@test.com",
        "full_name": "SOTA Test 2",
        "dob": "1990-01-01",
    })
    r = client.post("/token", data={"username": "sotatest2", "password": "SotaPassword123!"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # 2. Inject dummy imputer and class-conditional conformal_q dict
    from sklearn.impute import SimpleImputer

    from backend import prediction as _pred

    dummy_imputer = SimpleImputer()
    dummy_imputer.fit(np.random.rand(5, 24))

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0])
    mock_model.predict_proba.return_value = np.array([[0.8, 0.2]]) # p0=0.8, p1=0.2

    # Set model service attributes
    model_service._entries["kidney"].model = mock_model
    model_service._entries["kidney"].imputer = dummy_imputer
    # Conformal thresholds dict: 1-q0 = 0.3, 1-q1 = 0.1
    model_service._entries["kidney"].conformal_q = {0: 0.7, 1: 0.9}

    _pred.kidney_model = mock_model

    payload = {
        "age": 45.0,
        "bp": 80.0,
        "sg": 1.020,
        "al": 1.0,
        "su": 0.0,
        "rbc": None,
        "pc": 1,
        "pcc": 0,
        "ba": 0,
        "bgr": 120.0,
        "bu": None,
        "sc": 1.2,
        "sod": 138.0,
        "pot": 4.5,
        "hemo": 15.0,
        "pcv": None,
        "wc": 8000.0,
        "rc": 5.0,
        "htn": 0,
        "dm": 0,
        "cad": 0,
        "appet": 0,
        "pe": 0,
        "ane": 0,
        "gender": 1
    }

    # Check 1: p0=0.8 >= 1-0.7=0.3 (includes 0), p1=0.2 >= 1-0.9=0.1 (includes 1) -> prediction set [0, 1]
    response = client.post("/predict/kidney", json=payload, headers=headers)
    assert response.status_code == 200
    clinical = response.json()["clinical_indices"]
    assert clinical["conformal_prediction_set"] == [0, 1]
    assert clinical["uncertainty_status"] == "High Uncertainty (Ambiguous Case)"

    # Check 2: p0=0.8, p1=0.2. With q0=0.7 (threshold 0.3), q1=0.7 (threshold 0.3) -> prediction set [0]
    model_service._entries["kidney"].conformal_q = {0: 0.7, 1: 0.7}
    response = client.post("/predict/kidney", json=payload, headers=headers)
    clinical = response.json()["clinical_indices"]
    assert clinical["conformal_prediction_set"] == [0]
    assert clinical["uncertainty_status"] == "Low Uncertainty"


def test_clinical_recourse_and_model_provenance(client, db_session):
    # 1. Create a user and log in to get token
    client.post("/signup", json={
        "username": "provenancetest",
        "password": "SotaPassword123!",
        "email": "provenance@test.com",
        "full_name": "Provenance Test",
        "dob": "1990-01-01",
    })
    r = client.post("/token", data={"username": "provenancetest", "password": "SotaPassword123!"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # 2. Mock model service entry for kidney to simulate high-risk (disease detected)
    from sklearn.impute import SimpleImputer

    from backend import prediction as _pred

    dummy_imputer = SimpleImputer()
    dummy_imputer.fit(np.random.rand(5, 24))

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1])
    mock_model.predict_proba.return_value = np.array([[0.2, 0.8]]) # 20% Healthy, 80% Disease (High-Risk)

    # Set model service attributes
    model_service._entries["kidney"].model = mock_model
    model_service._entries["kidney"].imputer = dummy_imputer
    model_service._entries["kidney"].conformal_q = 0.7
    setattr(model_service._entries["kidney"], "model_version", "3.0.0-test")
    setattr(model_service._entries["kidney"], "training_timestamp", "2026-06-18T12:00:00")
    setattr(model_service._entries["kidney"], "model_card_id", "card-kidney-test")

    _pred.kidney_model = mock_model

    payload = {
        "age": 45.0,
        "bp": 130.0, # High BP to trigger recourse modifications
        "sg": 1.020,
        "al": 1.0,
        "su": 0.0,
        "rbc": 0,
        "pc": 1,
        "pcc": 0,
        "ba": 0,
        "bgr": 120.0,
        "bu": 40.0,
        "sc": 1.2,
        "sod": 138.0,
        "pot": 4.5,
        "hemo": 15.0,
        "pcv": 45.0,
        "wc": 8000.0,
        "rc": 5.0,
        "htn": 1, # hypertension to trigger recourse
        "dm": 1, # diabetes to trigger recourse
        "cad": 0,
        "appet": 0,
        "pe": 0,
        "ane": 0,
        "gender": 1
    }

    import backend.core_ai
    import backend.prediction
    print(f"DEBUG: backend.core_ai.generate is {backend.core_ai.generate}")
    print(f"DEBUG: backend.prediction.generate is {getattr(backend.prediction, 'generate', 'NOT FOUND')}")

    response = client.post("/predict/kidney", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "model_metadata" in data
    meta = data["model_metadata"]
    assert meta["model_version"] == "3.0.0-test"
    assert meta["training_timestamp"] == "2026-06-18T12:00:00"
    assert meta["model_card_id"] == "card-kidney-test"

    assert "clinical_indices" in data
    clinical = data["clinical_indices"]
    assert "clinical_recourse" in clinical
    assert "reduce risk probability" in clinical["clinical_recourse"] or "Lifestyle modifications alone" in clinical["clinical_recourse"]

    assert "clinical_narrative" in data
    # Kidney endpoint currently returns empty narrative stub
    assert data["clinical_narrative"] == ""


# --- Merged from test_sota_upgrades_extended.py ---

class TestSemanticCache:
    """Tests for LLM Semantic Caching in core_ai."""

    @pytest.fixture(autouse=True)
    def mock_core_ai_generate(self):
        # Override the module-level autouse mock to let the real generate logic run
        pass

    @pytest.mark.asyncio
    @patch("backend.core_ai.has_gemini_api_key")
    @patch("backend.core_ai.get_ollama_models")
    @patch("backend.core_ai.embed_text")
    @patch("backend.core_ai._generate_cloud")
    @patch("backend.core_ai._generate_gemini")
    async def test_semantic_cache_generate(self, mock_gemini_gen, mock_gen_cloud, mock_embed, mock_get_ollama, mock_has_key):
        import os
        from backend.core_ai import generate, semantic_cache

        # Reset cache
        semantic_cache.clear()

        # Mock Ollama to be unavailable and Gemini API key to exist to force falling back to Gemini
        mock_get_ollama.return_value = []
        mock_has_key.return_value = True
        mock_gen_cloud.return_value = ""

        # Mock embeddings to be identical
        mock_embed.return_value = [0.1] * 768
        mock_gemini_gen.return_value = "Cached narrative text"

        with patch.dict(os.environ, {"SEMANTIC_CACHE_ENABLED": "true"}):
            # First execution (Cache Miss)
            res1 = await generate("Tell me about diabetes", system="MedAssistant")
            assert res1 == "Cached narrative text"
            assert mock_gemini_gen.call_count == 1

            # Second execution (Cache Hit)
            res2 = await generate("Tell me about diabetes", system="MedAssistant")
            assert res2 == "Cached narrative text"
            # Gemini generation should not be called again
            assert mock_gemini_gen.call_count == 1


class TestAdaptiveConformalPrediction:
    """Tests for Adaptive Conformal Prediction (ACP) threshold scaling."""

    def test_acp_missingness_scaling(self):
        from backend.prediction import _calculate_adaptive_conformal_prediction
        # 1. Base case: no missing features (missingness_ratio = 0.0)
        # q = 0.8 -> threshold = 1 - 0.8 = 0.2
        input_list_clean = [1.0] * 10
        metrics_clean = _calculate_adaptive_conformal_prediction(
            proba_positive=0.25,
            conformal_q=0.8,
            input_list=input_list_clean,
            raw_pred=0
        )
        assert metrics_clean["missingness_ratio"] == 0.0
        # p0 = 0.75 >= 0.2 (includes 0), p1 = 0.25 >= 0.2 (includes 1) -> set [0, 1]
        assert metrics_clean["conformal_prediction_set"] == [0, 1]

        # 2. High missingness case: 50% missing (missingness_ratio = 0.5)
        # q is boosted by 0.5 * 0.5 = 0.25
        # adjusted_q = 0.8 + 0.2 * 0.25 = 0.85
        # threshold = 1 - 0.85 = 0.15
        input_list_sparse = [1.0, None, 1.0, None, 1.0, None, 1.0, None, 1.0, None]
        metrics_sparse = _calculate_adaptive_conformal_prediction(
            proba_positive=0.12,
            conformal_q=0.8,
            input_list=input_list_sparse,
            raw_pred=0
        )
        assert metrics_sparse["missingness_ratio"] == 0.5
        assert metrics_sparse["adjusted_thresholds"] > 0.80


import backend.explainability

@pytest.mark.skipif(not backend.explainability.SHAP_AVAILABLE, reason="SHAP not installed")
class TestAttributionDriftMonitoring:
    """Tests for SHAP feature attribution logging and drift report endpoint."""

    def test_drift_report_and_logging(self, client, db_session):
        from backend import models
        # 1. Authenticate user to get admin token
        client.post("/signup", json={
            "username": "adminuser",
            "password": "AdminPassword123!",
            "email": "admin@test.com",
            "full_name": "Admin User",
            "dob": "1990-01-01",
        })
        # Set role as admin
        user = db_session.query(models.User).filter(models.User.username == "adminuser").first()
        user.role = "admin"
        db_session.commit()

        r = client.post("/token", data={"username": "adminuser", "password": "AdminPassword123!"})
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        # 2. Mock model service entry for kidney to log predictions
        from sklearn.impute import SimpleImputer
        from backend import prediction as _pred

        dummy_imputer = SimpleImputer()
        dummy_imputer.fit(np.random.rand(5, 24))

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_model.predict_proba.return_value = np.array([[0.8, 0.2]])

        model_service._entries["kidney"].model = mock_model
        model_service._entries["kidney"].imputer = dummy_imputer
        model_service._entries["kidney"].conformal_q = 0.7
        _pred.kidney_model = mock_model

        # 3. Request predictions to generate attribution logs
        payload = {
            "age": 45.0, "bp": 80.0, "sg": 1.020, "al": 1.0, "su": 0.0,
            "rbc": 0, "pc": 1, "pcc": 0, "ba": 0, "bgr": 120.0,
            "bu": 40.0, "sc": 1.2, "sod": 138.0, "pot": 4.5, "hemo": 15.0,
            "pcv": 45.0, "wc": 8000.0, "rc": 5.0, "htn": 1, "dm": 1,
            "cad": 0, "appet": 0, "pe": 0, "ane": 0, "gender": 1
        }

        mock_explainer = MagicMock()
        mock_explainer.expected_value = 0.5
        mock_explainer.shap_values.return_value = np.random.rand(1, 24)

        async def mock_generate(*args, **kwargs):
            return "Clinical analysis mock response: This is a mocked clinical narrative."

        with patch("shap.TreeExplainer", return_value=mock_explainer), \
             patch("backend.explainability.SHAP_AVAILABLE", True), \
             patch("backend.core_ai.generate", mock_generate):
            # Call predict endpoint
            res = client.post("/predict/kidney", json=payload, headers=headers)
            assert res.status_code == 200

            # Verify attribution logs were written
            from backend.models import DbFeatureAttributionLog
            logs = db_session.query(DbFeatureAttributionLog).all()
            assert len(logs) > 0
            assert logs[0].model_name == "kidney"
            assert "age" in logs[0].attributions

            # 4. Request the admin drift report
            drift_res = client.get("/admin/attribution-drift", headers=headers)
            assert drift_res.status_code == 200
            drift_data = drift_res.json()
            assert drift_data["status"] == "success"
            assert "kidney" in drift_data["models"]
            assert drift_data["models"]["kidney"]["sample_count"] > 0
            assert drift_data["models"]["kidney"]["drift_score"] is not None


class TestSemanticCacheAdminEndpoints:
    """Tests for the semantic cache admin endpoints."""

    def test_semantic_cache_admin_stats_and_clear(self, client, db_session):
        from backend import models
        # 1. Authenticate user to get admin token
        client.post("/signup", json={
            "username": "adminuser_cache",
            "password": "AdminPassword123!",
            "email": "admin_cache@test.com",
            "full_name": "Admin Cache User",
            "dob": "1990-01-01",
        })
        # Set role as admin
        user = db_session.query(models.User).filter(models.User.username == "adminuser_cache").first()
        user.role = "admin"
        db_session.commit()

        r = client.post("/token", data={"username": "adminuser_cache", "password": "AdminPassword123!"})
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        # 2. Get stats (should start empty/cleared)
        from backend.core_ai import semantic_cache
        semantic_cache.clear()

        # Let's seed the cache directly for testing the admin report
        semantic_cache.add("Query 1", [0.1] * 768, "Response 1")

        # 3. Call GET /admin/semantic-cache
        res = client.get("/admin/semantic-cache", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "stats" in data
        assert data["stats"]["size"] == 1
        assert data["stats"]["hits"] == 0
        assert data["stats"]["misses"] == 0
        assert data["stats"]["entries"][0]["query"] == "Query 1"

        # 4. Call DELETE /admin/semantic-cache
        del_res = client.delete("/admin/semantic-cache", headers=headers)
        assert del_res.status_code == 200
        del_data = del_res.json()
        assert del_data["status"] == "success"
        assert del_data["message"] == "Semantic cache evicted successfully"

        # 5. Check stats again
        res_after = client.get("/admin/semantic-cache", headers=headers)
        assert res_after.status_code == 200
        data_after = res_after.json()


