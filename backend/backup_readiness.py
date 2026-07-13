"""Backup and restore readiness metadata.

This module does not execute backups or restores. It reports PHI-safe
configuration evidence so administrators can verify that deployment-specific
backup, retention, and restore-test runbooks are in place.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

RESTORE_TEST_MAX_AGE_DAYS = 90
BACKUP_CAPABILITIES = {
    "scheduled_backups": "database and storage backups are configured by the deployment operator",
    "restore_rehearsal": "restore evidence is recorded for production-readiness review",
    "retention_policy": "backup retention is explicit and contract-reviewed",
    "encryption": "backup encryption is required before handling production PHI",
    "deletion_guard": "restore procedures must not reintroduce deleted patient data outside approved rollback windows",
}


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


def _env_int(name: str) -> int | None:
    value = _env_text(name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _parse_datetime(name: str) -> datetime | None:
    value = _env_text(name)
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_stale(value: datetime | None, *, max_age_days: int = RESTORE_TEST_MAX_AGE_DAYS) -> bool:
    if value is None:
        return False
    age = datetime.now(timezone.utc) - value
    return age.days > max_age_days


def _iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def get_readiness() -> dict[str, Any]:
    enabled = _env_bool("BACKUP_ENABLED", False)
    provider = _env_text("BACKUP_PROVIDER")
    storage_region = _env_text("BACKUP_STORAGE_REGION")
    retention_days = _env_int("BACKUP_RETENTION_DAYS")
    last_success_at = _parse_datetime("BACKUP_LAST_SUCCESS_AT")
    restore_tested_at = _parse_datetime("BACKUP_RESTORE_TESTED_AT")
    encryption_enabled = _env_bool("BACKUP_ENCRYPTION_ENABLED", False)
    owner_contact_configured = bool(_env_text("BACKUP_OWNER_CONTACT"))
    runbook_configured = bool(_env_text("BACKUP_RUNBOOK_URL"))
    restore_test_stale = _is_stale(restore_tested_at)

    missing: list[str] = []
    if enabled:
        required = {
            "BACKUP_PROVIDER": bool(provider),
            "BACKUP_STORAGE_REGION": bool(storage_region),
            "BACKUP_RETENTION_DAYS": retention_days is not None,
            "BACKUP_LAST_SUCCESS_AT": last_success_at is not None,
            "BACKUP_RESTORE_TESTED_AT": restore_tested_at is not None and not restore_test_stale,
            "BACKUP_ENCRYPTION_ENABLED": encryption_enabled,
            "BACKUP_OWNER_CONTACT": owner_contact_configured,
            "BACKUP_RUNBOOK_URL": runbook_configured,
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
        "source": "backend.backup_readiness",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "enabled": enabled,
        "configured": configured,
        "status": status,
        "provider": provider,
        "storage_region": storage_region,
        "retention_days": retention_days,
        "last_success_at": _iso_or_none(last_success_at),
        "restore_tested_at": _iso_or_none(restore_tested_at),
        "restore_test_stale": restore_test_stale,
        "restore_test_max_age_days": RESTORE_TEST_MAX_AGE_DAYS,
        "encryption_enabled": encryption_enabled,
        "owner_contact_configured": owner_contact_configured,
        "runbook_configured": runbook_configured,
        "missing": missing,
        "capabilities": dict(BACKUP_CAPABILITIES),
        "secret_values_exposed": False,
        "privacy_note": "Backup readiness reports operational metadata only and do not expose backup credentials, owner contact values, runbook URLs, patient identifiers, or clinical data.",
    }
