from datetime import datetime, timedelta
from unittest.mock import patch

from backend import auth, models


def _create_user(db_session, username: str, role: str, facility_id: int = 1) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        full_name=f"{username} User",
        facility_id=facility_id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def _auth_headers(username: str) -> dict[str, str]:
    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}

def test_create_appointment_success(client, db_session):
    _create_user(db_session, "appt_patient", "patient", facility_id=1)
    doc_user = _create_user(db_session, "appt_doctor", "doctor", facility_id=1)
    doc_user.specialization = "Cardiology"
    db_session.commit()

    tomorrow = datetime.now() + timedelta(days=1)

    payload = {
        "doctor_id": doc_user.id,
        "specialist": "Cardiology",
        "date": tomorrow.strftime("%Y-%m-%d"),
        "time": "10:00",
        "reason": "Routine Checkup"
    }

    patient_headers = _auth_headers("appt_patient")

    doc_user_id = doc_user.id

    with patch("backend.appointments.email_service.send_booking_confirmation") as mock_email:
        response = client.post("/appointments/", json=payload, headers=patient_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["specialist"] == "Cardiology"
        assert data["doctor_id"] == doc_user_id
        mock_email.assert_called_once()

def test_get_appointments(client, db_session):
    pat_user = _create_user(db_session, "appt_patient2", "patient", facility_id=1)
    doc_user = _create_user(db_session, "appt_doctor2", "doctor", facility_id=1)
    doc_user.specialization = "Cardiology"

    # create an appointment
    appt = models.Appointment(
        facility_id=1,
        user_id=pat_user.id,
        doctor_id=doc_user.id,
        specialist="Cardiology",
        date_time=datetime.now() + timedelta(days=1),
        reason="Test appt",
        status="Scheduled"
    )
    db_session.add(appt)
    db_session.commit()

    patient_headers = _auth_headers("appt_patient2")
    response = client.get("/appointments/", headers=patient_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_doctors(client, db_session):
    _create_user(db_session, "appt_patient3", "patient", facility_id=1)
    doc_user = _create_user(db_session, "appt_doctor3", "doctor", facility_id=1)
    doc_user.specialization = "Cardiology"
    db_session.commit()

    patient_headers = _auth_headers("appt_patient3")
    response = client.get("/appointments/doctors", headers=patient_headers)
    assert response.status_code == 200

    # Should at least contain appt_doctor3
    assert any(doc["full_name"] == "appt_doctor3 User" for doc in response.json())

def test_create_appointment_past_date(client, db_session):
    _create_user(db_session, "appt_patient4", "patient", facility_id=1)
    doc_user = _create_user(db_session, "appt_doctor4", "doctor", facility_id=1)
    doc_user.specialization = "Cardiology"
    db_session.commit()

    yesterday = datetime.now() - timedelta(days=1)

    payload = {
        "doctor_id": doc_user.id,
        "specialist": "Cardiology",
        "date": yesterday.strftime("%Y-%m-%d"),
        "time": "10:00",
        "reason": "Routine Checkup"
    }

    patient_headers = _auth_headers("appt_patient4")
    response = client.post("/appointments/", json=payload, headers=patient_headers)
    assert response.status_code == 400
    assert "future" in response.json()["detail"].lower()
