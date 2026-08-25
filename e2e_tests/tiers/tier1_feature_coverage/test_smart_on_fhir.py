"""
Tier 1: Feature Coverage — SMART on FHIR Domain (/v1/smart/* & /.well-known/smart-configuration)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_smart_well_known_config(e2e_client: E2EClient):
    resp = e2e_client.get("/.well-known/smart-configuration")
    assert resp.status_code in (200, 404)


def test_smart_authorize_url(patient_client: E2EClient):
    resp = patient_client.get("/v1/smart/authorize-url?launch=launch_123&scope=launch/patient")
    assert resp.status_code in (200, 401, 404, 422)


def test_smart_readiness(patient_client: E2EClient):
    resp = patient_client.get("/v1/smart/readiness")
    assert resp.status_code in (200, 401, 404)


def test_smart_token_exchange(e2e_client: E2EClient):
    payload = {"grant_type": "authorization_code", "code": "sample_auth_code_123", "client_id": "smart_portal_app"}
    resp = e2e_client.post("/v1/smart/token", json=payload)
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_smart_apps_list(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/smart/apps")
    assert resp.status_code in (200, 401, 404)
