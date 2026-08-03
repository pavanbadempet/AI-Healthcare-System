"""
Unit & API integration tests for Agent Governance, FDA 21 CFR Part 11 Audit Trail,
Lineage Provenance, & Auto-Resolution Engine.
"""

from fastapi.testclient import TestClient

from backend.agents.agent_governance_engine import agent_governance_engine
from backend.main import app

client = TestClient(app)


def test_governed_agent_execution_and_auto_resolution():
    def sample_func(data):
        return {"patient_id": "P-GOV-10", "sepsis_risk_level": "SEPTIC_SHOCK_WARNING", "qsofa_score": 3}

    res = agent_governance_engine.execute_governed_action(
        agent_id="AGENT-GOV-TEST",
        action_name="evaluate_sepsis_risk",
        input_data={"patient_name": "John Doe", "respiratory_rate": 26},
        agent_func=sample_func,
    )

    assert res.status == "AUTO_RESOLVED"
    assert "AUTO-RESOLUTION TRIGGERED" in res.auto_resolution_summary
    assert len(res.fda_audit_hash) == 64
    assert res.medical_disclaimer is not None


def test_agent_lineage_graph_tracking():
    chain = agent_governance_engine.get_lineage_chain()
    assert len(chain) >= 1
    node = chain[0]
    assert "agent_id" in node
    assert "input_fingerprint" in node


def test_api_agent_governance_endpoints():
    # Governed Execution API
    resp1 = client.post("/api/v1/data-platform/agents/governed-execute", json={
        "agent_id": "AGENT-ICU-SEPSIS",
        "action_name": "evaluate_sepsis_risk",
        "input_data": {"respiratory_rate": 25, "systolic_bp": 90, "gcs_score": 13},
    })
    assert resp1.status_code == 200
    body = resp1.json()
    assert body["status"] == "AUTO_RESOLVED"
    assert len(body["fda_audit_hash"]) == 64

    # Lineage API
    resp2 = client.get("/api/v1/data-platform/agents/lineage")
    assert resp2.status_code == 200
    assert resp2.json()["total_nodes"] >= 1
