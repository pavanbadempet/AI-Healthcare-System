import logging
import os
import sys
from datetime import date, datetime, timezone
from types import ModuleType
from typing import Any, Iterable

import requests

logger = logging.getLogger(__name__)

try:
    import clinical_fhir_abdm.fhir as _pkg_fhir
except ImportError:
    _pkg_fhir = None

def _call_fhir_patient(patient):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    data = {k: str(v) for k, v in patient.__dict__.items() if not k.startswith("_")}
    try:
        res = requests.post(f"{service_url}/fhir/patient", json={"patient": data}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")

def _call_fhir_encounter(encounter, patient_id):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    data = {k: str(v) for k, v in encounter.__dict__.items() if not k.startswith("_")}
    try:
        res = requests.post(f"{service_url}/fhir/encounter", json={"encounter": data, "patient_id": patient_id}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")

def _call_fhir_observation(observation, patient_id):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    data = {k: str(v) for k, v in observation.__dict__.items() if not k.startswith("_")}
    try:
        res = requests.post(f"{service_url}/fhir/observation", json={"observation": data, "patient_id": patient_id}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")

def _call_fhir_diagnostic_report(result, patient_id):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    data = {k: str(v) for k, v in result.__dict__.items() if not k.startswith("_")}
    try:
        res = requests.post(f"{service_url}/fhir/diagnostic_report", json={"result": data, "patient_id": patient_id}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")

def _call_fhir_medication_request(prescription, patient_id):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    data = {k: str(v) for k, v in prescription.__dict__.items() if not k.startswith("_")}
    try:
        res = requests.post(f"{service_url}/fhir/medication_request", json={"prescription": data, "patient_id": patient_id}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")

def _call_fhir_invoice(invoice, patient_id):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    data = {k: str(v) for k, v in invoice.__dict__.items() if not k.startswith("_")}
    try:
        res = requests.post(f"{service_url}/fhir/invoice", json={"invoice": data, "patient_id": patient_id}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")

def _call_fhir_care_event(event, patient_id):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    data = {k: str(v) for k, v in event.__dict__.items() if not k.startswith("_")}
    try:
        res = requests.post(f"{service_url}/fhir/care_event", json={"event": data, "patient_id": patient_id}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")

def _call_fhir_build_bundle(resources, timestamp=None):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    try:
        res = requests.post(f"{service_url}/fhir/build_bundle", json={"resources": list(resources)}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")

def _call_fhir_audit_event(audit_log):
    service_url = os.environ.get("ABDM_FHIR_SERVICE_URL", "http://127.0.0.1:8003")
    data = {k: str(v) for k, v in audit_log.__dict__.items() if not k.startswith("_")}
    try:
        res = requests.post(f"{service_url}/fhir/audit_event", json={"audit_log": data}, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        from fastapi import HTTPException
        logger.error(f"FHIR service error: {e}")
        raise HTTPException(status_code=502, detail="FHIR service is unavailable")


class _FhirModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if os.environ.get("MICROSERVICES_MODE") == "true":
            if name == "patient_resource":
                return _call_fhir_patient
            elif name == "encounter_resource":
                return _call_fhir_encounter
            elif name == "observation_resource":
                return _call_fhir_observation
            elif name == "diagnostic_report_resource":
                return _call_fhir_diagnostic_report
            elif name == "medication_request_resource":
                return _call_fhir_medication_request
            elif name == "invoice_resource":
                return _call_fhir_invoice
            elif name == "care_event_resource":
                return _call_fhir_care_event
            elif name == "build_bundle":
                return _call_fhir_build_bundle
            elif name == "audit_event_resource":
                return _call_fhir_audit_event

        if _pkg_fhir is not None and hasattr(_pkg_fhir, name):
            return getattr(_pkg_fhir, name)

        if name in globals():
            return globals()[name]

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
        ("spo2", "59408-5", "Oxygen saturation in arterial blood by oximetry", "%", "%"),
        ("temperature_c", "8310-5", "Body temperature", "Celsius", "Cel"),
        ("respiratory_rate", "9279-1", "Respiratory rate", "breaths/minute", "/min"),
    )

    def _string_id(value: Any) -> str:
        if value is None:
            raise FHIRValidationError("Invalid FHIR resource")
        return str(value)

    def _remove_none(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: _remove_none(nested)
                for key, nested in value.items()
                if nested is not None
            }
        if isinstance(value, list):
            return [_remove_none(item) for item in value if item is not None]
        return value

    def _date_string(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)

    def fhir_datetime(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    def patient_resource(patient: Any) -> dict[str, Any]:
        patient_id = _string_id(getattr(patient, "id", "demo-id"))
        gender = getattr(patient, "gender", None)
        if gender == "unknown":
            gender = None
        dob = getattr(patient, "dob", None)
        return _remove_none({
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [{"system": "ai-healthcare-system:user-id", "value": patient_id}],
            "name": [{"text": getattr(patient, "full_name", None) or getattr(patient, "username", None) or getattr(patient, "name", None) or "Demo Patient"}],
            "gender": gender,
            "birthDate": _date_string(dob),
        })

    def encounter_resource(encounter: Any, patient_id: int | str) -> dict[str, Any]:
        return _remove_none({
            "resourceType": "Encounter",
            "id": _string_id(getattr(encounter, "id", "demo-encounter")),
            "status": getattr(encounter, "status", "unknown") or "unknown",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": getattr(encounter, "encounter_type", None) or "AMB",
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "period": {
                "start": fhir_datetime(getattr(encounter, "started_at", None)),
                "end": fhir_datetime(getattr(encounter, "ended_at", None)),
            },
        })

    def observation_resource(observation: Any, patient_id: int | str) -> dict[str, Any]:
        components = []
        for field, code, display, unit, unit_code in VITAL_COMPONENTS:
            val = getattr(observation, field, None)
            if val is None:
                continue
            components.append({
                "code": {"coding": [{"system": LOINC_SYSTEM, "code": code, "display": display}], "text": display},
                "valueQuantity": {
                    "value": float(val),
                    "unit": unit,
                    "system": UCUM_SYSTEM,
                    "code": unit_code,
                },
            })
        return _remove_none({
            "resourceType": "Observation",
            "id": _string_id(getattr(observation, "id", "demo-obs")),
            "status": "final",
            "code": {"text": getattr(observation, "code_text", "Vital Sign")},
            "subject": {"reference": f"Patient/{patient_id}"},
            "encounter": {"reference": f"Encounter/{getattr(observation, 'encounter_id', '')}"} if getattr(observation, "encounter_id", None) else None,
            "effectiveDateTime": fhir_datetime(getattr(observation, "observed_at", None)),
            "component": components if components else None,
            "valueQuantity": {"value": float(getattr(observation, "value", 0.0))} if not components else None,
        })

    def diagnostic_report_resource(result: Any, patient_id: int | str) -> dict[str, Any]:
        return _remove_none({
            "resourceType": "DiagnosticReport",
            "id": _string_id(getattr(result, "id", "demo-report")),
            "status": getattr(result, "status", "final") or "final",
            "code": {"text": getattr(result, "title", None) or getattr(result, "code_text", "Clinical Diagnostic Report")},
            "subject": {"reference": f"Patient/{patient_id}"},
            "conclusion": getattr(result, "summary", None) or getattr(result, "conclusion", None),
            "encounter": {"reference": f"Encounter/{getattr(result, 'encounter_id', '')}"} if getattr(result, "encounter_id", None) else None,
            "issued": fhir_datetime(getattr(result, "created_at", None)),
        })

    def medication_request_resource(prescription: Any, patient_id: int | str) -> dict[str, Any]:
        items = getattr(prescription, "items", []) or []
        med_names = [getattr(it, "medication_name", "") for it in items if getattr(it, "medication_name", None)]
        med_text = "; ".join(med_names) if med_names else "Medication"

        dosage_instructions = []
        for it in items:
            med_name = getattr(it, "medication_name", "")
            dosage = getattr(it, "dosage", "")
            freq = getattr(it, "frequency", "")
            dur = getattr(it, "duration", "")
            inst = getattr(it, "instructions", "")

            desc = f"{med_name}: {dosage}"
            extra = []
            if freq:
                extra.append(freq)
            if dur:
                extra.append(dur)
            if inst:
                extra.append(inst)
            if extra:
                desc += ", " + ", ".join(extra)
            dosage_instructions.append({"text": desc})

        return _remove_none({
            "resourceType": "MedicationRequest",
            "id": _string_id(getattr(prescription, "id", "demo-med")),
            "status": getattr(prescription, "status", "active") or "active",
            "intent": "order",
            "subject": {"reference": f"Patient/{patient_id}"},
            "authoredOn": fhir_datetime(getattr(prescription, "created_at", None)),
            "medicationCodeableConcept": {"text": med_text},
            "dosageInstruction": dosage_instructions if dosage_instructions else [{"text": "No specific instructions"}],
            "encounter": {"reference": f"Encounter/{getattr(prescription, 'encounter_id', '')}"} if getattr(prescription, "encounter_id", None) else None,
        })

    def invoice_resource(invoice: Any, patient_id: int | str) -> dict[str, Any]:
        return _remove_none({
            "resourceType": "Invoice",
            "id": _string_id(getattr(invoice, "id", "demo-invoice")),
            "status": getattr(invoice, "status", "issued") or "issued",
            "subject": {"reference": f"Patient/{patient_id}"},
            "totalNet": {
                "value": float(getattr(invoice, "total_amount", 0.0)),
                "currency": getattr(invoice, "currency", "INR") or "INR",
            },
            "date": fhir_datetime(getattr(invoice, "issued_at", None)),
            "encounter": {"reference": f"Encounter/{getattr(invoice, 'encounter_id', '')}"} if getattr(invoice, "encounter_id", None) else None,
        })

    def care_event_resource(event: Any, patient_id: int | str) -> dict[str, Any]:
        return _remove_none({
            "resourceType": "CareEvent",
            "id": _string_id(getattr(event, "id", "demo-careplan")),
            "status": "recorded",
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {"text": getattr(event, "event_type", None)},
            "title": getattr(event, "title", None),
            "severity": getattr(event, "severity", None),
            "recorded": fhir_datetime(getattr(event, "created_at", None)),
        })

    def bundle_entry(resource: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(resource, dict) or not resource.get("resourceType") or not resource.get("id"):
            raise FHIRValidationError("Invalid FHIR resource")
        return {
            "fullUrl": f"urn:uuid:{resource['resourceType']}-{resource['id']}",
            "resource": resource,
        }

    def _validate_references(resource: Any, present_resources: set[str]) -> None:
        if isinstance(resource, dict):
            if "reference" in resource:
                ref = resource["reference"]
                if isinstance(ref, str) and "/" in ref:
                    ref_type, ref_id = ref.split("/", 1)
                    local_types = {"Patient", "Encounter", "Observation", "DiagnosticReport", "MedicationRequest", "Invoice", "CareEvent"}
                    if ref_type in local_types and ref not in present_resources:
                        raise FHIRValidationError(f"Unresolved FHIR reference: {ref}")
            for value in resource.values():
                _validate_references(value, present_resources)
        elif isinstance(resource, list):
            for item in resource:
                _validate_references(item, present_resources)

    def build_bundle(resources: Iterable[dict[str, Any]], timestamp: Any = None) -> dict[str, Any]:
        entries = []
        full_urls = set()
        present = set()
        for r in resources:
            if not isinstance(r, dict) or not r.get("resourceType") or not r.get("id"):
                raise FHIRValidationError("Invalid FHIR resource")
            present.add(f"{r['resourceType']}/{r['id']}")

        for r in resources:
            if r.get("resourceType") == "Observation":
                if "valueQuantity" not in r and "component" not in r:
                    raise FHIRValidationError("Observation must include a value or component")
            _validate_references(r, present)
            entry = bundle_entry(r)
            full_url = entry["fullUrl"]
            if full_url in full_urls:
                raise FHIRValidationError("Duplicate FHIR bundle entry")
            full_urls.add(full_url)
            entries.append(entry)
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": fhir_datetime(timestamp or datetime.now(timezone.utc)),
            "entry": entries,
        }

    def audit_event_resource(audit_log: Any) -> dict[str, Any]:
        return {
            "resourceType": "AuditEvent",
            "id": _string_id(getattr(audit_log, "id", "demo-audit")),
            "type": {"code": "rest"},
            "agent": [{"requestor": True}],
            "source": {"observer": {"reference": "Device/healthcare-app"}},
        }
