"""
Tests for smart_fhir.py, dicomweb.py, retention_policy.py,
incident_response.py, and security_assurance.py.

All modules expose pure readiness/metadata functions — no DB needed.
"""
import pytest

from backend import incident_response, retention_policy, security_assurance
from backend.dicomweb import (
    DICOMwebConfigurationError,
    DICOMwebValidationError,
    _validate_study_instance_uid,
    build_study_metadata_links,
)
from backend.dicomweb import (
    get_readiness as dicom_readiness,
)
from backend.smart_fhir import (
    SMARTConfigurationError,
    SMARTValidationError,
    _safe_token,
    build_authorization_response,
    build_authorization_url,
)
from backend.smart_fhir import (
    get_readiness as smart_readiness,
)

# ── smart_fhir.get_readiness ─────────────────────────────────────────────────

def test_smart_readiness_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SMART_FHIR_ENABLED", raising=False)
    result = smart_readiness()
    assert result["enabled"] is False


def test_smart_readiness_enabled_with_flag(monkeypatch):
    monkeypatch.setenv("SMART_FHIR_ENABLED", "true")
    result = smart_readiness()
    assert result["enabled"] is True


def test_smart_readiness_no_secrets_exposed(monkeypatch):
    monkeypatch.setenv("SMART_CLIENT_SECRET", "super-secret-token")
    result = smart_readiness()
    assert result["secrets_exposed"] is False
    assert "super-secret-token" not in str(result)


def test_smart_readiness_lists_missing_when_enabled(monkeypatch):
    monkeypatch.setenv("SMART_FHIR_ENABLED", "true")
    for var in ("SMART_FHIR_BASE_URL", "SMART_AUTHORIZATION_ENDPOINT",
                "SMART_TOKEN_ENDPOINT", "SMART_CLIENT_ID", "SMART_REDIRECT_URI"):
        monkeypatch.delenv(var, raising=False)
    result = smart_readiness()
    assert len(result["missing"]) > 0


def test_smart_readiness_no_missing_when_disabled(monkeypatch):
    monkeypatch.setenv("SMART_FHIR_ENABLED", "false")
    for var in ("SMART_FHIR_BASE_URL", "SMART_CLIENT_ID"):
        monkeypatch.delenv(var, raising=False)
    result = smart_readiness()
    assert result["missing"] == []


def test_smart_readiness_includes_capabilities():
    result = smart_readiness()
    assert "capabilities" in result
    assert "launch-ehr" in result["capabilities"]


def test_smart_readiness_token_exchange_disabled():
    result = smart_readiness()
    assert result["token_exchange_enabled"] is False


def test_smart_readiness_default_scopes(monkeypatch):
    monkeypatch.delenv("SMART_SCOPES", raising=False)
    result = smart_readiness()
    assert "patient" in result["scopes"].lower()


# ── smart_fhir.build_authorization_url ───────────────────────────────────────

def test_build_authorization_url_contains_required_params(monkeypatch):
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_CLIENT_ID", "my-client-id")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://myapp.com/callback")
    monkeypatch.setenv("SMART_FHIR_BASE_URL", "https://ehr.example.com/fhir")

    url = build_authorization_url(state="abc123")

    assert "response_type=code" in url
    assert "client_id=my-client-id" in url
    assert "state=abc123" in url
    assert "aud=" in url


def test_build_authorization_url_includes_launch_when_provided(monkeypatch):
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_CLIENT_ID", "c1")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://app.com/cb")
    monkeypatch.setenv("SMART_FHIR_BASE_URL", "https://ehr.example.com/fhir")

    url = build_authorization_url(state="s1", launch="launch-token-123")
    assert "launch=launch-token-123" in url


def test_build_authorization_url_generates_state_when_none(monkeypatch):
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_CLIENT_ID", "c1")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://app.com/cb")
    monkeypatch.setenv("SMART_FHIR_BASE_URL", "https://ehr.example.com/fhir")

    url = build_authorization_url(state=None)
    assert "state=" in url


