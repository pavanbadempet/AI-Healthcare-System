"""
Unit tests for Clinical Research & Remote Patient Monitoring AI Agents:
- Agent Trial Matching
- Agent RPM Adherence
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.agents.clinical_research_rpm_agents import (
    agent_trial_matching,
    agent_rpm_adherence,
)

client = TestClient(app)


def test_agent_trial_matching():
    profile = {
        "patient_id": "P-ONC-55",
        "condition": "NSCLC",
        "biomarker": "EGFR_L858R",
    }
    res = agent_trial_matching.match_trials(profile)
    assert res.match_confidence > 0.8
    assert len(res.eligible_trials) >= 1


def test_agent_rpm_adherence():
    telemetry = {
        "patient_id": "P-RPM-77",
        "missed_doses_last_7d": 4,
        "avg_systolic_bp": 135,
    }
    res = agent_rpm_adherence.evaluate_rpm(telemetry)
    assert res.vitals_status == "ATTENTION_REQUIRED"
    assert res.adherence_score_pct < 80.0
    assert len(res.recommended_interventions) >= 1


def test_api_research_rpm_agent_endpoints():
    resp1 = client.post("/api/v1/data-platform/agents/trial-matching/match", json={
        "condition": "NSCLC", "biomarker": "EGFR",
    })
    assert resp1.status_code == 200
    assert resp1.json()["match_confidence"] > 0.0

    resp2 = client.post("/api/v1/data-platform/agents/rpm-adherence/evaluate", json={
        "missed_doses_last_7d": 1, "avg_systolic_bp": 120,
    })
    assert resp2.status_code == 200
    assert resp2.json()["vitals_status"] == "NORMAL"
