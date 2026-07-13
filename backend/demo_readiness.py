"""PHI-safe demo readiness metadata."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/demo-readiness", tags=["Demo Readiness"])

TRUEISH_VALUES = {"1", "true", "yes", "on"}
REQUIRED_PRODUCTION_ENV = ("SECRET_KEY", "DATABASE_URL")
OPTIONAL_INTEGRATIONS: dict[str, tuple[str, ...]] = {
    "Gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "Ollama": ("OLLAMA_BASE_URL",),
    "ABDM": ("ABDM_CLIENT_ID", "ABDM_CLIENT_SECRET"),
    "DICOM": ("DICOMWEB_BASE_URL",),
    "SMART": ("SMART_CLIENT_ID", "SMART_ISSUER_URL"),
}


def _env_configured(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def _env_trueish(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in TRUEISH_VALUES


def _required_status() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "configured": _env_configured(name),
            "required_for": "production",
        }
        for name in REQUIRED_PRODUCTION_ENV
    }


def _optional_status() -> dict[str, dict[str, Any]]:
    optional: dict[str, dict[str, Any]] = {}
    for capability, env_names in OPTIONAL_INTEGRATIONS.items():
        configured = any(_env_configured(name) for name in env_names)
        optional[capability] = {
            "configured": configured,
            "blocker_for_demo": False,
        }
    return optional


def _status(demo_mode: bool, missing_required: list[str]) -> str:
    if demo_mode:
        return "demo-ready"
    if missing_required:
        return "production-blocked"
    return "pilot-ready"


@router.get("/")
def get_demo_readiness() -> dict[str, Any]:
    """Return operational demo readiness metadata without PHI or secrets."""
    demo_mode = _env_trueish("ABDM_DEMO_MODE")
    required = _required_status()
    optional = _optional_status()
    missing_required = [
        name
        for name, metadata in required.items()
        if not metadata["configured"]
    ]

    return {
        "status": _status(demo_mode, missing_required),
        "demo_mode": demo_mode,
        "environment": "demo" if demo_mode else "runtime",
        "required": required,
        "optional": optional,
        "missing_required": [] if demo_mode else missing_required,
        "capabilities": {
            "synthetic_demo": demo_mode,
            "external_ai_optional": optional["Gemini"]["configured"] or optional["Ollama"]["configured"],
            "interoperability_optional": optional["ABDM"]["configured"]
            or optional["DICOM"]["configured"]
            or optional["SMART"]["configured"],
            "production_runtime_configured": not missing_required,
        },
        "clinical_safety_note": (
            "Demo readiness is operational metadata only and does not certify "
            "clinical/legal/regulatory/production readiness."
        ),
        "privacy_note": (
            "This readiness endpoint reports operational metadata only and does "
            "not expose patient data, PHI, or secret values."
        ),
        "source": "backend.demo_readiness",
    }
