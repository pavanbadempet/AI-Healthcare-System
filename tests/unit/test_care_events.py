from backend import auth, models


def _create_user(
    db_session,
    username: str,
    role: str,
    *,
    facility_id: int | None = None,
) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        allow_data_collection=1,
        facility_id=facility_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


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


def _assign_doctor(db_session, patient_id: int, doctor_id: int) -> models.Encounter:
    department = models.Department(
        name=f"Events Department {patient_id}-{doctor_id}",
        department_type="OPD",
        status="active",
    )
    db_session.add(department)
    db_session.flush()
    encounter = models.Encounter(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department.id,
        encounter_type="OPD",
        reason="Event review",
        status="open",
    )
    db_session.add(encounter)
    db_session.commit()
    db_session.refresh(encounter)
    return encounter


def _add_event(
    db_session,
    *,
    patient_id: int,
    facility_id: int | None = None,
    actor_user_id: int | None = None,
    event_type: str = "SYNTHETIC_EVENT",
    title: str = "Synthetic event",
    severity: str = "info",
) -> models.CareEvent:
    event = models.CareEvent(
        facility_id=facility_id,
        patient_id=patient_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        title=title,
        summary="Synthetic event summary for dashboard workflow.",
        severity=severity,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def test_patient_event_feed_is_scoped_to_current_patient(client, db_session):
    patient = _create_user(db_session, "events_patient", "patient")
    other_patient = _create_user(db_session, "events_other_patient", "patient")
    patient_username = patient.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    own_event = _add_event(db_session, patient_id=patient_id, event_type="OWN_EVENT")
    _add_event(db_session, patient_id=other_patient_id, event_type="OTHER_EVENT")

    response = client.get("/events/patient/feed", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert [event["id"] for event in response.json()["events"]] == [own_event.id]
    assert response.json()["next_after_id"] == own_event.id


def test_admin_recent_event_feed_supports_after_id_cursor(client, db_session):
    admin = _create_user(db_session, "events_admin", "admin")
    patient = _create_user(db_session, "events_admin_patient", "patient")
    admin_username = admin.username
    patient_id = patient.id
    first = _add_event(db_session, patient_id=patient_id, event_type="FIRST_EVENT")
    second = _add_event(db_session, patient_id=patient_id, event_type="SECOND_EVENT")

    response = client.get(
        f"/events/admin/recent?after_id={first.id}",
        headers=_auth_headers(admin_username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert [event["id"] for event in payload["events"]] == [second.id]
    assert payload["next_after_id"] == second.id


def test_facility_admin_recent_event_feed_is_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Events Admin Recent Primary")
    other_facility = _create_facility(db_session, "Events Admin Recent Other")
    admin = _create_user(db_session, "events_recent_facility_admin", "admin", facility_id=primary_facility.id)
    patient = _create_user(db_session, "events_recent_facility_patient", "patient", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "events_recent_other_patient", "patient", facility_id=other_facility.id)
    local_event = _add_event(
        db_session,
        facility_id=primary_facility.id,
        patient_id=patient.id,
        event_type="LOCAL_RECENT_EVENT",
    )
    _add_event(
        db_session,
        facility_id=other_facility.id,
        patient_id=other_patient.id,
        event_type="OTHER_RECENT_EVENT",
    )

    response = client.get("/events/admin/recent", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert [event["id"] for event in payload["events"]] == [local_event.id]
    assert payload["next_after_id"] == local_event.id


def test_admin_patient_event_feed_is_scoped_to_requested_patient(client, db_session):
    admin = _create_user(db_session, "events_patient_feed_admin", "admin")
    patient = _create_user(db_session, "events_patient_feed_patient", "patient")
    other_patient = _create_user(db_session, "events_patient_feed_other", "patient")
    admin_username = admin.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    event = _add_event(db_session, patient_id=patient_id, event_type="ADMIN_PATIENT_EVENT")
    _add_event(db_session, patient_id=other_patient_id, event_type="OTHER_PATIENT_EVENT")

    response = client.get(
        f"/events/admin/patients/{patient_id}/feed",
        headers=_auth_headers(admin_username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert [item["id"] for item in payload["events"]] == [event.id]
    assert payload["next_after_id"] == event.id
    assert payload["clinical_safety_note"] == "Care events are operational records and do not replace clinician review."


def test_facility_admin_patient_event_feed_rejects_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Events Admin Patient Primary")
    other_facility = _create_facility(db_session, "Events Admin Patient Other")
    admin = _create_user(db_session, "events_patient_facility_admin", "admin", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "events_patient_other_facility", "patient", facility_id=other_facility.id)
    _add_event(
        db_session,
        facility_id=other_facility.id,
        patient_id=other_patient.id,
        event_type="OTHER_PATIENT_FACILITY_EVENT",
    )

    response = client.get(
        f"/events/admin/patients/{other_patient.id}/feed",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Care event resource is outside the user's facility"


def test_admin_patient_event_feed_requires_admin(client, db_session):
    patient = _create_user(db_session, "events_patient_feed_self", "patient")
    patient_username = patient.username
    patient_id = patient.id
    _add_event(db_session, patient_id=patient_id, event_type="PATIENT_PRIVATE_EVENT")

    response = client.get(
        f"/events/admin/patients/{patient_id}/feed",
        headers=_auth_headers(patient_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_facility_admin_doctor_event_feed_rejects_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Events Doctor Admin Primary")
    other_facility = _create_facility(db_session, "Events Doctor Admin Other")
    admin = _create_user(db_session, "events_doctor_facility_admin", "admin", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "events_doctor_other_patient", "patient", facility_id=other_facility.id)
    _add_event(
        db_session,
        facility_id=other_facility.id,
        patient_id=other_patient.id,
        event_type="OTHER_DOCTOR_ROUTE_EVENT",
    )

    response = client.get(
        f"/events/doctor/patients/{other_patient.id}/feed",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Care event resource is outside the user's facility"


def test_assigned_doctor_can_view_patient_event_feed(client, db_session):
    doctor = _create_user(db_session, "events_doctor", "doctor")
    patient = _create_user(db_session, "events_doctor_patient", "patient")
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    _assign_doctor(db_session, patient_id, doctor_id)
    event = _add_event(db_session, patient_id=patient_id, event_type="DOCTOR_EVENT")

    response = client.get(
        f"/events/doctor/patients/{patient_id}/feed",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 200
    assert response.json()["patient_id"] == patient_id
    assert [item["id"] for item in response.json()["events"]] == [event.id]


def test_unassigned_doctor_cannot_view_patient_event_feed(client, db_session):
    assigned_doctor = _create_user(db_session, "events_assigned_doctor", "doctor")
    other_doctor = _create_user(db_session, "events_other_doctor", "doctor")
    patient = _create_user(db_session, "events_private_patient", "patient")
    other_username = other_doctor.username
    patient_id = patient.id
    _assign_doctor(db_session, patient_id, assigned_doctor.id)
    _add_event(db_session, patient_id=patient_id, event_type="PRIVATE_EVENT")

    response = client.get(
        f"/events/doctor/patients/{patient_id}/feed",
        headers=_auth_headers(other_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_cross_facility_appointment_does_not_grant_doctor_event_feed(client, db_session):
    first_facility = _create_facility(db_session, "Events North Clinic")
    second_facility = _create_facility(db_session, "Events South Clinic")
    doctor = _create_user(db_session, "events_tenant_doctor", "doctor")
    patient = _create_user(db_session, "events_tenant_patient", "patient")
    doctor_id = doctor.id
    patient_id = patient.id
    doctor_username = doctor.username
    doctor.facility_id = first_facility.id
    patient.facility_id = second_facility.id
    db_session.add(models.Appointment(
        user_id=patient_id,
        doctor_id=doctor_id,
        specialist="General Physician",
        date_time=first_facility.created_at,
        reason="Legacy cross-facility appointment",
        status="Scheduled",
    ))
    db_session.commit()
    _add_event(db_session, patient_id=patient_id, event_type="TENANT_PRIVATE_EVENT")

    response = client.get(
        f"/events/doctor/patients/{patient_id}/feed",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_admin_event_metrics_group_by_type_and_severity(client, db_session):
    admin = _create_user(db_session, "events_metrics_admin", "admin")
    patient = _create_user(db_session, "events_metrics_patient", "patient")
    admin_username = admin.username
    patient_id = patient.id
    _add_event(db_session, patient_id=patient_id, event_type="NURSING_TASK_CREATED", severity="info")
    _add_event(db_session, patient_id=patient_id, event_type="MONITORING_SIGNAL", severity="warning")

    response = client.get("/events/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_events"] == 2
    assert payload["events_by_type"]["NURSING_TASK_CREATED"] == 1
    assert payload["events_by_type"]["MONITORING_SIGNAL"] == 1
    assert payload["events_by_severity"]["warning"] == 1


def test_facility_admin_event_metrics_are_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Events Metrics Primary")
    other_facility = _create_facility(db_session, "Events Metrics Other")
    admin = _create_user(db_session, "events_metrics_facility_admin", "admin", facility_id=primary_facility.id)
    patient = _create_user(db_session, "events_metrics_facility_patient", "patient", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "events_metrics_other_patient", "patient", facility_id=other_facility.id)
    _add_event(
        db_session,
        facility_id=primary_facility.id,
        patient_id=patient.id,
        event_type="LOCAL_METRIC_EVENT",
        severity="warning",
    )
    _add_event(
        db_session,
        facility_id=other_facility.id,
        patient_id=other_patient.id,
        event_type="OTHER_METRIC_EVENT",
        severity="critical",
    )

    response = client.get("/events/admin/metrics", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_events"] == 1
    assert payload["events_by_type"] == {"LOCAL_METRIC_EVENT": 1}
    assert payload["events_by_severity"] == {"warning": 1}
