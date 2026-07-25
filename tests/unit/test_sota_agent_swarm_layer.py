"""
Unit tests for SOTA Agent Swarm Engine (backend/sota_agent_swarm_layer.py).
"""

from backend.sota_agent_swarm_layer import SOTAAgentSwarmLayerEngine


def test_clinical_agent_swarm_execution():
    engine = SOTAAgentSwarmLayerEngine()

    wf_id = "WF_CLINICAL_TRIAGE_001"
    result = engine.execute_clinical_agent_swarm(wf_id, "Patient has severe chest pressure.")

    assert result.workflow_id == wf_id
    assert len(result.agents_involved) == 3
    assert result.completed_steps == 3
    assert result.is_verified_safe
    assert result.execution_time_ms >= 0.0
