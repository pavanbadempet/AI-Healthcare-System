"""
Unit tests for SOTA Multi-Agent Orchestration Engine (backend/sota_ai_agents_layer.py).
"""

from backend.sota_ai_agents_layer import SOTAAIAgentsEngine


def test_multi_agent_evaluation_and_consensus_synthesis():
    engine = SOTAAIAgentsEngine()

    triage_rec = engine.triage_agent_evaluate({"heart_rate": 115})
    assert triage_rec.agent_name == "TriageAgent"
    assert "HIGH_URGENCY" in triage_rec.opinion

    pharma_rec = engine.pharma_agent_evaluate(["HYPERTENSION"])
    assert pharma_rec.agent_name == "PharmaAgent"

    consensus = engine.synthesize_consensus_plan([triage_rec, pharma_rec])
    assert len(consensus.participating_agents) == 2
    assert consensus.consensus_confidence >= 0.90
    assert "TriageAgent" in consensus.final_plan
