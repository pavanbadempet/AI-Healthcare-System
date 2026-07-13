import json
from unittest.mock import AsyncMock, patch

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
        # Seed default facility
        facility = models.HospitalFacility(id=1, name="Primary Test Facility")
        db.add(facility)
        db.commit()
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

def _get_auth_headers(client, db_session, username, role="admin"):
    from backend import auth as backend_auth
    user = models.User(
        username=username,
        email=f"{username}@test.com",
        role=role,
        hashed_password=backend_auth.get_password_hash("Password123!"),
        facility_id=1,
    )
    db_session.add(user)
    db_session.commit()
    user_id = user.id
    r = client.post("/v1/token", data={"username": username, "password": "Password123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, user_id

@pytest.mark.asyncio
async def test_pharmacy_pricing_compare(client, db_session):
    headers, _ = _get_auth_headers(client, db_session, "pharm_user", "patient")
    r = client.get("/v1/pharmacy/compare-pricing?medication_name=Metformin", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["medication"] == "Metformin"
    assert len(data["prices"]) == 5
    assert data["prices"][0]["chain"] == "Costco Pharmacy"

@pytest.mark.asyncio
async def test_pharmacy_generic_substitution(client, db_session):
    headers, _ = _get_auth_headers(client, db_session, "pharm_doc", "doctor")
    r = client.get("/v1/pharmacy/generic-substitute?branded_name=Lipitor", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["substituted"] is True
    assert data["generic_name"] == "Atorvastatin"
    assert data["savings"] == 85.0

@pytest.mark.asyncio
async def test_diagnosis_consensus(client, db_session):
    headers, doc_id = _get_auth_headers(client, db_session, "cons_doc", "doctor")
    
    # Create patient and assign doctor via appointment
    patient = models.User(
        username="cons_patient",
        email="patient@test.com",
        role="patient",
        facility_id=1,
        existing_ailments="No chronic ailments"
    )
    db_session.add(patient)
    db_session.commit()
    patient_id = patient.id
    
    from datetime import datetime
    appt = models.Appointment(
        user_id=patient_id,
        doctor_id=doc_id,
        date_time=datetime.now(),
        status="Scheduled"
    )
    db_session.add(appt)
    
    # Seed high glucose vitals and low diabetes risk to trigger conflict
    vitals = models.VitalObservation(
        patient_id=patient_id,
        blood_glucose=180.0,
        observed_at=datetime.now()
    )
    db_session.add(vitals)
    
    record = models.HealthRecord(
        user_id=patient_id,
        record_type="diabetes",
        prediction="Low Risk",
        timestamp=datetime.now()
    )
    db_session.add(record)
    db_session.commit()

    mock_consensus = {
        "consensus_level": "major_conflict",
        "summary": "AI Clinician Consensus: Diagnostic mismatch identified.",
        "detailed_audit": "Vitals show hyperglycemia but model risk is low. HbA1c review recommended.",
        "recommended_tests": ["HbA1c test"]
    }

    with patch("backend.core_ai.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = json.dumps(mock_consensus)
        
        r = client.get(f"/v1/predict/consensus/{patient_id}", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["consensus_level"] == "major_conflict"
        assert "HbA1c" in data["recommended_tests"][0]

@pytest.mark.asyncio
async def test_esi_triage_queue(client, db_session):
    headers, _ = _get_auth_headers(client, db_session, "triage_doc", "doctor")
    
    # Create critical patient
    patient = models.User(username="crit_pat", email="crit@test.com", role="patient", facility_id=1)
    db_session.add(patient)
    db_session.commit()
    patient_id = patient.id
    
    from datetime import datetime
    vitals = models.VitalObservation(
        patient_id=patient_id,
        heart_rate=170.0,  # Critical ESI 1
        observed_at=datetime.now()
    )
    db_session.add(vitals)
    db_session.commit()

    r = client.get("/v1/hospital/triage-queue", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_waiting"] >= 1
    assert data["queue"][0]["esi_level"] == 1

@pytest.mark.asyncio
async def test_abdm_external_records(client, db_session):
    headers, doc_id = _get_auth_headers(client, db_session, "ext_doc", "doctor")
    patient = models.User(username="ext_pat", email="extpat@test.com", role="patient", facility_id=1)
    db_session.add(patient)
    db_session.commit()
    patient_id = patient.id
    
    from datetime import datetime
    appt = models.Appointment(
        user_id=patient_id,
        doctor_id=doc_id,
        date_time=datetime.now(),
        status="Scheduled"
    )
    db_session.add(appt)
    db_session.commit()

    r = client.get(f"/v1/interop/external-records/{patient_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["external_records"]) == 3
    assert data["external_records"][0]["source_facility"] == "City General Hospital"

@pytest.mark.asyncio
async def test_health_passport_qr(client, db_session):
    headers, pat_id = _get_auth_headers(client, db_session, "passport_pat", "patient")
    r = client.get(f"/v1/interop/health-passport/{pat_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "qr_code_url" in data
    assert data["status"] == "active_passport"

@pytest.mark.asyncio
async def test_home_lab_kits(client, db_session):
    headers, pat_id = _get_auth_headers(client, db_session, "kit_pat", "patient")
    
    # Order kit
    r = client.post(
        "/v1/diagnostics/lab-kits",
        json={"patient_id": pat_id, "kit_type": "HbA1c test", "shipping_address": "123 Main St"},
        headers=headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ordered"
    assert data["kit_type"] == "HbA1c test"

    # List kits
    r_list = client.get(f"/v1/diagnostics/lab-kits/{pat_id}", headers=headers)
    assert r_list.status_code == 200
    kits = r_list.json()
    assert kits["total_kits"] == 1
    assert kits["kits"][0]["kit_type"] == "HbA1c test"

@pytest.mark.asyncio
async def test_special_care_booking(client, db_session):
    headers, pat_id = _get_auth_headers(client, db_session, "spec_pat", "patient")
    r = client.post(
        "/v1/appointments/special-care",
        json={
            "patient_id": pat_id,
            "specialist": "Gynecology",
            "date_time": "2026-06-25T10:00:00",
            "reason": "Routine Consultation",
            "request_female_clinician": True,
            "home_visit_van": True
        },
        headers=headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["female_clinician_assigned"] is True
    assert data["home_visit_arranged"] is True

@pytest.mark.asyncio
async def test_specialist_referral_matcher(client, db_session):
    headers, pat_id = _get_auth_headers(client, db_session, "ref_pat", "patient")
    
    # Seed high risk disease records
    from datetime import datetime
    db_session.add(models.HealthRecord(
        user_id=pat_id,
        record_type="heart",
        prediction="High Risk (92%)",
        timestamp=datetime.now()
    ))
    db_session.commit()

    r = client.get(f"/v1/appointments/recommend-specialists/{pat_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_recommendations"] == 1
    assert data["recommended_specialties"][0]["specialty"] == "Cardiology"

@pytest.mark.asyncio
async def test_procedure_cost_estimator(client, db_session):
    headers, _ = _get_auth_headers(client, db_session, "cost_pat", "patient")
    r = client.get("/v1/billing/estimate?procedure_type=MRI&insurance_provider=Medicare", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["procedure_type"] == "MRI"
    assert data["insurance_provider"] == "Medicare"
    assert data["patient_responsibility"] == 140.0  # 10% of 1400
