"""Retention policy readiness metadata.

This module does not delete, anonymize, archive, or export records. It reports
PHI-safe retention-window and legal-hold configuration evidence for production
readiness review.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

POLICY_WINDOWS = (
    ("patient_records", "Patient medical and account records", "PATIENT_RECORD_RETENTION_YEARS", "years"),
    ("chat_logs", "AI chat logs and conversational context", "CHAT_LOG_RETENTION_DAYS", "days"),
    ("audit_logs", "PHI-minimized security and compliance audit logs", "AUDIT_LOG_RETENTION_DAYS", "days"),
    (
        "interoperability_exports",
        "FHIR/ABDM/partner export manifests and reconciliation evidence",
        "INTEROPERABILITY_EXPORT_RETENTION_DAYS",
        "days",
    ),
    ("vector_store", "Derived vector-search records", "VECTOR_STORE_RETENTION_DAYS", "days"),
    ("lakehouse", "Raw, curated, and analytics lakehouse datasets", "LAKEHOUSE_RETENTION_DAYS", "days"),
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


def _env_positive_int(name: str) -> int | None:
    value = _env_text(name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _policy(policy_id: str, label: str, env_name: str, unit: str) -> dict[str, Any]:
    value = _env_positive_int(env_name)
    return {
        "id": policy_id,
        "label": label,
        "env": env_name,
        "retention": value,
        "unit": unit,
        "configured": value is not None,
    }


def get_readiness() -> dict[str, Any]:
    enabled = _env_bool("RETENTION_POLICY_ENABLED", False)
    owner_contact_configured = bool(_env_text("RETENTION_OWNER_CONTACT"))
    runbook_configured = bool(_env_text("RETENTION_RUNBOOK_URL"))
    legal_hold_process_configured = bool(_env_text("LEGAL_HOLD_PROCESS_URL"))
    policies = [_policy(policy_id, label, env_name, unit) for policy_id, label, env_name, unit in POLICY_WINDOWS]

    missing: list[str] = []
    if enabled:
        required = {
            "RETENTION_OWNER_CONTACT": owner_contact_configured,
            "RETENTION_RUNBOOK_URL": runbook_configured,
            "LEGAL_HOLD_PROCESS_URL": legal_hold_process_configured,
        }
        missing.extend(name for name, present in required.items() if not present)
        missing.extend(policy["env"] for policy in policies if not policy["configured"])

    configured = enabled and not missing
    if configured:
        status = "ready"
    elif enabled:
        status = "action_required"
    else:
        status = "disabled"

    return {
        "source": "backend.retention_policy",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "enabled": enabled,
        "configured": configured,
        "status": status,
        "owner_contact_configured": owner_contact_configured,
        "runbook_configured": runbook_configured,
        "legal_hold_process_configured": legal_hold_process_configured,
        "missing": missing,
        "policies": policies,
        "legal_hold_blocks_destructive_actions": legal_hold_process_configured,
        "destructive_actions_executed": False,
        "secret_values_exposed": False,
        "privacy_note": "Retention readiness reports policy metadata only and does not expose contacts, runbook URLs, legal-hold URLs, secrets, patient identifiers, or clinical data.",
    }
