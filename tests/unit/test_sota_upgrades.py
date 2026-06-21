from unittest.mock import MagicMock

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
    assert "Clinical analysis" in data["clinical_narrative"] or len(data["clinical_narrative"]) > 0

