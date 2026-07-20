"""Focused FHIR R4-shaped serialization helpers for interoperability exports."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Iterable


class FHIRValidationError(ValueError):
    """Raised when a generated FHIR-shaped payload is not bundle-safe."""


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


def _value(entity: object, field: str, default: Any = None) -> Any:
    return getattr(entity, field, default)


def _string_id(value: Any) -> str:
    if value is None:
        raise FHIRValidationError("Invalid FHIR resource")
    return str(value)


def _json_number(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


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


def _date_string(value: date | datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def fhir_datetime(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def patient_resource(patient: object) -> dict[str, Any]:
    patient_id = _string_id(_value(patient, "id"))
    return _remove_none({
        "resourceType": "Patient",
        "id": patient_id,
        "identifier": [{"system": "ai-healthcare-system:user-id", "value": patient_id}],
        "name": [{"text": _value(patient, "full_name") or _value(patient, "username") or patient_id}],
        "gender": _value(patient, "gender"),
        "birthDate": _date_string(_value(patient, "dob")),
    })


def encounter_resource(encounter: object, patient_id: int | str) -> dict[str, Any]:
    return _remove_none({
        "resourceType": "Encounter",
        "id": _string_id(_value(encounter, "id")),
        "status": _value(encounter, "status") or "unknown",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": _value(encounter, "encounter_type") or "AMB",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {
            "start": fhir_datetime(_value(encounter, "started_at")),
            "end": fhir_datetime(_value(encounter, "ended_at")),
        },
    })


def observation_resource(observation: object, patient_id: int | str) -> dict[str, Any]:
    components = []
    for field, code, display, unit, unit_code in VITAL_COMPONENTS:
        value = _value(observation, field)
        if value is None:
            continue
        components.append({
            "code": {"coding": [{"system": LOINC_SYSTEM, "code": code, "display": display}], "text": display},
            "valueQuantity": {
                "value": _json_number(value),
                "unit": unit,
                "system": UCUM_SYSTEM,
                "code": unit_code,
            },
        })
    encounter_id = _value(observation, "encounter_id")
    return _remove_none({
        "resourceType": "Observation",
        "id": _string_id(_value(observation, "id")),
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "encounter": {"reference": f"Encounter/{encounter_id}"} if encounter_id else None,
        "effectiveDateTime": fhir_datetime(_value(observation, "observed_at")),
        "component": components,
    })


def diagnostic_report_resource(result: object, patient_id: int | str) -> dict[str, Any]:
    return _remove_none({
        "resourceType": "DiagnosticReport",
        "id": _string_id(_value(result, "id")),
        "status": _value(result, "status") or "unknown",
        "code": {"text": _value(result, "title") or _value(result, "result_type") or "Diagnostic result"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "conclusion": _value(result, "summary"),
        "issued": fhir_datetime(_value(result, "created_at")),
    })


def _medication_items(prescription: object) -> list[object]:
    items = _value(prescription, "items", []) or []
    return list(items)


def _item_name(item: object) -> str | None:
    name = _value(item, "medication_name")
    return str(name) if name else None


def _dosage_text(item: object) -> str | None:
    name = _item_name(item)
    parts = [
        _value(item, "dosage"),
        _value(item, "frequency"),
        _value(item, "duration"),
        _value(item, "instructions"),
    ]
    details = [str(part) for part in parts if part]
    if name and details:
        return f"{name}: {', '.join(details)}"
    if name:
        return name
    if details:
        return ", ".join(details)
    return None


def medication_request_resource(prescription: object, patient_id: int | str) -> dict[str, Any]:
    items = _medication_items(prescription)
    item_names = [name for item in items if (name := _item_name(item))]
    dosage_instructions = [
        {"text": text}
        for item in items
        if (text := _dosage_text(item))
    ]
    return _remove_none({
        "resourceType": "MedicationRequest",
        "id": _string_id(_value(prescription, "id")),
        "status": _value(prescription, "status") or "unknown",
        "subject": {"reference": f"Patient/{patient_id}"},
        "authoredOn": fhir_datetime(_value(prescription, "created_at")),
        "medicationCodeableConcept": {
            "text": "; ".join(item_names) if item_names else "Medication request",
        },
        "dosageInstruction": dosage_instructions,
    })


def invoice_resource(invoice: object, patient_id: int | str) -> dict[str, Any]:
    return _remove_none({
        "resourceType": "Invoice",
        "id": _string_id(_value(invoice, "id")),
        "status": _value(invoice, "status") or "unknown",
        "subject": {"reference": f"Patient/{patient_id}"},
        "totalNet": {
            "value": _json_number(_value(invoice, "total_amount")),
            "currency": _value(invoice, "currency"),
        },
        "date": fhir_datetime(_value(invoice, "issued_at")),
    })


def care_event_resource(event: object, patient_id: int | str) -> dict[str, Any]:
    return _remove_none({
        "resourceType": "CareEvent",
        "id": _string_id(_value(event, "id")),
        "status": "recorded",
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {"text": _value(event, "event_type")},
        "title": _value(event, "title"),
        "severity": _value(event, "severity"),
        "recorded": fhir_datetime(_value(event, "created_at")),
    })


def _validate_resource(resource: dict[str, Any]) -> None:
    if not isinstance(resource, dict) or not resource.get("resourceType") or not resource.get("id"):
        raise FHIRValidationError("Invalid FHIR resource")
    if resource["resourceType"] == "Observation":
        has_value = any(
            key in resource
            for key in (
                "valueQuantity",
                "valueString",
                "valueCodeableConcept",
                "valueBoolean",
                "valueInteger",
                "valueDateTime",
                "valuePeriod",
            )
        )
        if not has_value and not resource.get("component"):
            raise FHIRValidationError("Observation must include a value or component")


def _resource_key(resource: dict[str, Any]) -> tuple[str, str]:
    return resource["resourceType"], str(resource["id"])


def _parse_reference(reference: str) -> tuple[str, str] | None:
    if not reference or reference.startswith("#") or "/" not in reference:
        return None
    resource_type, resource_id = reference.split("/", 1)
    if not resource_type or not resource_id:
        return None
    return resource_type, resource_id


def _subject_reference(resource: dict[str, Any]) -> tuple[str, str] | None:
    subject = resource.get("subject")
    if not isinstance(subject, dict):
        return None
    reference = subject.get("reference")
    if not isinstance(reference, str):
        return None
    return _parse_reference(reference)


def _validate_bundle_references(entries: list[dict[str, Any]]) -> None:
    available = {_resource_key(entry["resource"]) for entry in entries}
    for entry in entries:
        reference = _subject_reference(entry["resource"])
        if reference and reference not in available:
            raise FHIRValidationError("Unresolved FHIR reference")


def bundle_entry(resource: dict[str, Any]) -> dict[str, Any]:
    _validate_resource(resource)
    return {
        "fullUrl": f"urn:uuid:{resource['resourceType']}-{resource['id']}",
        "resource": resource,
    }


def build_bundle(resources: Iterable[dict[str, Any]], timestamp: datetime | str | None = None) -> dict[str, Any]:
    entries = []
    full_urls = set()
    for resource in resources:
        entry = bundle_entry(resource)
        full_url = entry["fullUrl"]
        if full_url in full_urls:
            raise FHIRValidationError("Duplicate FHIR bundle entry")
        full_urls.add(full_url)
        entries.append(entry)
    _validate_bundle_references(entries)
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": fhir_datetime(timestamp or datetime.now(timezone.utc)),
        "entry": entries,
    }


def audit_event_resource(audit_log: object) -> dict[str, Any]:
    """Map a database audit log / security event to a FHIR R4 AuditEvent resource."""
    import json
    log_id = str(_value(audit_log, "id", "unknown"))
    action_code = _value(audit_log, "action", "EXECUTE")

    fhir_action = "E"
    if "CREATE" in action_code or "SIGNUP" in action_code or "BOOK" in action_code:
        fhir_action = "C"
    elif "READ" in action_code or "GET" in action_code or "VIEW" in action_code:
        fhir_action = "R"
    elif "UPDATE" in action_code or "EDIT" in action_code:
        fhir_action = "U"
    elif "DELETE" in action_code:
        fhir_action = "D"

    created_at = _value(audit_log, "timestamp") or _value(audit_log, "created_at") or datetime.now(timezone.utc)
    actor_id = _value(audit_log, "admin_id") or _value(audit_log, "actor_user_id")
    target_id = _value(audit_log, "target_user_id")
    details = _value(audit_log, "details")

    if isinstance(details, str):
        try:
            details = json.loads(details)
        except Exception:
            details = {"raw": details}
    elif not isinstance(details, dict):
        details = {}

    outcome = "0"
    if "BLOCKED" in action_code or "FAILED" in action_code or "DENIED" in action_code:
        outcome = "4"

    resource = {
        "resourceType": "AuditEvent",
        "id": f"audit-{log_id}",
        "type": {
            "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
            "code": action_code.lower().replace("_", "-"),
            "display": action_code
        },
        "action": fhir_action,
        "recorded": fhir_datetime(created_at),
        "outcome": outcome,
        "agent": [
            {
                "requestor": True,
                "who": {
                    "reference": f"Practitioner/{actor_id}" if actor_id else "Device/system"
                }
            }
        ],
        "source": {
            "observer": {
                "display": "AI Healthcare System Triage Portal"
            }
        }
    }

    if target_id:
        resource["entity"] = [
            {
                "what": {
                    "reference": f"Patient/{target_id}"
                }
            }
        ]

    return resource

