from datetime import datetime, timedelta, timezone

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


def _create_facility_record(db_session, name: str) -> models.HospitalFacility:
    facility = models.HospitalFacility(
        name=name,
        facility_type="hospital",
        country="IN",
        region="KA",
        status="active",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility


def _create_department_record(
    db_session,
    name: str,
    facility_id: int | None,
    department_type: str = "OPD",
) -> models.Department:
    department = models.Department(
        name=name,
        facility_id=facility_id,
        department_type=department_type,
        status="active",
    )
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


def _department_payload(name: str = "Cardiology") -> dict:
    return {
        "name": name,
        "department_type": "OPD",
        "location": "First floor",
        "description": "Clinic department",
    }


def _create_department(client, admin_username: str, name: str = "Cardiology") -> dict:
    response = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin_username),
        json=_department_payload(name),
    )
    assert response.status_code == 200
    return response.json()


def _create_facility(client, admin_username: str, name: str) -> dict:
    response = client.post(
        "/hospital/facilities",
        headers=_auth_headers(admin_username),
        json={
            "name": name,
            "facility_type": "hospital",
            "country": "IN",
            "region": "KA",
        },
    )
    assert response.status_code == 200
    return response.json()


def _assign_facility(client, admin_username: str, user_id: int, facility_id: int) -> dict:
    response = client.put(
        f"/admin/users/{user_id}/facility?facility_id={facility_id}",
        headers=_auth_headers(admin_username),
    )
    assert response.status_code == 200
    return response.json()


def _create_encounter(
    client,
    doctor_username: str,
    doctor_id: int,
    patient_id: int,
    department_id: int,
    encounter_type: str = "OPD",
) -> dict:
    response = client.post(
        "/hospital/encounters",
        headers=_auth_headers(doctor_username),
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department_id,
            "encounter_type": encounter_type,
            "reason": "Follow-up review",
            "priority": "routine",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_admin_can_create_facility_and_facility_department(client, db_session):
    admin = _create_user(db_session, "facility_admin", "admin")
    admin_username = admin.username
    facility = _create_facility(client, admin_username, "Bengaluru General")

    response = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin_username),
        json={
            **_department_payload("Bengaluru Cardiology"),
            "facility_id": facility["id"],
        },
    )

    assert response.status_code == 200
    assert response.json()["facility_id"] == facility["id"]
    list_response = client.get("/hospital/facilities", headers=_auth_headers(admin_username))
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "Bengaluru General"


def test_facility_admin_facility_list_is_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility_record(db_session, "Ops Facility List Primary")
    other_facility = _create_facility_record(db_session, "Ops Facility List Other")
    admin = _create_user(db_session, "ops_facility_list_admin", "admin", facility_id=primary_facility.id)
    primary_facility_id = primary_facility.id
    other_facility_id = other_facility.id

    response = client.get("/hospital/facilities", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    assert [facility["id"] for facility in response.json()] == [primary_facility_id]
    assert other_facility_id not in {facility["id"] for facility in response.json()}


def test_facility_admin_department_list_is_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility_record(db_session, "Ops Department List Primary")
    other_facility = _create_facility_record(db_session, "Ops Department List Other")
    admin = _create_user(db_session, "ops_department_list_admin", "admin", facility_id=primary_facility.id)
    local_department = _create_department_record(db_session, "Ops Local Department", primary_facility.id)
    other_department = _create_department_record(db_session, "Ops Other Department", other_facility.id)

    response = client.get("/hospital/departments", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    assert [department["id"] for department in response.json()] == [local_department.id]
    assert other_department.id not in {department["id"] for department in response.json()}


def test_facility_admin_department_create_defaults_to_own_facility(client, db_session):
    facility = _create_facility_record(db_session, "Ops Department Create Primary")
    admin = _create_user(db_session, "ops_department_create_admin", "admin", facility_id=facility.id)
    facility_id = facility.id

    response = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin.username),
        json=_department_payload("Ops Scoped Department"),
    )

    assert response.status_code == 200
    assert response.json()["facility_id"] == facility_id


def test_facility_admin_rejects_department_for_other_facility(client, db_session):
    primary_facility = _create_facility_record(db_session, "Ops Department Reject Primary")
    other_facility = _create_facility_record(db_session, "Ops Department Reject Other")
    admin = _create_user(db_session, "ops_department_reject_admin", "admin", facility_id=primary_facility.id)

    response = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin.username),
        json={**_department_payload("Ops Rejected Department"), "facility_id": other_facility.id},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Hospital resource is outside the user's facility"


