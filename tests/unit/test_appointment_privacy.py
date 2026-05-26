from datetime import datetime
from unittest.mock import patch

from backend import auth, models


def _create_user(
    db_session,
    username: str,
    role: str,
    *,
    full_name: str | None = None,
    specialization: str | None = None,
    facility_id: int | None = None,
) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=full_name,
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        specialization=specialization,
        facility_id=facility_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}


def _create_facility(db_session, name: str) -> models.HospitalFacility:
    facility = models.HospitalFacility(
        name=name,
        facility_type="hospital",
        country="India",
        status="active",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility


def _create_appointment(
    db_session,
    patient: models.User,
    doctor: models.User,
    reason: str,
    *,
    facility_id: int | None = None,
) -> models.Appointment:
    appointment = models.Appointment(
        facility_id=facility_id,
        user_id=patient.id,
        doctor_id=doctor.id,
        specialist="General Physician",
        date_time=datetime(2099, 6, 1, 9, 0),
        reason=reason,
        status="Scheduled",
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


def _booking_payload(
    doctor_id: int | None,
    reason: str = "Follow-up",
    *,
    date: str = "2099-06-01",
    time: str = "09:00",
    specialist: str = "General Physician",
) -> dict:
    return {
        "doctor_id": doctor_id,
        "specialist": specialist,
        "date": date,
        "time": time,
        "reason": reason,
    }


def test_doctor_listing_returns_stored_specialization_and_fallback(client, db_session):
    viewer = _create_user(db_session, "doctor_directory_viewer", "patient")
    cardiologist = _create_user(
        db_session,
        "cardio_doc",
        "doctor",
        full_name="Dr Cardio",
        specialization="Cardiology",
    )
    generalist = _create_user(db_session, "general_doc", "doctor", full_name="Dr General")

    response = client.get("/appointments/doctors", headers=_auth_headers(viewer.username))

    assert response.status_code == 200
    doctors = {doctor["id"]: doctor for doctor in response.json()}
    assert doctors[cardiologist.id]["full_name"] == "Dr Cardio"
    assert doctors[cardiologist.id]["specialization"] == "Cardiology"
    assert doctors[generalist.id]["specialization"] == "General Physician"


def test_unauthenticated_user_cannot_list_doctors(client, db_session):
    _create_user(db_session, "public_directory_doctor", "doctor")

    response = client.get("/appointments/doctors")

    assert response.status_code == 401


def test_patient_doctor_listing_hides_doctors_from_other_facilities(client, db_session):
    primary_facility = _create_facility(db_session, "Primary Appointment Hospital")
    other_facility = _create_facility(db_session, "Other Appointment Hospital")
    patient = _create_user(
        db_session,
        "facility_directory_patient",
        "patient",
        facility_id=primary_facility.id,
    )
    local_doctor = _create_user(
        db_session,
        "facility_directory_local_doctor",
        "doctor",
        facility_id=primary_facility.id,
    )
    legacy_doctor = _create_user(db_session, "facility_directory_legacy_doctor", "doctor")
    other_doctor = _create_user(
        db_session,
        "facility_directory_other_doctor",
        "doctor",
        facility_id=other_facility.id,
    )

    response = client.get(
        "/appointments/doctors",
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 200
    doctor_ids = {doctor["id"] for doctor in response.json()}
    assert local_doctor.id in doctor_ids
    assert legacy_doctor.id in doctor_ids
    assert other_doctor.id not in doctor_ids


def test_facility_admin_doctor_listing_is_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Admin Doctor Directory Primary")
    other_facility = _create_facility(db_session, "Admin Doctor Directory Other")
    admin = _create_user(
        db_session,
        "appointment_directory_facility_admin",
        "admin",
        facility_id=primary_facility.id,
    )
    local_doctor = _create_user(
        db_session,
        "appointment_directory_admin_local_doctor",
        "doctor",
        facility_id=primary_facility.id,
    )
    other_doctor = _create_user(
        db_session,
        "appointment_directory_admin_other_doctor",
        "doctor",
        facility_id=other_facility.id,
    )
    legacy_doctor = _create_user(db_session, "appointment_directory_admin_legacy_doctor", "doctor")
    local_doctor_id = local_doctor.id
    other_doctor_id = other_doctor.id
    legacy_doctor_id = legacy_doctor.id

    response = client.get("/appointments/doctors", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    doctor_ids = {doctor["id"] for doctor in response.json()}
    assert local_doctor_id in doctor_ids
    assert other_doctor_id not in doctor_ids
    assert legacy_doctor_id not in doctor_ids


def test_doctor_profile_can_store_specialization(client, db_session):
    doctor = _create_user(db_session, "profile_specialist_doctor", "doctor")

    update_response = client.put(
        "/profile",
        json={"specialization": "Endocrinology"},
        headers=_auth_headers(doctor.username),
    )
    get_response = client.get("/profile", headers=_auth_headers(doctor.username))

    assert update_response.status_code == 200
    assert update_response.json()["user"]["specialization"] == "Endocrinology"
    assert get_response.status_code == 200
    assert get_response.json()["specialization"] == "Endocrinology"


def test_patient_cannot_book_appointment_with_non_doctor_user(client, db_session):
    patient = _create_user(db_session, "booking_patient", "patient")
    non_doctor = _create_user(db_session, "not_a_doctor", "patient")

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(non_doctor.id),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selected doctor not found"
    assert db_session.query(models.Appointment).count() == 0
    send_email.assert_not_called()


def test_patient_cannot_book_appointment_with_missing_doctor(client, db_session):
    patient = _create_user(db_session, "missing_doctor_patient", "patient")

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(99999),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selected doctor not found"
    assert db_session.query(models.Appointment).count() == 0
    send_email.assert_not_called()


def test_patient_can_book_appointment_with_doctor(client, db_session):
    patient = _create_user(db_session, "valid_booking_patient", "patient")
    doctor = _create_user(db_session, "valid_doctor", "doctor")
    patient_id = patient.id
    doctor_id = doctor.id

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor_id, reason="Valid consult"),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert response.json()["doctor_id"] == doctor_id
    assert response.json()["user_id"] == patient_id
    assert db_session.query(models.Appointment).count() == 1
    send_email.assert_called_once()


def test_patient_cannot_book_appointment_with_doctor_from_another_facility(client, db_session):
    patient_facility = _create_facility(db_session, "Patient Booking Facility")
    doctor_facility = _create_facility(db_session, "Doctor Booking Facility")
    patient = _create_user(
        db_session,
        "cross_facility_booking_patient",
        "patient",
        facility_id=patient_facility.id,
    )
    doctor = _create_user(
        db_session,
        "cross_facility_booking_doctor",
        "doctor",
        facility_id=doctor_facility.id,
    )

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor.id, reason="Cross facility consult"),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Appointment participants must belong to the same facility"
    assert db_session.query(models.Appointment).count() == 0
    send_email.assert_not_called()


def test_patient_booking_persists_shared_facility_id(client, db_session):
    facility = _create_facility(db_session, "Shared Booking Facility")
    facility_id = facility.id
    patient = _create_user(
        db_session,
        "shared_facility_booking_patient",
        "patient",
        facility_id=facility_id,
    )
    doctor = _create_user(
        db_session,
        "shared_facility_booking_doctor",
        "doctor",
        facility_id=facility_id,
    )

    with patch("backend.email_service.send_booking_confirmation"):
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor.id, reason="Same facility consult"),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert response.json()["facility_id"] == facility_id
    appointment = db_session.query(models.Appointment).one()
    assert appointment.facility_id == facility_id


def test_patient_booking_uses_doctor_specialization_not_client_specialist(client, db_session):
    patient = _create_user(db_session, "authoritative_patient", "patient")
    doctor = _create_user(
        db_session,
        "authoritative_doctor",
        "doctor",
        full_name="Dr Heart",
        specialization="Cardiology",
    )

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(
                doctor.id,
                reason="Chest discomfort follow-up",
                specialist="Dermatology",
            ),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert response.json()["specialist"] == "Cardiology"
    appointment = db_session.query(models.Appointment).one()
    assert appointment.specialist == "Cardiology"
    send_email.assert_called_once()
    assert send_email.call_args.kwargs["doctor_name"] == "Dr Heart"


def test_patient_must_select_doctor_id(client, db_session):
    patient = _create_user(db_session, "missing_doctor_id_patient", "patient")

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(None),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selected doctor not found"
    assert db_session.query(models.Appointment).count() == 0
    send_email.assert_not_called()


def test_patient_cannot_book_past_appointment(client, db_session):
    patient = _create_user(db_session, "past_slot_patient", "patient")
    doctor = _create_user(db_session, "past_slot_doctor", "doctor")

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor.id, date="2000-01-01", time="09:00"),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Appointment time must be in the future"
    assert db_session.query(models.Appointment).count() == 0
    send_email.assert_not_called()


