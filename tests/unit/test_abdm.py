from datetime import datetime, timezone

import pytest


def _abdm_module():
    try:
        from backend import abdm
    except ImportError:
        pytest.fail("backend.abdm module is required for ABDM connector support")
    return abdm


def test_abdm_readiness_reports_missing_config_without_exposing_secrets(monkeypatch):
    abdm = _abdm_module()
    monkeypatch.setenv("ABDM_ENABLED", "true")
    monkeypatch.setenv("ABDM_CLIENT_SECRET", "super-secret-client-value")
    monkeypatch.delenv("ABDM_BASE_URL", raising=False)
    monkeypatch.delenv("ABDM_HIU_ID", raising=False)

    readiness = abdm.get_readiness()

    assert readiness["configured"] is False
    assert "ABDM_BASE_URL" in readiness["missing"]
    assert "ABDM_HIU_ID" in readiness["missing"]
    assert "super-secret-client-value" not in str(readiness)
    assert readiness["environment"] == "sandbox"


def test_build_consent_request_payload_uses_abdm_hiu_shape(monkeypatch):
    abdm = _abdm_module()
    monkeypatch.setenv("ABDM_HIU_ID", "AIH-HIU")
    monkeypatch.setenv("ABDM_REQUESTER_NAME", "Synthetic Hospital")
    monkeypatch.setenv("ABDM_REQUESTER_IDENTIFIER_VALUE", "HFR-SYNTHETIC")
    requested_at = datetime(2026, 5, 27, 8, 0, tzinfo=timezone.utc)

    payload = abdm.build_consent_request_payload(
        patient_abha_address="synthetic@sbx",
        purpose_code="CAREMGT",
        hi_types=["DiagnosticReport", "Prescription"],
        date_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
        date_to=datetime(2026, 5, 27, tzinfo=timezone.utc),
        data_erase_at=datetime(2026, 6, 26, tzinfo=timezone.utc),
        hip_id="HIP-SYNTHETIC",
        care_context_reference="visit-123",
        request_id="request-123",
        timestamp=requested_at,
    )

    assert payload["requestId"] == "request-123"
    assert payload["timestamp"] == "2026-05-27T08:00:00+00:00"
    assert payload["consent"]["purpose"]["code"] == "CAREMGT"
    assert payload["consent"]["purpose"]["text"] == "Care Management"
    assert payload["consent"]["patient"]["id"] == "synthetic@sbx"
    assert payload["consent"]["hiu"]["id"] == "AIH-HIU"
    assert payload["consent"]["hip"]["id"] == "HIP-SYNTHETIC"
    assert payload["consent"]["careContexts"] == [{"referenceNumber": "visit-123"}]
    assert payload["consent"]["requester"]["name"] == "Synthetic Hospital"
    assert payload["consent"]["requester"]["identifier"]["value"] == "HFR-SYNTHETIC"
    assert payload["consent"]["hiTypes"] == ["DiagnosticReport", "Prescription"]
    assert payload["consent"]["permission"]["accessMode"] == "VIEW"
    assert payload["consent"]["permission"]["dateRange"] == {
        "from": "2026-05-01T00:00:00+00:00",
        "to": "2026-05-27T00:00:00+00:00",
    }
    assert payload["consent"]["permission"]["dataEraseAt"] == "2026-06-26T00:00:00+00:00"


def test_build_consent_request_payload_rejects_unsupported_hi_type():
    abdm = _abdm_module()

    with pytest.raises(abdm.ABDMValidationError, match="Unsupported ABDM health information type"):
        abdm.build_consent_request_payload(
            patient_abha_address="synthetic@sbx",
            purpose_code="CAREMGT",
            hi_types=["UnknownType"],
            date_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 5, 27, tzinfo=timezone.utc),
            data_erase_at=datetime(2026, 6, 26, tzinfo=timezone.utc),
        )


def test_prepare_consent_request_dry_run_does_not_call_transport(monkeypatch):
    abdm = _abdm_module()
    monkeypatch.setenv("ABDM_HIU_ID", "AIH-HIU")

    def fail_transport(*args, **kwargs):
        raise AssertionError("transport should not be called for dry-run consent requests")

    result = abdm.prepare_consent_request(
        patient_abha_address="synthetic@sbx",
        purpose_code="CAREMGT",
        hi_types=["DiagnosticReport"],
        date_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
        date_to=datetime(2026, 5, 27, tzinfo=timezone.utc),
        data_erase_at=datetime(2026, 6, 26, tzinfo=timezone.utc),
        submit=False,
        transport=fail_transport,
        request_id="request-123",
        timestamp=datetime(2026, 5, 27, 8, 0, tzinfo=timezone.utc),
    )

    assert result["submitted"] is False
    assert result["status"] == "ready_for_submission"
    assert result["payload"]["requestId"] == "request-123"


def test_prepare_consent_request_requires_configuration_for_submission(monkeypatch):
    abdm = _abdm_module()
    monkeypatch.setenv("ABDM_ENABLED", "true")
    monkeypatch.delenv("ABDM_BASE_URL", raising=False)

    with pytest.raises(abdm.ABDMConfigurationError, match="ABDM connector is not fully configured"):
        abdm.prepare_consent_request(
            patient_abha_address="synthetic@sbx",
            purpose_code="CAREMGT",
            hi_types=["DiagnosticReport"],
            date_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 5, 27, tzinfo=timezone.utc),
            data_erase_at=datetime(2026, 6, 26, tzinfo=timezone.utc),
            submit=True,
        )


def test_normalize_consent_callback_hashes_payload_without_patient_identifier():
    abdm = _abdm_module()

    callback = abdm.normalize_consent_callback(
        request_id="request-123",
        status="granted",
        abdm_consent_id="consent-123",
        hi_types=["DiagnosticReport", "Prescription"],
        event_type="consent_status",
        notification_at=datetime(2026, 5, 28, 8, 0, tzinfo=timezone.utc),
        error_code=None,
    )

    assert callback["status"] == "GRANTED"
    assert callback["local_consent_status"] == "active"
    assert callback["hi_types"] == ["DiagnosticReport", "Prescription"]
    assert len(callback["payload_sha256"]) == 64
    assert callback["raw_payload_stored"] is False
    assert "synthetic@sbx" not in str(callback)


def test_normalize_consent_callback_rejects_abha_like_request_id():
    abdm = _abdm_module()

    with pytest.raises(abdm.ABDMValidationError, match="ABDM request id is invalid"):
        abdm.normalize_consent_callback(
            request_id="synthetic@sbx",
            status="GRANTED",
            abdm_consent_id="consent-123",
        )


def test_prepare_consent_request_allows_demo_mode_bypass(monkeypatch):
    abdm = _abdm_module()
    monkeypatch.setenv("ABDM_ENABLED", "true")
    monkeypatch.setenv("ABDM_DEMO_MODE", "true")
    monkeypatch.delenv("ABDM_BASE_URL", raising=False)
    monkeypatch.delenv("ABDM_HIU_ID", raising=False)

    result = abdm.prepare_consent_request(
        patient_abha_address="demo@sbx",
        purpose_code="CAREMGT",
        hi_types=["DiagnosticReport"],
        date_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
        date_to=datetime(2026, 5, 27, tzinfo=timezone.utc),
        data_erase_at=datetime(2026, 6, 26, tzinfo=timezone.utc),
        submit=True,
    )

    assert result["submitted"] is True
    assert result["status"] == "submitted"
    assert "MOCK" in result["endpoint"]
    assert result["abdm_response"]["status"] == "SUCCESS"
    assert result["payload"]["consent"]["patient"]["id"] == "demo@sbx"
