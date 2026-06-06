"""Security assurance readiness metadata.

This module does not run scans or generate SBOM artifacts. It reports PHI-safe
evidence metadata for secret scanning, dependency scanning, SBOM generation,
vulnerability scanning, and penetration-test review.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

CONTROL_DEFINITIONS = (
    ("secret_scan", "Secret scan evidence", "SECRET_SCAN_LAST_RUN_AT", "timestamp"),
    ("dependency_scan", "Dependency scan evidence", "DEPENDENCY_SCAN_LAST_RUN_AT", "timestamp"),
    ("sbom", "Software bill of materials evidence", "SBOM_GENERATED_AT", "timestamp"),
    ("vulnerability_scan", "Vulnerability scan evidence", "VULNERABILITY_SCAN_LAST_RUN_AT", "timestamp"),
    ("penetration_test", "Penetration test report evidence", "PEN_TEST_REPORT_URL", "configured"),
)


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


def _env_non_negative_int(name: str) -> int | None:
    value = _env_text(name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _parse_datetime(name: str) -> str | None:
    value = _env_text(name)
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _evidence_control(control_id: str, label: str, env_name: str, evidence_type: str) -> dict[str, Any]:
    evidence = bool(_env_text(env_name)) if evidence_type == "configured" else bool(_parse_datetime(env_name))
    return {
        "id": control_id,
        "label": label,
        "env": env_name,
        "evidence_type": evidence_type,
        "configured": evidence,
    }


def _finding_control(control_id: str, label: str, env_name: str) -> dict[str, Any]:
    count = _env_non_negative_int(env_name)
    return {
        "id": control_id,
        "label": label,
        "env": env_name,
        "open_count": count,
        "configured": count == 0,
    }


def get_readiness() -> dict[str, Any]:
    enabled = _env_bool("SECURITY_ASSURANCE_ENABLED", False)
    owner_contact_configured = bool(_env_text("SECURITY_OWNER_CONTACT"))
    runbook_configured = bool(_env_text("SECURITY_RUNBOOK_URL"))
    controls = [
        _evidence_control(control_id, label, env_name, evidence_type)
        for control_id, label, env_name, evidence_type in CONTROL_DEFINITIONS
    ]
    controls.extend([
        _finding_control("critical_findings", "Open critical security findings", "SECURITY_FINDINGS_OPEN_CRITICAL"),
        _finding_control("high_findings", "Open high security findings", "SECURITY_FINDINGS_OPEN_HIGH"),
    ])

    missing: list[str] = []
    if enabled:
        required = {
            "SECURITY_OWNER_CONTACT": owner_contact_configured,
            "SECURITY_RUNBOOK_URL": runbook_configured,
        }
        missing.extend(name for name, present in required.items() if not present)
        missing.extend(control["env"] for control in controls if not control["configured"])

    configured = enabled and not missing
    if configured:
        status = "ready"
    elif enabled:
        status = "action_required"
    else:
        status = "disabled"

    return {
        "source": "backend.security_assurance",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "enabled": enabled,
        "configured": configured,
        "status": status,
        "owner_contact_configured": owner_contact_configured,
        "runbook_configured": runbook_configured,
        "missing": missing,
        "controls": controls,
        "secret_values_exposed": False,
        "privacy_note": "Security assurance reports evidence metadata only and does not expose contacts, URLs, secrets, patient identifiers, or clinical data.",
    }
