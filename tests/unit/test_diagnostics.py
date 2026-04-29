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


def _create_diagnostic_order(
    db_session,
    *,
    patient_id: int,
    doctor_id: int,
    order_type: str = "lab",
    facility_id: int | None = None,
) -> tuple[models.Department, models.Encounter, models.ClinicalOrder]:
    department = models.Department(
        name=f"Diagnostics {patient_id}-{doctor_id}-{order_type}",
        facility_id=facility_id,
        department_type="Diagnostics",
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
        reason="Diagnostic review",
        status="open",
    )
    db_session.add(encounter)
    db_session.flush()
    order = models.ClinicalOrder(
        facility_id=facility_id,
        encounter_id=encounter.id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department.id,
        order_type=order_type,
        title="CBC",
        status="ordered",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(department)
    db_session.refresh(encounter)
    db_session.refresh(order)
    return department, encounter, order


def _result_payload(order_id: int) -> dict:
    return {
        "order_id": order_id,
        "result_type": "lab",
        "title": "CBC Result",
        "summary": "Synthetic result summary for clinician review.",
        "abnormal_flag": True,
        "status": "final",
    }


def test_patient_cannot_post_diagnostic_result(client, db_session):
    patient = _create_user(db_session, "diag_patient", "patient")
    doctor = _create_user(db_session, "diag_doctor", "doctor")
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=doctor_id)
    order_id = order.id

    response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(patient_username),
        json=_result_payload(order_id),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor or admin privileges required"


def test_doctor_posts_result_and_order_is_completed(client, db_session):
    patient = _create_user(db_session, "diag_result_patient", "patient")
    doctor = _create_user(db_session, "diag_result_doctor", "doctor")
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=doctor_id)
    order_id = order.id

    response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(doctor_username),
        json=_result_payload(order_id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["order_id"] == order_id
    assert payload["review_status"] == "pending_review"
    assert payload["abnormal_flag"] is True
    refreshed_order = db_session.get(models.ClinicalOrder, order_id)
    assert refreshed_order.status == "completed"
    assert refreshed_order.completed_at is not None
    event = db_session.query(models.CareEvent).filter_by(event_type="DIAGNOSTIC_RESULT_POSTED").one()
    assert event.patient_id == patient_id


def test_diagnostic_result_persists_order_facility_and_care_event_facility(client, db_session):
    facility = _create_facility(db_session, "Diagnostics Result Facility")
    facility_id = facility.id
    patient = _create_user(db_session, "diag_facility_patient", "patient", facility_id=facility_id)
    doctor = _create_user(db_session, "diag_facility_doctor", "doctor", facility_id=facility_id)
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=facility_id,
    )
    order_id = order.id

    response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(doctor_username),
        json=_result_payload(order_id),
    )

    assert response.status_code == 200
    assert response.json()["facility_id"] == facility_id
    event = db_session.query(models.CareEvent).filter_by(event_type="DIAGNOSTIC_RESULT_POSTED").one()
    assert event.facility_id == facility_id


def test_facility_admin_cannot_post_result_for_other_facility_order(client, db_session):
    primary_facility = _create_facility(db_session, "Diagnostics Admin Primary")
    other_facility = _create_facility(db_session, "Diagnostics Admin Other")
    admin = _create_user(db_session, "diag_facility_admin", "admin", facility_id=primary_facility.id)
    doctor = _create_user(db_session, "diag_other_facility_doctor", "doctor", facility_id=other_facility.id)
    patient = _create_user(db_session, "diag_other_facility_patient", "patient", facility_id=other_facility.id)
    admin_username = admin.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=other_facility.id,
    )
    order_id = order.id

    response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(admin_username),
        json=_result_payload(order_id),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Diagnostic resource is outside the user's facility"


