import json

from backend import auth, models, privacy_operations


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
        facility_id=facility_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


def test_patient_deletion_plan_counts_surfaces_without_pii(db_session):
    facility = _create_facility(db_session, "Privacy Plan Facility")
    patient = _create_user(db_session, "privacy_plan_patient", "patient", facility_id=facility.id)
    doctor = _create_user(db_session, "privacy_plan_doctor", "doctor", facility_id=facility.id)
    db_session.add(models.HealthRecord(
        user_id=patient.id,
        record_type="diabetes",
        data='{"glucose": 120}',
        prediction="Synthetic risk",
    ))
    db_session.add(models.ChatLog(user_id=patient.id, role="user", content="Synthetic message"))
    db_session.add(models.Appointment(
        user_id=patient.id,
        doctor_id=doctor.id,
        specialist="General Physician",
        date_time=facility.created_at,
        reason="Synthetic visit",
        status="Scheduled",
    ))
    db_session.add(models.InteroperabilityExport(
        facility_id=facility.id,
        patient_id=patient.id,
        requested_by_id=doctor.id,
        export_type="fhir_bundle",
        resource_count=1,
        status="completed",
    ))
    db_session.add(models.ABDMConsentEvent(
        facility_id=facility.id,
        patient_id=patient.id,
        abdm_request_id="request-privacy-plan",
        status="GRANTED",
        payload_sha256="a" * 64,
    ))
    db_session.commit()

    plan = privacy_operations.build_patient_deletion_plan(db_session, patient.id)

    assert plan["patient_id"] == patient.id
    assert plan["facility_id"] == facility.id
    assert plan["destructive_actions_executed"] is False
    assert plan["database"]["total_records"] >= 4
    assert plan["database"]["tables"]["health_records"] == 1
    assert plan["database"]["tables"]["chat_logs"] == 1
    assert plan["database"]["tables"]["appointments"] == 1
    assert plan["database"]["tables"]["interoperability_exports"] == 1
    assert plan["database"]["tables"]["abdm_consent_events"] == 1
    assert plan["vector_store"]["record_ids_pending_delete"] == 1
    assert plan["lakehouse"]["propagation_required"] is True
    assert "patient_accounts" in plan["lakehouse"]["datasets"]
    assert plan["audit"]["retain_phi_safe_audit_events"] is True
    serialized = json.dumps(plan)
    assert patient.username not in serialized
    assert patient.email not in serialized
    assert patient.full_name not in serialized
    assert "glucose" not in serialized
    assert "Synthetic message" not in serialized


def test_admin_reads_patient_deletion_plan(client, db_session):
    facility = _create_facility(db_session, "Privacy Admin Facility")
    admin = _create_user(db_session, "privacy_plan_admin", "admin", facility_id=facility.id)
    patient = _create_user(db_session, "privacy_plan_admin_patient", "patient", facility_id=facility.id)
    facility_id = facility.id
    admin_id = admin.id
    patient_id = patient.id
    patient_username = patient.username
    patient_email = patient.email

    response = client.get(
        f"/admin/privacy/deletion-plan/{patient_id}",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["facility_id"] == facility_id
    assert payload["destructive_actions_executed"] is False
    assert patient_username not in response.text
    assert patient_email not in response.text
    audit_entry = db_session.query(models.AuditLog).filter(
        models.AuditLog.admin_id == admin_id,
        models.AuditLog.target_user_id == patient_id,
        models.AuditLog.action == "VIEW_PATIENT_DELETION_PLAN",
    ).one()
    assert audit_entry.facility_id == facility_id
    assert "privacy_deletion_plan" in audit_entry.details
    assert patient_username not in audit_entry.details
    assert patient_email not in audit_entry.details


def test_patient_cannot_read_deletion_plan(client, db_session):
    patient = _create_user(db_session, "privacy_plan_forbidden_patient", "patient")

    response = client.get(
        f"/admin/privacy/deletion-plan/{patient.id}",
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_facility_admin_cannot_read_other_facility_deletion_plan(client, db_session):
    primary = _create_facility(db_session, "Privacy Primary")
    other = _create_facility(db_session, "Privacy Other")
    admin = _create_user(db_session, "privacy_plan_facility_admin", "admin", facility_id=primary.id)
    patient = _create_user(db_session, "privacy_plan_other_patient", "patient", facility_id=other.id)

    response = client.get(
        f"/admin/privacy/deletion-plan/{patient.id}",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin resource is outside the user's facility"
