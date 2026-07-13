from unittest.mock import MagicMock, patch

from backend import auth, models


def _create_user(db_session, username: str, role: str = "patient") -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        allow_data_collection=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}


def test_audit_event_sanitizes_sensitive_details(db_session):
    from backend import audit

    actor = _create_user(db_session, "audit_actor")

    entry = audit.record_audit_event(
        db_session,
        actor_user_id=actor.id,
        target_user_id=actor.id,
        action="VIEW_HEALTH_RECORD",
        details={
            "resource_type": "health_record",
            "resource_id": 42,
            "email": "patient@example.com",
            "dob": "1990-01-01",
            "token": "secret-token-value",
            "note": "Call 555-123-4567 about diabetes symptoms",
        },
    )

    assert entry is not None
    saved = db_session.query(models.AuditLog).filter_by(action="VIEW_HEALTH_RECORD").one()
    assert saved.admin_id == actor.id
    assert saved.target_user_id == actor.id
    assert "health_record" in saved.details
    assert "patient@example.com" not in saved.details
    assert "1990-01-01" not in saved.details
    assert "secret-token-value" not in saved.details
    assert "555-123-4567" not in saved.details
    assert "diabetes symptoms" not in saved.details


def test_admin_audit_logs_require_admin_role(client, db_session):
    patient = _create_user(db_session, "audit_patient", "patient")

    response = client.get("/admin/audit-logs", headers=_auth_headers(patient.username))

    assert response.status_code == 403


def test_admin_can_review_sanitized_audit_logs(client, db_session):
    from backend import audit

    admin = _create_user(db_session, "audit_admin", "admin")
    patient = _create_user(db_session, "audit_review_patient", "patient")
    admin_id = admin.id
    patient_id = patient.id
    audit.record_audit_event(
        db_session,
        actor_user_id=admin_id,
        target_user_id=patient_id,
        action="VIEW_SENSITIVE_DATA",
        details="Viewed patient@example.com DOB 1990-01-01 token=secret-token",
    )

    response = client.get("/admin/audit-logs", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["action"] == "VIEW_SENSITIVE_DATA"
    assert payload[0]["actor_user_id"] == admin_id
    assert payload[0]["target_user_id"] == patient_id
    assert "timestamp" in payload[0]
    response_text = response.text
    assert "patient@example.com" not in response_text
    assert "1990-01-01" not in response_text
    assert "secret-token" not in response_text


def test_health_record_create_and_delete_are_audited(client, db_session, monkeypatch):
    monkeypatch.setattr("backend.chat.rag.add_checkup_to_db", lambda *args, **kwargs: True)
    monkeypatch.setattr("backend.chat.rag.delete_record_from_db", lambda *args, **kwargs: True)
    patient = _create_user(db_session, "audit_record_patient", "patient")
    headers = _auth_headers(patient.username)

    create_response = client.post(
        "/records",
        headers=headers,
        json={
            "record_type": "diabetes",
            "data": {"glucose": 180, "email": "patient@example.com"},
            "prediction": "High Risk",
        },
    )
    assert create_response.status_code == 200
    record_id = db_session.query(models.HealthRecord).one().id

    delete_response = client.delete(f"/records/{record_id}", headers=headers)

    assert delete_response.status_code == 200
    actions = [
        row.action
        for row in db_session.query(models.AuditLog)
        .filter(models.AuditLog.target_user_id == patient.id)
        .order_by(models.AuditLog.id)
        .all()
    ]
    assert actions == ["CREATE_HEALTH_RECORD", "DELETE_HEALTH_RECORD"]
    details = " ".join(row.details or "" for row in db_session.query(models.AuditLog).all())
    assert "patient@example.com" not in details
    assert "glucose" not in details
    assert "180" not in details
    assert "diabetes" not in details
    assert "High Risk" not in details


def test_legacy_security_audit_helper_sanitizes_sensitive_details(db_session):
    from backend import security

    actor = _create_user(db_session, "legacy_audit_actor")

    security.log_audit_event(
        db_session,
        action="LEGACY_VIEW_PATIENT",
        target_user_id=actor.id,
        admin_id=actor.id,
        details="Viewed patient@example.com DOB 1990-01-01 token=secret-token",
    )

    saved = db_session.query(models.AuditLog).filter_by(action="LEGACY_VIEW_PATIENT").one()
    assert "patient@example.com" not in saved.details
    assert "1990-01-01" not in saved.details
    assert "secret-token" not in saved.details


def test_legacy_security_audit_helper_hides_error_details(caplog):
    from backend import security

    sensitive_error = "audit insert failed patient_email=patient@example.com token=secret-token"
    mock_db = MagicMock()
    caplog.set_level("ERROR", logger="backend.security")

    with patch("backend.security.models.AuditLog", side_effect=Exception(sensitive_error)):
        security.log_audit_event(
            mock_db,
            action="LEGACY_AUDIT_FAILURE",
            target_user_id=1,
            admin_id=1,
            details="safe metadata",
        )

    mock_db.rollback.assert_called_once()
    assert sensitive_error not in caplog.text
    assert "patient@example.com" not in caplog.text
    assert "secret-token" not in caplog.text
