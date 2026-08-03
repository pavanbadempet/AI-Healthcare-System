"""
Unit & API integration tests for Agent Performance & Benchmark Suite.
"""

from fastapi.testclient import TestClient

from backend.agents.agent_benchmark_suite import agent_benchmark_runner
from backend.main import app

client = TestClient(app)


def test_agent_benchmark_runner_scorecard():
    card = agent_benchmark_runner.run_full_benchmark()
    assert card.total_agents_tested >= 7
    assert card.overall_performance_score >= 80.0
    assert card.letter_grade in ("A+", "A", "B")
    assert card.audit_chain_integrity_pct == 100.0
    assert card.avg_latency_ms < 500.0  # Sub-second latency benchmark


def test_api_agent_benchmark_endpoint():
    res = client.get("/api/v1/data-platform/agents/benchmark/run")
    assert res.status_code == 200
    body = res.json()
    assert "overall_performance_score" in body
    assert "letter_grade" in body
    assert len(body["agent_metrics"]) >= 7
