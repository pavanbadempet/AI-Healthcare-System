"""DICOMweb configuration and metadata-link helpers.

This module does not store images, fetch pixel data, or call a PACS. It only
builds PHI-safe readiness metadata and DICOMweb URL shapes for configured
archives.
"""

from __future__ import annotations

import os
import re
from typing import Any

DICOMWEB_STANDARDS_NOTE = (
    "DICOMweb metadata links for PACS integration planning; validate against "
    "the target archive conformance statement before production exchange."
)
DICOMWEB_CAPABILITIES = {
    "QIDO-RS": "study search metadata links",
    "WADO-RS": "study metadata retrieval links",
    "STOW-RS": "configured store endpoint metadata",
}
_UID_PATTERN = re.compile(r"^[0-9]+(\.[0-9]+)*$")


class DICOMwebConfigurationError(ValueError):
    pass


class DICOMwebValidationError(ValueError):
    pass


def _enabled() -> bool:
    return os.getenv("DICOMWEB_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def _configured_base_url(base_url: str | None = None) -> str:
    configured = (base_url or os.getenv("DICOMWEB_BASE_URL", "")).strip().rstrip("/")
    if not configured:
        raise DICOMwebConfigurationError("DICOMWEB_BASE_URL is required")
    return configured


def _validate_study_instance_uid(study_instance_uid: str) -> str:
    uid = study_instance_uid.strip()
    if not uid or len(uid) > 64 or not _UID_PATTERN.fullmatch(uid):
        raise DICOMwebValidationError("Invalid DICOM StudyInstanceUID")
    return uid


def get_readiness() -> dict[str, Any]:
    base_url = os.getenv("DICOMWEB_BASE_URL", "").strip()
    ae_title = os.getenv("DICOMWEB_AE_TITLE", "").strip()
    token = os.getenv("DICOMWEB_BEARER_TOKEN", "").strip()
    enabled = _enabled()
    missing = []
    if enabled and not base_url:
        missing.append("DICOMWEB_BASE_URL")
    if enabled and not ae_title:
        missing.append("DICOMWEB_AE_TITLE")
    return {
        "enabled": enabled,
        "base_url_configured": bool(base_url),
        "ae_title_configured": bool(ae_title),
        "token_configured": bool(token),
        "missing": missing,
        "capabilities": dict(DICOMWEB_CAPABILITIES),
        "secrets_exposed": False,
        "pixel_data_included": False,
        "standards_note": DICOMWEB_STANDARDS_NOTE,
    }


def build_study_metadata_links(
    study_instance_uid: str,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    uid = _validate_study_instance_uid(study_instance_uid)
    configured_base_url = _configured_base_url(base_url)
    return {
        "study_instance_uid": uid,
        "qido_rs_study_search": f"{configured_base_url}/studies?StudyInstanceUID={uid}",
        "wado_rs_study_metadata": f"{configured_base_url}/studies/{uid}/metadata",
        "stow_rs_store": f"{configured_base_url}/studies",
        "pixel_data_included": False,
        "pii_exposed": False,
        "standards_note": DICOMWEB_STANDARDS_NOTE,
    }
