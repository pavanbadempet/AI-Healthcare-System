"""
Unit & API integration tests for Enterprise Autonomous AI Agents:
- Agent Fraud Detection
- Agent Entity Resolution (EMPI)
- Agent Cost Analyzer
- Agent Future Forecast
"""

from fastapi.testclient import TestClient

from backend.agents.enterprise_clinical_agents import (
    agent_cost_analyzer,
    agent_entity_resolution,
    agent_fraud_detection,
    agent_future_forecast,
)
from backend.main import app

client = TestClient(app)


def test_agent_fraud_detection():
    claim = {
        "claim_id": "CLM-9901",
        "amount": 15000.0,
        "cpt_codes": ["CPT-99211"],
        "is_duplicate": True,
    }
    res = agent_fraud_detection.analyze_claim(claim)
    assert res.fraud_score > 0.5
    assert "DUPLICATE_CLAIM_SUBMISSION_DETECTED" in res.detected_anomalies
    assert res.recommended_action == "REJECT_AND_FLAG_FOR_AUDIT"


def test_agent_entity_resolution():
    candidate = {"ssn": "123-45-6789", "name": "Alice Smith", "dob": "1990-01-01"}
    master = [
        {"patient_id": "P-MASTER-1", "ssn": "123-45-6789", "name": "Alice Smith", "dob": "1990-01-01"},
        {"patient_id": "P-MASTER-2", "ssn": "999-99-9999", "name": "Bob Jones", "dob": "1985-05-05"},
    ]
    res = agent_entity_resolution.resolve_entity(candidate, master)
    assert res.match_found is True
    assert res.primary_patient_id == "P-MASTER-1"
    assert res.confidence_score >= 0.7


def test_agent_cost_analyzer():
    case = {
        "patient_id": "P-7001",
        "drg_code": "DRG-291",
        "length_of_stay_days": 6,
        "has_generic_substitute": True,
    }
    res = agent_cost_analyzer.analyze_cost(case)
    assert res.estimated_total_cost > 0.0
    assert len(res.cost_saving_opportunities) >= 1


def test_agent_future_forecast():
    history = [45.0, 50.0, 52.0, 58.0, 65.0, 70.0, 78.0]
    res = agent_future_forecast.forecast_demand(history, forecast_horizon_days=7)
    assert res.predicted_metric_value > 0.0
    assert res.trajectory_trend in ("INCREASING", "CRITICAL_SURGE", "STABLE")


def test_api_enterprise_agents_endpoints():
    # Fraud API
    resp1 = client.post("/api/v1/data-platform/agents/fraud-detection/analyze", json={
        "amount": 20000.0, "cpt_codes": ["CPT-99211"],
    })
    assert resp1.status_code == 200
    assert resp1.json()["fraud_score"] > 0.0

    # Forecast API
    resp2 = client.post("/api/v1/data-platform/agents/future-forecast/predict", json={
        "historical_counts": [60.0, 65.0, 70.0],
        "forecast_horizon_days": 7,
    })
    assert resp2.status_code == 200
    assert resp2.json()["predicted_metric_value"] > 0.0
