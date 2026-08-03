"""
Unit & API integration tests for Ultimate State-of-the-Art Agentic AI Intelligence Mesh:
- ReAct + Reflexion Self-Correction Loop
- Multi-Agent Consensus Debate Protocol
- Hierarchical DAG Plan-and-Execute Engine
- Master Governed Mesh Execution
"""

from fastapi.testclient import TestClient

from backend.agents.ultimate_agent_mesh import ultimate_agent_mesh
from backend.main import app

client = TestClient(app)


def test_react_reflexion_self_correction():
    goal = "Verify medication dosage & redact PHI"
    plan = [
        {"tool_name": "query_fhir", "tool_kwargs": {"patient_id": "P-100"}},
        {"tool_name": "redact_phi", "tool_kwargs": {"text": "Patient Jane Doe"}},
    ]
    results = ultimate_agent_mesh.react_loop.execute_react_cycle(goal, plan)
    assert len(results) == 2
    assert results[0].status in ("SUCCESS", "RETRIED")
    assert results[1].confidence > 0.50


def test_multi_agent_consensus_debate_protocol():
    case_id = "CASE-DEBATE-77"
    case_data = {"amount": 15000, "cpt_codes": ["CPT-99211"], "qsofa_score": 3}
    agents = ["AGENT-FRAUD-DETECTION", "AGENT-ICU-SEPSIS", "AGENT-PHARM-SAFETY"]

    res = ultimate_agent_mesh.debate_protocol.run_debate(case_id, case_data, agents)
    assert res.case_id == case_id
    assert res.total_agents_participated == 3
    assert res.consensus_decision in ("REJECT", "ESCALATE", "APPROVE")
    assert res.consensus_confidence > 0.0


def test_hierarchical_dag_plan_execution():
    goal = "Emergency Admission & Prior Auth Workflow"
    tasks = [
        {"task_id": "T1", "description": "ED Risk Assessment", "capability": "TRIAGE", "depends_on": []},
        {"task_id": "T2", "description": "Verify Pharmacy Safety", "capability": "PHARMACY", "depends_on": ["T1"]},
        {"task_id": "T3", "description": "Process Insurance Prior Auth", "capability": "PRIOR_AUTH", "depends_on": ["T1"]},
    ]
    plan = ultimate_agent_mesh.dag_orchestrator.build_dag_plan(goal, tasks)
    res_plan = ultimate_agent_mesh.dag_orchestrator.execute_dag_plan(plan)

    assert res_plan.overall_status == "COMPLETED"
    assert len(res_plan.nodes) == 3
    assert res_plan.nodes["T2"].status == "COMPLETED"


def test_master_governed_mesh_task():
    case_data = {"case_id": "CASE-GOV-99", "amount": 20000, "cpt_codes": ["CPT-99211"]}
    agents = ["AGENT-FRAUD-DETECTION", "AGENT-PHARM-SAFETY"]

    res = ultimate_agent_mesh.run_governed_mesh_task("Evaluate High-Risk Claim", case_data, agents)
    assert "execution_id" in res
    assert res["status"] in ("SUCCESS", "AUTO_RESOLVED")
    assert len(res["fda_audit_hash"]) == 64


def test_api_mesh_endpoints():
    # Debate API
    resp1 = client.post("/api/v1/data-platform/agents/mesh/consensus-debate", json={
        "case_id": "CASE-TEST-100",
        "case_data": {"qsofa_score": 3},
    })
    assert resp1.status_code == 200
    assert resp1.json()["total_agents_participated"] >= 1

    # ReAct API
    resp2 = client.post("/api/v1/data-platform/agents/mesh/execute-react-goal", json={
        "goal": "Test ReAct Cycle",
    })
    assert resp2.status_code == 200
    assert resp2.json()["total_steps"] >= 1

    # DAG API
    resp3 = client.post("/api/v1/data-platform/agents/mesh/dag-orchestrate", json={
        "goal": "Test DAG Workflow",
    })
    assert resp3.status_code == 200
    assert resp3.json()["overall_status"] == "COMPLETED"
