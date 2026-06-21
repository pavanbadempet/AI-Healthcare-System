import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.agents.scribe_agent import ClinicalScribeAgent
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

@pytest.mark.asyncio
async def test_scribe_agent_success(db_session):
    # 1. Seed patient
    patient = models.User(
        username="scribepatient",
        email="scribe@test.com",
        role="patient",
        full_name="Scribe Patient",
        dob="1985-05-15",
        gender=1,
    )
    db_session.add(patient)
    db_session.commit()

    agent = ClinicalScribeAgent(db_session)

    mock_soap_response = {
        "subjective": "Patient reports mild chest pain and dyspnea.",
        "objective": "BP 130/85 mmHg, HR 78 bpm, SpO2 96%.",
        "assessment": "Essential hypertension with coronary artery risk.",
        "plan": "Prescribe Lisinopril 10mg daily. Order follow-up ECG.",
        "icd10_codes": ["I10", "I25.9"],
        "billing_codes": ["99213"],
        "prescriptions": [
            {
                "medication_name": "Lisinopril",
                "dosage": "10mg",
                "frequency": "Once daily",
                "duration": "30 days",
                "quantity_prescribed": 30.0,
            }
        ],
        "billing_items": [
            {
                "description": "Standard Outpatient Visit",
                "amount": 1500.0,
            }
        ],
    }

    with patch("backend.agents.scribe_agent.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = json.dumps(mock_soap_response)

        res = await agent.generate_soap_note(patient.id, "Patient has chest pain.")

        assert "data" in res
        assert res["data"]["subjective"] == "Patient reports mild chest pain and dyspnea."
        assert res["data"]["icd10_codes"] == ["I10", "I25.9"]
        assert res["data"]["prescriptions"][0]["medication_name"] == "Lisinopril"
        assert mock_generate.call_count == 1

def test_scribe_api_endpoints(client, db_session):
    from datetime import datetime

    from backend import auth as backend_auth
    # 1. Create doctor user and patient user
    doctor = models.User(
        username="scribe_doc",
        email="doc@test.com",
        role="doctor",
        hashed_password=backend_auth.get_password_hash("DocPassword123!"),
        facility_id=1,
    )
    patient = models.User(
        username="scribe_pat",
        email="pat@test.com",
        role="patient",
        full_name="EHR Patient",
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
    r = client.post("/v1/token", data={"username": "scribe_doc", "password": "DocPassword123!"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # Call scribe generation endpoint
    mock_soap_response = {
        "subjective": "Patient reports cough.",
        "objective": "Clear lungs.",
        "assessment": "Acute bronchitis.",
        "plan": "Rest and hydration.",
        "icd10_codes": ["J20.9"],
        "billing_codes": ["99212"],
        "prescriptions": [],
        "billing_items": [],
    }

    with patch("backend.agents.scribe_agent.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = json.dumps(mock_soap_response)
        response = client.post(
            f"/v1/predict/scribe/{patient_id}",
            json={"transcript": "Patient has a cough for three days."},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["assessment"] == "Acute bronchitis."

    # Call commit endpoint
    commit_payload = {
        "patient_id": patient_id,
        "subjective": "Patient reports cough.",
        "objective": "Clear lungs.",
        "assessment": "Acute bronchitis.",
        "plan": "Rest and hydration.",
        "icd10_codes": ["J20.9"],
        "billing_codes": ["99212"],
        "prescriptions": [
            {
                "medication_name": "Albuterol inhaler",
                "dosage": "90mcg",
                "frequency": "As needed",
                "duration": "10 days",
                "quantity_prescribed": 1.0,
            }
        ],
        "billing_items": [
            {
                "description": "Telehealth Consultation",
                "amount": 1200.0,
            }
        ],
    }

    commit_resp = client.post(
        "/v1/predict/scribe/commit",
        json=commit_payload,
        headers=headers
    )
    assert commit_resp.status_code == 200
    assert commit_resp.json()["status"] == "success"

    # Verify database commits
    care_event = db_session.query(models.CareEvent).filter_by(patient_id=patient_id).first()
    assert care_event is not None
    assert care_event.event_type == "ambient_scribe_note"
    assert "Acute bronchitis." in care_event.summary

    prescription = db_session.query(models.Prescription).filter_by(patient_id=patient_id).first()
    assert prescription is not None
    assert len(prescription.items) == 1
    assert prescription.items[0].medication_name == "Albuterol inhaler"

    invoice = db_session.query(models.Invoice).filter_by(patient_id=patient_id).first()
    assert invoice is not None
    assert invoice.total_amount == 1200.0
