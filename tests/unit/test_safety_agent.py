import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.agents.safety_agent import PrescribingSafetyAgent
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
async def test_safety_agent_runs_compatibility(db_session):
    # 1. Seed patient with demographics and prior conditions
    patient = models.User(
        username="safety_pat",
        email="safety@test.com",
        role="patient",
        full_name="Safety Patient",
        dob="1975-06-20",
        gender=0,
        existing_ailments="Chronic Kidney Disease Stage 3, Penicillin allergy",
    )
    db_session.add(patient)
    db_session.commit()

    # 2. Add an active prescription
    active_presc = models.Prescription(
        patient_id=patient.id,
        status="active",
        facility_id=1,
    )
    db_session.add(active_presc)
    db_session.commit()

    item = models.PrescriptionItem(
        prescription_id=active_presc.id,
        medication_name="Metformin",
        dosage="500mg",
        frequency="Twice daily",
        duration="90 days",
        quantity_prescribed=180.0,
        status="dispensed",
    )
    db_session.add(item)

    # 3. Add an ML risk prediction health record
    from datetime import datetime
    prediction_record = models.HealthRecord(
        user_id=patient.id,
        record_type="kidney",
        prediction="High Risk (82% probability)",
        timestamp=datetime.now(),
    )
    db_session.add(prediction_record)
    db_session.commit()

    agent = PrescribingSafetyAgent(db_session)

    mock_safety_response = {
        "alerts": [
            {
                "type": "interaction",
                "severity": "critical",
                "message": "Metformin is contraindicated with Contrast Media due to high kidney disease risk.",
                "evidence": "Lactic acidosis risk increased in Stage 3 CKD."
            }
        ]
    }

    with patch("backend.agents.safety_agent.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = json.dumps(mock_safety_response)

        res = await agent.check_prescription_safety(
            patient_id=patient.id,
            medication_name="Contrast Media",
            dosage="50ml",
            frequency="Once",
            duration="1 day",
            additional_allergies=["Sulfa"]
        )

        assert "alerts" in res
        assert len(res["alerts"]) == 1
        assert res["alerts"][0]["severity"] == "critical"
        assert "Metformin is contraindicated" in res["alerts"][0]["message"]
        assert mock_generate.call_count == 1

def test_check_safety_api_endpoint(client, db_session):
    from backend import auth as backend_auth
    # 1. Create doctor user and patient user
    doctor = models.User(
        username="safety_doc",
        email="safety_doc@test.com",
        role="doctor",
        hashed_password=backend_auth.get_password_hash("DocPassword123!"),
        facility_id=1,
    )
    patient = models.User(
        username="safety_pat_api",
        email="pat_api@test.com",
        role="patient",
        full_name="Safety Patient API",
        facility_id=1,
    )
    db_session.add(doctor)
    db_session.add(patient)
    db_session.commit()

    # Assign doctor to patient via appointment
    from datetime import datetime
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
    r = client.post("/v1/token", data={"username": "safety_doc", "password": "DocPassword123!"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # Setup mock response
    mock_safety_response = {
        "alerts": [
            {
                "type": "allergy",
                "severity": "warning",
                "message": "Potential cross-reactivity with recorded allergy.",
                "evidence": "Penicillin allergic patients may react."
            }
        ]
    }

    with patch("backend.agents.safety_agent.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = json.dumps(mock_safety_response)

        response = client.post(
            "/v1/pharmacy/check-safety",
            json={
                "patient_id": patient_id,
                "medication_name": "Amoxicillin",
                "dosage": "500mg",
                "frequency": "Three times daily",
                "duration": "7 days",
                "additional_allergies": ["Penicillin"]
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["severity"] == "warning"
        assert "cross-reactivity" in data["alerts"][0]["message"]