def test_patient_cannot_double_book_doctor_active_slot(client, db_session):
    patient = _create_user(db_session, "double_booking_patient", "patient")
    other_patient = _create_user(db_session, "double_booking_other_patient", "patient")
    doctor = _create_user(db_session, "double_booking_doctor", "doctor")
    existing = models.Appointment(
        user_id=other_patient.id,
        doctor_id=doctor.id,
        specialist="General Physician",
        date_time=datetime(2099, 6, 1, 9, 0),
        reason="Existing appointment",
        status="Scheduled",
    )
    db_session.add(existing)
    db_session.commit()

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor.id),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Doctor already has an active appointment at that time"
    assert db_session.query(models.Appointment).count() == 1
    send_email.assert_not_called()


def test_patient_can_book_cancelled_slot(client, db_session):
    patient = _create_user(db_session, "cancelled_slot_patient", "patient")
    other_patient = _create_user(db_session, "cancelled_slot_other_patient", "patient")
    doctor = _create_user(db_session, "cancelled_slot_doctor", "doctor")
    cancelled = models.Appointment(
        user_id=other_patient.id,
        doctor_id=doctor.id,
        specialist="General Physician",
        date_time=datetime(2099, 6, 1, 9, 0),
        reason="Cancelled appointment",
        status="Cancelled",
    )
    db_session.add(cancelled)
    db_session.commit()

    with patch("backend.email_service.send_booking_confirmation"):
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor.id),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert db_session.query(models.Appointment).count() == 2


