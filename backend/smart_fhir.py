"""SMART on FHIR readiness and launch URL helpers.

This module does not exchange authorization codes or store EHR tokens. It only
builds PHI-safe readiness metadata and authorization URLs for registered EHR
client configuration.
"""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

DEFAULT_SMART_SCOPES = "launch/patient patient/*.read openid fhirUser"
SMART_STANDARDS_NOTE = (
    "SMART on FHIR launch metadata for EHR integration planning; complete "
    "client registration, redirect URI approval, and buyer security review are "
    "required before production launch."
)
SMART_CAPABILITIES = [
    "launch-ehr",
    "launch-standalone",
    "client-public",
    "sso-openid-connect",
    "context-passthrough-patient",
]
_SAFE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class SMARTConfigurationError(ValueError):
    pass


class SMARTValidationError(ValueError):
    pass


def _enabled() -> bool:
    return os.getenv("SMART_FHIR_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _required_env(name: str) -> str:
    value = _env(name)
    if not value:
        raise SMARTConfigurationError(f"{name} is required")
    return value


def _safe_token(value: str | None, *, field_name: str) -> str:
    token = (value or "").strip()
    if not token:
        return str(uuid4())
    if not _SAFE_TOKEN_PATTERN.fullmatch(token):
        raise SMARTValidationError(f"Invalid SMART {field_name}")
    return token


def get_readiness() -> dict[str, Any]:
    enabled = _enabled()
    configured = {
        "base_url": bool(_env("SMART_FHIR_BASE_URL")),
        "authorization_endpoint": bool(_env("SMART_AUTHORIZATION_ENDPOINT")),
        "token_endpoint": bool(_env("SMART_TOKEN_ENDPOINT")),
        "client_id": bool(_env("SMART_CLIENT_ID")),
        "redirect_uri": bool(_env("SMART_REDIRECT_URI")),
    }
    missing = []
    if enabled:
        for key, present in configured.items():
            if not present:
                missing.append(f"SMART_{key.upper()}")
    return {
        "enabled": enabled,
        "base_url_configured": configured["base_url"],
        "authorization_endpoint_configured": configured["authorization_endpoint"],
        "token_endpoint_configured": configured["token_endpoint"],
        "client_id_configured": configured["client_id"],
        "redirect_uri_configured": configured["redirect_uri"],
        "client_secret_configured": bool(_env("SMART_CLIENT_SECRET")),
        "scopes": _env("SMART_SCOPES") or DEFAULT_SMART_SCOPES,
        "capabilities": list(SMART_CAPABILITIES),
        "missing": missing,
        "secrets_exposed": False,
        "token_exchange_enabled": False,
        "standards_note": SMART_STANDARDS_NOTE,
    }


def build_authorization_url(
    *,
    state: str | None = None,
    launch: str | None = None,
    scope: str | None = None,
) -> str:
    authorization_endpoint = _required_env("SMART_AUTHORIZATION_ENDPOINT")
    client_id = _required_env("SMART_CLIENT_ID")
    redirect_uri = _required_env("SMART_REDIRECT_URI")
    audience = _required_env("SMART_FHIR_BASE_URL")
    safe_state = _safe_token(state, field_name="state")
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": (scope or _env("SMART_SCOPES") or DEFAULT_SMART_SCOPES).strip(),
        "state": safe_state,
        "aud": audience,
    }
    if launch:
        params["launch"] = _safe_token(launch, field_name="launch")
    return f"{authorization_endpoint}?{urlencode(params)}"


def build_authorization_response(
    *,
    state: str | None = None,
    launch: str | None = None,
    scope: str | None = None,
) -> dict[str, Any]:
    return {
        "authorization_url": build_authorization_url(state=state, launch=launch, scope=scope),
        "response_type": "code",
        "secrets_exposed": False,
        "token_exchange_enabled": False,
        "standards_note": SMART_STANDARDS_NOTE,
    }
