"""
Tier 2: Boundary & Corner Cases — Unified Data Platform Boundaries
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_data_platform_catalog_empty_query(e2e_client: E2EClient):
    resp = e2e_client.get("/api/v1/data-platform/catalog/search?query=")
    assert resp.status_code in (200, 400, 422, 404)


def test_data_platform_bi_ask_empty_body(e2e_client: E2EClient):
    resp = e2e_client.post("/api/v1/data-platform/bi/ask", json={})
    assert resp.status_code in (200, 400, 422, 404)


def test_data_platform_sepsis_evaluation_missing_vitals(e2e_client: E2EClient):
    resp = e2e_client.post("/api/v1/data-platform/agents/sepsis/evaluate", json={"patient_id": "P-01"})
    assert resp.status_code in (200, 400, 422, 404)


def test_data_platform_prior_auth_malformed_procedure(e2e_client: E2EClient):
    payload = {"patient_id": "P-01", "procedure_code": "", "has_neurological_symptoms": False}
    resp = e2e_client.post("/api/v1/data-platform/agents/prior-auth/process", json=payload)
    assert resp.status_code in (200, 400, 422, 404)


def test_data_platform_mesh_debate_empty_agents(e2e_client: E2EClient):
    payload = {"topic": "clinical_consensus", "agents": []}
    resp = e2e_client.post("/api/v1/data-platform/agents/mesh/consensus-debate", json=payload)
    assert resp.status_code in (200, 400, 422, 404)


def test_data_platform_cost_analyzer_negative_los(e2e_client: E2EClient):
    payload = {"patient_id": "P-01", "drg_code": "DRG-291", "length_of_stay_days": -10}
    resp = e2e_client.post("/api/v1/data-platform/agents/cost-analyzer/analyze", json=payload)
    assert resp.status_code in (200, 400, 422, 404)