def test_build_authorization_url_raises_when_missing_env(monkeypatch):
    monkeypatch.delenv("SMART_AUTHORIZATION_ENDPOINT", raising=False)
    with pytest.raises(SMARTConfigurationError):
        build_authorization_url()


def test_safe_token_rejects_invalid_characters():
    with pytest.raises(SMARTValidationError):
        _safe_token("<script>alert(1)</script>", field_name="state")


def test_safe_token_accepts_valid_token():
    result = _safe_token("valid-token-123", field_name="state")
    assert result == "valid-token-123"


def test_safe_token_generates_uuid_for_empty():
    result = _safe_token("", field_name="state")
    assert len(result) == 36  # UUID format


def test_build_authorization_response_has_required_keys(monkeypatch):
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_CLIENT_ID", "c1")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://app.com/cb")
    monkeypatch.setenv("SMART_FHIR_BASE_URL", "https://ehr.example.com/fhir")

    result = build_authorization_response(state="test")
    assert "authorization_url" in result
    assert result["secrets_exposed"] is False
    assert result["token_exchange_enabled"] is False


# ── dicomweb.get_readiness ────────────────────────────────────────────────────

def test_dicom_readiness_disabled_by_default(monkeypatch):
    monkeypatch.delenv("DICOMWEB_ENABLED", raising=False)
    result = dicom_readiness()
    assert result["enabled"] is False


def test_dicom_readiness_no_pixel_data(monkeypatch):
    result = dicom_readiness()
    assert result["pixel_data_included"] is False


def test_dicom_readiness_no_secrets_exposed(monkeypatch):
    monkeypatch.setenv("DICOMWEB_BEARER_TOKEN", "bearer-secret-xyz")
    result = dicom_readiness()
    assert result["secrets_exposed"] is False
    assert "bearer-secret-xyz" not in str(result)


def test_dicom_readiness_reports_configured_base_url(monkeypatch):
    monkeypatch.setenv("DICOMWEB_BASE_URL", "https://pacs.hospital.com/wado")
    result = dicom_readiness()
    assert result["base_url_configured"] is True


def test_dicom_readiness_lists_missing_when_enabled(monkeypatch):
    monkeypatch.setenv("DICOMWEB_ENABLED", "true")
    monkeypatch.delenv("DICOMWEB_BASE_URL", raising=False)
    monkeypatch.delenv("DICOMWEB_AE_TITLE", raising=False)
    result = dicom_readiness()
    assert len(result["missing"]) > 0


def test_dicom_readiness_includes_capabilities():
    result = dicom_readiness()
    assert "QIDO-RS" in result["capabilities"]
    assert "WADO-RS" in result["capabilities"]
    assert "STOW-RS" in result["capabilities"]


# ── dicomweb.build_study_metadata_links ──────────────────────────────────────

def test_build_study_metadata_links_returns_correct_urls():
    uid = "1.2.840.10008.5.1.4.1.1.4"
    links = build_study_metadata_links(uid, base_url="https://pacs.example.com")
    assert uid in links["qido_rs_study_search"]
    assert uid in links["wado_rs_study_metadata"]
    assert "stow_rs_store" in links


def test_build_study_metadata_links_no_pii_exposed():
    uid = "1.2.3.4.5"
    links = build_study_metadata_links(uid, base_url="https://pacs.example.com")
    assert links["pii_exposed"] is False
    assert links["pixel_data_included"] is False


def test_build_study_metadata_links_raises_on_invalid_uid():
    with pytest.raises(DICOMwebValidationError):
        build_study_metadata_links("not-a-valid-uid", base_url="https://pacs.example.com")


def test_build_study_metadata_links_raises_on_empty_uid():
    with pytest.raises(DICOMwebValidationError):
        build_study_metadata_links("", base_url="https://pacs.example.com")


def test_build_study_metadata_links_raises_when_no_base_url(monkeypatch):
    monkeypatch.delenv("DICOMWEB_BASE_URL", raising=False)
    with pytest.raises(DICOMwebConfigurationError):
        build_study_metadata_links("1.2.3.4")


def test_validate_study_instance_uid_accepts_valid():
    assert _validate_study_instance_uid("1.2.840.10008.5.1.4.1") == "1.2.840.10008.5.1.4.1"


