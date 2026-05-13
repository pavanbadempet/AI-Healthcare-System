"""ABDM connector helpers for India-first interoperability workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from typing import Any, Callable
from urllib import request as urllib_request
from uuid import uuid4


class ABDMConfigurationError(RuntimeError):
    """Raised when outbound ABDM submission is requested without configuration."""


class ABDMValidationError(ValueError):
    """Raised when an ABDM request payload cannot be constructed safely."""


PURPOSE_CODES = {
    "CAREMGT": "Care Management",
    "BTG": "Break the Glass",
    "PUBHLTH": "Public Health",
    "HPAYMT": "Healthcare Payment",
    "DSRCH": "Disease Specific Healthcare Research",
    "PATRQT": "Self Requested",
}

DEFAULT_HI_TYPES = [
    "Prescription",
    "DiagnosticReport",
    "OPConsultation",
    "DischargeSummary",
    "ImmunizationRecord",
    "HealthDocumentRecord",
]
SUPPORTED_HI_TYPES = set(DEFAULT_HI_TYPES) | {"WellnessRecord"}

ABDM_PURPOSE_REF_URI = "http://terminology.hl7.org/CodeSystem/v3-ActReason"
DEFAULT_CONSENT_PATH = "/v3/consent/request/init"
CALLBACK_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
SUPPORTED_CALLBACK_STATUSES = {
    "REQUESTED": "requested",
    "GRANTED": "active",
    "ACTIVE": "active",
    "DENIED": "denied",
    "REVOKED": "revoked",
    "EXPIRED": "expired",
}

Transport = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


@dataclass(frozen=True)
class ABDMSettings:
    enabled: bool
    environment: str
    base_url: str | None
    consent_request_path: str
    hiu_id: str | None
    hip_id: str | None
    cm_id: str
    client_id: str | None
    client_secret: str | None
    access_token: str | None
    requester_name: str
    requester_identifier_type: str
    requester_identifier_system: str
    requester_identifier_value: str | None
    timeout_seconds: float

    @property
    def missing_for_submission(self) -> list[str]:
        required = {
            "ABDM_BASE_URL": self.base_url,
            "ABDM_HIU_ID": self.hiu_id,
            "ABDM_CLIENT_ID": self.client_id,
            "ABDM_CLIENT_SECRET": self.client_secret,
            "ABDM_ACCESS_TOKEN": self.access_token,
            "ABDM_REQUESTER_IDENTIFIER_VALUE": self.requester_identifier_value,
        }
        return [name for name, value in required.items() if not value]

    @property
    def configured_for_submission(self) -> bool:
        return self.enabled and not self.missing_for_submission


def _env_text(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def get_settings() -> ABDMSettings:
    return ABDMSettings(
        enabled=_env_bool("ABDM_ENABLED", False),
        environment=_env_text("ABDM_ENVIRONMENT", "sandbox") or "sandbox",
        base_url=_env_text("ABDM_BASE_URL"),
        consent_request_path=_env_text("ABDM_CONSENT_REQUEST_PATH", DEFAULT_CONSENT_PATH) or DEFAULT_CONSENT_PATH,
        hiu_id=_env_text("ABDM_HIU_ID"),
        hip_id=_env_text("ABDM_HIP_ID"),
        cm_id=_env_text("ABDM_CM_ID", "sbx") or "sbx",
        client_id=_env_text("ABDM_CLIENT_ID"),
        client_secret=_env_text("ABDM_CLIENT_SECRET"),
        access_token=_env_text("ABDM_ACCESS_TOKEN"),
        requester_name=_env_text("ABDM_REQUESTER_NAME", "AI Healthcare System") or "AI Healthcare System",
        requester_identifier_type=_env_text("ABDM_REQUESTER_IDENTIFIER_TYPE", "REGNO") or "REGNO",
        requester_identifier_system=(
            _env_text("ABDM_REQUESTER_IDENTIFIER_SYSTEM", "https://facility.abdm.gov.in")
            or "https://facility.abdm.gov.in"
        ),
        requester_identifier_value=_env_text("ABDM_REQUESTER_IDENTIFIER_VALUE"),
        timeout_seconds=_env_float("ABDM_TIMEOUT_SECONDS", 20.0),
    )


def get_readiness() -> dict[str, Any]:
    settings = get_settings()
    return {
        "enabled": settings.enabled,
        "configured": settings.configured_for_submission,
        "environment": settings.environment,
        "base_url_configured": bool(settings.base_url),
        "cm_id": settings.cm_id,
        "hiu_id_configured": bool(settings.hiu_id),
        "hip_id_configured": bool(settings.hip_id),
        "requester_identifier_configured": bool(settings.requester_identifier_value),
        "missing": settings.missing_for_submission,
        "supported_hi_types": sorted(SUPPORTED_HI_TYPES),
        "default_hi_types": DEFAULT_HI_TYPES,
        "supported_purpose_codes": sorted(PURPOSE_CODES),
        "submission_path": settings.consent_request_path,
    }


def _fhir_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _validate_callback_id(value: str | None, label: str, *, required: bool = False) -> str | None:
    normalized = (value or "").strip()
    if not normalized:
        if required:
            raise ABDMValidationError(f"{label} is invalid")
        return None
    if not CALLBACK_ID_PATTERN.fullmatch(normalized):
        raise ABDMValidationError(f"{label} is invalid")
    return normalized


def _validate_callback_status(status: str) -> str:
    normalized = status.strip().upper()
    if normalized not in SUPPORTED_CALLBACK_STATUSES:
        raise ABDMValidationError("Unsupported ABDM consent callback status")
    return normalized


def _validate_patient_abha_address(patient_abha_address: str) -> str:
    normalized = patient_abha_address.strip()
    if not normalized or "@" not in normalized:
        raise ABDMValidationError("Valid patient ABHA address is required")
    return normalized


def _validate_purpose_code(purpose_code: str) -> str:
    code = purpose_code.strip().upper()
    if code not in PURPOSE_CODES:
        raise ABDMValidationError("Unsupported ABDM purpose code")
    return code


def _validate_hi_types(hi_types: list[str] | None) -> list[str]:
    requested = hi_types or DEFAULT_HI_TYPES
    validated: list[str] = []
    for raw_hi_type in requested:
        hi_type = raw_hi_type.strip()
        if hi_type not in SUPPORTED_HI_TYPES:
            raise ABDMValidationError("Unsupported ABDM health information type")
        if hi_type not in validated:
            validated.append(hi_type)
    if not validated:
        raise ABDMValidationError("At least one ABDM health information type is required")
    return validated


def normalize_consent_callback(
    *,
    request_id: str,
    status: str,
    abdm_consent_id: str | None = None,
    hi_types: list[str] | None = None,
    event_type: str | None = None,
    notification_at: datetime | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    """Normalize ABDM consent callback metadata without storing raw payloads."""
    normalized_request_id = _validate_callback_id(request_id, "ABDM request id", required=True)
    normalized_consent_id = _validate_callback_id(abdm_consent_id, "ABDM consent id")
    normalized_error_code = _validate_callback_id(error_code, "ABDM error code")
    normalized_event_type = _validate_callback_id(event_type or "consent_status", "ABDM event type", required=True)
    normalized_status = _validate_callback_status(status)
    normalized_hi_types = _validate_hi_types(hi_types) if hi_types else []
    observed_at = notification_at or datetime.now(timezone.utc)
    normalized_payload = {
        "request_id": normalized_request_id,
        "abdm_consent_id": normalized_consent_id,
        "status": normalized_status,
        "hi_types": normalized_hi_types,
        "event_type": normalized_event_type,
        "notification_at": _fhir_datetime(observed_at),
        "error_code": normalized_error_code,
    }
    canonical = json.dumps(normalized_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return {
        **normalized_payload,
        "local_consent_status": SUPPORTED_CALLBACK_STATUSES[normalized_status],
        "payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "raw_payload_stored": False,
    }


def _validate_date_range(date_from: datetime, date_to: datetime, data_erase_at: datetime) -> None:
    if date_to < date_from:
        raise ABDMValidationError("ABDM consent date range is invalid")
    if data_erase_at <= date_to:
        raise ABDMValidationError("ABDM data erase time must be after the requested date range")


def _clean_dict(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, dict):
            nested = _clean_dict(value)
            if nested:
                cleaned[key] = nested
            continue
        if isinstance(value, list):
            cleaned_list = [
                _clean_dict(item) if isinstance(item, dict) else item
                for item in value
                if item is not None
            ]
            if cleaned_list:
                cleaned[key] = cleaned_list
            continue
        cleaned[key] = value
    return cleaned


def build_consent_request_payload(
    *,
    patient_abha_address: str,
    purpose_code: str,
    hi_types: list[str] | None,
    date_from: datetime,
    date_to: datetime,
    data_erase_at: datetime,
    hip_id: str | None = None,
    care_context_reference: str | None = None,
    request_id: str | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    abha_address = _validate_patient_abha_address(patient_abha_address)
    purpose = _validate_purpose_code(purpose_code)
    selected_hi_types = _validate_hi_types(hi_types)
    _validate_date_range(date_from, date_to, data_erase_at)

    settings = get_settings()
    if not settings.hiu_id:
        raise ABDMConfigurationError("ABDM_HIU_ID is required to build consent request")

    care_context = None
    if care_context_reference and care_context_reference.strip():
        care_context = [{"referenceNumber": care_context_reference.strip()}]

    requested_at = timestamp or datetime.now(timezone.utc)
    requester_identifier = {
        "type": settings.requester_identifier_type,
        "value": settings.requester_identifier_value,
        "system": settings.requester_identifier_system,
    }
    return _clean_dict({
        "requestId": request_id or str(uuid4()),
        "timestamp": _fhir_datetime(requested_at),
        "consent": {
            "purpose": {
                "text": PURPOSE_CODES[purpose],
                "code": purpose,
                "refUri": ABDM_PURPOSE_REF_URI,
            },
            "patient": {"id": abha_address},
            "hiu": {"id": settings.hiu_id},
            "hip": {"id": hip_id.strip()} if hip_id and hip_id.strip() else None,
            "careContexts": care_context,
            "requester": {
                "name": settings.requester_name,
                "identifier": requester_identifier,
            },
            "hiTypes": selected_hi_types,
            "permission": {
                "accessMode": "VIEW",
                "dateRange": {
                    "from": _fhir_datetime(date_from),
                    "to": _fhir_datetime(date_to),
                },
                "dataEraseAt": _fhir_datetime(data_erase_at),
                "frequency": {
                    "unit": "HOUR",
                    "value": 0,
                    "repeats": 0,
                },
            },
        },
    })


def _default_transport(endpoint: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    req = urllib_request.Request(endpoint, data=body, headers=headers, method="POST")
    with urllib_request.urlopen(req, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
    if not response_body:
        return {}
    return json.loads(response_body)


def _submission_headers(settings: ABDMSettings) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-CM-ID": settings.cm_id,
        "X-HIU-ID": settings.hiu_id or "",
    }
    if settings.access_token:
        headers["Authorization"] = f"Bearer {settings.access_token}"
    return headers


def prepare_consent_request(
    *,
    patient_abha_address: str,
    purpose_code: str,
    hi_types: list[str] | None,
    date_from: datetime,
    date_to: datetime,
    data_erase_at: datetime,
    hip_id: str | None = None,
    care_context_reference: str | None = None,
    submit: bool = False,
    transport: Transport | None = None,
    request_id: str | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    endpoint = f"{settings.base_url.rstrip('/')}{settings.consent_request_path}" if settings.base_url else None
    if submit and (not settings.configured_for_submission or not endpoint):
        raise ABDMConfigurationError("ABDM connector is not fully configured")

    payload = build_consent_request_payload(
        patient_abha_address=patient_abha_address,
        purpose_code=purpose_code,
        hi_types=hi_types,
        date_from=date_from,
        date_to=date_to,
        data_erase_at=data_erase_at,
        hip_id=hip_id,
        care_context_reference=care_context_reference,
        request_id=request_id,
        timestamp=timestamp,
    )
    if not submit:
        return {
            "submitted": False,
            "status": "ready_for_submission",
            "endpoint": endpoint,
            "payload": payload,
        }

    active_transport = transport or _default_transport
    response = active_transport(
        endpoint,
        _submission_headers(settings),
        payload,
        settings.timeout_seconds,
    )
    return {
        "submitted": True,
        "status": "submitted",
        "endpoint": endpoint,
        "payload": payload,
        "abdm_response": response,
    }
