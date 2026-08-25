"""
Tier 1: Feature Coverage — Interoperability Domain (/v1/interop/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_interop_abdm_readiness(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/abdm/readiness")
    assert resp.status_code in (200, 401)


def test_interop_smart_readiness(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/smart/readiness")
    assert resp.status_code in (200, 401)


def test_interop_dicomweb_readiness(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/dicomweb/readiness")
    assert resp.status_code in (200, 401)


def test_interop_terminology_systems(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/terminology/systems")
    assert resp.status_code in (200, 401)


def test_interop_terminology_lookup(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/terminology/lookup?system=http://snomed.info/sct&code=38341003")
    assert resp.status_code in (200, 401, 422)


def test_interop_terminology_search(patient_client: E2EClient):
    payload = {"query": "Hypertension", "system": "SNOMED", "max_results": 5}
    resp = patient_client.post("/v1/interop/terminology/search", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_interop_ehr_providers(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/ehr/providers")
    assert resp.status_code in (200, 401)


def test_interop_admin_metrics(admin_client: E2EClient):
    resp = admin_client.get("/v1/interop/admin/metrics")
    assert resp.status_code in (200, 401, 403)
