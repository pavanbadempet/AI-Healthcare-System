"""
Unit tests for Agentic AI infrastructure:
- Agent Tool Registry
- Reflective Memory Store
- Supervisor Agent Router
- Plan-and-Execute Orchestrator
"""

from backend.agents.tool_registry import agent_tool_registry
from backend.agents.reflective_memory import AgentReflectiveMemory
from backend.agents.supervisor_orchestrator import (
    supervisor_router,
    plan_and_execute_orchestrator,
    AgentCapability,
    PlanStep,
)


def test_tool_registry_discovery_and_invocation():
    tools = agent_tool_registry.list_tools()
    assert agent_tool_registry.tool_count >= 4
    names = [t.name for t in tools]
    assert "compute_egfr" in names
    assert "redact_phi" in names

    schema = agent_tool_registry.get_schema("compute_egfr")
    assert schema is not None
    assert schema.is_rust_native is True

    result = agent_tool_registry.invoke("compute_egfr", serum_creatinine=0.9, age=45, is_female=True)
    assert 80.0 < result < 120.0


def test_reflective_memory_record_and_reflect():
    mem = AgentReflectiveMemory()

    mem.record_episode("EP-1", "TriageAgent", "Assessed vitals", "Patient stable", reward_signal=0.8)
    mem.record_episode("EP-2", "TriageAgent", "Missed hypoxia", "Patient deteriorated", reward_signal=-0.7)

    recalled = mem.recall(agent_name="TriageAgent")
    assert len(recalled) == 2

    insights = mem.reflect()
    assert len(insights) >= 1


def test_supervisor_router_selects_best_agent():
    assert supervisor_router.agent_count >= 6

    decision = supervisor_router.route(AgentCapability.TRIAGE)
    assert decision.selected_agent_name == "EDTriageAgent"
    assert decision.confidence > 0.0

    decision_rad = supervisor_router.route(AgentCapability.RADIOLOGY)
    assert decision_rad.selected_agent_name == "RadiologyPrereaderAgent"


def test_plan_and_execute_orchestrator_end_to_end():
    plan = plan_and_execute_orchestrator.plan(
        goal="Evaluate patient renal function and redact PHI from notes",
        steps=[
            PlanStep(
                description="Compute eGFR for renal dosage check",
                required_capability=AgentCapability.TRIAGE,
                tool_name="compute_egfr",
                tool_kwargs={"serum_creatinine": 1.1, "age": 60, "is_female": False},
            ),
            PlanStep(
                description="Redact PHI from clinical narrative",
                required_capability=AgentCapability.SAFETY,
                tool_name="redact_phi",
                tool_kwargs={"text": "Patient SSN 123-45-6789 email doc@hosp.org"},
            ),
        ],
    )

    executed = plan_and_execute_orchestrator.execute(plan)
    assert executed.overall_status == "COMPLETED"
    assert all(s.status == "COMPLETED" for s in executed.steps)
    assert "compute_egfr" in executed.steps[0].result
    assert "redact_phi" in executed.steps[1].result
