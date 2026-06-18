import json

import pytest

from backend import auth, models

INCIDENT_ENV_KEYS = (
    "INCIDENT_RESPONSE_ENABLED",
    "INCIDENT_RESPONSE_OWNER_CONTACT",
    "INCIDENT_RESPONSE_CHANNEL",
    "INCIDENT_RESPONSE_RUNBOOK_URL",
    "INCIDENT_RESPONSE_SEVERITY_MATRIX_URL",
    "INCIDENT_BREACH_NOTIFICATION_CONTACT",
    "ALERT_ERROR_RATE_THRESHOLD_PERCENT",
    "ALERT_AI_FAILURE_RATE_THRESHOLD_PERCENT",
    "ALERT_PIPELINE_STALENESS_MINUTES",
    "ALERT_SECURITY_EVENT_THRESHOLD",
    "INCIDENT_RESPONSE_WEBHOOK_SECRET",
)


def _incident_response_module():
    try:
        from backend import incident_response
    except ImportError:
        pytest.fail("backend.incident_response module is required for incident readiness")
    return incident_response


def _clear_incident_env(monkeypatch):
    for key in INCIDENT_ENV_KEYS:
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


def test_incident_readiness_reports_alert_rules_without_contact_or_secret_values(monkeypatch):
    incident_response = _incident_response_module()
    _clear_incident_env(monkeypatch)
    monkeypatch.setenv("INCIDENT_RESPONSE_ENABLED", "true")
    monkeypatch.setenv("INCIDENT_RESPONSE_OWNER_CONTACT", "ops-on-call")
    monkeypatch.setenv("INCIDENT_RESPONSE_CHANNEL", "security-alerts")
    monkeypatch.setenv("INCIDENT_RESPONSE_RUNBOOK_URL", "https://docs.example.invalid/incidents")
    monkeypatch.setenv("INCIDENT_RESPONSE_SEVERITY_MATRIX_URL", "https://docs.example.invalid/severity")
    monkeypatch.setenv("INCIDENT_BREACH_NOTIFICATION_CONTACT", "breach@example.invalid")
    monkeypatch.setenv("ALERT_ERROR_RATE_THRESHOLD_PERCENT", "5")
    monkeypatch.setenv("ALERT_AI_FAILURE_RATE_THRESHOLD_PERCENT", "10")
    monkeypatch.setenv("ALERT_PIPELINE_STALENESS_MINUTES", "30")
    monkeypatch.setenv("ALERT_SECURITY_EVENT_THRESHOLD", "3")
    monkeypatch.setenv("INCIDENT_RESPONSE_WEBHOOK_SECRET", "incident-secret-value")

    readiness = incident_response.get_readiness()

    assert readiness["source"] == "backend.incident_response"
    assert readiness["enabled"] is True
    assert readiness["configured"] is True
    assert readiness["status"] == "ready"
    assert readiness["owner_contact_configured"] is True
    assert readiness["breach_notification_contact_configured"] is True
    assert readiness["missing"] == []
    assert {rule["id"] for rule in readiness["alert_rules"]} == {
        "api_error_rate",
        "ai_provider_failure_rate",
        "pipeline_staleness",
        "security_event_spike",
    }
    assert readiness["secret_values_exposed"] is False
    serialized = json.dumps(readiness)
    assert "ops-on-call" not in serialized
    assert "security-alerts" not in serialized
    assert "docs.example.invalid" not in serialized
    assert "breach@example.invalid" not in serialized
    assert "incident-secret-value" not in serialized


def test_incident_readiness_flags_missing_thresholds_and_runbooks(monkeypatch):
    incident_response = _incident_response_module()
    _clear_incident_env(monkeypatch)
    monkeypatch.setenv("INCIDENT_RESPONSE_ENABLED", "true")
    monkeypatch.setenv("INCIDENT_RESPONSE_OWNER_CONTACT", "ops-on-call")
    monkeypatch.setenv("ALERT_ERROR_RATE_THRESHOLD_PERCENT", "not-a-number")

    readiness = incident_response.get_readiness()

    assert readiness["configured"] is False
    assert readiness["status"] == "action_required"
    assert "INCIDENT_RESPONSE_CHANNEL" in readiness["missing"]
    assert "INCIDENT_RESPONSE_RUNBOOK_URL" in readiness["missing"]
    assert "INCIDENT_RESPONSE_SEVERITY_MATRIX_URL" in readiness["missing"]
    assert "INCIDENT_BREACH_NOTIFICATION_CONTACT" in readiness["missing"]
    assert "ALERT_ERROR_RATE_THRESHOLD_PERCENT" in readiness["missing"]
    assert "ALERT_AI_FAILURE_RATE_THRESHOLD_PERCENT" in readiness["missing"]
    assert "ALERT_PIPELINE_STALENESS_MINUTES" in readiness["missing"]
    assert "ALERT_SECURITY_EVENT_THRESHOLD" in readiness["missing"]


def test_admin_reads_incident_readiness(client, db_session, monkeypatch):
    _clear_incident_env(monkeypatch)
    monkeypatch.setenv("INCIDENT_RESPONSE_ENABLED", "false")
    admin = _create_user(db_session, "incident_readiness_admin", "admin")

    response = client.get("/admin/incident-readiness", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "backend.incident_response"
    assert "alert_rules" in payload
    assert payload["secret_values_exposed"] is False


def test_patient_cannot_read_incident_readiness(client, db_session):
    patient = _create_user(db_session, "incident_readiness_patient", "patient")

    response = client.get("/admin/incident-readiness", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
