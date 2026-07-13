import json

import pytest

from backend import auth, models

BACKUP_ENV_KEYS = (
    "BACKUP_ENABLED",
    "BACKUP_PROVIDER",
    "BACKUP_STORAGE_REGION",
    "BACKUP_RETENTION_DAYS",
    "BACKUP_LAST_SUCCESS_AT",
    "BACKUP_RESTORE_TESTED_AT",
    "BACKUP_ENCRYPTION_ENABLED",
    "BACKUP_OWNER_CONTACT",
    "BACKUP_RUNBOOK_URL",
    "BACKUP_ACCESS_KEY_SECRET",
)


def _backup_readiness_module():
    try:
        from backend import backup_readiness
    except ImportError:
        pytest.fail("backend.backup_readiness module is required for backup and restore readiness")
    return backup_readiness


def _clear_backup_env(monkeypatch):
    for key in BACKUP_ENV_KEYS:
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


def test_backup_readiness_reports_required_evidence_without_secrets(monkeypatch):
    backup_readiness = _backup_readiness_module()
    _clear_backup_env(monkeypatch)
    monkeypatch.setenv("BACKUP_ENABLED", "true")
    monkeypatch.setenv("BACKUP_PROVIDER", "managed-postgres")
    monkeypatch.setenv("BACKUP_STORAGE_REGION", "ap-south-1")
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "35")
    monkeypatch.setenv("BACKUP_LAST_SUCCESS_AT", "2026-05-27T10:00:00+00:00")
    monkeypatch.setenv("BACKUP_RESTORE_TESTED_AT", "2026-05-01T10:00:00+00:00")
    monkeypatch.setenv("BACKUP_ENCRYPTION_ENABLED", "true")
    monkeypatch.setenv("BACKUP_OWNER_CONTACT", "ops-on-call")
    monkeypatch.setenv("BACKUP_RUNBOOK_URL", "https://docs.example.invalid/runbooks/backup")
    monkeypatch.setenv("BACKUP_ACCESS_KEY_SECRET", "super-secret-backup-key")

    readiness = backup_readiness.get_readiness()

    assert readiness["source"] == "backend.backup_readiness"
    assert readiness["status"] == "ready"
    assert readiness["enabled"] is True
    assert readiness["configured"] is True
    assert readiness["restore_test_stale"] is False
    assert readiness["provider"] == "managed-postgres"
    assert readiness["retention_days"] == 35
    assert readiness["missing"] == []
    assert readiness["secret_values_exposed"] is False
    serialized = json.dumps(readiness)
    assert "super-secret-backup-key" not in serialized
    assert "ops-on-call" not in serialized
    assert "docs.example.invalid" not in serialized


def test_backup_readiness_flags_missing_and_stale_restore_evidence(monkeypatch):
    backup_readiness = _backup_readiness_module()
    _clear_backup_env(monkeypatch)
    monkeypatch.setenv("BACKUP_ENABLED", "true")
    monkeypatch.setenv("BACKUP_PROVIDER", "managed-postgres")
    monkeypatch.setenv("BACKUP_STORAGE_REGION", "ap-south-1")
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "35")
    monkeypatch.setenv("BACKUP_LAST_SUCCESS_AT", "2026-05-27T10:00:00+00:00")
    monkeypatch.setenv("BACKUP_RESTORE_TESTED_AT", "2020-01-01T00:00:00+00:00")
    monkeypatch.setenv("BACKUP_ENCRYPTION_ENABLED", "false")

    readiness = backup_readiness.get_readiness()

    assert readiness["configured"] is False
    assert readiness["status"] == "action_required"
    assert readiness["restore_test_stale"] is True
    assert "BACKUP_ENCRYPTION_ENABLED" in readiness["missing"]
    assert "BACKUP_OWNER_CONTACT" in readiness["missing"]
    assert "BACKUP_RUNBOOK_URL" in readiness["missing"]


def test_admin_reads_backup_readiness(client, db_session, monkeypatch):
    _clear_backup_env(monkeypatch)
    monkeypatch.setenv("BACKUP_ENABLED", "false")
    admin = _create_user(db_session, "backup_readiness_admin", "admin")

    response = client.get("/admin/backup-readiness", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "backend.backup_readiness"
    assert "missing" in payload
    assert payload["secret_values_exposed"] is False


def test_patient_cannot_read_backup_readiness(client, db_session):
    patient = _create_user(db_session, "backup_readiness_patient", "patient")

    response = client.get("/admin/backup-readiness", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