def test_global_admin_department_create_audit_is_visible_to_facility_admin(client, db_session):
    global_admin = _create_user(db_session, "ops_audit_global_admin", "admin")
    global_admin_username = global_admin.username
    facility = _create_facility(client, global_admin_username, "Ops Audit Facility")
    facility_admin = _create_user(
        db_session,
        "ops_audit_facility_admin",
        "admin",
        facility_id=facility["id"],
    )
    facility_admin_username = facility_admin.username

    create_response = client.post(
        "/hospital/departments",
        headers=_auth_headers(global_admin_username),
        json={**_department_payload("Ops Audit Department"), "facility_id": facility["id"]},
    )
    audit_response = client.get(
        "/admin/audit-logs?action=CREATE_DEPARTMENT",
        headers=_auth_headers(facility_admin_username),
    )

    assert create_response.status_code == 200
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert [entry["facility_id"] for entry in payload] == [facility["id"]]


def test_encounter_rejects_cross_facility_patient_assignment(client, db_session):
    admin = _create_user(db_session, "tenant_admin", "admin")
    doctor = _create_user(db_session, "tenant_doctor", "doctor")
    patient = _create_user(db_session, "tenant_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    first_facility = _create_facility(client, admin_username, "North Clinic")
    second_facility = _create_facility(client, admin_username, "South Clinic")
    _assign_facility(client, admin_username, doctor_id, first_facility["id"])
    _assign_facility(client, admin_username, patient_id, second_facility["id"])
    department_response = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin_username),
        json={
            **_department_payload("North OPD"),
            "facility_id": first_facility["id"],
        },
    )
    assert department_response.status_code == 200

    response = client.post(
        "/hospital/encounters",
        headers=_auth_headers(doctor_username),
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department_response.json()["id"],
            "encounter_type": "OPD",
            "reason": "Cross facility attempt",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Encounter participants must belong to the same facility"


def test_order_rejects_cross_facility_department(client, db_session):
    admin = _create_user(db_session, "order_facility_admin", "admin")
    doctor = _create_user(db_session, "order_facility_doctor", "doctor")
    patient = _create_user(db_session, "order_facility_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    first_facility = _create_facility(client, admin_username, "East Hospital")
    second_facility = _create_facility(client, admin_username, "West Hospital")
    _assign_facility(client, admin_username, doctor_id, first_facility["id"])
    _assign_facility(client, admin_username, patient_id, first_facility["id"])
    encounter_department = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin_username),
        json={**_department_payload("East OPD"), "facility_id": first_facility["id"]},
    ).json()
    other_department = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin_username),
        json={**_department_payload("West Diagnostics"), "facility_id": second_facility["id"]},
    ).json()
    encounter = _create_encounter(client, doctor_username, doctor_id, patient_id, encounter_department["id"])

    response = client.post(
        "/hospital/orders",
        headers=_auth_headers(doctor_username),
        json={
            "encounter_id": encounter["id"],
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": other_department["id"],
            "order_type": "lab",
            "title": "CBC",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Order participants must belong to the same facility"


def test_admission_rejects_cross_facility_department(client, db_session):
    admin = _create_user(db_session, "admission_facility_admin", "admin")
    doctor = _create_user(db_session, "admission_facility_doctor", "doctor")
    patient = _create_user(db_session, "admission_facility_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    first_facility = _create_facility(client, admin_username, "City Hospital")
    second_facility = _create_facility(client, admin_username, "Rural Hospital")
    _assign_facility(client, admin_username, doctor_id, first_facility["id"])
    _assign_facility(client, admin_username, patient_id, first_facility["id"])
    ward_department = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin_username),
        json={**_department_payload("City Ward"), "facility_id": first_facility["id"]},
    ).json()
    other_department = client.post(
        "/hospital/departments",
        headers=_auth_headers(admin_username),
        json={**_department_payload("Rural Ward"), "facility_id": second_facility["id"]},
    ).json()
    encounter = _create_encounter(
        client,
        doctor_username,
        doctor_id,
        patient_id,
        ward_department["id"],
        encounter_type="IPD",
    )

    response = client.post(
        "/hospital/admissions",
        headers=_auth_headers(doctor_username),
        json={
            "encounter_id": encounter["id"],
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": other_department["id"],
            "reason": "Observation",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Admission participants must belong to the same facility"


def test_patient_cannot_manage_departments(client, db_session):
    patient = _create_user(db_session, "ops_patient", "patient")
    patient_username = patient.username

    response = client.post(
        "/hospital/departments",
        headers=_auth_headers(patient_username),
        json=_department_payload(),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_admin_can_manage_departments_and_beds(client, db_session):
    admin = _create_user(db_session, "ops_admin", "admin")
    admin_username = admin.username
    department = _create_department(client, admin_username, "Emergency")

    bed_response = client.post(
        "/hospital/beds",
        headers=_auth_headers(admin_username),
        json={
            "department_id": department["id"],
            "bed_number": "ER-01",
            "ward": "Emergency",
            "status": "available",
        },
    )

    assert bed_response.status_code == 200
    assert bed_response.json()["bed_number"] == "ER-01"
    list_response = client.get("/hospital/departments", headers=_auth_headers(admin_username))
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "Emergency"


def test_doctor_creates_encounter_and_patient_timeline_is_scoped(client, db_session):
    admin = _create_user(db_session, "timeline_admin", "admin")
    doctor = _create_user(db_session, "timeline_doctor", "doctor")
    patient = _create_user(db_session, "timeline_patient", "patient")
    other_patient = _create_user(db_session, "timeline_other_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_username = patient.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    department = _create_department(client, admin_username)
    encounter = _create_encounter(client, doctor_username, doctor_id, patient_id, department["id"])
    _create_encounter(client, doctor_username, doctor_id, other_patient_id, department["id"])

    timeline_response = client.get(
        "/hospital/patient/timeline",
        headers=_auth_headers(patient_username),
    )

    assert timeline_response.status_code == 200
    payload = timeline_response.json()
    assert [item["id"] for item in payload["encounters"]] == [encounter["id"]]
    assert payload["events"][0]["event_type"] == "ENCOUNTER_OPENED"
    assert payload["events"][0]["patient_id"] == patient_id
    assert other_patient_id not in {item["patient_id"] for item in payload["events"]}


def test_doctor_can_order_department_workflow_and_view_assigned_patients(client, db_session):
    admin = _create_user(db_session, "orders_admin", "admin")
    doctor = _create_user(db_session, "orders_doctor", "doctor")
    patient = _create_user(db_session, "orders_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    department = _create_department(client, admin_username, "Diagnostics")
    encounter = _create_encounter(client, doctor_username, doctor_id, patient_id, department["id"])

    order_response = client.post(
        "/hospital/orders",
        headers=_auth_headers(doctor_username),
        json={
            "encounter_id": encounter["id"],
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department["id"],
            "order_type": "lab",
            "title": "CBC",
            "priority": "routine",
        },
    )

    assert order_response.status_code == 200
    assert order_response.json()["status"] == "ordered"
    panel_response = client.get(
        "/hospital/doctor/patients",
        headers=_auth_headers(doctor_username),
    )
    assert panel_response.status_code == 200
    assert panel_response.json()[0]["patient_id"] == patient_id
    assert panel_response.json()[0]["open_orders"] == 1


def test_doctor_order_must_be_linked_to_encounter(client, db_session):
    admin = _create_user(db_session, "order_context_admin", "admin")
    doctor = _create_user(db_session, "order_context_doctor", "doctor")
    patient = _create_user(db_session, "order_context_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    department = _create_department(client, admin_username, "Order Context")

    response = client.post(
        "/hospital/orders",
        headers=_auth_headers(doctor_username),
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department["id"],
            "order_type": "lab",
            "title": "CBC",
            "priority": "routine",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Doctor orders must be linked to an encounter"


def test_order_doctor_must_match_encounter_doctor(client, db_session):
    admin = _create_user(db_session, "order_mismatch_admin", "admin")
    encounter_doctor = _create_user(db_session, "order_mismatch_encounter_doctor", "doctor")
    ordering_doctor = _create_user(db_session, "order_mismatch_ordering_doctor", "doctor")
    patient = _create_user(db_session, "order_mismatch_patient", "patient")
    admin_username = admin.username
    encounter_doctor_username = encounter_doctor.username
    encounter_doctor_id = encounter_doctor.id
    ordering_username = ordering_doctor.username
    ordering_doctor_id = ordering_doctor.id
    patient_id = patient.id
    department = _create_department(client, admin_username, "Order Mismatch")
    encounter = _create_encounter(
        client,
        encounter_doctor_username,
        encounter_doctor_id,
        patient_id,
        department["id"],
    )

    response = client.post(
        "/hospital/orders",
        headers=_auth_headers(ordering_username),
        json={
            "encounter_id": encounter["id"],
            "patient_id": patient_id,
            "doctor_id": ordering_doctor_id,
            "department_id": department["id"],
            "order_type": "lab",
            "title": "CBC",
            "priority": "routine",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Order doctor must match encounter doctor"


def test_patient_cannot_create_order_for_another_patient(client, db_session):
    admin = _create_user(db_session, "blocked_order_admin", "admin")
    doctor = _create_user(db_session, "blocked_order_doctor", "doctor")
    patient = _create_user(db_session, "blocked_order_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    department = _create_department(client, admin_username)
    encounter = _create_encounter(client, doctor_username, doctor_id, patient_id, department["id"])

    response = client.post(
        "/hospital/orders",
        headers=_auth_headers(patient_username),
        json={
            "encounter_id": encounter["id"],
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department["id"],
            "order_type": "pharmacy",
            "title": "Medication review",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor or admin privileges required"


def test_admin_operations_view_summarizes_hospital_activity(client, db_session):
    admin = _create_user(db_session, "metrics_admin", "admin")
    doctor = _create_user(db_session, "metrics_doctor", "doctor")
    patient = _create_user(db_session, "metrics_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    department = _create_department(client, admin_username, "IPD")
    bed_response = client.post(
        "/hospital/beds",
        headers=_auth_headers(admin_username),
        json={
            "department_id": department["id"],
            "bed_number": "IPD-01",
            "ward": "General",
        },
    )
    encounter = _create_encounter(client, doctor_username, doctor_id, patient_id, department["id"], encounter_type="IPD")
    admit_response = client.post(
        "/hospital/admissions",
        headers=_auth_headers(doctor_username),
        json={
            "encounter_id": encounter["id"],
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department["id"],
            "bed_id": bed_response.json()["id"],
            "admitted_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            "reason": "Observation",
        },
    )
    assert admit_response.status_code == 200

    response = client.get(
        "/hospital/admin/operations",
        headers=_auth_headers(admin_username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_departments"] == 1
    assert payload["active_admissions"] == 1
    assert payload["occupied_beds"] == 1
    assert payload["encounters_by_type"]["IPD"] == 1


def test_facility_admin_operations_view_is_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility_record(db_session, "Ops Metrics Primary")
    other_facility = _create_facility_record(db_session, "Ops Metrics Other")
    admin = _create_user(db_session, "ops_metrics_facility_admin", "admin", facility_id=primary_facility.id)
    patient = _create_user(db_session, "ops_metrics_patient", "patient", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "ops_metrics_other_patient", "patient", facility_id=other_facility.id)
    department = _create_department_record(db_session, "Ops Metrics Department", primary_facility.id, "IPD")
    other_department = _create_department_record(db_session, "Ops Metrics Other Department", other_facility.id, "IPD")
    db_session.add_all([
        models.Bed(
            facility_id=primary_facility.id,
            department_id=department.id,
            bed_number="OPS-01",
            status="occupied",
            current_patient_id=patient.id,
        ),
        models.Bed(
            facility_id=other_facility.id,
            department_id=other_department.id,
            bed_number="OPS-02",
            status="occupied",
            current_patient_id=other_patient.id,
        ),
        models.Encounter(
            facility_id=primary_facility.id,
            patient_id=patient.id,
            department_id=department.id,
            encounter_type="IPD",
            status="open",
        ),
        models.Encounter(
            facility_id=other_facility.id,
            patient_id=other_patient.id,
            department_id=other_department.id,
            encounter_type="Emergency",
            status="open",
        ),
        models.Admission(
            facility_id=primary_facility.id,
            patient_id=patient.id,
            department_id=department.id,
            status="active",
            reason="Observation",
        ),
        models.Admission(
            facility_id=other_facility.id,
            patient_id=other_patient.id,
            department_id=other_department.id,
            status="active",
            reason="Observation",
        ),
        models.ClinicalOrder(
            facility_id=primary_facility.id,
            patient_id=patient.id,
            department_id=department.id,
            order_type="lab",
            title="CBC",
            status="ordered",
        ),
        models.ClinicalOrder(
            facility_id=other_facility.id,
            patient_id=other_patient.id,
            department_id=other_department.id,
            order_type="radiology",
            title="X-ray",
            status="ordered",
        ),
    ])
    db_session.commit()

    response = client.get(
        "/hospital/admin/operations",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_facilities"] == 1
    assert payload["total_departments"] == 1
    assert payload["total_beds"] == 1
    assert payload["occupied_beds"] == 1
    assert payload["open_encounters"] == 1
    assert payload["active_admissions"] == 1
    assert payload["open_orders"] == 1
    assert payload["encounters_by_type"] == {"IPD": 1}
    assert payload["orders_by_type"] == {"lab": 1}


def test_admission_doctor_must_match_encounter_doctor(client, db_session):
    admin = _create_user(db_session, "admission_mismatch_admin", "admin")
    encounter_doctor = _create_user(db_session, "admission_mismatch_encounter_doctor", "doctor")
    admitting_doctor = _create_user(db_session, "admission_mismatch_admitting_doctor", "doctor")
    patient = _create_user(db_session, "admission_mismatch_patient", "patient")
    admin_username = admin.username
    encounter_doctor_username = encounter_doctor.username
    encounter_doctor_id = encounter_doctor.id
    admitting_username = admitting_doctor.username
    admitting_doctor_id = admitting_doctor.id
    patient_id = patient.id
    department = _create_department(client, admin_username, "Admission Mismatch")
    encounter = _create_encounter(
        client,
        encounter_doctor_username,
        encounter_doctor_id,
        patient_id,
        department["id"],
        encounter_type="IPD",
    )

    response = client.post(
        "/hospital/admissions",
        headers=_auth_headers(admitting_username),
        json={
            "encounter_id": encounter["id"],
            "patient_id": patient_id,
            "doctor_id": admitting_doctor_id,
            "department_id": department["id"],
            "reason": "Observation",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Admission doctor must match encounter doctor"


def test_patient_cannot_have_duplicate_active_admissions(client, db_session):
    admin = _create_user(db_session, "duplicate_admission_admin", "admin")
    doctor = _create_user(db_session, "duplicate_admission_doctor", "doctor")
    patient = _create_user(db_session, "duplicate_admission_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    department = _create_department(client, admin_username, "Observation")
    first_encounter = _create_encounter(client, doctor_username, doctor_id, patient_id, department["id"], encounter_type="IPD")
    second_encounter = _create_encounter(client, doctor_username, doctor_id, patient_id, department["id"], encounter_type="IPD")

    first_response = client.post(
        "/hospital/admissions",
        headers=_auth_headers(doctor_username),
        json={
            "encounter_id": first_encounter["id"],
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department["id"],
            "reason": "Observation",
        },
    )
    assert first_response.status_code == 200

    duplicate_response = client.post(
        "/hospital/admissions",
        headers=_auth_headers(doctor_username),
        json={
            "encounter_id": second_encounter["id"],
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department["id"],
            "reason": "Second active admission",
        },
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Patient already has an active admission"


def test_admission_bed_must_match_admission_department(client, db_session):
    admin = _create_user(db_session, "bed_department_admin", "admin")
    doctor = _create_user(db_session, "bed_department_doctor", "doctor")
    patient = _create_user(db_session, "bed_department_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    ward_department = _create_department(client, admin_username, "Ward")
    emergency_department = _create_department(client, admin_username, "Emergency Ward")
    bed_response = client.post(
        "/hospital/beds",
        headers=_auth_headers(admin_username),
        json={
            "department_id": ward_department["id"],
            "bed_number": "WARD-01",
            "ward": "Ward",
            "status": "available",
        },
    )
    assert bed_response.status_code == 200
    encounter = _create_encounter(
        client,
        doctor_username,
        doctor_id,
        patient_id,
        emergency_department["id"],
        encounter_type="IPD",
    )

    response = client.post(
        "/hospital/admissions",
        headers=_auth_headers(doctor_username),
        json={
            "encounter_id": encounter["id"],
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": emergency_department["id"],
            "bed_id": bed_response.json()["id"],
            "reason": "Observation",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Admission bed must belong to admission department"


def test_list_beds(client, db_session):
    admin = _create_user(db_session, "beds_list_admin", "admin")
    admin_username = admin.username
    department = _create_department(client, admin_username, "General Dept")

    # Create two beds
    client.post(
        "/hospital/beds",
        headers=_auth_headers(admin_username),
        json={
            "department_id": department["id"],
            "bed_number": "G-01",
            "status": "available",
        },
    ).json()

    client.post(
        "/hospital/beds",
        headers=_auth_headers(admin_username),
        json={
            "department_id": department["id"],
            "bed_number": "G-02",
            "status": "occupied",
        },
    ).json()

    # List all beds
    list_response = client.get(
        "/hospital/beds",
        headers=_auth_headers(admin_username),
    )
    assert list_response.status_code == 200
    beds = list_response.json()
    assert len(beds) == 2

    # List available beds only
    avail_response = client.get(
        "/hospital/beds?status=available",
        headers=_auth_headers(admin_username),
    )
    assert avail_response.status_code == 200
    avail_beds = avail_response.json()
    assert len(avail_beds) == 1
    assert avail_beds[0]["bed_number"] == "G-01"
