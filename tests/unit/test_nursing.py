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


def _create_care_context(
    db_session,
    *,
    patient_id: int,
    doctor_id: int,
    facility_id: int | None = None,
) -> tuple[models.Department, models.Encounter, models.Admission]:
    department = models.Department(
        name=f"Nursing Department {patient_id}-{doctor_id}",
        facility_id=facility_id,
        department_type="IPD",
        status="active",
    )
    db_session.add(department)
    db_session.flush()
    encounter = models.Encounter(
        facility_id=facility_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department.id,
        encounter_type="IPD",
        reason="Nursing care",
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
        reason="Observation",
        status="active",
    )
    db_session.add(admission)
    db_session.commit()
    db_session.refresh(department)
    db_session.refresh(encounter)
    db_session.refresh(admission)
    return department, encounter, admission


def _task_payload(
    *,
    patient_id: int,
    doctor_id: int,
    nurse_id: int,
    department_id: int,
    encounter_id: int,
    admission_id: int,
) -> dict:
    return {
        "patient_id": patient_id,
        "assigned_nurse_id": nurse_id,
        "encounter_id": encounter_id,
        "admission_id": admission_id,
        "department_id": department_id,
        "task_type": "vitals",
        "title": "Record vitals",
        "instructions": "Synthetic nursing instruction for task workflow.",
        "priority": "routine",
    }


def _create_task(
    client,
    doctor_username: str,
    *,
    patient_id: int,
    doctor_id: int,
    nurse_id: int,
    department_id: int,
    encounter_id: int,
    admission_id: int,
) -> dict:
    response = client.post(
        "/nursing/tasks",
        headers=_auth_headers(doctor_username),
        json=_task_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            nurse_id=nurse_id,
            department_id=department_id,
            encounter_id=encounter_id,
            admission_id=admission_id,
        ),
    )
    assert response.status_code == 200
    return response.json()


def test_patient_cannot_create_nursing_task(client, db_session):
    patient = _create_user(db_session, "nursing_patient", "patient")
    doctor = _create_user(db_session, "nursing_doctor", "doctor")
    nurse = _create_user(db_session, "nursing_nurse", "nurse")
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    nurse_id = nurse.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )

    response = client.post(
        "/nursing/tasks",
        headers=_auth_headers(patient_username),
        json=_task_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            nurse_id=nurse_id,
            department_id=department.id,
            encounter_id=None,
            admission_id=admission.id,
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor or admin privileges required"


def test_nursing_task_department_must_match_admission_department(client, db_session):
    doctor = _create_user(db_session, "nursing_dept_doctor", "doctor")
    nurse = _create_user(db_session, "nursing_dept_nurse", "nurse")
    patient = _create_user(db_session, "nursing_dept_patient", "patient")
    doctor_username = doctor.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    other_department = models.Department(
        name="Nursing Other Department",
        department_type="IPD",
        status="active",
    )
    db_session.add(other_department)
    db_session.commit()
    db_session.refresh(other_department)

    response = client.post(
        "/nursing/tasks",
        headers=_auth_headers(doctor_username),
        json=_task_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            nurse_id=nurse_id,
            department_id=other_department.id,
            encounter_id=None,
            admission_id=admission.id,
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Admission department must match nursing task department"


def test_doctor_creates_nursing_task_and_nurse_sees_assignment(client, db_session):
    doctor = _create_user(db_session, "nursing_task_doctor", "doctor")
    nurse = _create_user(db_session, "nursing_task_nurse", "nurse")
    patient = _create_user(db_session, "nursing_task_patient", "patient")
    doctor_username = doctor.username
    nurse_username = nurse.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    department_id = department.id
    encounter_id = encounter.id
    admission_id = admission.id

    task = _create_task(
        client,
        doctor_username,
        patient_id=patient_id,
        doctor_id=doctor_id,
        nurse_id=nurse_id,
        department_id=department_id,
        encounter_id=encounter_id,
        admission_id=admission_id,
    )
    response = client.get("/nursing/nurse/tasks", headers=_auth_headers(nurse_username))

    assert response.status_code == 200
    assert task["status"] == "assigned"
    assert [item["id"] for item in response.json()] == [task["id"]]
    event = db_session.query(models.CareEvent).filter_by(event_type="NURSING_TASK_CREATED").one()
    assert event.patient_id == patient_id


def test_nursing_task_persists_facility_and_care_event_facility(client, db_session):
    facility = _create_facility(db_session, "Nursing Task Facility")
    facility_id = facility.id
    doctor = _create_user(db_session, "nursing_facility_doctor", "doctor", facility_id=facility_id)
    nurse = _create_user(db_session, "nursing_facility_nurse", "nurse", facility_id=facility_id)
    patient = _create_user(db_session, "nursing_facility_patient", "patient", facility_id=facility_id)
    doctor_username = doctor.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=facility_id,
    )

    response = client.post(
        "/nursing/tasks",
        headers=_auth_headers(doctor_username),
        json=_task_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            nurse_id=nurse_id,
            department_id=department.id,
            encounter_id=encounter.id,
            admission_id=admission.id,
        ),
    )

    assert response.status_code == 200
    assert response.json()["facility_id"] == facility_id
    event = db_session.query(models.CareEvent).filter_by(event_type="NURSING_TASK_CREATED").one()
    assert event.facility_id == facility_id


