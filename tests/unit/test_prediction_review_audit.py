import json

from backend import auth, models


def _create_user(db_session, username: str, role: str, facility_id: int | None = None) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        facility_id=facility_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


def _assign_doctor(db_session, patient_id: int, doctor_id: int, facility_id: int | None = None) -> None:
    db_session.add(models.Encounter(
        facility_id=facility_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        encounter_type="OPD",
        reason="AI prediction review",
        status="open",
    ))
    db_session.commit()


def test_doctor_records_prediction_review_audit_without_phi(client, db_session):
    doctor = _create_user(db_session, "prediction_review_doctor", "doctor")
    patient = _create_user(db_session, "prediction_review_patient", "patient")
    _assign_doctor(db_session, patient.id, doctor.id)

    response = client.post(
        "/predict/reviews",
        json={
            "patient_id": patient.id,
            "prediction_type": "heart",
            "decision": "overridden",
            "clinical_use_category": "clinician_review",
            "model_card_id": "heart_disease_screening",
            "review_note": "Sensitive Patient should repeat test; email sensitive@example.com",
        },
        headers=_auth_headers(doctor.username),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "recorded"
    assert payload["patient_id"] == patient.id
    assert payload["reviewed_by_id"] == doctor.id
    audit_log = db_session.query(models.AuditLog).one()
    assert audit_log.action == "REVIEW_AI_PREDICTION"
    assert audit_log.target_user_id == patient.id
    details = json.loads(audit_log.details)
    assert details["screening_area"] == "heart"
    assert details["decision"] == "overridden"
    assert details["model_card_id"] == "heart_disease_screening"
    assert details["review_text_present"] is True
    assert "Sensitive Patient" not in audit_log.details
    assert "sensitive@example.com" not in audit_log.details


def test_prediction_review_rejects_invalid_decision(client, db_session):
    doctor = _create_user(db_session, "prediction_review_invalid_doctor", "doctor")
    patient = _create_user(db_session, "prediction_review_invalid_patient", "patient")
    _assign_doctor(db_session, patient.id, doctor.id)

    response = client.post(
        "/predict/reviews",
        json={
            "patient_id": patient.id,
            "prediction_type": "heart",
            "decision": "diagnosed",
        },
        headers=_auth_headers(doctor.username),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported prediction review decision"


def test_unassigned_doctor_cannot_record_prediction_review(client, db_session):
    assigned_doctor = _create_user(db_session, "prediction_review_assigned", "doctor")
    other_doctor = _create_user(db_session, "prediction_review_other", "doctor")
    patient = _create_user(db_session, "prediction_review_private_patient", "patient")
    _assign_doctor(db_session, patient.id, assigned_doctor.id)

    response = client.post(
        "/predict/reviews",
        json={
            "patient_id": patient.id,
            "prediction_type": "heart",
            "decision": "accepted",
        },
        headers=_auth_headers(other_doctor.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_patient_cannot_record_prediction_review(client, db_session):
    patient = _create_user(db_session, "prediction_review_forbidden_patient", "patient")

    response = client.post(
        "/predict/reviews",
        json={
            "patient_id": patient.id,
            "prediction_type": "heart",
            "decision": "accepted",
        },
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor or admin privileges required"
