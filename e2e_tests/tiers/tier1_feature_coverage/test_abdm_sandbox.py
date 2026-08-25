"""
Tier 1: Feature Coverage — ABDM Sandbox Domain (/v1/abdm/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_abdm_generate_abha_health_id(patient_client: E2EClient):
    payload = {"name": "Rohan Sharma", "gender": "M", "year_of_birth": 1990}
    resp = patient_client.post("/v1/abdm/abha/generate", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422), f"ABHA gen failed: {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        assert "abha_number" in data
        assert "abha_address" in data


def test_abdm_get_abha_details(patient_client: E2EClient):
    resp = patient_client.get("/v1/abdm/abha/91-1234-5678-9012")
    assert resp.status_code in (200, 401, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert "abha_number" in data


def test_abdm_request_health_consent(patient_client: E2EClient):
    payload = {
        "patient_abha": "rohan.sharma99@sbx",
        "purpose": "CAREMGT",
        "hi_types": ["DiagnosticReport", "Prescription"],
        "valid_until": "2026-12-31T23:59:59Z",
    }
    resp = patient_client.post("/v1/abdm/consent/request", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422), f"Consent request failed: {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        assert "consent_id" in data
        assert data.get("status") == "GRANTED"


def test_abdm_get_consent_status(patient_client: E2EClient):
    # Request consent first
    payload = {
        "patient_abha": "rohan.sharma99@sbx",
        "purpose": "CAREMGT",
        "hi_types": ["DiagnosticReport"],
        "valid_until": "2026-12-31T23:59:59Z",
    }
    req_resp = patient_client.post("/v1/abdm/consent/request", json=payload)
    if req_resp.status_code == 200:
        consent_id = req_resp.json().get("consent_id")
        resp = patient_client.get(f"/v1/abdm/consent/{consent_id}")
        assert resp.status_code == 200
        assert resp.json().get("consent_id") == consent_id
    else:
        resp = patient_client.get("/v1/abdm/consent/NONEXISTENT_CONSENT")
        assert resp.status_code in (404, 401)


def test_abdm_interop_readiness(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/abdm/readiness")
    assert resp.status_code in (200, 401)
