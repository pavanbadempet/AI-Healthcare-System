from urllib.parse import parse_qs, urlparse

import pytest

from backend import smart_fhir


def test_smart_readiness_reports_oauth_metadata_without_secrets(monkeypatch):
    monkeypatch.setenv("SMART_FHIR_ENABLED", "true")
    monkeypatch.setenv("SMART_FHIR_BASE_URL", "https://ehr.example.com/fhir")
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_TOKEN_ENDPOINT", "https://ehr.example.com/token")
    monkeypatch.setenv("SMART_CLIENT_ID", "client-123")
    monkeypatch.setenv("SMART_CLIENT_SECRET", "smart-secret")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://app.example.com/callback")

    readiness = smart_fhir.get_readiness()

    assert readiness["enabled"] is True
    assert readiness["base_url_configured"] is True
    assert readiness["authorization_endpoint_configured"] is True
    assert readiness["token_endpoint_configured"] is True
    assert readiness["client_id_configured"] is True
    assert readiness["redirect_uri_configured"] is True
    assert readiness["secrets_exposed"] is False
    assert "smart-secret" not in str(readiness)
    assert "launch-ehr" in readiness["capabilities"]


def test_build_authorization_url_contains_required_smart_parameters(monkeypatch):
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_FHIR_BASE_URL", "https://ehr.example.com/fhir")
    monkeypatch.setenv("SMART_CLIENT_ID", "client-123")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://app.example.com/callback")
    monkeypatch.setenv("SMART_SCOPES", "launch/patient patient/*.read openid fhirUser")

    authorize_url = smart_fhir.build_authorization_url(
        state="state-123",
        launch="launch-token-123",
    )

    parsed = urlparse(authorize_url)
    params = parse_qs(parsed.query)
    assert parsed.geturl().startswith("https://ehr.example.com/auth?")
    assert params["response_type"] == ["code"]
    assert params["client_id"] == ["client-123"]
    assert params["redirect_uri"] == ["https://app.example.com/callback"]
    assert params["scope"] == ["launch/patient patient/*.read openid fhirUser"]
    assert params["state"] == ["state-123"]
    assert params["launch"] == ["launch-token-123"]
    assert params["aud"] == ["https://ehr.example.com/fhir"]


def test_build_authorization_url_rejects_unsafe_state(monkeypatch):
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_FHIR_BASE_URL", "https://ehr.example.com/fhir")
    monkeypatch.setenv("SMART_CLIENT_ID", "client-123")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://app.example.com/callback")

    with pytest.raises(smart_fhir.SMARTValidationError):
        smart_fhir.build_authorization_url(state="patient_name=Sensitive User")


def test_build_authorization_url_requires_core_config(monkeypatch):
    monkeypatch.delenv("SMART_AUTHORIZATION_ENDPOINT", raising=False)
    monkeypatch.delenv("SMART_CLIENT_ID", raising=False)
    monkeypatch.delenv("SMART_REDIRECT_URI", raising=False)

    with pytest.raises(smart_fhir.SMARTConfigurationError):
        smart_fhir.build_authorization_url(state="state-123")