def test_facility_admin_doctor_results_route_rejects_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Diagnostics Doctor Admin Primary")
    other_facility = _create_facility(db_session, "Diagnostics Doctor Admin Other")
    admin = _create_user(db_session, "diag_doctor_route_facility_admin", "admin", facility_id=primary_facility.id)
    doctor = _create_user(db_session, "diag_doctor_route_other_doctor", "doctor", facility_id=other_facility.id)
    patient = _create_user(db_session, "diag_doctor_route_other_patient", "patient", facility_id=other_facility.id)
    _, _, order = _create_diagnostic_order(
        db_session,
        patient_id=patient.id,
        doctor_id=doctor.id,
        facility_id=other_facility.id,
    )
    db_session.add(models.DiagnosticResult(
        facility_id=other_facility.id,
        order_id=order.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        result_type="lab",
        title="CBC Result",
        summary="Synthetic result summary.",
        review_status="reviewed",
    ))
    db_session.commit()

    response = client.get(
        f"/diagnostics/doctor/patients/{patient.id}/results",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Diagnostic resource is outside the user's facility"


def test_diagnostic_result_type_must_match_order_type(client, db_session):
    patient = _create_user(db_session, "diag_type_patient", "patient")
    doctor = _create_user(db_session, "diag_type_doctor", "doctor")
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=doctor_id, order_type="lab")
    order_id = order.id

    response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(doctor_username),
        json={
            **_result_payload(order_id),
            "result_type": "radiology",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Diagnostic result type must match order type"


def test_patient_sees_only_own_diagnostic_results(client, db_session):
    patient = _create_user(db_session, "diag_scope_patient", "patient")
    other_patient = _create_user(db_session, "diag_scope_other", "patient")
    doctor = _create_user(db_session, "diag_scope_doctor", "doctor")
    patient_username = patient.username
    doctor_username = doctor.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=doctor_id)
    _, _, other_order = _create_diagnostic_order(db_session, patient_id=other_patient_id, doctor_id=doctor_id)
    order_id = order.id
    other_order_id = other_order.id

    own_result = client.post(
        "/diagnostics/results",
        headers=_auth_headers(doctor_username),
        json=_result_payload(order_id),
    ).json()
    other_result = client.post(
        "/diagnostics/results",
        headers=_auth_headers(doctor_username),
        json=_result_payload(other_order_id),
    ).json()
    client.put(
        f"/diagnostics/results/{own_result['id']}/review",
        headers=_auth_headers(doctor_username),
        json={"review_status": "reviewed"},
    )
    client.put(
        f"/diagnostics/results/{other_result['id']}/review",
        headers=_auth_headers(doctor_username),
        json={"review_status": "reviewed"},
    )

    response = client.get("/diagnostics/patient/results", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert [item["patient_id"] for item in response.json()] == [patient_id]


def test_patient_does_not_see_result_until_clinician_review(client, db_session):
    patient = _create_user(db_session, "diag_release_patient", "patient")
    doctor = _create_user(db_session, "diag_release_doctor", "doctor")
    patient_username = patient.username
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=doctor_id)
    order_id = order.id

    create_response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(doctor_username),
        json=_result_payload(order_id),
    )
    result_id = create_response.json()["id"]

    pending_response = client.get("/diagnostics/patient/results", headers=_auth_headers(patient_username))

    assert pending_response.status_code == 200
    assert pending_response.json() == []

    review_response = client.put(
        f"/diagnostics/results/{result_id}/review",
        headers=_auth_headers(doctor_username),
        json={
            "review_status": "reviewed",
            "review_note": "Reviewed and released to patient.",
        },
    )
    assert review_response.status_code == 200

    released_response = client.get("/diagnostics/patient/results", headers=_auth_headers(patient_username))

    assert released_response.status_code == 200
    assert [item["id"] for item in released_response.json()] == [result_id]


def test_assigned_doctor_reviews_diagnostic_result(client, db_session):
    patient = _create_user(db_session, "diag_review_patient", "patient")
    doctor = _create_user(db_session, "diag_review_doctor", "doctor")
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=doctor_id)
    order_id = order.id
    create_response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(doctor_username),
        json=_result_payload(order_id),
    )
    result_id = create_response.json()["id"]

    review_response = client.put(
        f"/diagnostics/results/{result_id}/review",
        headers=_auth_headers(doctor_username),
        json={
            "review_status": "reviewed",
            "review_note": "Reviewed with patient; follow-up scheduled.",
        },
    )

    assert review_response.status_code == 200
    payload = review_response.json()
    assert payload["review_status"] == "reviewed"
    assert payload["reviewed_by_id"] == doctor_id
    assert payload["reviewed_at"] is not None


