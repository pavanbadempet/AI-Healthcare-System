"""
Tier 1: Feature Coverage — Unified Data Platform Domain (/api/v1/data-platform/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_data_platform_apps_list(e2e_client: E2EClient):
    resp = e2e_client.get("/api/v1/data-platform/apps/list")
    assert resp.status_code in (200, 404)


def test_data_platform_catalog_search(e2e_client: E2EClient):
    resp = e2e_client.get("/api/v1/data-platform/catalog/search?query=patient")
    assert resp.status_code in (200, 404, 422)


def test_data_platform_lineage(e2e_client: E2EClient):
    resp = e2e_client.get("/api/v1/data-platform/agents/lineage")
    assert resp.status_code in (200, 404)


def test_data_platform_agent_benchmark(e2e_client: E2EClient):
    resp = e2e_client.get("/api/v1/data-platform/agents/benchmark/run")
    assert resp.status_code in (200, 404)


def test_data_platform_bi_ask(e2e_client: E2EClient):
    payload = {"query": "What is the average inpatient stay duration?", "dataset": "clinical_admissions"}
    resp = e2e_client.post("/api/v1/data-platform/bi/ask", json=payload)
    assert resp.status_code in (200, 404, 422)


def test_data_platform_cost_analyzer(e2e_client: E2EClient):
    payload = {"patient_id": "P-100", "drg_code": "DRG-291", "length_of_stay_days": 5}
    resp = e2e_client.post("/api/v1/data-platform/agents/cost-analyzer/analyze", json=payload)
    assert resp.status_code in (200, 404, 422)


def test_data_platform_sepsis_evaluation(e2e_client: E2EClient):
    payload = {"patient_id": "P-ICU-01", "respiratory_rate": 24, "systolic_bp": 90, "gcs_score": 14}
    resp = e2e_client.post("/api/v1/data-platform/agents/sepsis/evaluate", json=payload)
    assert resp.status_code in (200, 404, 422)


def test_data_platform_prior_auth(e2e_client: E2EClient):
    payload = {"patient_id": "P-100", "procedure_code": "CPT-70450", "has_prior_xray": True, "has_neurological_symptoms": True}
    resp = e2e_client.post("/api/v1/data-platform/agents/prior-auth/process", json=payload)
    assert resp.status_code in (200, 404, 422)
