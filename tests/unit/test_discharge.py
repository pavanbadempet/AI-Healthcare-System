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
        facility_type="hospital",
        country="India",
        status="active",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility


def _create_admission_flow(
    db_session,
    *,
    patient_id: int,
    doctor_id: int,
    facility_id: int | None = None,
) -> tuple[models.Department, models.Bed, models.Encounter, models.Admission]:
    department = models.Department(
        name=f"Discharge Department {patient_id}-{doctor_id}",
        facility_id=facility_id,
        department_type="IPD",
        status="active",
    )
    db_session.add(department)
    db_session.flush()
    bed = models.Bed(
        facility_id=facility_id,
        department_id=department.id,
        bed_number=f"DISC-{patient_id}-{doctor_id}",
        ward="General",
        status="occupied",
        current_patient_id=patient_id,
    )
    db_session.add(bed)
    db_session.flush()
    encounter = models.Encounter(
        facility_id=facility_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department.id,
        encounter_type="IPD",
        reason="Inpatient care",
        status="open",
    )
    db_session.add(encounter)
    db_session.flush()
    admission = models.Admission(
        facility_id=facility_id,
        encounter_id=encounter.id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department.id,
        bed_id=bed.id,
        reason="Observation",
        status="active",
    )
    db_session.add(admission)
    db_session.commit()
    db_session.refresh(department)
    db_session.refresh(bed)
    db_session.refresh(encounter)
    db_session.refresh(admission)
    return department, bed, encounter, admission


def _summary_payload(
    *,
    admission_id: int,
    encounter_id: int,
    patient_id: int,
    doctor_id: int,
) -> dict:
    return {
        "admission_id": admission_id,
        "encounter_id": encounter_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "diagnosis_summary": "Clinician-authored synthetic diagnosis summary.",
        "hospital_course": "Synthetic hospital course for discharge workflow.",
        "medications": "Continue prescribed medication as reviewed by clinician.",
        "follow_up_plan": "Follow up in clinic after one week.",
        "discharge_instructions": "Return for urgent clinician review if symptoms worsen.",
    }


def _create_summary(
    client,
    doctor_username: str,
    *,
    admission_id: int,
    encounter_id: int,
    patient_id: int,
    doctor_id: int,
) -> dict:
    response = client.post(
        "/discharge/summaries",
        headers=_auth_headers(doctor_username),
        json=_summary_payload(
            admission_id=admission_id,
            encounter_id=encounter_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        ),
    )
    assert response.status_code == 200
    return response.json()


