from unittest.mock import patch, MagicMock
import pytest
import requests
from datetime import datetime, timezone, date
from fastapi import HTTPException
import backend.fhir as fhir_module
from backend.fhir import (
    _call_fhir_patient,
    _call_fhir_encounter,
    _call_fhir_observation,
    _call_fhir_diagnostic_report,
    _call_fhir_medication_request,
    _call_fhir_invoice,
    _call_fhir_care_event,
    _call_fhir_build_bundle,
    _call_fhir_audit_event
)

class MockModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@patch("backend.fhir.requests.post")
def test_call_fhir_patient_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response

    patient = MockModel(id=1, name="John Doe")
    result = _call_fhir_patient(patient)
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_patient_failure(mock_post):
    mock_post.side_effect = requests.RequestException("Request failed")
    patient = MockModel(id=1)
    with pytest.raises(HTTPException):
        _call_fhir_patient(patient)

@patch("backend.fhir.requests.post")
def test_call_fhir_encounter_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    result = _call_fhir_encounter(MockModel(id=1), patient_id=123)
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_observation_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    result = _call_fhir_observation(MockModel(id=1), patient_id=123)
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_diagnostic_report_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    result = _call_fhir_diagnostic_report(MockModel(id=1), patient_id=123)
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_medication_request_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    result = _call_fhir_medication_request(MockModel(id=1), patient_id=123)
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_invoice_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    result = _call_fhir_invoice(MockModel(id=1), patient_id=123)
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_care_event_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    result = _call_fhir_care_event(MockModel(id=1), patient_id=123)
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_build_bundle_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    result = _call_fhir_build_bundle([{"res": 1}])
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_build_bundle_failure(mock_post):
    mock_post.side_effect = requests.RequestException("Request failed")
    with pytest.raises(HTTPException):
        _call_fhir_build_bundle([{"res": 1}])

@patch("backend.fhir.requests.post")
def test_call_fhir_audit_event_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    result = _call_fhir_audit_event(MockModel(id=1))
    assert result == {"status": "success"}

@patch("backend.fhir.requests.post")
def test_call_fhir_audit_event_failure(mock_post):
    mock_post.side_effect = requests.RequestException("Request failed")
    with pytest.raises(HTTPException):
        _call_fhir_audit_event(MockModel(id=1))

def test_patient_resource_fallback():
    patient = MockModel(id="123", full_name="Jane Doe", gender="female", dob=date(1990, 1, 1))
    res = fhir_module.patient_resource(patient)
    assert res["resourceType"] == "Patient"
    assert res["id"] == "123"
    assert res["gender"] == "female"
    assert res["birthDate"] == "1990-01-01"
    assert res["name"][0]["text"] == "Jane Doe"

def test_encounter_resource_fallback():
    encounter = MockModel(id="enc1", status="finished", encounter_type="IMP", started_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc), ended_at=datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc))
    res = fhir_module.encounter_resource(encounter, patient_id="123")
    assert res["resourceType"] == "Encounter"
    assert res["id"] == "enc1"
    assert res["status"] == "finished"
    assert res["class"]["code"] == "IMP"
    assert res["period"]["start"] == "2023-01-01T10:00:00+00:00"

def test_observation_resource_fallback():
    obs = MockModel(id="obs1", heart_rate=80.0, systolic_bp=120.0, code_text="Vitals", observed_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc))
    res = fhir_module.observation_resource(obs, patient_id="123")
    assert res["resourceType"] == "Observation"
    assert len(res["component"]) == 2

def test_diagnostic_report_resource_fallback():
    report = MockModel(id="rpt1", status="final", title="Lab Report", summary="All good", created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc))
    res = fhir_module.diagnostic_report_resource(report, patient_id="123")
    assert res["resourceType"] == "DiagnosticReport"
    assert res["id"] == "rpt1"
    assert res["status"] == "final"

def test_medication_request_resource_fallback():
    item1 = MockModel(medication_name="Aspirin", dosage="10mg", frequency="daily", duration="7 days")
    prescription = MockModel(id="rx1", status="active", items=[item1], prescribed_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc))
    res = fhir_module.medication_request_resource(prescription, patient_id="123")
    assert res["resourceType"] == "MedicationRequest"
    assert res["id"] == "rx1"
    assert "Aspirin" in res["medicationCodeableConcept"]["text"]

def test_invoice_resource_fallback():
    invoice = MockModel(id="inv1", total_amount=150.50, status="issued", created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc))
    res = fhir_module.invoice_resource(invoice, patient_id="123")
    assert res["resourceType"] == "Invoice"
    assert res["id"] == "inv1"
    assert res["totalNet"]["value"] == 150.5

def test_care_event_resource_fallback():
    event = MockModel(id="ev1", action="Checkup", status="completed", timestamp=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc))
    res = fhir_module.care_event_resource(event, patient_id="123")
    assert res["resourceType"] == "CareEvent"
    assert res["id"] == "ev1"

def test_build_bundle_fallback():
    res = fhir_module.build_bundle([{"resourceType": "Patient", "id": "1"}], timestamp=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc))
    assert res["resourceType"] == "Bundle"
    assert res["type"] == "collection"

def test_audit_event_resource_fallback():
    audit = MockModel(id="au1", action="login", outcome="success", timestamp=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc), user_id=1, ip_address="127.0.0.1")
    res = fhir_module.audit_event_resource(audit)
    assert res["resourceType"] == "AuditEvent"
    assert res["id"] == "au1"