def test_doctor_cannot_assign_task_to_nurse_from_another_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Nursing Assign Primary")
    other_facility = _create_facility(db_session, "Nursing Assign Other")
    primary_id = primary_facility.id
    doctor = _create_user(db_session, "nursing_cross_doctor", "doctor", facility_id=primary_id)
    patient = _create_user(db_session, "nursing_cross_patient", "patient", facility_id=primary_id)
    nurse = _create_user(db_session, "nursing_cross_nurse", "nurse", facility_id=other_facility.id)
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    nurse_id = nurse.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=primary_id,
    )

    response = client.post(
        "/nursing/tasks",
        headers=_auth_headers(doctor_username),
        json=_task_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            nurse_id=nurse_id,
            department_id=department.id,
            encounter_id=encounter.id,
            admission_id=admission.id,
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Nursing resources must belong to the same facility"


def test_facility_admin_cannot_create_nursing_task_for_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Nursing Admin Primary")
    other_facility = _create_facility(db_session, "Nursing Admin Other")
    admin = _create_user(db_session, "nursing_facility_admin", "admin", facility_id=primary_facility.id)
    doctor = _create_user(db_session, "nursing_other_facility_doctor", "doctor", facility_id=other_facility.id)
    nurse = _create_user(db_session, "nursing_other_facility_nurse", "nurse", facility_id=other_facility.id)
    patient = _create_user(db_session, "nursing_other_facility_patient", "patient", facility_id=other_facility.id)
    admin_username = admin.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=other_facility.id,
    )

    response = client.post(
        "/nursing/tasks",
        headers=_auth_headers(admin_username),
        json=_task_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            nurse_id=nurse_id,
            department_id=department.id,
            encounter_id=encounter.id,
            admission_id=admission.id,
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Nursing resource is outside the user's facility"


def test_assigned_nurse_completes_task(client, db_session):
    doctor = _create_user(db_session, "nursing_complete_doctor", "doctor")
    nurse = _create_user(db_session, "nursing_complete_nurse", "nurse")
    patient = _create_user(db_session, "nursing_complete_patient", "patient")
    doctor_username = doctor.username
    nurse_username = nurse.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    task = _create_task(
        client,
        doctor_username,
        patient_id=patient_id,
        doctor_id=doctor_id,
        nurse_id=nurse_id,
        department_id=department.id,
        encounter_id=encounter.id,
        admission_id=admission.id,
    )

    response = client.put(
        f"/nursing/tasks/{task['id']}/complete",
        headers=_auth_headers(nurse_username),
        json={"completion_note": "Synthetic task completion note."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["completed_by_id"] == nurse_id
    assert payload["completed_at"] is not None
    event = db_session.query(models.CareEvent).filter_by(event_type="NURSING_TASK_COMPLETED").one()
    assert event.patient_id == patient_id


def test_completed_nursing_task_cannot_be_completed_again(client, db_session):
    doctor = _create_user(db_session, "nursing_repeat_doctor", "doctor")
    nurse = _create_user(db_session, "nursing_repeat_nurse", "nurse")
    patient = _create_user(db_session, "nursing_repeat_patient", "patient")
    doctor_username = doctor.username
    nurse_username = nurse.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    task = _create_task(
        client,
        doctor_username,
        patient_id=patient_id,
        doctor_id=doctor_id,
        nurse_id=nurse_id,
        department_id=department.id,
        encounter_id=encounter.id,
        admission_id=admission.id,
    )

    first_response = client.put(
        f"/nursing/tasks/{task['id']}/complete",
        headers=_auth_headers(nurse_username),
        json={"completion_note": "First completion."},
    )
    second_response = client.put(
        f"/nursing/tasks/{task['id']}/complete",
        headers=_auth_headers(nurse_username),
        json={"completion_note": "Duplicate completion."},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Nursing task is already completed"
    completed_events = db_session.query(models.CareEvent).filter_by(event_type="NURSING_TASK_COMPLETED").all()
    assert len(completed_events) == 1


def test_unassigned_nurse_cannot_complete_task(client, db_session):
    doctor = _create_user(db_session, "nursing_private_doctor", "doctor")
    assigned_nurse = _create_user(db_session, "nursing_private_assigned", "nurse")
    other_nurse = _create_user(db_session, "nursing_private_other", "nurse")
    patient = _create_user(db_session, "nursing_private_patient", "patient")
    doctor_username = doctor.username
    other_nurse_username = other_nurse.username
    doctor_id = doctor.id
    nurse_id = assigned_nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    task = _create_task(
        client,
        doctor_username,
        patient_id=patient_id,
        doctor_id=doctor_id,
        nurse_id=nurse_id,
        department_id=department.id,
        encounter_id=encounter.id,
        admission_id=admission.id,
    )

    response = client.put(
        f"/nursing/tasks/{task['id']}/complete",
        headers=_auth_headers(other_nurse_username),
        json={"completion_note": "Attempted completion."},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Nurse is not assigned to this task"


def test_patient_sees_only_own_nursing_tasks(client, db_session):
    doctor = _create_user(db_session, "nursing_scope_doctor", "doctor")
    nurse = _create_user(db_session, "nursing_scope_nurse", "nurse")
    patient = _create_user(db_session, "nursing_scope_patient", "patient")
    other_patient = _create_user(db_session, "nursing_scope_other", "patient")
    doctor_username = doctor.username
    patient_username = patient.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    other_patient_id = other_patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    other_department, other_encounter, other_admission = _create_care_context(
        db_session,
        patient_id=other_patient_id,
        doctor_id=doctor_id,
    )
    department_id = department.id
    encounter_id = encounter.id
    admission_id = admission.id
    other_department_id = other_department.id
    other_encounter_id = other_encounter.id
    other_admission_id = other_admission.id
    own_task = _create_task(
        client,
        doctor_username,
        patient_id=patient_id,
        doctor_id=doctor_id,
        nurse_id=nurse_id,
        department_id=department_id,
        encounter_id=encounter_id,
        admission_id=admission_id,
    )
    _create_task(
        client,
        doctor_username,
        patient_id=other_patient_id,
        doctor_id=doctor_id,
        nurse_id=nurse_id,
        department_id=other_department_id,
        encounter_id=other_encounter_id,
        admission_id=other_admission_id,
    )

    response = client.get("/nursing/patient/tasks", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own_task["id"]]


def test_unassigned_doctor_cannot_view_patient_nursing_tasks(client, db_session):
    assigned_doctor = _create_user(db_session, "nursing_assigned_doctor", "doctor")
    other_doctor = _create_user(db_session, "nursing_other_doctor", "doctor")
    nurse = _create_user(db_session, "nursing_view_nurse", "nurse")
    patient = _create_user(db_session, "nursing_view_patient", "patient")
    assigned_username = assigned_doctor.username
    other_username = other_doctor.username
    assigned_doctor_id = assigned_doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=assigned_doctor_id,
    )
    _create_task(
        client,
        assigned_username,
        patient_id=patient_id,
        doctor_id=assigned_doctor_id,
        nurse_id=nurse_id,
        department_id=department.id,
        encounter_id=encounter.id,
        admission_id=admission.id,
    )

    response = client.get(
        f"/nursing/doctor/patients/{patient_id}/tasks",
        headers=_auth_headers(other_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_facility_admin_doctor_tasks_route_rejects_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Nursing Doctor Admin Primary")
    other_facility = _create_facility(db_session, "Nursing Doctor Admin Other")
    admin = _create_user(db_session, "nursing_doctor_route_admin", "admin", facility_id=primary_facility.id)
    doctor = _create_user(db_session, "nursing_doctor_route_other_doctor", "doctor", facility_id=other_facility.id)
    nurse = _create_user(db_session, "nursing_doctor_route_other_nurse", "nurse", facility_id=other_facility.id)
    patient = _create_user(db_session, "nursing_doctor_route_other_patient", "patient", facility_id=other_facility.id)
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient.id,
        doctor_id=doctor.id,
        facility_id=other_facility.id,
    )
    db_session.add(models.NursingTask(
        facility_id=other_facility.id,
        patient_id=patient.id,
        assigned_nurse_id=nurse.id,
        created_by_id=doctor.id,
        encounter_id=encounter.id,
        admission_id=admission.id,
        department_id=department.id,
        task_type="vitals",
        title="Record vitals",
        status="assigned",
    ))
    db_session.commit()

    response = client.get(
        f"/nursing/doctor/patients/{patient.id}/tasks",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Nursing resource is outside the user's facility"


def test_admin_nursing_metrics(client, db_session):
    admin = _create_user(db_session, "nursing_metrics_admin", "admin")
    doctor = _create_user(db_session, "nursing_metrics_doctor", "doctor")
    nurse = _create_user(db_session, "nursing_metrics_nurse", "nurse")
    patient = _create_user(db_session, "nursing_metrics_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    nurse_username = nurse.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
    )
    task = _create_task(
        client,
        doctor_username,
        patient_id=patient_id,
        doctor_id=doctor_id,
        nurse_id=nurse_id,
        department_id=department.id,
        encounter_id=encounter.id,
        admission_id=admission.id,
    )
    client.put(
        f"/nursing/tasks/{task['id']}/complete",
        headers=_auth_headers(nurse_username),
        json={"completion_note": "Synthetic completion."},
    )

    response = client.get("/nursing/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_tasks"] == 1
    assert payload["assigned_tasks"] == 0
    assert payload["completed_tasks"] == 1
    assert payload["tasks_by_type"]["vitals"] == 1


def test_nursing_metrics_are_facility_scoped_for_assigned_admin(client, db_session):
    primary_facility = _create_facility(db_session, "Nursing Metrics Primary")
    other_facility = _create_facility(db_session, "Nursing Metrics Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    admin = _create_user(db_session, "nursing_metrics_facility_admin", "admin", facility_id=primary_id)
    doctor = _create_user(db_session, "nursing_metrics_facility_doctor", "doctor", facility_id=primary_id)
    nurse = _create_user(db_session, "nursing_metrics_facility_nurse", "nurse", facility_id=primary_id)
    patient = _create_user(db_session, "nursing_metrics_facility_patient", "patient", facility_id=primary_id)
    other_doctor = _create_user(db_session, "nursing_metrics_other_doctor", "doctor", facility_id=other_id)
    other_nurse = _create_user(db_session, "nursing_metrics_other_nurse", "nurse", facility_id=other_id)
    other_patient = _create_user(db_session, "nursing_metrics_other_patient", "patient", facility_id=other_id)
    admin_username = admin.username
    doctor_username = doctor.username
    other_doctor_username = other_doctor.username
    doctor_id = doctor.id
    nurse_id = nurse.id
    patient_id = patient.id
    other_doctor_id = other_doctor.id
    other_nurse_id = other_nurse.id
    other_patient_id = other_patient.id
    department, encounter, admission = _create_care_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=primary_id,
    )
    other_department, other_encounter, other_admission = _create_care_context(
        db_session,
        patient_id=other_patient_id,
        doctor_id=other_doctor_id,
        facility_id=other_id,
    )
    department_id = department.id
    encounter_id = encounter.id
    admission_id = admission.id
    other_department_id = other_department.id
    other_encounter_id = other_encounter.id
    other_admission_id = other_admission.id
    _create_task(
        client,
        doctor_username,
        patient_id=patient_id,
        doctor_id=doctor_id,
        nurse_id=nurse_id,
        department_id=department_id,
        encounter_id=encounter_id,
        admission_id=admission_id,
    )
    _create_task(
        client,
        other_doctor_username,
        patient_id=other_patient_id,
        doctor_id=other_doctor_id,
        nurse_id=other_nurse_id,
        department_id=other_department_id,
        encounter_id=other_encounter_id,
        admission_id=other_admission_id,
    )

    response = client.get("/nursing/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_tasks"] == 1
    assert payload["assigned_tasks"] == 1
    assert payload["tasks_by_type"]["vitals"] == 1
