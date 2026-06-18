import json

import pytest

from backend import auth, models

RETENTION_ENV_KEYS = (
    "RETENTION_POLICY_ENABLED",
    "RETENTION_OWNER_CONTACT",
    "RETENTION_RUNBOOK_URL",
    "LEGAL_HOLD_PROCESS_URL",
    "PATIENT_RECORD_RETENTION_YEARS",
    "CHAT_LOG_RETENTION_DAYS",
    "AUDIT_LOG_RETENTION_DAYS",
    "INTEROPERABILITY_EXPORT_RETENTION_DAYS",
    "VECTOR_STORE_RETENTION_DAYS",
    "LAKEHOUSE_RETENTION_DAYS",
    "RETENTION_WORKFLOW_SECRET",
)


def _retention_policy_module():
    try:
        from backend import retention_policy
    except ImportError:
        pytest.fail("backend.retention_policy module is required for retention readiness")
    return retention_policy


def _clear_retention_env(monkeypatch):
    for key in RETENTION_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _create_user(db_session, username: str, role: str) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


def test_retention_readiness_reports_policy_windows_without_contacts_or_secrets(monkeypatch):
    retention_policy = _retention_policy_module()
    _clear_retention_env(monkeypatch)
    monkeypatch.setenv("RETENTION_POLICY_ENABLED", "true")
    monkeypatch.setenv("RETENTION_OWNER_CONTACT", "privacy-owner")
    monkeypatch.setenv("RETENTION_RUNBOOK_URL", "https://docs.example.invalid/retention")
    monkeypatch.setenv("LEGAL_HOLD_PROCESS_URL", "https://docs.example.invalid/legal-hold")
    monkeypatch.setenv("PATIENT_RECORD_RETENTION_YEARS", "8")
    monkeypatch.setenv("CHAT_LOG_RETENTION_DAYS", "365")
    monkeypatch.setenv("AUDIT_LOG_RETENTION_DAYS", "2555")
    monkeypatch.setenv("INTEROPERABILITY_EXPORT_RETENTION_DAYS", "365")
    monkeypatch.setenv("VECTOR_STORE_RETENTION_DAYS", "365")
    monkeypatch.setenv("LAKEHOUSE_RETENTION_DAYS", "730")
    monkeypatch.setenv("RETENTION_WORKFLOW_SECRET", "retention-secret-value")

    readiness = retention_policy.get_readiness()

    assert readiness["source"] == "backend.retention_policy"
    assert readiness["enabled"] is True
    assert readiness["configured"] is True
    assert readiness["status"] == "ready"
    assert readiness["missing"] == []
    policy_ids = {policy["id"] for policy in readiness["policies"]}
    assert {
        "patient_records",
        "chat_logs",
        "audit_logs",
        "interoperability_exports",
        "vector_store",
        "lakehouse",
    } == policy_ids
    assert readiness["secret_values_exposed"] is False
    serialized = json.dumps(readiness)
    assert "privacy-owner" not in serialized
    assert "docs.example.invalid" not in serialized
    assert "retention-secret-value" not in serialized


def test_retention_readiness_flags_missing_windows_and_legal_hold(monkeypatch):
    retention_policy = _retention_policy_module()
    _clear_retention_env(monkeypatch)
    monkeypatch.setenv("RETENTION_POLICY_ENABLED", "true")
    monkeypatch.setenv("RETENTION_OWNER_CONTACT", "privacy-owner")
    monkeypatch.setenv("PATIENT_RECORD_RETENTION_YEARS", "invalid")
    monkeypatch.setenv("CHAT_LOG_RETENTION_DAYS", "365")

    readiness = retention_policy.get_readiness()

    assert readiness["configured"] is False
    assert readiness["status"] == "action_required"
    assert "RETENTION_RUNBOOK_URL" in readiness["missing"]
    assert "LEGAL_HOLD_PROCESS_URL" in readiness["missing"]
    assert "PATIENT_RECORD_RETENTION_YEARS" in readiness["missing"]
    assert "AUDIT_LOG_RETENTION_DAYS" in readiness["missing"]
    assert "INTEROPERABILITY_EXPORT_RETENTION_DAYS" in readiness["missing"]
    assert "VECTOR_STORE_RETENTION_DAYS" in readiness["missing"]
    assert "LAKEHOUSE_RETENTION_DAYS" in readiness["missing"]


def test_admin_reads_retention_readiness(client, db_session, monkeypatch):
    _clear_retention_env(monkeypatch)
    monkeypatch.setenv("RETENTION_POLICY_ENABLED", "false")
    admin = _create_user(db_session, "retention_readiness_admin", "admin")

    response = client.get("/admin/retention-readiness", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "backend.retention_policy"
    assert "policies" in payload
    assert payload["secret_values_exposed"] is False


def test_patient_cannot_read_retention_readiness(client, db_session):
    patient = _create_user(db_session, "retention_readiness_patient", "patient")

    response = client.get("/admin/retention-readiness", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
