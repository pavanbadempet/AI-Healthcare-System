"""Incident response and alert readiness metadata.

This module does not send alerts, page responders, or process breach notices.
It reports PHI-safe readiness evidence so production operators can verify that
incident ownership, escalation, and alert thresholds are configured.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

INCIDENT_PHASES = [
    "prepare",
    "detect",
    "analyze",
    "contain",
    "eradicate",
    "recover",
    "post_incident_review",
]


def _env_text(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _env_bool(name: str, default: bool = False) -> bool:
    value = _env_text(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _env_float(name: str) -> float | None:
    value = _env_text(name)
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _env_int(name: str) -> int | None:
    value = _env_text(name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _alert_rule(rule_id: str, label: str, threshold: float | int | None, unit: str) -> dict[str, Any]:
    return {
        "id": rule_id,
        "label": label,
        "threshold": threshold,
        "unit": unit,
        "configured": threshold is not None,
    }


def get_readiness() -> dict[str, Any]:
    enabled = _env_bool("INCIDENT_RESPONSE_ENABLED", False)
    owner_contact_configured = bool(_env_text("INCIDENT_RESPONSE_OWNER_CONTACT"))
    channel_configured = bool(_env_text("INCIDENT_RESPONSE_CHANNEL"))
    runbook_configured = bool(_env_text("INCIDENT_RESPONSE_RUNBOOK_URL"))
    severity_matrix_configured = bool(_env_text("INCIDENT_RESPONSE_SEVERITY_MATRIX_URL"))
    breach_notification_contact_configured = bool(_env_text("INCIDENT_BREACH_NOTIFICATION_CONTACT"))
    error_rate_threshold = _env_float("ALERT_ERROR_RATE_THRESHOLD_PERCENT")
    ai_failure_threshold = _env_float("ALERT_AI_FAILURE_RATE_THRESHOLD_PERCENT")
    pipeline_staleness_minutes = _env_int("ALERT_PIPELINE_STALENESS_MINUTES")
    security_event_threshold = _env_int("ALERT_SECURITY_EVENT_THRESHOLD")

    alert_rules = [
        _alert_rule("api_error_rate", "API error rate", error_rate_threshold, "percent"),
        _alert_rule("ai_provider_failure_rate", "AI provider failure rate", ai_failure_threshold, "percent"),
        _alert_rule("pipeline_staleness", "Data pipeline staleness", pipeline_staleness_minutes, "minutes"),
        _alert_rule("security_event_spike", "Security event spike", security_event_threshold, "events"),
    ]

    missing: list[str] = []
    if enabled:
        required = {
            "INCIDENT_RESPONSE_OWNER_CONTACT": owner_contact_configured,
            "INCIDENT_RESPONSE_CHANNEL": channel_configured,
            "INCIDENT_RESPONSE_RUNBOOK_URL": runbook_configured,
            "INCIDENT_RESPONSE_SEVERITY_MATRIX_URL": severity_matrix_configured,
            "INCIDENT_BREACH_NOTIFICATION_CONTACT": breach_notification_contact_configured,
            "ALERT_ERROR_RATE_THRESHOLD_PERCENT": error_rate_threshold is not None,
            "ALERT_AI_FAILURE_RATE_THRESHOLD_PERCENT": ai_failure_threshold is not None,
            "ALERT_PIPELINE_STALENESS_MINUTES": pipeline_staleness_minutes is not None,
            "ALERT_SECURITY_EVENT_THRESHOLD": security_event_threshold is not None,
        }
        missing = [name for name, present in required.items() if not present]

    configured = enabled and not missing
    if configured:
        status = "ready"
    elif enabled:
        status = "action_required"
    else:
        status = "disabled"

    return {
        "source": "backend.incident_response",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "enabled": enabled,
        "configured": configured,
        "status": status,
        "owner_contact_configured": owner_contact_configured,
        "channel_configured": channel_configured,
        "runbook_configured": runbook_configured,
        "severity_matrix_configured": severity_matrix_configured,
        "breach_notification_contact_configured": breach_notification_contact_configured,
        "missing": missing,
        "incident_phases": INCIDENT_PHASES,
        "alert_rules": alert_rules,
        "secret_values_exposed": False,
        "privacy_note": "Incident readiness reports configuration evidence only and do not expose patient identifiers, clinical text, webhook secrets, contact values, channel names, or runbook URLs.",
    }
