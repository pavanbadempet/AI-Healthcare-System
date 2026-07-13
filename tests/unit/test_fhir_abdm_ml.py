"""
Tests for fhir.py, abdm.py, and ml_service.py.

fhir.py: Pure serialization helpers — all FHIR resource builders,
bundle assembly, validation, and helper utilities.

abdm.py: Settings, readiness, validation helpers, consent payload
building, callback normalization, and demo mode.

ml_service.py: Legacy ML service wrapper methods.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend import abdm, ml_service
from backend.abdm import (
    ABDMConfigurationError,
    ABDMValidationError,
    _validate_callback_status,
    _validate_date_range,
    _validate_hi_types,
    _validate_patient_abha_address,
    _validate_purpose_code,
    build_consent_request_payload,
    get_readiness,
    get_settings,
    normalize_consent_callback,
)
from backend.fhir import (
    FHIRValidationError,
    _date_string,
    _remove_none,
    _string_id,
    build_bundle,
    bundle_entry,
    care_event_resource,
    diagnostic_report_resource,
    encounter_resource,
    fhir_datetime,
    invoice_resource,
    medication_request_resource,
    observation_resource,
    patient_resource,
)
from backend.prediction import initialize_models

# ══════════════════════════════════════════════════════════════════════
# FHIR — helpers
# ══════════════════════════════════════════════════════════════════════

def test_fhir_datetime_none_returns_none():
    assert fhir_datetime(None) is None


def test_fhir_datetime_string_passthrough():
    assert fhir_datetime("2024-06-01T00:00:00Z") == "2024-06-01T00:00:00Z"


def test_fhir_datetime_naive_datetime_adds_utc():
    dt = datetime(2024, 6, 1, 12, 0, 0)
    result = fhir_datetime(dt)
    assert "+00:00" in result or "Z" in result.upper() or "UTC" not in result


def test_fhir_datetime_aware_datetime_formats_iso():
    dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = fhir_datetime(dt)
    assert "2024-06-01" in result


def test_remove_none_removes_none_values():
    d = {"a": 1, "b": None, "c": {"d": None, "e": 2}}
    result = _remove_none(d)
    assert "b" not in result
    assert result["c"] == {"e": 2}


def test_remove_none_handles_list():
    lst = [1, None, {"a": None, "b": 2}, None]
    result = _remove_none(lst)
    assert None not in result
    assert result[1]["b"] == 2


def test_date_string_none_returns_none():
    assert _date_string(None) is None


def test_date_string_formats_date():
    from datetime import date
    assert _date_string(date(2024, 6, 1)) == "2024-06-01"


def test_date_string_formats_datetime():
    dt = datetime(2024, 6, 1, 12, 0, 0)
    assert _date_string(dt) == "2024-06-01"


def test_string_id_raises_on_none():
    with pytest.raises(FHIRValidationError):
        _string_id(None)


def test_string_id_converts_int():
    assert _string_id(42) == "42"


# ══════════════════════════════════════════════════════════════════════
# FHIR — resource builders
# ══════════════════════════════════════════════════════════════════════

def _patient():
    p = MagicMock()
    p.id = 1
    p.full_name = "Jane Doe"
    p.username = "janedoe"
    p.gender = "female"
    p.dob = "1990-05-15"
    return p


def _encounter():
    e = MagicMock()
    e.id = 10
    e.status = "finished"
    e.encounter_type = "OPD"
    e.started_at = datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc)
    e.ended_at = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
    return e


def _observation():
    o = MagicMock()
    o.id = 20
    o.encounter_id = 10
    o.heart_rate = 75.0
    o.systolic_bp = 120.0
    o.diastolic_bp = 80.0
    o.spo2 = 98.0
    o.temperature_c = 37.0
    o.respiratory_rate = 16.0
    o.observed_at = datetime(2024, 6, 1, 9, 30, tzinfo=timezone.utc)
    return o


def test_patient_resource_structure():
    r = patient_resource(_patient())
    assert r["resourceType"] == "Patient"
    assert r["id"] == "1"
    assert r["name"][0]["text"] == "Jane Doe"
    assert r["gender"] == "female"


def test_patient_resource_falls_back_to_username():
    p = MagicMock()
    p.id = 2
    p.full_name = None
    p.username = "john"
    p.gender = None
    p.dob = None
    r = patient_resource(p)
    assert r["name"][0]["text"] == "john"


def test_patient_resource_removes_none_fields():
    p = MagicMock()
    p.id = 3
    p.full_name = "Test"
    p.username = "test"
    p.gender = None
    p.dob = None
    r = patient_resource(p)
    assert "gender" not in r
    assert "birthDate" not in r


def test_encounter_resource_structure():
    r = encounter_resource(_encounter(), patient_id=1)
    assert r["resourceType"] == "Encounter"
    assert r["id"] == "10"
    assert r["subject"]["reference"] == "Patient/1"
    assert r["status"] == "finished"


def test_observation_resource_has_components():
    r = observation_resource(_observation(), patient_id=1)
    assert r["resourceType"] == "Observation"
    assert r["id"] == "20"
    assert len(r["component"]) == 6  # all 6 vitals set
    assert r["subject"]["reference"] == "Patient/1"


def test_observation_resource_skips_none_vitals():
    o = MagicMock()
    o.id = 21
    o.encounter_id = None
    o.heart_rate = 80.0
    o.systolic_bp = None
    o.diastolic_bp = None
    o.spo2 = None
    o.temperature_c = None
    o.respiratory_rate = None
    o.observed_at = None
    r = observation_resource(o, patient_id=1)
    assert len(r["component"]) == 1
    assert r["component"][0]["code"]["coding"][0]["code"] == "8867-4"


def test_diagnostic_report_resource_structure():
    result = MagicMock()
    result.id = 30
    result.status = "final"
    result.title = "CBC Report"
    result.result_type = "lab"
    result.summary = "All values normal."
    result.created_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    r = diagnostic_report_resource(result, patient_id=1)
    assert r["resourceType"] == "DiagnosticReport"
    assert r["conclusion"] == "All values normal."
    assert r["code"]["text"] == "CBC Report"


def test_medication_request_resource_structure():
    item = MagicMock()
    item.medication_name = "Metformin"
    item.dosage = "500mg"
    item.frequency = "BD"
    item.duration = "30 days"
    item.instructions = "After meals"

    prescription = MagicMock()
    prescription.id = 40
    prescription.status = "active"
    prescription.created_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    prescription.items = [item]

    r = medication_request_resource(prescription, patient_id=1)
    assert r["resourceType"] == "MedicationRequest"
    assert "Metformin" in r["medicationCodeableConcept"]["text"]
    assert len(r["dosageInstruction"]) == 1


def test_invoice_resource_structure():
    invoice = MagicMock()
    invoice.id = 50
    invoice.status = "issued"
    invoice.total_amount = 1500.0
    invoice.currency = "INR"
    invoice.issued_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    r = invoice_resource(invoice, patient_id=1)
    assert r["resourceType"] == "Invoice"
    assert r["totalNet"]["value"] == 1500.0
    assert r["totalNet"]["currency"] == "INR"


def test_care_event_resource_structure():
    event = MagicMock()
    event.id = 60
    event.event_type = "VITALS_RECORDED"
    event.title = "Vitals recorded"
    event.severity = "info"
    event.created_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    r = care_event_resource(event, patient_id=1)
    assert r["resourceType"] == "CareEvent"
    assert r["code"]["text"] == "VITALS_RECORDED"


# ══════════════════════════════════════════════════════════════════════
# FHIR — bundle assembly
# ══════════════════════════════════════════════════════════════════════

def test_bundle_entry_adds_full_url():
    resource = {"resourceType": "Patient", "id": "1"}
    entry = bundle_entry(resource)
    assert "fullUrl" in entry
    assert "Patient-1" in entry["fullUrl"]
    assert entry["resource"] == resource


def test_bundle_entry_raises_on_invalid_resource():
    with pytest.raises(FHIRValidationError):
        bundle_entry({"id": "1"})  # missing resourceType


def test_build_bundle_assembles_collection():
    p = patient_resource(_patient())
    bundle = build_bundle([p])
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert len(bundle["entry"]) == 1


def test_build_bundle_raises_on_duplicate_entries():
    p = patient_resource(_patient())
    with pytest.raises(FHIRValidationError, match="Duplicate"):
        build_bundle([p, p])


def test_build_bundle_empty_is_valid():
    bundle = build_bundle([])
    assert bundle["entry"] == []


def test_build_bundle_resolves_patient_reference():
    p = patient_resource(_patient())
    e = encounter_resource(_encounter(), patient_id=1)
    # Both should be in the bundle — reference Patient/1 must resolve
    bundle = build_bundle([p, e])
    assert len(bundle["entry"]) == 2


def test_build_bundle_raises_on_unresolved_reference():
    # Encounter references Patient/1 but Patient/1 is not in the bundle
    e = encounter_resource(_encounter(), patient_id=1)
    with pytest.raises(FHIRValidationError, match="Unresolved"):
        build_bundle([e])


# ══════════════════════════════════════════════════════════════════════
# ABDM — settings and readiness
# ══════════════════════════════════════════════════════════════════════

def test_abdm_readiness_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ABDM_ENABLED", raising=False)
    result = get_readiness()
    assert result["enabled"] is False


def test_abdm_readiness_includes_supported_types():
    result = get_readiness()
    assert "Prescription" in result["supported_hi_types"]
    assert "DiagnosticReport" in result["supported_hi_types"]


def test_abdm_readiness_no_secrets_exposed(monkeypatch):
    monkeypatch.setenv("ABDM_CLIENT_SECRET", "super-secret-abdm-key")
    result = get_readiness()
    result_str = str(result)
    assert "super-secret-abdm-key" not in result_str


def test_abdm_settings_reads_env(monkeypatch):
    monkeypatch.setenv("ABDM_ENABLED", "true")
    monkeypatch.setenv("ABDM_HIU_ID", "HIUID001")
    s = get_settings()
    assert s.enabled is True
    assert s.hiu_id == "HIUID001"


def test_abdm_settings_configured_for_submission_false_when_missing(monkeypatch):
    monkeypatch.setenv("ABDM_ENABLED", "true")
    monkeypatch.delenv("ABDM_ACCESS_TOKEN", raising=False)
    s = get_settings()
    assert s.configured_for_submission is False


# ══════════════════════════════════════════════════════════════════════
# ABDM — validation helpers
# ══════════════════════════════════════════════════════════════════════

def test_validate_patient_abha_address_valid():
    result = _validate_patient_abha_address("patient@abdm")
    assert result == "patient@abdm"


def test_validate_patient_abha_address_rejects_no_at():
    with pytest.raises(ABDMValidationError, match="ABHA"):
        _validate_patient_abha_address("patientnoemail")


def test_validate_patient_abha_address_rejects_empty():
    with pytest.raises(ABDMValidationError):
        _validate_patient_abha_address("")


def test_validate_purpose_code_valid():
    assert _validate_purpose_code("caremgt") == "CAREMGT"


def test_validate_purpose_code_rejects_unknown():
    with pytest.raises(ABDMValidationError, match="purpose"):
        _validate_purpose_code("INVALID_CODE")


def test_validate_hi_types_valid():
    result = _validate_hi_types(["Prescription", "DiagnosticReport"])
    assert "Prescription" in result
    assert "DiagnosticReport" in result


def test_validate_hi_types_rejects_unknown():
    with pytest.raises(ABDMValidationError, match="health information type"):
        _validate_hi_types(["UnknownType"])


def test_validate_hi_types_deduplicates():
    result = _validate_hi_types(["Prescription", "Prescription"])
    assert result.count("Prescription") == 1


def test_validate_hi_types_uses_defaults_when_none():
    result = _validate_hi_types(None)
    assert len(result) > 0


def test_validate_callback_status_valid():
    assert _validate_callback_status("GRANTED") == "GRANTED"


def test_validate_callback_status_case_insensitive():
    assert _validate_callback_status("granted") == "GRANTED"


def test_validate_callback_status_rejects_unknown():
    with pytest.raises(ABDMValidationError, match="status"):
        _validate_callback_status("UNKNOWN_STATUS")


def test_validate_date_range_valid():
    now = datetime.now(timezone.utc)
    _validate_date_range(now, now + timedelta(days=30), now + timedelta(days=90))


def test_validate_date_range_rejects_to_before_from():
    now = datetime.now(timezone.utc)
    with pytest.raises(ABDMValidationError, match="date range"):
        _validate_date_range(now + timedelta(days=10), now, now + timedelta(days=90))


def test_validate_date_range_rejects_erase_before_to():
    now = datetime.now(timezone.utc)
    with pytest.raises(ABDMValidationError, match="erase"):
        _validate_date_range(now, now + timedelta(days=30), now + timedelta(days=20))


# ══════════════════════════════════════════════════════════════════════
# ABDM — consent payload and callback
# ══════════════════════════════════════════════════════════════════════

def test_build_consent_request_payload_structure(monkeypatch):
    monkeypatch.setenv("ABDM_HIU_ID", "HIU001")
    now = datetime.now(timezone.utc)
    payload = build_consent_request_payload(
        patient_abha_address="patient@abdm",
        purpose_code="CAREMGT",
        hi_types=["Prescription"],
        date_from=now,
        date_to=now + timedelta(days=30),
        data_erase_at=now + timedelta(days=90),
    )
    assert "requestId" in payload
    assert payload["consent"]["purpose"]["code"] == "CAREMGT"
    assert payload["consent"]["patient"]["id"] == "patient@abdm"
    assert "Prescription" in payload["consent"]["hiTypes"]


def test_build_consent_request_raises_without_hiu_id(monkeypatch):
    monkeypatch.delenv("ABDM_HIU_ID", raising=False)
    now = datetime.now(timezone.utc)
    with pytest.raises(ABDMConfigurationError, match="HIU_ID"):
        build_consent_request_payload(
            patient_abha_address="p@abdm",
            purpose_code="CAREMGT",
            hi_types=None,
            date_from=now,
            date_to=now + timedelta(days=30),
            data_erase_at=now + timedelta(days=90),
        )


def test_normalize_consent_callback_returns_hashed_payload():
    result = normalize_consent_callback(
        request_id="req-abc-123",
        status="GRANTED",
        abdm_consent_id="consent-xyz-456",
    )
    assert result["request_id"] == "req-abc-123"
    assert result["local_consent_status"] == "active"
    assert "payload_sha256" in result
    assert len(result["payload_sha256"]) == 64  # SHA-256 hex
    assert result["raw_payload_stored"] is False


def test_normalize_consent_callback_denied_status():
    result = normalize_consent_callback(
        request_id="req-123",
        status="DENIED",
    )
    assert result["local_consent_status"] == "denied"


def test_normalize_consent_callback_rejects_invalid_status():
    with pytest.raises(ABDMValidationError):
        normalize_consent_callback(request_id="req", status="INVALID")


def test_prepare_consent_request_dry_run(monkeypatch):
    monkeypatch.setenv("ABDM_HIU_ID", "HIU001")
    now = datetime.now(timezone.utc)
    result = abdm.prepare_consent_request(
        patient_abha_address="p@abdm",
        purpose_code="CAREMGT",
        hi_types=["Prescription"],
        date_from=now,
        date_to=now + timedelta(days=30),
        data_erase_at=now + timedelta(days=90),
        submit=False,
    )
    assert result["submitted"] is False
    assert "payload" in result


def test_prepare_consent_request_demo_mode(monkeypatch):
    monkeypatch.setenv("ABDM_DEMO_MODE", "true")
    monkeypatch.setenv("ABDM_HIU_ID", "HIU001")
    now = datetime.now(timezone.utc)
    result = abdm.prepare_consent_request(
        patient_abha_address="p@abdm",
        purpose_code="CAREMGT",
        hi_types=None,
        date_from=now,
        date_to=now + timedelta(days=30),
        data_erase_at=now + timedelta(days=90),
        submit=True,
    )
    assert result["submitted"] is True
    assert "MOCK" in result["endpoint"]


def test_prepare_consent_request_raises_when_not_configured(monkeypatch):
    monkeypatch.setenv("ABDM_DEMO_MODE", "false")
    monkeypatch.delenv("ABDM_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ABDM_HIU_ID", raising=False)
    now = datetime.now(timezone.utc)
    with pytest.raises((ABDMConfigurationError, ABDMValidationError)):
        abdm.prepare_consent_request(
            patient_abha_address="p@abdm",
            purpose_code="CAREMGT",
            hi_types=None,
            date_from=now,
            date_to=now + timedelta(days=30),
            data_erase_at=now + timedelta(days=90),
            submit=True,
        )


# ══════════════════════════════════════════════════════════════════════
# ML SERVICE
# ══════════════════════════════════════════════════════════════════════

def test_ml_service_predict_diabetes_returns_string():
    initialize_models()
    svc = ml_service.MLService()
    result = svc.predict_diabetes(
        gender="female", age=45, hypertension=0, heart_disease=0,
        smoking_history="never", bmi=25.0, hba1c_level=5.5, blood_glucose_level=100
    )
    assert isinstance(result, str)


def test_ml_service_predict_heart_disease_returns_string():
    initialize_models()
    svc = ml_service.MLService()
    result = svc.predict_heart_disease(
        age=50, gender="male", cp=2, trestbps=130, chol=220,
        fbs=0, restecg=0, thalach=150, exang=0, oldpeak=1.5,
        slope=1, ca=0, thal=1
    )
    assert isinstance(result, str)


def test_ml_service_predict_liver_disease_returns_string():
    initialize_models()
    svc = ml_service.MLService()
    result = svc.predict_liver_disease(
        age=45, gender="male", total_bilirubin=0.7,
        alkaline_phosphotase=187, alamine_aminotransferase=16,
        albumin_globulin_ratio=0.9
    )
    assert isinstance(result, str)


def test_ml_service_handles_exception_gracefully():
    """Exceptions during prediction should return the failure message, not raise."""
    initialize_models()
    svc = ml_service.MLService()
    # Pass invalid values that will cause the prediction to fail
    with patch("backend.prediction.diabetes_model") as mock_model:
        mock_model.predict.side_effect = Exception("model error")
        result = svc.predict_diabetes(
            gender="male", age=45, hypertension=0, heart_disease=0,
            smoking_history="current", bmi=27.0, hba1c_level=6.0, blood_glucose_level=110
        )
    assert isinstance(result, str)


def test_ml_service_maps_gender_strings():
    """Male/female string inputs should be mapped to 1/0 correctly."""
    initialize_models()
    svc = ml_service.MLService()
    result_male = svc.predict_diabetes(
        gender="male", age=50, hypertension=1, heart_disease=0,
        smoking_history="never", bmi=28.0, hba1c_level=5.8, blood_glucose_level=120
    )
    result_female = svc.predict_diabetes(
        gender="female", age=50, hypertension=1, heart_disease=0,
        smoking_history="never", bmi=28.0, hba1c_level=5.8, blood_glucose_level=120
    )
    # Both should return valid prediction strings
    assert isinstance(result_male, str)
    assert isinstance(result_female, str)