def test_diagnostic_review_rejects_unknown_status(client, db_session):
    patient = _create_user(db_session, "diag_status_patient", "patient")
    doctor = _create_user(db_session, "diag_status_doctor", "doctor")
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=doctor_id)
    order_id = order.id
    create_response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(doctor_username),
        json=_result_payload(order_id),
    )
    result_id = create_response.json()["id"]

    review_response = client.put(
        f"/diagnostics/results/{result_id}/review",
        headers=_auth_headers(doctor_username),
        json={"review_status": "banana"},
    )

    assert review_response.status_code == 400
    assert review_response.json()["detail"] == "Invalid diagnostic review status"


def test_unassigned_doctor_cannot_review_diagnostic_result(client, db_session):
    patient = _create_user(db_session, "diag_private_patient", "patient")
    assigned_doctor = _create_user(db_session, "diag_private_assigned", "doctor")
    other_doctor = _create_user(db_session, "diag_private_other", "doctor")
    patient_id = patient.id
    assigned_doctor_username = assigned_doctor.username
    other_doctor_username = other_doctor.username
    assigned_doctor_id = assigned_doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=assigned_doctor_id)
    order_id = order.id
    create_response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(assigned_doctor_username),
        json=_result_payload(order_id),
    )
    result_id = create_response.json()["id"]

    response = client.put(
        f"/diagnostics/results/{result_id}/review",
        headers=_auth_headers(other_doctor_username),
        json={"review_status": "reviewed"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this diagnostic result"


def test_admin_diagnostics_metrics(client, db_session):
    admin = _create_user(db_session, "diag_admin", "admin")
    doctor = _create_user(db_session, "diag_metrics_doctor", "doctor")
    patient = _create_user(db_session, "diag_metrics_patient", "patient")
    admin_username = admin.username
    patient_id = patient.id
    doctor_id = doctor.id
    _, _, order = _create_diagnostic_order(db_session, patient_id=patient_id, doctor_id=doctor_id, order_type="radiology")
    order_id = order.id

    response = client.post(
        "/diagnostics/results",
        headers=_auth_headers(admin_username),
        json={
            **_result_payload(order_id),
            "result_type": "radiology",
            "title": "Chest X-Ray Result",
        },
    )
    assert response.status_code == 200

    metrics_response = client.get("/diagnostics/admin/metrics", headers=_auth_headers(admin_username))

    assert metrics_response.status_code == 200
    payload = metrics_response.json()
    assert payload["total_results"] == 1
    assert payload["pending_review"] == 1
    assert payload["abnormal_results"] == 1
    assert payload["results_by_type"]["radiology"] == 1
    assert "clinician" in payload["clinical_safety_note"].lower()


def test_diagnostics_metrics_are_facility_scoped_for_assigned_admin(client, db_session):
    primary_facility = _create_facility(db_session, "Diagnostics Metrics Primary")
    other_facility = _create_facility(db_session, "Diagnostics Metrics Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    admin = _create_user(db_session, "diag_metrics_facility_admin", "admin", facility_id=primary_id)
    other_admin = _create_user(db_session, "diag_metrics_other_admin", "admin", facility_id=other_id)
    doctor = _create_user(db_session, "diag_metrics_facility_doctor", "doctor", facility_id=primary_id)
    other_doctor = _create_user(db_session, "diag_metrics_other_doctor", "doctor", facility_id=other_id)
    patient = _create_user(db_session, "diag_metrics_facility_patient", "patient", facility_id=primary_id)
    other_patient = _create_user(db_session, "diag_metrics_other_patient", "patient", facility_id=other_id)
    admin_username = admin.username
    other_admin_username = other_admin.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    doctor_id = doctor.id
    other_doctor_id = other_doctor.id
    _, _, order = _create_diagnostic_order(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        facility_id=primary_id,
    )
    _, _, other_order = _create_diagnostic_order(
        db_session,
        patient_id=other_patient_id,
        doctor_id=other_doctor_id,
        facility_id=other_id,
    )
    order_id = order.id
    other_order_id = other_order.id
    client.post("/diagnostics/results", headers=_auth_headers(admin_username), json=_result_payload(order_id))
    client.post(
        "/diagnostics/results",
        headers=_auth_headers(other_admin_username),
        json={**_result_payload(other_order_id), "title": "Other CBC Result"},
    )

    metrics_response = client.get("/diagnostics/admin/metrics", headers=_auth_headers(admin_username))

    assert metrics_response.status_code == 200
    payload = metrics_response.json()
    assert payload["total_results"] == 1
    assert payload["pending_review"] == 1
    assert payload["abnormal_results"] == 1
