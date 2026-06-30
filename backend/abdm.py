import logging
import os
import sys
from types import ModuleType
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

try:
    import clinical_fhir_abdm.abdm as _pkg_abdm
except ImportError:
    _pkg_abdm = None

class _MicroservicesABDMSettings:
    def __init__(self, data):
        self.client_id = data["client_id"]
        self.client_secret = data["client_secret"]
        self.abdm_url = data["abdm_url"]
        self.consent_request_path = data["consent_request_path"]
        self._configured = data["configured"]
        self._missing_keys = data["missing_keys"]

    def configured_for_submission(self) -> bool:
        return self._configured

    def missing_for_submission(self) -> list[str]:
        return self._missing_keys

def _call_abdm_get_settings():
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    res = requests.get(f"{service_url}/abdm/settings", timeout=10)
    res.raise_for_status()
    return _MicroservicesABDMSettings(res.json())

def _call_abdm_get_readiness():
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    res = requests.get(f"{service_url}/abdm/readiness", timeout=10)
    res.raise_for_status()
    return res.json()

def _call_abdm_normalize_consent_callback(payload):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    res = requests.post(f"{service_url}/abdm/consent/callback", json=payload, timeout=10)
    res.raise_for_status()
    return res.json()

def _call_abdm_prepare_consent_request(
    patient_abha_address, purpose_code, hi_types, date_from, date_to, data_erase_at, requester_id, consent_manager_id=None, transport=None
):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    payload = {
        "patient_abha_address": patient_abha_address,
        "purpose_code": purpose_code,
        "hi_types": hi_types,
        "date_from": str(date_from) if date_from else None,
        "date_to": str(date_to) if date_to else None,
        "data_erase_at": str(data_erase_at) if data_erase_at else None,
        "requester_id": requester_id,
        "consent_manager_id": consent_manager_id
    }
    res = requests.post(f"{service_url}/abdm/consent/request", json=payload, timeout=10)
    res.raise_for_status()
    return res.json()


class _AbdmModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if os.environ.get("MICROSERVICES_MODE") == "true":
            if name == "get_settings":
                return _call_abdm_get_settings
            elif name == "get_readiness":
                return _call_abdm_get_readiness
            elif name == "normalize_consent_callback":
                return _call_abdm_normalize_consent_callback
            elif name == "prepare_consent_request":
                return _call_abdm_prepare_consent_request

        if _pkg_abdm is not None and hasattr(_pkg_abdm, name):
            return getattr(_pkg_abdm, name)
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if _pkg_abdm is not None and hasattr(_pkg_abdm, name):
            setattr(_pkg_abdm, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _AbdmModule

# Populate globals with package attributes to make mock/patch happy
if _pkg_abdm is not None:
    for _name in dir(_pkg_abdm):
        if not _name.startswith("__"):
            globals()[_name] = getattr(_pkg_abdm, _name)

if _pkg_abdm is None:
    logger.warning("clinical-fhir-abdm package not installed. Running in mock/fallback mode.")

    class ABDMSettings:
        def __init__(self):
            self.client_id = "mock-client-id"
            self.client_secret = "mock-client-secret"
            self.abdm_url = "https://mock.abdm.gov.in"
            self.consent_request_path = "/v0.5/consent-requests/init"

        def configured_for_submission(self) -> bool:
            return True

        def missing_for_submission(self) -> list[str]:
            return []

    def get_settings() -> ABDMSettings:
        return ABDMSettings()

    def get_readiness() -> dict[str, Any]:
        return {"configured": True, "missing_keys": [], "status": "mock_ready"}

    def normalize_consent_callback(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "consent_id": payload.get("consentId", "mock-consent-id"),
            "status": payload.get("status", "GRANTED"),
            "patient_id": "demo@sbx",
            "consent_detail": payload,
        }

    def build_consent_request_payload(
        patient_abha_address: str,
        purpose_code: str,
        hi_types: list[str],
        date_from: Any,
        date_to: Any,
        data_erase_at: Any,
        requester_id: str,
        consent_manager_id: Optional[str] = None,
    ) -> dict[str, Any]:
        return {
            "requestId": "mock-request-id",
            "timestamp": "2026-06-30T10:00:00Z",
            "consent": {
                "purpose": {"code": purpose_code},
                "patient": {"id": patient_abha_address},
                "hiTypes": hi_types,
            },
        }

    def prepare_consent_request(
        patient_abha_address: str,
        purpose_code: str,
        hi_types: list[str],
        date_from: Any,
        date_to: Any,
        data_erase_at: Any,
        requester_id: str,
        consent_manager_id: Optional[str] = None,
        transport: Optional[Any] = None,
    ) -> dict[str, Any]:
        return {"status": "initiated", "consentRequestId": "mock-consent-request-id", "payload": {}}
