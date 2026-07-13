import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from backend import auth, models


def _create_user(db_session, username: str, role: str, facility_id: int | None = None) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        allow_data_collection=1,
        facility_id=facility_id,
        gender="male",
        dob="1990-01-01"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def _create_facility(db_session, name: str) -> models.HospitalFacility:
    facility = models.HospitalFacility(
        name=name,
        facility_type="clinic",
        country="IN",
        region="KA",
        status="active",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility

@patch("backend.core_ai.generate")
@patch("backend.model_service.model_service.predict_heart")
def test_casa_booking_persists_prediction(mock_predict_heart, mock_generate, client, db_session):
    # Setup doctor and patient under the same facility context
    fac = _create_facility(db_session, "Test Clinic")
    patient = _create_user(db_session, "casa_patient", "patient", facility_id=fac.id)
    doctor = _create_user(db_session, "casa_doctor", "doctor", facility_id=fac.id)
    doctor.specialization = "Cardiologist"
    db_session.commit()

    # Mock ML prediction result
    mock_res = MagicMock()
    mock_res.prediction = "High Risk"
    mock_res.confidence = 85.0
    mock_res.risk_level = "High"
    mock_res.disclaimer = "AI Screen only"
    mock_predict_heart.return_value = mock_res

    # Mock LLM generated response to trigger booking action tag
    mock_generate.return_value = f"[BOOKING_ACTION: doctor_id={doctor.id}, date=2028-10-10, time=10:30, reason=Chest pain checkup] Booked!"

    # Perform request to agent chat endpoint
    headers = {"Authorization": f"Bearer {auth.create_access_token({'sub': patient.username})}"}
    response = client.post(
        "/appointments/agent-chat",
        headers=headers,
        json={"message": "I want to book an appointment for heart chest pain.", "history": []}
    )

    assert response.status_code == 200
    res_json = response.json()
    assert res_json["action_triggered"] is True
    assert res_json["booking_details"] is not None

    # Check that Appointment exists in db
    appt = db_session.query(models.Appointment).filter_by(user_id=patient.id).first()
    assert appt is not None
    assert appt.doctor_id == doctor.id
    assert "AI Risk Screen: Heart High Risk" in appt.reason

    # Check that HealthRecord exists in db
    hrec = db_session.query(models.HealthRecord).filter_by(user_id=patient.id).first()
    assert hrec is not None
    assert hrec.record_type == "heart"
    assert "High Risk" in hrec.prediction
    assert "85.0" in hrec.prediction

    # Check data is stored as json
    input_data = json.loads(hrec.data)
    assert input_data["age"] > 0
    assert input_data["sex"] == 1


@patch("backend.agents.scheduling_agent.SchedulingAgent.prefetch_and_index_history")
def test_abdm_consent_granted_triggers_prefetch(mock_prefetch, client, db_session):
    # Setup admin and patient under same context
    fac = _create_facility(db_session, "ABDM Clinic")
    admin = _create_user(db_session, "abdm_admin", "admin", facility_id=fac.id)
    patient = _create_user(db_session, "abdm_patient", "patient", facility_id=fac.id)

    # Create interoperability consent record
    consent = models.InteroperabilityConsent(
        facility_id=fac.id,
        patient_id=patient.id,
        purpose="CARE_MANAGEMENT",
        status="requested",
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(consent)
    db_session.commit()
    db_session.refresh(consent)

    # Perform callback POST indicating GRANTED status
    headers = {"Authorization": f"Bearer {auth.create_access_token({'sub': admin.username})}"}
    payload = {
        "abdm_request_id": "req-123-abc",
        "status": "GRANTED",
        "abdm_consent_id": "consent-abc-123",
        "hi_types": ["OPConsultation"],
        "event_type": "consent_granted",
        "local_consent_id": consent.id,
        "patient_id": patient.id,
        "notification_at": datetime.now(timezone.utc).isoformat()
    }

    response = client.post(
        "/interop/abdm/consent-callbacks",
        headers=headers,
        json=payload
    )

    assert response.status_code == 201

    # Verify prefetch was triggered
    mock_prefetch.assert_called_once()