def test_patient_cannot_create_discharge_summary(client, db_session):
    patient = _create_user(db_session, "discharge_patient", "patient")
    doctor = _create_user(db_session, "discharge_doctor", "doctor")
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    encounter_id = encounter.id
    admission_id = admission.id

    response = client.post(
        "/discharge/summaries",
        headers=_auth_headers(patient_username),
        json=_summary_payload(
            admission_id=admission_id,
            encounter_id=encounter_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor or admin privileges required"


def test_doctor_creates_discharge_summary_for_assigned_admission(client, db_session):
    doctor = _create_user(db_session, "discharge_create_doctor", "doctor")
    patient = _create_user(db_session, "discharge_create_patient", "patient")
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    encounter_id = encounter.id
    admission_id = admission.id

    response = client.post(
        "/discharge/summaries",
        headers=_auth_headers(doctor_username),
        json=_summary_payload(
            admission_id=admission_id,
            encounter_id=encounter_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        ),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["admission_id"] == admission_id
    assert payload["status"] == "draft"
    event = db_session.query(models.CareEvent).filter_by(event_type="DISCHARGE_SUMMARY_CREATED").one()
    assert event.patient_id == patient_id


def test_discharge_summary_persists_facility_and_care_event_facility(client, db_session):
    facility = _create_facility(db_session, "Discharge Summary Facility")
    facility_id = facility.id
    doctor = _create_user(db_session, "discharge_facility_doctor", "doctor", facility_id=facility_id)
    patient = _create_user(db_session, "discharge_facility_patient", "patient", facility_id=facility_id)
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=facility_id,
    )

    response = client.post(
        "/discharge/summaries",
        headers=_auth_headers(doctor_username),
        json=_summary_payload(
            admission_id=admission.id,
            encounter_id=encounter.id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        ),
    )

    assert response.status_code == 200
    assert response.json()["facility_id"] == facility_id
    event = db_session.query(models.CareEvent).filter_by(event_type="DISCHARGE_SUMMARY_CREATED").one()
    assert event.facility_id == facility_id


def test_facility_admin_cannot_create_discharge_summary_for_other_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Discharge Admin Primary")
    other_facility = _create_facility(db_session, "Discharge Admin Other")
    admin = _create_user(db_session, "discharge_facility_admin", "admin", facility_id=primary_facility.id)
    doctor = _create_user(db_session, "discharge_other_facility_doctor", "doctor", facility_id=other_facility.id)
    patient = _create_user(db_session, "discharge_other_facility_patient", "patient", facility_id=other_facility.id)
    admin_username = admin.username
    doctor_id = doctor.id
    patient_id = patient.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=other_facility.id,
    )

    response = client.post(
        "/discharge/summaries",
        headers=_auth_headers(admin_username),
        json=_summary_payload(
            admission_id=admission.id,
            encounter_id=encounter.id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Discharge resource is outside the user's facility"


def test_finalize_discharge_summary_closes_admission_and_frees_bed(client, db_session):
    doctor = _create_user(db_session, "discharge_finalize_doctor", "doctor")
    patient = _create_user(db_session, "discharge_finalize_patient", "patient")
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    _, bed, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    bed_id = bed.id
    encounter_id = encounter.id
    admission_id = admission.id
    summary = _create_summary(
        client,
        doctor_username,
        admission_id=admission_id,
        encounter_id=encounter_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )

    response = client.put(
        f"/discharge/summaries/{summary['id']}/finalize",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "finalized"
    assert payload["finalized_at"] is not None
    refreshed_admission = db_session.get(models.Admission, admission_id)
    refreshed_bed = db_session.get(models.Bed, bed_id)
    assert refreshed_admission.status == "discharged"
    assert refreshed_admission.discharged_at is not None
    assert refreshed_bed.status == "available"
    assert refreshed_bed.current_patient_id is None


def test_finalized_discharge_summary_cannot_be_finalized_again(client, db_session):
    doctor = _create_user(db_session, "discharge_repeat_doctor", "doctor")
    patient = _create_user(db_session, "discharge_repeat_patient", "patient")
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    summary = _create_summary(
        client,
        doctor_username,
        admission_id=admission.id,
        encounter_id=encounter.id,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )

    first_response = client.put(
        f"/discharge/summaries/{summary['id']}/finalize",
        headers=_auth_headers(doctor_username),
    )
    second_response = client.put(
        f"/discharge/summaries/{summary['id']}/finalize",
        headers=_auth_headers(doctor_username),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Discharge summary is already finalized"
    finalized_events = db_session.query(models.CareEvent).filter_by(event_type="DISCHARGE_FINALIZED").all()
    assert len(finalized_events) == 1


def test_patient_sees_only_own_finalized_discharge_summaries(client, db_session):
    doctor = _create_user(db_session, "discharge_scope_doctor", "doctor")
    patient = _create_user(db_session, "discharge_scope_patient", "patient")
    other_patient = _create_user(db_session, "discharge_scope_other", "patient")
    doctor_username = doctor.username
    patient_username = patient.username
    doctor_id = doctor.id
    patient_id = patient.id
    other_patient_id = other_patient.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    _, _, other_encounter, other_admission = _create_admission_flow(
        db_session,
        patient_id=other_patient_id,
        doctor_id=doctor_id,
    )
    encounter_id = encounter.id
    admission_id = admission.id
    other_encounter_id = other_encounter.id
    other_admission_id = other_admission.id
    own_summary = _create_summary(
        client,
        doctor_username,
        admission_id=admission_id,
        encounter_id=encounter_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    other_summary = _create_summary(
        client,
        doctor_username,
        admission_id=other_admission_id,
        encounter_id=other_encounter_id,
        patient_id=other_patient_id,
        doctor_id=doctor_id,
    )
    client.put(f"/discharge/summaries/{own_summary['id']}/finalize", headers=_auth_headers(doctor_username))
    client.put(f"/discharge/summaries/{other_summary['id']}/finalize", headers=_auth_headers(doctor_username))

    response = client.get("/discharge/patient/summaries", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own_summary["id"]]


def test_unassigned_doctor_cannot_view_patient_discharge_summaries(client, db_session):
    assigned_doctor = _create_user(db_session, "discharge_assigned_doctor", "doctor")
    other_doctor = _create_user(db_session, "discharge_other_doctor", "doctor")
    patient = _create_user(db_session, "discharge_private_patient", "patient")
    assigned_username = assigned_doctor.username
    other_username = other_doctor.username
    assigned_doctor_id = assigned_doctor.id
    patient_id = patient.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=assigned_doctor_id,
    )
    _create_summary(
        client,
        assigned_username,
        admission_id=admission.id,
        encounter_id=encounter.id,
        patient_id=patient_id,
        doctor_id=assigned_doctor_id,
    )

    response = client.get(
        f"/discharge/doctor/patients/{patient_id}/summaries",
        headers=_auth_headers(other_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_facility_admin_doctor_summaries_route_rejects_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Discharge Doctor Admin Primary")
    other_facility = _create_facility(db_session, "Discharge Doctor Admin Other")
    admin = _create_user(db_session, "discharge_doctor_route_admin", "admin", facility_id=primary_facility.id)
    doctor = _create_user(db_session, "discharge_doctor_route_other_doctor", "doctor", facility_id=other_facility.id)
    patient = _create_user(db_session, "discharge_doctor_route_other_patient", "patient", facility_id=other_facility.id)
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient.id,
        doctor_id=doctor.id,
        facility_id=other_facility.id,
    )
    db_session.add(models.DischargeSummary(
        facility_id=other_facility.id,
        admission_id=admission.id,
        encounter_id=encounter.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        diagnosis_summary="Synthetic diagnosis summary.",
        hospital_course="Synthetic hospital course.",
        status="finalized",
    ))
    db_session.commit()

    response = client.get(
        f"/discharge/doctor/patients/{patient.id}/summaries",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Discharge resource is outside the user's facility"


def test_admin_discharge_metrics(client, db_session):
    admin = _create_user(db_session, "discharge_metrics_admin", "admin")
    doctor = _create_user(db_session, "discharge_metrics_doctor", "doctor")
    patient = _create_user(db_session, "discharge_metrics_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    summary = _create_summary(
        client,
        doctor_username,
        admission_id=admission.id,
        encounter_id=encounter.id,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    client.put(f"/discharge/summaries/{summary['id']}/finalize", headers=_auth_headers(doctor_username))

    response = client.get("/discharge/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_summaries"] == 1
    assert payload["finalized_summaries"] == 1
    assert payload["draft_summaries"] == 0
    assert payload["discharged_admissions"] == 1


def test_discharge_metrics_are_facility_scoped_for_assigned_admin(client, db_session):
    primary_facility = _create_facility(db_session, "Discharge Metrics Primary")
    other_facility = _create_facility(db_session, "Discharge Metrics Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    admin = _create_user(db_session, "discharge_metrics_facility_admin", "admin", facility_id=primary_id)
    doctor = _create_user(db_session, "discharge_metrics_facility_doctor", "doctor", facility_id=primary_id)
    patient = _create_user(db_session, "discharge_metrics_facility_patient", "patient", facility_id=primary_id)
    other_doctor = _create_user(db_session, "discharge_metrics_other_doctor", "doctor", facility_id=other_id)
    other_patient = _create_user(db_session, "discharge_metrics_other_patient", "patient", facility_id=other_id)
    admin_username = admin.username
    doctor_username = doctor.username
    other_doctor_username = other_doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    other_doctor_id = other_doctor.id
    other_patient_id = other_patient.id
    _, _, encounter, admission = _create_admission_flow(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=primary_id,
    )
    _, _, other_encounter, other_admission = _create_admission_flow(
        db_session,
        patient_id=other_patient_id,
        doctor_id=other_doctor_id,
        facility_id=other_id,
    )
    admission_id = admission.id
    encounter_id = encounter.id
    other_admission_id = other_admission.id
    other_encounter_id = other_encounter.id
    summary = _create_summary(
        client,
        doctor_username,
        admission_id=admission_id,
        encounter_id=encounter_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    _create_summary(
        client,
        other_doctor_username,
        admission_id=other_admission_id,
        encounter_id=other_encounter_id,
        patient_id=other_patient_id,
        doctor_id=other_doctor_id,
    )
    client.put(f"/discharge/summaries/{summary['id']}/finalize", headers=_auth_headers(doctor_username))

    response = client.get("/discharge/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_summaries"] == 1
    assert payload["finalized_summaries"] == 1
    assert payload["active_admissions"] == 0
    assert payload["discharged_admissions"] == 1
