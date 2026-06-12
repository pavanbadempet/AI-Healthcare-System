import json

import pytest

from backend import auth, models

SECURITY_ENV_KEYS = (
    "SECURITY_ASSURANCE_ENABLED",
    "SECURITY_OWNER_CONTACT",
    "SECURITY_RUNBOOK_URL",
    "SECRET_SCAN_LAST_RUN_AT",
    "DEPENDENCY_SCAN_LAST_RUN_AT",
    "SBOM_GENERATED_AT",
    "VULNERABILITY_SCAN_LAST_RUN_AT",
    "PEN_TEST_REPORT_URL",
    "SECURITY_FINDINGS_OPEN_CRITICAL",
    "SECURITY_FINDINGS_OPEN_HIGH",
    "SECURITY_ASSURANCE_SECRET",
)


def _security_assurance_module():
    try:
        from backend import security_assurance
    except ImportError:
        pytest.fail("backend.security_assurance module is required for security assurance readiness")
    return security_assurance


def _clear_security_env(monkeypatch):
    for key in SECURITY_ENV_KEYS:
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


def test_security_assurance_reports_scan_evidence_without_contacts_or_secrets(monkeypatch):
    security_assurance = _security_assurance_module()
    _clear_security_env(monkeypatch)
    monkeypatch.setenv("SECURITY_ASSURANCE_ENABLED", "true")
    monkeypatch.setenv("SECURITY_OWNER_CONTACT", "security-owner")
    monkeypatch.setenv("SECURITY_RUNBOOK_URL", "https://docs.example.invalid/security")
    monkeypatch.setenv("SECRET_SCAN_LAST_RUN_AT", "2026-05-27T10:00:00+00:00")
    monkeypatch.setenv("DEPENDENCY_SCAN_LAST_RUN_AT", "2026-05-27T10:00:00+00:00")
    monkeypatch.setenv("SBOM_GENERATED_AT", "2026-05-27T10:00:00+00:00")
    monkeypatch.setenv("VULNERABILITY_SCAN_LAST_RUN_AT", "2026-05-27T10:00:00+00:00")
    monkeypatch.setenv("PEN_TEST_REPORT_URL", "https://docs.example.invalid/pentest")
    monkeypatch.setenv("SECURITY_FINDINGS_OPEN_CRITICAL", "0")
    monkeypatch.setenv("SECURITY_FINDINGS_OPEN_HIGH", "0")
    monkeypatch.setenv("SECURITY_ASSURANCE_SECRET", "security-secret-value")

    readiness = security_assurance.get_readiness()

    assert readiness["source"] == "backend.security_assurance"
    assert readiness["enabled"] is True
    assert readiness["configured"] is True
    assert readiness["status"] == "ready"
    assert readiness["missing"] == []
    assert {control["id"] for control in readiness["controls"]} == {
        "secret_scan",
        "dependency_scan",
        "sbom",
        "vulnerability_scan",
        "penetration_test",
        "critical_findings",
        "high_findings",
    }
    assert readiness["secret_values_exposed"] is False
    serialized = json.dumps(readiness)
    assert "security-owner" not in serialized
    assert "docs.example.invalid" not in serialized
    assert "security-secret-value" not in serialized


def test_security_assurance_flags_missing_scans_and_open_critical_findings(monkeypatch):
    security_assurance = _security_assurance_module()
    _clear_security_env(monkeypatch)
    monkeypatch.setenv("SECURITY_ASSURANCE_ENABLED", "true")
    monkeypatch.setenv("SECURITY_OWNER_CONTACT", "security-owner")
    monkeypatch.setenv("SECURITY_FINDINGS_OPEN_CRITICAL", "1")
    monkeypatch.setenv("SECURITY_FINDINGS_OPEN_HIGH", "0")

    readiness = security_assurance.get_readiness()

    assert readiness["configured"] is False
    assert readiness["status"] == "action_required"
    assert "SECURITY_RUNBOOK_URL" in readiness["missing"]
    assert "SECRET_SCAN_LAST_RUN_AT" in readiness["missing"]
    assert "DEPENDENCY_SCAN_LAST_RUN_AT" in readiness["missing"]
    assert "SBOM_GENERATED_AT" in readiness["missing"]
    assert "VULNERABILITY_SCAN_LAST_RUN_AT" in readiness["missing"]
    assert "PEN_TEST_REPORT_URL" in readiness["missing"]
    assert "SECURITY_FINDINGS_OPEN_CRITICAL" in readiness["missing"]


def test_admin_reads_security_assurance(client, db_session, monkeypatch):
    _clear_security_env(monkeypatch)
    monkeypatch.setenv("SECURITY_ASSURANCE_ENABLED", "false")
    admin = _create_user(db_session, "security_assurance_admin", "admin")

    response = client.get("/admin/security-assurance", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "backend.security_assurance"
    assert "controls" in payload
    assert payload["secret_values_exposed"] is False


def test_patient_cannot_read_security_assurance(client, db_session):
    patient = _create_user(db_session, "security_assurance_patient", "patient")

    response = client.get("/admin/security-assurance", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
