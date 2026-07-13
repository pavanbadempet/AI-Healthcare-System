from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.database import Base, get_db
from backend.main import app
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

def test_counterfactual_recourse_diabetes(client, db_session):
    from datetime import datetime

    from backend import auth as backend_auth
    # 1. Create doctor user and patient user
    doctor = models.User(
        username="cf_doc",
        email="cf_doc@test.com",
        role="doctor",
        hashed_password=backend_auth.get_password_hash("DocPassword123!"),
        facility_id=1,
    )
    patient = models.User(
        username="cf_pat",
        email="cf_pat@test.com",
        role="patient",
        full_name="CF Patient",
        facility_id=1,
    )
    db_session.add(doctor)
    db_session.add(patient)
    db_session.commit()

    # Assign doctor to patient via appointment
    appt = models.Appointment(
        user_id=patient.id,
        doctor_id=doctor.id,
        date_time=datetime.now(),
        status="Scheduled"
    )
    db_session.add(appt)
    db_session.commit()
    patient_id = patient.id

    # Log in as doctor
    r = client.post("/v1/token", data={"username": "cf_doc", "password": "DocPassword123!"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # Mock models and predict_proba to control recourse optimization
    mock_model = MagicMock()
    def mock_predict_proba(X):
        hypertension = X[0][0]
        if hypertension == 1.0:
            return [[0.3, 0.7]]
        else:
            return [[0.6, 0.4]]
    mock_model.predict_proba.side_effect = mock_predict_proba

    from backend import prediction as _pred
    original_model = _pred.diabetes_model
    _pred.diabetes_model = mock_model

    try:
        payload = {
            "target_model": "diabetes",
            "features": {
                "hypertension": 1.0,
                "high_chol": 1.0,
                "bmi": 28.0,
                "smoking_history": 1.0,
                "heart_disease": 0.0,
                "physical_activity": 1.0,
                "general_health": 3.0,
                "gender": 1.0,
                "age": 45.0
            }
        }

        response = client.post(
            f"/v1/predict/counterfactual/{patient_id}",
            json=payload,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["baseline_risk"] == 0.7
        assert data["optimized_risk"] == 0.4
        assert data["changes_applied"]["smoking_history"] == "Quit smoking"
        assert data["changes_applied"]["high_chol"] == "Control cholesterol (target High Chol to No)"
        assert data["changes_applied"]["hypertension"] == "Manage hypertension (target Hypertension to No)"
        assert data["recourse_recommendation"]["hypertension"] == 0.0
        assert data["recourse_recommendation"]["high_chol"] == 0.0
        assert data["recourse_recommendation"]["smoking_history"] == 0.0
    finally:
        _pred.diabetes_model = original_model

def test_counterfactual_recourse_heart(client, db_session):
    from datetime import datetime

    from backend import auth as backend_auth
    # Create doctor user and patient user
    doctor = models.User(
        username="cf_doc2",
        email="cf_doc2@test.com",
        role="doctor",
        hashed_password=backend_auth.get_password_hash("DocPassword123!"),
        facility_id=1,
    )
    patient = models.User(
        username="cf_pat2",
        email="cf_pat2@test.com",
        role="patient",
        full_name="CF Patient 2",
        facility_id=1,
    )
    db_session.add(doctor)
    db_session.add(patient)
    db_session.commit()

    # Assign doctor to patient via appointment
    appt = models.Appointment(
        user_id=patient.id,
        doctor_id=doctor.id,
        date_time=datetime.now(),
        status="Scheduled"
    )
    db_session.add(appt)
    db_session.commit()
    patient_id = patient.id

    # Log in as doctor
    r = client.post("/v1/token", data={"username": "cf_doc2", "password": "DocPassword123!"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # Mock models and predict_proba
    mock_model = MagicMock()
    def mock_predict_proba(X):
        bp = X[0][3]
        if bp > 120.0:
            return [[0.2, 0.8]]
        else:
            return [[0.7, 0.3]]
    mock_model.predict_proba.side_effect = mock_predict_proba

    from backend import prediction as _pred
    original_model = _pred.heart_model
    _pred.heart_model = mock_model

    try:
        payload = {
            "target_model": "heart",
            "features": {
                "age": 60.0,
                "sex": 1.0,
                "cp": 2.0,
                "trestbps": 150.0,
                "chol": 240.0,
                "fbs": 0.0,
                "restecg": 1.0,
                "thalach": 140.0,
                "exang": 0.0,
                "oldpeak": 1.5,
                "slope": 1.0,
                "ca": 0.0,
                "thal": 2.0,
                "smoker": 1
            }
        }

        response = client.post(
            f"/v1/predict/counterfactual/{patient_id}",
            json=payload,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["baseline_risk"] == 0.8
        assert data["optimized_risk"] == 0.3
        assert data["changes_applied"]["smoker"] == "Stop smoking"
        assert "Reduce resting blood pressure" in data["changes_applied"]["trestbps"]
    finally:
        _pred.heart_model = original_model