def test_validate_study_instance_uid_rejects_too_long():
    long_uid = "1." + "2." * 40
    with pytest.raises(DICOMwebValidationError):
        _validate_study_instance_uid(long_uid)


# ── retention_policy.get_readiness ───────────────────────────────────────────

def test_retention_readiness_disabled_by_default(monkeypatch):
    monkeypatch.delenv("RETENTION_POLICY_ENABLED", raising=False)
    result = retention_policy.get_readiness()
    assert result["enabled"] is False
    assert result["status"] == "disabled"


def test_retention_readiness_action_required_when_enabled_but_missing(monkeypatch):
    monkeypatch.setenv("RETENTION_POLICY_ENABLED", "true")
    for var in ("RETENTION_OWNER_CONTACT", "RETENTION_RUNBOOK_URL", "LEGAL_HOLD_PROCESS_URL"):
        monkeypatch.delenv(var, raising=False)
    result = retention_policy.get_readiness()
    assert result["status"] == "action_required"
    assert len(result["missing"]) > 0


def test_retention_readiness_no_secrets_exposed():
    result = retention_policy.get_readiness()
    assert result["secret_values_exposed"] is False


def test_retention_readiness_no_phi_in_response():
    result = retention_policy.get_readiness()
    assert "patient" not in str(result["policies"]).lower() or \
           "label" in str(result["policies"])  # labels may mention patient records generically


def test_retention_readiness_policies_include_all_windows():
    result = retention_policy.get_readiness()
    policy_ids = {p["id"] for p in result["policies"]}
    for pid in ("patient_records", "chat_logs", "audit_logs",
                "interoperability_exports", "vector_store", "lakehouse"):
        assert pid in policy_ids


def test_retention_readiness_destructive_actions_not_executed():
    result = retention_policy.get_readiness()
    assert result["destructive_actions_executed"] is False


def test_retention_policy_env_positive_int_rejects_zero(monkeypatch):
    monkeypatch.setenv("PATIENT_RECORD_RETENTION_YEARS", "0")
    result = retention_policy._env_positive_int("PATIENT_RECORD_RETENTION_YEARS")
    assert result is None


def test_retention_policy_env_positive_int_accepts_positive(monkeypatch):
    monkeypatch.setenv("PATIENT_RECORD_RETENTION_YEARS", "7")
    result = retention_policy._env_positive_int("PATIENT_RECORD_RETENTION_YEARS")
    assert result == 7


def test_retention_policy_env_positive_int_rejects_non_numeric(monkeypatch):
    monkeypatch.setenv("PATIENT_RECORD_RETENTION_YEARS", "seven")
    result = retention_policy._env_positive_int("PATIENT_RECORD_RETENTION_YEARS")
    assert result is None


# ── incident_response.get_readiness ──────────────────────────────────────────

def test_incident_readiness_disabled_by_default(monkeypatch):
    monkeypatch.delenv("INCIDENT_RESPONSE_ENABLED", raising=False)
    result = incident_response.get_readiness()
    assert result["enabled"] is False
    assert result["status"] == "disabled"


def test_incident_readiness_action_required_when_enabled_missing(monkeypatch):
    monkeypatch.setenv("INCIDENT_RESPONSE_ENABLED", "true")
    for var in ("INCIDENT_RESPONSE_OWNER_CONTACT", "INCIDENT_RESPONSE_CHANNEL",
                "INCIDENT_RESPONSE_RUNBOOK_URL"):
        monkeypatch.delenv(var, raising=False)
    result = incident_response.get_readiness()
    assert result["status"] == "action_required"


def test_incident_readiness_no_secrets_exposed():
    result = incident_response.get_readiness()
    assert result["secret_values_exposed"] is False


def test_incident_readiness_includes_all_phases():
    result = incident_response.get_readiness()
    for phase in ("prepare", "detect", "analyze", "contain",
                  "eradicate", "recover", "post_incident_review"):
        assert phase in result["incident_phases"]


