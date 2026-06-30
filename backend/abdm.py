import logging
import sys
from types import ModuleType
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import clinical_fhir_abdm.abdm as _pkg_abdm
except ImportError:
    _pkg_abdm = None


class _AbdmModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
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