def test_reschedule_rejects_past_slot(client, db_session):
    patient = _create_user(db_session, "reschedule_past_patient", "patient")
    doctor = _create_user(db_session, "reschedule_past_doctor", "doctor")
    appointment = _create_appointment(db_session, patient, doctor, "Future visit")

    response = client.put(
        f"/appointments/{appointment.id}/reschedule",
        params={"date": "2000-01-01", "time": "09:00"},
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Appointment time must be in the future"


def test_reschedule_rejects_duplicate_active_doctor_slot(client, db_session):
    patient = _create_user(db_session, "reschedule_duplicate_patient", "patient")
    other_patient = _create_user(db_session, "reschedule_duplicate_other", "patient")
    doctor = _create_user(db_session, "reschedule_duplicate_doctor", "doctor")
    appointment = _create_appointment(db_session, patient, doctor, "Move me")
    other = models.Appointment(
        user_id=other_patient.id,
        doctor_id=doctor.id,
        specialist="General Physician",
        date_time=datetime(2099, 6, 2, 10, 0),
        reason="Existing slot",
        status="Rescheduled",
    )
    db_session.add(other)
    db_session.commit()

    response = client.put(
        f"/appointments/{appointment.id}/reschedule",
        params={"date": "2099-06-02", "time": "10:00"},
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Doctor already has an active appointment at that time"


def test_doctor_lists_only_assigned_appointments(client, db_session):
    assigned_doctor = _create_user(db_session, "doctor_assigned", "doctor")
    other_doctor = _create_user(db_session, "doctor_other", "doctor")
    patient_one = _create_user(db_session, "patient_one", "patient")
    patient_two = _create_user(db_session, "patient_two", "patient")
    assigned = _create_appointment(db_session, patient_one, assigned_doctor, "Assigned visit")
    _create_appointment(db_session, patient_two, other_doctor, "Other doctor visit")

    response = client.get("/appointments/", headers=_auth_headers(assigned_doctor.username))

    assert response.status_code == 200
    appointments = response.json()
    assert [appointment["id"] for appointment in appointments] == [assigned.id]
    assert appointments[0]["doctor_id"] == assigned_doctor.id


def test_admin_still_lists_all_appointments(client, db_session):
    admin = _create_user(db_session, "appointment_admin", "admin")
    doctor_one = _create_user(db_session, "doctor_one", "doctor")
    doctor_two = _create_user(db_session, "doctor_two", "doctor")
    patient_one = _create_user(db_session, "patient_alpha", "patient")
    patient_two = _create_user(db_session, "patient_beta", "patient")
    first = _create_appointment(db_session, patient_one, doctor_one, "First visit")
    second = _create_appointment(db_session, patient_two, doctor_two, "Second visit")

    response = client.get("/appointments/", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    assert [appointment["id"] for appointment in response.json()] == [first.id, second.id]


def test_facility_admin_appointment_list_is_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Appointment List Primary")
    other_facility = _create_facility(db_session, "Appointment List Other")
    admin = _create_user(db_session, "appointment_list_facility_admin", "admin", facility_id=primary_facility.id)
    local_doctor = _create_user(db_session, "appointment_list_local_doctor", "doctor", facility_id=primary_facility.id)
    local_patient = _create_user(db_session, "appointment_list_local_patient", "patient", facility_id=primary_facility.id)
    other_doctor = _create_user(db_session, "appointment_list_other_doctor", "doctor", facility_id=other_facility.id)
    other_patient = _create_user(db_session, "appointment_list_other_patient", "patient", facility_id=other_facility.id)
    local_appointment = _create_appointment(
        db_session,
        local_patient,
        local_doctor,
        "Local visit",
        facility_id=primary_facility.id,
    )
    local_appointment_id = local_appointment.id
    _create_appointment(
        db_session,
        other_patient,
        other_doctor,
        "Other visit",
        facility_id=other_facility.id,
    )

    response = client.get("/appointments/", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    assert [appointment["id"] for appointment in response.json()] == [local_appointment_id]


def test_facility_admin_cannot_cancel_other_facility_appointment(client, db_session):
    primary_facility = _create_facility(db_session, "Appointment Cancel Primary")
    other_facility = _create_facility(db_session, "Appointment Cancel Other")
    admin = _create_user(db_session, "appointment_cancel_facility_admin", "admin", facility_id=primary_facility.id)
    other_doctor = _create_user(db_session, "appointment_cancel_other_doctor", "doctor", facility_id=other_facility.id)
    other_patient = _create_user(db_session, "appointment_cancel_other_patient", "patient", facility_id=other_facility.id)
    appointment = _create_appointment(
        db_session,
        other_patient,
        other_doctor,
        "Other facility visit",
        facility_id=other_facility.id,
    )
    appointment_id = appointment.id

    response = client.put(
        f"/appointments/{appointment_id}/cancel",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Appointment resource is outside the user's facility"
    assert db_session.get(models.Appointment, appointment_id).status == "Scheduled"
