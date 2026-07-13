"""PHI-safe audit logging utilities."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from sqlalchemy.orm import Session

from . import models

logger = logging.getLogger(__name__)

MAX_AUDIT_DETAIL_LENGTH = 1200
REDACTED = "[redacted]"

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_DOB_RE = re.compile(r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
_LONG_NUMBER_RE = re.compile(r"\b\d{9,}\b")
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key|authorization)\b\s*[:=]\s*[^,\s;]+"
)

_SENSITIVE_KEY_PARTS = {
    "about",
    "ailment",
    "authorization",
    "clinical",
    "condition",
    "content",
    "data",
    "diagnosis",
    "dob",
    "email",
    "full_name",
    "message",
    "name",
    "note",
    "password",
    "phone",
    "prediction",
    "profile_picture",
    "reason",
    "secret",
    "ssn",
    "symptom",
    "token",
}


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _sanitize_text(value: str) -> str:
    sanitized = _SECRET_ASSIGNMENT_RE.sub(r"\1=[redacted-secret]", value)
    sanitized = _EMAIL_RE.sub("[redacted-email]", sanitized)
    sanitized = _DOB_RE.sub("[redacted-date]", sanitized)
    sanitized = _PHONE_RE.sub("[redacted-phone]", sanitized)
    sanitized = _LONG_NUMBER_RE.sub("[redacted-number]", sanitized)
    if len(sanitized) > MAX_AUDIT_DETAIL_LENGTH:
        sanitized = sanitized[:MAX_AUDIT_DETAIL_LENGTH] + "...[truncated]"
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        sanitized = {}
        for raw_key, raw_value in value.items():
            key = _sanitize_text(str(raw_key))
            sanitized[key] = REDACTED if _is_sensitive_key(key) else _sanitize_value(raw_value)
        return sanitized

    if isinstance(value, (list, tuple, set)):
        return [_sanitize_value(item) for item in value]

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()

    if value is None or isinstance(value, (bool, int, float)):
        return value

    return _sanitize_text(str(value))


def sanitize_audit_details(details: Any) -> str:
    """Serialize audit details after removing likely PHI, PII, and secrets."""
    if details is None:
        return ""

    if isinstance(details, str):
        return _sanitize_text(details)

    sanitized = _sanitize_value(details)
    try:
        rendered = json.dumps(sanitized, sort_keys=True, separators=(",", ":"), default=str)
    except TypeError:
        rendered = str(sanitized)
    return _sanitize_text(rendered)


def _lookup_user_facility_id(db: Session, user_id: Optional[int]) -> Optional[int]:
    if user_id is None:
        return None
    row = db.query(models.User.facility_id).filter(models.User.id == user_id).first()
    if row is None:
        return None
    return row[0]


def _resolve_audit_facility_id(
    db: Session,
    *,
    facility_id: Optional[int],
    actor_user_id: Optional[int],
    target_user_id: Optional[int],
) -> Optional[int]:
    if facility_id is not None:
        return facility_id
    return _lookup_user_facility_id(db, target_user_id) or _lookup_user_facility_id(db, actor_user_id)


def record_audit_event(
    db: Session,
    *,
    actor_user_id: Optional[int],
    action: str,
    target_user_id: Optional[int] = None,
    facility_id: Optional[int] = None,
    details: Any = None,
) -> Optional[models.AuditLog]:
    """
    Persist an audit event without exposing PHI in the details column.

    Audit failure should not block the primary user workflow; callers should
    perform the business write first, then call this helper.
    """
    try:
        entry = models.AuditLog(
            facility_id=_resolve_audit_facility_id(
                db,
                facility_id=facility_id,
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
            ),
            admin_id=actor_user_id,
            target_user_id=target_user_id,
            action=action,
            details=sanitize_audit_details(details),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        logger.error("Audit log failed")
        return None


def audit_log_to_response(entry: models.AuditLog) -> dict[str, Any]:
    """Return a PHI-safe audit log representation for admin review."""
    timestamp = entry.timestamp
    if isinstance(timestamp, datetime):
        timestamp = timestamp.astimezone(timezone.utc).isoformat()

    return {
        "id": entry.id,
        "facility_id": entry.facility_id,
        "actor_user_id": entry.admin_id,
        "target_user_id": entry.target_user_id,
        "action": entry.action,
        "timestamp": timestamp,
        "details": sanitize_audit_details(entry.details),
    }
