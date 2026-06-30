import logging
import sys
from types import ModuleType
from typing import Any, Iterable

logger = logging.getLogger(__name__)

try:
    import clinical_fhir_abdm.fhir as _pkg_fhir
except ImportError:
    _pkg_fhir = None


class _FhirModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if _pkg_fhir is not None and hasattr(_pkg_fhir, name):
            return getattr(_pkg_fhir, name)
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if _pkg_fhir is not None and hasattr(_pkg_fhir, name):
            setattr(_pkg_fhir, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _FhirModule

# Populate globals with package attributes to make mock/patch happy
if _pkg_fhir is not None:
    for _name in dir(_pkg_fhir):
        if not _name.startswith("__"):
            globals()[_name] = getattr(_pkg_fhir, _name)

if _pkg_fhir is None:
    logger.warning("clinical-fhir-abdm package not installed. Running in mock/fallback mode.")

    class FHIRValidationError(ValueError):
        pass

    LOINC_SYSTEM = "http://loinc.org"
    UCUM_SYSTEM = "http://unitsofmeasure.org"
    VITAL_COMPONENTS = (
        ("heart_rate", "8867-4", "Heart rate", "beats/minute", "/min"),
        ("systolic_bp", "8480-6", "Systolic blood pressure", "mmHg", "mm[Hg]"),
        ("diastolic_bp", "8462-4", "Diastolic blood pressure", "mmHg", "mm[Hg]"),
        ("spo2", "59408-5", "Oxygen saturation in arterial blood by pulse oximetry", "%", "%"),
        ("temperature_c", "8310-5", "Body temperature", "Celsius", "Cel"),
        ("respiratory_rate", "9279-1", "Respiratory rate", "breaths/minute", "/min"),
    )

    def patient_resource(patient: Any) -> dict[str, Any]:
        return {
            "resourceType": "Patient",
            "id": str(getattr(patient, "id", "demo-id")),
            "name": [{"text": getattr(patient, "name", "Demo Patient")}],
            "gender": getattr(patient, "gender", "unknown"),
            "birthDate": str(getattr(patient, "dob", "2000-01-01")),
            "text": {"status": "generated", "div": "<div>Mock Patient Resource</div>"},
        }

    def encounter_resource(encounter: Any, patient_id: int | str) -> dict[str, Any]:
        return {
            "resourceType": "Encounter",
            "id": str(getattr(encounter, "id", "demo-encounter")),
            "status": "finished",
            "class": {"code": "AMB", "display": "ambulatory"},
            "subject": {"reference": f"Patient/{patient_id}"},
        }

    def observation_resource(observation: Any, patient_id: int | str) -> dict[str, Any]:
        return {
            "resourceType": "Observation",
            "id": str(getattr(observation, "id", "demo-obs")),
            "status": "final",
            "code": {"text": getattr(observation, "code_text", "Vital Sign")},
            "subject": {"reference": f"Patient/{patient_id}"},
            "valueQuantity": {"value": float(getattr(observation, "value", 0.0))},
        }

    def diagnostic_report_resource(result: Any, patient_id: int | str) -> dict[str, Any]:
        return {
            "resourceType": "DiagnosticReport",
            "id": str(getattr(result, "id", "demo-report")),
            "status": "final",
            "code": {"text": "Clinical Diagnostic Report"},
            "subject": {"reference": f"Patient/{patient_id}"},
        }

    def medication_request_resource(prescription: Any, patient_id: int | str) -> dict[str, Any]:
        return {
            "resourceType": "MedicationRequest",
            "id": str(getattr(prescription, "id", "demo-med")),
            "status": "active",
            "intent": "order",
            "subject": {"reference": f"Patient/{patient_id}"},
        }

    def invoice_resource(invoice: Any, patient_id: int | str) -> dict[str, Any]:
        return {
            "resourceType": "Invoice",
            "id": str(getattr(invoice, "id", "demo-invoice")),
            "status": "issued",
            "subject": {"reference": f"Patient/{patient_id}"},
        }

    def care_event_resource(event: Any, patient_id: int | str) -> dict[str, Any]:
        return {
            "resourceType": "CarePlan",
            "id": str(getattr(event, "id", "demo-careplan")),
            "status": "active",
            "intent": "plan",
            "subject": {"reference": f"Patient/{patient_id}"},
        }

    def build_bundle(resources: Iterable[dict[str, Any]], timestamp: Any = None) -> dict[str, Any]:
        return {"resourceType": "Bundle", "type": "transaction", "entry": [{"resource": r} for r in resources]}

    def audit_event_resource(audit_log: Any) -> dict[str, Any]:
        return {
            "resourceType": "AuditEvent",
            "id": str(getattr(audit_log, "id", "demo-audit")),
            "type": {"code": "rest"},
            "agent": [{"requestor": True}],
            "source": {"observer": {"reference": "Device/healthcare-app"}},
        }