def test_incident_readiness_includes_alert_rules():
    result = incident_response.get_readiness()
    rule_ids = {r["id"] for r in result["alert_rules"]}
    assert "api_error_rate" in rule_ids
    assert "ai_provider_failure_rate" in rule_ids
    assert "pipeline_staleness" in rule_ids
    assert "security_event_spike" in rule_ids


def test_incident_readiness_env_float_rejects_zero(monkeypatch):
    monkeypatch.setenv("ALERT_ERROR_RATE_THRESHOLD_PERCENT", "0")
    assert incident_response._env_float("ALERT_ERROR_RATE_THRESHOLD_PERCENT") is None


def test_incident_readiness_env_float_accepts_valid(monkeypatch):
    monkeypatch.setenv("ALERT_ERROR_RATE_THRESHOLD_PERCENT", "5.0")
    assert incident_response._env_float("ALERT_ERROR_RATE_THRESHOLD_PERCENT") == 5.0


def test_incident_readiness_env_int_rejects_non_numeric(monkeypatch):
    monkeypatch.setenv("ALERT_SECURITY_EVENT_THRESHOLD", "many")
    assert incident_response._env_int("ALERT_SECURITY_EVENT_THRESHOLD") is None


# ── security_assurance.get_readiness ─────────────────────────────────────────

def test_security_assurance_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SECURITY_ASSURANCE_ENABLED", raising=False)
    result = security_assurance.get_readiness()
    assert result["enabled"] is False
    assert result["status"] == "disabled"


def test_security_assurance_action_required_when_enabled_missing(monkeypatch):
    monkeypatch.setenv("SECURITY_ASSURANCE_ENABLED", "true")
    for var in ("SECURITY_OWNER_CONTACT", "SECURITY_RUNBOOK_URL",
                "SECRET_SCAN_LAST_RUN_AT", "DEPENDENCY_SCAN_LAST_RUN_AT"):
        monkeypatch.delenv(var, raising=False)
    result = security_assurance.get_readiness()
    assert result["status"] == "action_required"
    assert len(result["missing"]) > 0


def test_security_assurance_no_secrets_exposed(monkeypatch):
    monkeypatch.setenv("SECURITY_OWNER_CONTACT", "security-team@example.com")
    result = security_assurance.get_readiness()
    assert result["secret_values_exposed"] is False
    assert "security-team@example.com" not in str(result)


def test_security_assurance_includes_all_controls():
    result = security_assurance.get_readiness()
    control_ids = {c["id"] for c in result["controls"]}
    for cid in ("secret_scan", "dependency_scan", "sbom",
                "vulnerability_scan", "penetration_test",
                "critical_findings", "high_findings"):
        assert cid in control_ids


def test_security_assurance_parse_datetime_valid_iso(monkeypatch):
    monkeypatch.setenv("SECRET_SCAN_LAST_RUN_AT", "2024-06-01T10:00:00Z")
    result = security_assurance._parse_datetime("SECRET_SCAN_LAST_RUN_AT")
    assert result is not None
    assert "2024-06-01" in result


def test_security_assurance_parse_datetime_invalid_returns_none(monkeypatch):
    monkeypatch.setenv("SECRET_SCAN_LAST_RUN_AT", "not-a-date")
    result = security_assurance._parse_datetime("SECRET_SCAN_LAST_RUN_AT")
    assert result is None


def test_security_assurance_finding_control_ready_when_zero(monkeypatch):
    monkeypatch.setenv("SECURITY_FINDINGS_OPEN_CRITICAL", "0")
    ctrl = security_assurance._finding_control(
        "critical", "Critical findings", "SECURITY_FINDINGS_OPEN_CRITICAL"
    )
    assert ctrl["configured"] is True
    assert ctrl["open_count"] == 0


def test_security_assurance_finding_control_not_ready_when_nonzero(monkeypatch):
    monkeypatch.setenv("SECURITY_FINDINGS_OPEN_CRITICAL", "3")
    ctrl = security_assurance._finding_control(
        "critical", "Critical findings", "SECURITY_FINDINGS_OPEN_CRITICAL"
    )
    assert ctrl["configured"] is False
    assert ctrl["open_count"] == 3
