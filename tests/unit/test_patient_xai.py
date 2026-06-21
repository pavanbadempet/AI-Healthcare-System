from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.model_service import model_service
from backend.prediction import _generate_patient_explanation, _log_feature_attributions, initialize_models

# Create an isolated test DB
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


class TestPatientExplainableAI:
    """Unit tests for the Patient-Facing Explainable AI (XAI) feature."""

    def test_log_feature_attributions_returns_dict(self, db_session):
        # Setup mock tree estimator
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_model.predict_proba.return_value = np.array([[0.8, 0.2]])

        # Mock SHAP TreeExplainer
        mock_explainer = MagicMock()
        mock_explainer.expected_value = 0.5
        mock_explainer.shap_values.return_value = np.array([[0.1, -0.05, 0.2]])

        with patch("shap.TreeExplainer", return_value=mock_explainer):
            attributions = _log_feature_attributions(
                db=db_session,
                model_name="diabetes",
                model_version="1.0.0",
                imputed_list=[1.0, 2.0, 3.0],
                feature_names=["f1", "f2", "f3"],
                raw_pred=0,
                model=mock_model
            )
            assert attributions is not None
            assert "f1" in attributions
            assert attributions["f1"] == 0.1
            assert attributions["f2"] == -0.05
            assert attributions["f3"] == 0.2

    @pytest.mark.asyncio
    @patch("backend.core_ai.generate")
    async def test_generate_patient_explanation(self, mock_generate):
        mock_generate.return_value = "Patient explanation: Your blood sugar is normal. Keep exercising!"
        explanation = await _generate_patient_explanation(
            model_name="diabetes",
            prediction="Low Risk",
            confidence=85.0,
            risk_level="Low",
            attributions={"bmi": 0.05, "physical_activity": -0.1}
        )
        assert "diabetes" in mock_generate.call_args[1]["prompt"].lower()
        assert "physical_activity" in mock_generate.call_args[1]["prompt"]
        assert explanation == "Patient explanation: Your blood sugar is normal. Keep exercising!"

    def test_predict_endpoints_include_xai_fields(self, client, db_session):
        # 1. Sign up user
        client.post("/signup", json={
            "username": "pat_xai",
            "password": "Password123!",
            "email": "patxai@test.com",
            "full_name": "Pat XAI",
            "dob": "1990-01-01",
        })
        r = client.post("/token", data={"username": "pat_xai", "password": "Password123!"})
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        # 2. Setup mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_model.predict_proba.return_value = np.array([[0.8, 0.2]])

        from sklearn.impute import SimpleImputer
        dummy_imputer = SimpleImputer()
        dummy_imputer.fit(np.random.rand(5, 9))

        model_service._entries["diabetes"].model = mock_model
        model_service._entries["diabetes"].imputer = dummy_imputer
        model_service._entries["diabetes"].conformal_q = 0.8

        from backend import prediction as _pred
        _pred.diabetes_model = mock_model

        # 3. Request prediction
        payload = {
            "gender": 1,
            "age": 45.0,
            "hypertension": 0,
            "heart_disease": 0,
            "smoking_history": 0,
            "bmi": 24.5,
            "high_chol": 0,
            "physical_activity": 1,
            "general_health": 2
        }

        mock_explainer = MagicMock()
        mock_explainer.expected_value = 0.5
        mock_explainer.shap_values.return_value = np.array([[0.01, -0.02, 0.05, 0.0, 0.0, -0.1, 0.0, 0.0, 0.0]])

        async def mock_generate_narrative(*args, **kwargs):
            return "Narrative response"

        with patch("shap.TreeExplainer", return_value=mock_explainer), \
             patch("backend.core_ai.generate", mock_generate_narrative):
            res = client.post("/predict/diabetes", json=payload, headers=headers)
            assert res.status_code == 200
            data = res.json()
            assert "attributions" in data
            assert "patient_explanation" in data
            assert data["patient_explanation"] == "Narrative response"
            assert "bmi" in data["attributions"]
            assert data["attributions"]["bmi"] == 0.05
