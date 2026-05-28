from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest


def _fhir_module():
    try:
        from backend import fhir
    except ImportError:
        pytest.fail("backend.fhir module is required for FHIR export serialization")
    return fhir


def test_patient_resource_uses_internal_identifier_without_contact_fields():
    fhir = _fhir_module()
    patient = SimpleNamespace(
        id=42,
        full_name="Synthetic Patient",
        username="synthetic_patient",
        email="synthetic@example.com",
        gender="female",
        dob=date(1991, 2, 3),
    )

    resource = fhir.patient_resource(patient)

    assert resource["resourceType"] == "Patient"
    assert resource["id"] == "42"
    assert resource["identifier"] == [{"system": "ai-healthcare-system:user-id", "value": "42"}]
    assert resource["name"] == [{"text": "Synthetic Patient"}]
    assert resource["gender"] == "female"
    assert resource["birthDate"] == "1991-02-03"
    assert "telecom" not in resource


def test_observation_resource_uses_coded_components_and_skips_empty_values():
    fhir = _fhir_module()
    observation = SimpleNamespace(
        id=100,
        patient_id=42,
        encounter_id=7,
        observed_at=datetime(2026, 5, 27, 8, 30, tzinfo=timezone.utc),
        heart_rate=72,
        systolic_bp=None,
        diastolic_bp=None,
        spo2=98,
        temperature_c=None,
        respiratory_rate=None,
    )

    resource = fhir.observation_resource(observation, patient_id=42)

    assert resource["resourceType"] == "Observation"
    assert resource["id"] == "100"
    assert resource["status"] == "final"
    assert resource["subject"] == {"reference": "Patient/42"}
    assert resource["encounter"] == {"reference": "Encounter/7"}
    assert resource["effectiveDateTime"] == "2026-05-27T08:30:00+00:00"
    components = resource["component"]
    assert [component["code"]["coding"][0]["code"] for component in components] == ["8867-4", "59408-5"]
    assert components[0]["valueQuantity"] == {
        "value": 72,
        "unit": "beats/minute",
        "system": "http://unitsofmeasure.org",
        "code": "/min",
    }
    assert components[1]["valueQuantity"] == {
        "value": 98,
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%",
    }


def test_medication_request_resource_includes_prescribed_items():
    fhir = _fhir_module()
    prescription = SimpleNamespace(
        id=12,
        patient_id=42,
        status="active",
        created_at=datetime(2026, 5, 27, 10, 0, tzinfo=timezone.utc),
        items=[
            SimpleNamespace(
                medication_name="Synthetic Medication A",
                dosage="5 mg",
                frequency="daily",
                duration="5 days",
                instructions="After food",
            ),
            SimpleNamespace(
                medication_name="Synthetic Medication B",
                dosage="10 mg",
                frequency="twice daily",
                duration=None,
                instructions=None,
            ),
        ],
    )

    resource = fhir.medication_request_resource(prescription, patient_id=42)

    assert resource["resourceType"] == "MedicationRequest"
    assert resource["id"] == "12"
    assert resource["status"] == "active"
    assert resource["subject"] == {"reference": "Patient/42"}
    assert resource["authoredOn"] == "2026-05-27T10:00:00+00:00"
    assert resource["medicationCodeableConcept"]["text"] == (
        "Synthetic Medication A; Synthetic Medication B"
    )
    assert resource["dosageInstruction"][0]["text"] == "Synthetic Medication A: 5 mg, daily, 5 days, After food"
    assert resource["dosageInstruction"][1]["text"] == "Synthetic Medication B: 10 mg, twice daily"


def test_build_bundle_rejects_resource_without_resource_type():
    fhir = _fhir_module()

    with pytest.raises(fhir.FHIRValidationError, match="Invalid FHIR resource"):
        fhir.build_bundle([{"id": "1"}])


def test_build_bundle_rejects_duplicate_full_urls():
    fhir = _fhir_module()
    resource = {"resourceType": "Patient", "id": "42"}

    with pytest.raises(fhir.FHIRValidationError, match="Duplicate FHIR bundle entry"):
        fhir.build_bundle([resource, resource])


def test_build_bundle_rejects_observation_without_values():
    fhir = _fhir_module()

    with pytest.raises(fhir.FHIRValidationError, match="Observation must include a value or component"):
        fhir.build_bundle([
            {"resourceType": "Patient", "id": "42"},
            {"resourceType": "Observation", "id": "100", "subject": {"reference": "Patient/42"}},
        ])


def test_build_bundle_rejects_unresolved_subject_reference():
    fhir = _fhir_module()

    with pytest.raises(fhir.FHIRValidationError, match="Unresolved FHIR reference"):
        fhir.build_bundle([
            {"resourceType": "Patient", "id": "42"},
            {
                "resourceType": "DiagnosticReport",
                "id": "200",
                "subject": {"reference": "Patient/999"},
                "status": "final",
                "code": {"text": "Synthetic report"},
            },
        ])


def test_bundle_entry_shape_is_stable():
    fhir = _fhir_module()
    resource = {"resourceType": "Patient", "id": "42"}

    assert fhir.bundle_entry(resource) == {
        "fullUrl": "urn:uuid:Patient-42",
        "resource": resource,
    }
