"""
Unit tests for essential hospital operations AI agents:
- Agent Prior Auth
- Agent Sepsis Deterioration
- Agent Surgical OR
"""

from fastapi.testclient import TestClient

from backend.agents.hospital_operations_agents import (
    agent_prior_auth,
    agent_sepsis_deterioration,
    agent_surgical_or,
)
from backend.main import app

client = TestClient(app)


def test_agent_prior_auth_automation():
    req = {
        "patient_id": "P-AUTH-909",
        "procedure_code": "CPT-70450",
        "has_prior_xray": True,
        "has_neurological_symptoms": True,
    }
    res = agent_prior_auth.process_prior_auth(req)
    assert res.approval_status == "AUTO_APPROVED"
    assert "Medical necessity established" in res.clinical_justification


def test_agent_sepsis_deterioration_evaluation():
    vitals = {
        "patient_id": "P-ICU-88",
        "respiratory_rate": 24,  # +1
        "systolic_bp": 95,       # +1
        "gcs_score": 14,         # +1 -> Total qSOFA = 3
    }
    res = agent_sepsis_deterioration.evaluate_sepsis_risk(vitals)
    assert res.qsofa_score == 3
    assert res.sepsis_risk_level == "SEPTIC_SHOCK_WARNING"
    assert len(res.immediate_interventions) >= 3


def test_agent_surgical_or_optimization():
    case = {
        "or_room_id": "OR-5",
        "case_id": "SURG-900",
        "case_type": "LAPAROSCOPIC",
    }
    res = agent_surgical_or.optimize_or_schedule(case)
    assert res.turnover_time_minutes == 25
    assert res.sterilization_status == "READY"


def test_api_hospital_operations_agent_endpoints():
    # Sepsis API
    resp1 = client.post("/api/v1/data-platform/agents/sepsis/evaluate", json={
        "respiratory_rate": 25, "systolic_bp": 90, "gcs_score": 13,
    })
    assert resp1.status_code == 200
    assert resp1.json()["qsofa_score"] == 3

    # Prior Auth API
    resp2 = client.post("/api/v1/data-platform/agents/prior-auth/process", json={
        "procedure_code": "CPT-70450", "has_neurological_symptoms": True,
    })
    assert resp2.status_code == 200
    assert resp2.json()["approval_status"] == "AUTO_APPROVED"
