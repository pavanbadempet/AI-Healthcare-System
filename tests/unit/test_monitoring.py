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


def _assign_patient_to_doctor(
    db_session,
    patient_id: int,
    doctor_id: int,
    *,
    facility_id: int | None = None,
) -> models.Department:
    department = models.Department(
        name=f"Monitoring Department {patient_id}-{doctor_id}",
        facility_id=facility_id,
        department_type="OPD",
        status="active",
    )
    db_session.add(department)
    db_session.flush()
    encounter = models.Encounter(
        facility_id=facility_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department.id,
        encounter_type="OPD",
        reason="Monitoring setup",
        status="open",
    )
    db_session.add(encounter)
    db_session.commit()
    db_session.refresh(department)
    return department


def _vitals_payload(patient_id: int, department_id: int | None = None) -> dict:
    return {
        "patient_id": patient_id,
        "department_id": department_id,
        "source": "device",
        "heart_rate": 128,
        "systolic_bp": 142,
        "diastolic_bp": 92,
        "spo2": 91,
        "temperature_c": 38.2,
        "respiratory_rate": 24,
    }


def test_patient_can_submit_own_vitals_and_get_review_signals(client, db_session):
    patient = _create_user(db_session, "monitor_patient", "patient")
    patient_username = patient.username
    patient_id = patient.id

    response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(patient_username),
        json=_vitals_payload(patient_id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["vital"]["patient_id"] == patient_id
    assert payload["signals"]
    assert {signal["signal_type"] for signal in payload["signals"]} >= {"oxygen_saturation", "blood_pressure"}
    assert all("review" in signal["summary"].lower() for signal in payload["signals"])
    assert "diagnos" not in response.text.lower()


def test_vital_submission_requires_at_least_one_measurement(client, db_session):
    patient = _create_user(db_session, "monitor_empty_vitals_patient", "patient")

    response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(patient.username),
        json={
            "patient_id": patient.id,
            "source": "device",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one vital measurement is required"
    assert db_session.query(models.VitalObservation).count() == 0
    assert db_session.query(models.CareEvent).count() == 0


def test_vital_submission_rejects_impossible_spo2(client, db_session):
    patient = _create_user(db_session, "monitor_invalid_spo2_patient", "patient")

    response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(patient.username),
        json={
            **_vitals_payload(patient.id),
            "spo2": 101,
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"][0]
    assert detail["loc"] == ["body", "spo2"]
    assert "between 0 and 100" in detail["msg"]
    assert db_session.query(models.VitalObservation).count() == 0
    assert db_session.query(models.CareEvent).count() == 0


def test_vitals_and_signals_persist_facility_context(client, db_session):
    facility = _create_facility(db_session, "Monitoring Facility Context")
    facility_id = facility.id
    doctor = _create_user(db_session, "monitor_facility_doctor", "doctor", facility_id=facility_id)
    patient = _create_user(db_session, "monitor_facility_patient", "patient", facility_id=facility_id)
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    department = _assign_patient_to_doctor(db_session, patient_id, doctor_id, facility_id=facility_id)
    department_id = department.id

    response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(doctor_username),
        json=_vitals_payload(patient_id, department_id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["vital"]["facility_id"] == facility_id
    assert {signal["facility_id"] for signal in payload["signals"]} == {facility_id}
    event_facilities = {
        event.facility_id
        for event in db_session.query(models.CareEvent).filter(
            models.CareEvent.event_type.in_(["VITALS_RECORDED", "MONITORING_SIGNAL"])
        )
    }
    assert event_facilities == {facility_id}


def test_patient_cannot_submit_vitals_for_another_patient(client, db_session):
    patient = _create_user(db_session, "monitor_blocked_patient", "patient")
    other_patient = _create_user(db_session, "monitor_other_patient", "patient")
    patient_username = patient.username
    other_patient_id = other_patient.id

    response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(patient_username),
        json=_vitals_payload(other_patient_id),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Patients can submit only their own vitals"


def test_facility_admin_cannot_submit_vitals_for_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Monitoring Admin Primary")
    other_facility = _create_facility(db_session, "Monitoring Admin Other")
    admin = _create_user(db_session, "monitor_facility_admin", "admin", facility_id=primary_facility.id)
    patient = _create_user(db_session, "monitor_other_facility_patient", "patient", facility_id=other_facility.id)
    admin_username = admin.username
    patient_id = patient.id

    response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(admin_username),
        json=_vitals_payload(patient_id),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Monitoring resource is outside the user's facility"


def test_vital_department_must_match_encounter_department(client, db_session):
    doctor = _create_user(db_session, "monitor_dept_doctor", "doctor")
    patient = _create_user(db_session, "monitor_dept_patient", "patient")
    doctor_username = doctor.username
    patient_id = patient.id
    _assign_patient_to_doctor(db_session, patient_id, doctor.id)
    other_department = models.Department(
        name="Monitoring Other Department",
        department_type="OPD",
        status="active",
    )
    db_session.add(other_department)
    db_session.commit()
    db_session.refresh(other_department)
    encounter = db_session.query(models.Encounter).filter_by(patient_id=patient_id).one()

    response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(doctor_username),
        json={
            **_vitals_payload(patient_id, other_department.id),
            "encounter_id": encounter.id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Encounter department must match vital department"


def test_doctor_can_submit_and_review_assigned_patient_signals(client, db_session):
    doctor = _create_user(db_session, "monitor_doctor", "doctor")
    patient = _create_user(db_session, "monitor_assigned_patient", "patient")
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    department = _assign_patient_to_doctor(db_session, patient_id, doctor_id)

    create_response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(doctor_username),
        json=_vitals_payload(patient_id, department.id),
    )
    assert create_response.status_code == 200

    review_response = client.get(
        f"/monitoring/doctor/patients/{patient_id}/signals",
        headers=_auth_headers(doctor_username),
    )

    assert review_response.status_code == 200
    payload = review_response.json()
    assert payload["patient_id"] == patient_id
    assert payload["open_signals"]
    assert payload["latest_vitals"][0]["patient_id"] == patient_id


def test_assigned_doctor_resolves_monitoring_signal(client, db_session):
    doctor = _create_user(db_session, "monitor_resolve_doctor", "doctor")
    patient = _create_user(db_session, "monitor_resolve_patient", "patient")
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    department = _assign_patient_to_doctor(db_session, patient_id, doctor_id)

    create_response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(doctor_username),
        json=_vitals_payload(patient_id, department.id),
    )
    signal_id = create_response.json()["signals"][0]["id"]

    resolve_response = client.put(
        f"/monitoring/signals/{signal_id}/resolve",
        headers=_auth_headers(doctor_username),
    )
    worklist_response = client.get(
        f"/monitoring/doctor/patients/{patient_id}/signals",
        headers=_auth_headers(doctor_username),
    )

    assert resolve_response.status_code == 200
    assert resolve_response.json()["status"] == "resolved"
    open_signal_ids = {signal["id"] for signal in worklist_response.json()["open_signals"]}
    assert signal_id not in open_signal_ids
    event = db_session.query(models.CareEvent).filter_by(event_type="MONITORING_SIGNAL_RESOLVED").one()
    assert event.patient_id == patient_id


def test_unassigned_doctor_cannot_resolve_monitoring_signal(client, db_session):
    assigned_doctor = _create_user(db_session, "monitor_signal_assigned_doctor", "doctor")
    other_doctor = _create_user(db_session, "monitor_signal_other_doctor", "doctor")
    patient = _create_user(db_session, "monitor_signal_patient", "patient")
    assigned_username = assigned_doctor.username
    other_username = other_doctor.username
    patient_id = patient.id
    department = _assign_patient_to_doctor(db_session, patient_id, assigned_doctor.id)

    create_response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(assigned_username),
        json=_vitals_payload(patient_id, department.id),
    )
    signal_id = create_response.json()["signals"][0]["id"]

    response = client.put(
        f"/monitoring/signals/{signal_id}/resolve",
        headers=_auth_headers(other_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_unassigned_doctor_cannot_review_patient_signals(client, db_session):
    doctor = _create_user(db_session, "monitor_unassigned_doctor", "doctor")
    other_doctor = _create_user(db_session, "monitor_other_doctor", "doctor")
    patient = _create_user(db_session, "monitor_private_patient", "patient")
    doctor_username = doctor.username
    patient_id = patient.id
    _assign_patient_to_doctor(db_session, patient_id, other_doctor.id)

    response = client.get(
        f"/monitoring/doctor/patients/{patient_id}/signals",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_facility_admin_doctor_signals_route_rejects_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Monitoring Doctor Admin Primary")
    other_facility = _create_facility(db_session, "Monitoring Doctor Admin Other")
    admin = _create_user(db_session, "monitor_doctor_route_admin", "admin", facility_id=primary_facility.id)
    doctor = _create_user(db_session, "monitor_doctor_route_other_doctor", "doctor", facility_id=other_facility.id)
    patient = _create_user(db_session, "monitor_doctor_route_other_patient", "patient", facility_id=other_facility.id)
    department = _assign_patient_to_doctor(
        db_session,
        patient.id,
        doctor.id,
        facility_id=other_facility.id,
    )
    vital = models.VitalObservation(
        facility_id=other_facility.id,
        patient_id=patient.id,
        recorded_by_id=doctor.id,
        department_id=department.id,
        source="device",
        heart_rate=128,
    )
    db_session.add(vital)
    db_session.flush()
    db_session.add(models.MonitoringSignal(
        facility_id=other_facility.id,
        patient_id=patient.id,
        vital_observation_id=vital.id,
        department_id=department.id,
        signal_type="heart_rate",
        severity="warning",
        title="Heart rate needs review",
        summary="Synthetic signal summary.",
        status="open",
    ))
    db_session.commit()

    response = client.get(
        f"/monitoring/doctor/patients/{patient.id}/signals",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Monitoring resource is outside the user's facility"


def test_cross_facility_appointment_does_not_grant_monitoring_review(client, db_session):
    first_facility = _create_facility(db_session, "Monitoring North Clinic")
    second_facility = _create_facility(db_session, "Monitoring South Clinic")
    doctor = _create_user(db_session, "monitor_tenant_doctor", "doctor")
    patient = _create_user(db_session, "monitor_tenant_patient", "patient")
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

    response = client.get(
        f"/monitoring/doctor/patients/{patient_id}/signals",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_patient_vitals_view_is_scoped(client, db_session):
    patient = _create_user(db_session, "monitor_scope_patient", "patient")
    other_patient = _create_user(db_session, "monitor_scope_other", "patient")
    patient_username = patient.username
    patient_id = patient.id
    other_patient_id = other_patient.id

    client.post("/monitoring/vitals", headers=_auth_headers(patient_username), json=_vitals_payload(patient_id))
    admin = _create_user(db_session, "monitor_scope_admin", "admin")
    client.post("/monitoring/vitals", headers=_auth_headers(admin.username), json=_vitals_payload(other_patient_id))

    response = client.get("/monitoring/patient/vitals", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert [item["patient_id"] for item in response.json()] == [patient_id]


def test_admin_patterns_summarize_monitoring_activity(client, db_session):
    admin = _create_user(db_session, "monitor_admin", "admin")
    doctor = _create_user(db_session, "monitor_pattern_doctor", "doctor")
    patient = _create_user(db_session, "monitor_pattern_patient", "patient")
    admin_username = admin.username
    patient_id = patient.id
    department = _assign_patient_to_doctor(db_session, patient_id, doctor.id)
    department_id = department.id

    create_response = client.post(
        "/monitoring/vitals",
        headers=_auth_headers(admin_username),
        json=_vitals_payload(patient_id, department_id),
    )
    assert create_response.status_code == 200

    response = client.get("/monitoring/admin/patterns", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_vital_observations"] == 1
    assert payload["open_signals"] >= 1
    assert payload["signals_by_type"]["oxygen_saturation"] == 1
    assert payload["signals_by_department"][str(department_id)] >= 1
    assert "clinician" in payload["clinical_safety_note"].lower()


def test_admin_patterns_are_facility_scoped_for_assigned_admin(client, db_session):
    primary_facility = _create_facility(db_session, "Monitoring Patterns Primary")
    other_facility = _create_facility(db_session, "Monitoring Patterns Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    admin = _create_user(db_session, "monitor_patterns_facility_admin", "admin", facility_id=primary_id)
    other_admin = _create_user(db_session, "monitor_patterns_other_admin", "admin", facility_id=other_id)
    doctor = _create_user(db_session, "monitor_patterns_facility_doctor", "doctor", facility_id=primary_id)
    other_doctor = _create_user(db_session, "monitor_patterns_other_doctor", "doctor", facility_id=other_id)
    patient = _create_user(db_session, "monitor_patterns_facility_patient", "patient", facility_id=primary_id)
    other_patient = _create_user(db_session, "monitor_patterns_other_patient", "patient", facility_id=other_id)
    admin_username = admin.username
    other_admin_username = other_admin.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    doctor_id = doctor.id
    other_doctor_id = other_doctor.id
    department = _assign_patient_to_doctor(db_session, patient_id, doctor_id, facility_id=primary_id)
    other_department = _assign_patient_to_doctor(
        db_session,
        other_patient_id,
        other_doctor_id,
        facility_id=other_id,
    )
    department_id = department.id
    other_department_id = other_department.id
    client.post(
        "/monitoring/vitals",
        headers=_auth_headers(admin_username),
        json=_vitals_payload(patient_id, department_id),
    )
    client.post(
        "/monitoring/vitals",
        headers=_auth_headers(other_admin_username),
        json=_vitals_payload(other_patient_id, other_department_id),
    )

    response = client.get("/monitoring/admin/patterns", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_vital_observations"] == 1
    assert payload["open_signals"] >= 1
    assert str(other_department_id) not in payload["signals_by_department"]


def test_admin_patterns_includes_spark_info(client, db_session):
    from datetime import datetime, timezone

    from backend.models.clinical import SparkStreamingMetrics

    admin = _create_user(db_session, "spark_admin", "admin")

    metric = SparkStreamingMetrics(
        batch_id=456,
        records_processed=5,
        processing_time_ms=15.2,
        ml_latency_ms=4.8,
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(metric)
    db_session.commit()

    response = client.get("/monitoring/admin/patterns", headers=_auth_headers(admin.username))
    assert response.status_code == 200
    payload = response.json()
    assert "spark_info" in payload
    assert payload["spark_info"] is not None
    assert payload["spark_info"]["spark_batch_id"] == 456
    assert payload["spark_info"]["spark_records_processed"] == 5
    assert payload["spark_info"]["spark_latency_ms"] == 15.2
    assert payload["spark_info"]["spark_ml_latency_ms"] == 4.8

