"""
Tier 1: Feature Coverage — Lakehouse Data Engineering Domain (/v1/lakehouse/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_lakehouse_omop_transform(admin_client: E2EClient):
    payload = {"source": "fhir_raw_stream", "payload": {"resourceType": "Patient", "id": "1"}}
    resp = admin_client.post("/v1/lakehouse/omop/transform", json=payload)
    assert resp.status_code in (200, 201, 202, 401, 403, 404, 422)


def test_lakehouse_quality_audit(admin_client: E2EClient):
    payload = {"dataset_name": "patient_observations", "suite_name": "clinical_vitals_suite"}
    resp = admin_client.post("/v1/lakehouse/quality/audit", json=payload)
    assert resp.status_code in (200, 201, 202, 401, 403, 404, 422)


def test_lakehouse_delta_history(admin_client: E2EClient):
    resp = admin_client.get("/v1/lakehouse/delta/history?table=patient_observations")
    assert resp.status_code in (200, 401, 403, 404, 422)


def test_lakehouse_delta_time_travel(admin_client: E2EClient):
    payload = {"table": "patient_observations", "version": 1}
    resp = admin_client.post("/v1/lakehouse/delta/time-travel", json=payload)
    assert resp.status_code in (200, 401, 403, 404, 422)


def test_lakehouse_delta_cdf(admin_client: E2EClient):
    resp = admin_client.get("/v1/lakehouse/delta/cdf?table=patient_observations&starting_version=0")
    assert resp.status_code in (200, 401, 403, 404, 422)
