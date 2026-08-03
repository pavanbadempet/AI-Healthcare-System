"""
AI Healthcare System — Agentic AI Supervisor Router & Plan-and-Execute Orchestrator.

Implements:
1. Supervisor Agent Router — routes patient cases to the best-fit specialist agent
2. Plan-and-Execute Orchestrator — decomposes complex clinical goals into ordered
   sub-tasks, delegates each to a specialist agent, and assembles the final result
"""

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.agents.tool_registry import agent_tool_registry
from backend.agents.reflective_memory import agent_reflective_memory


# =====================================================================
# 1. Supervisor Agent Router
# =====================================================================

class AgentCapability(str, Enum):
    TRIAGE = "TRIAGE"
    PHARMACY = "PHARMACY"
    RADIOLOGY = "RADIOLOGY"
    DISCHARGE = "DISCHARGE"
    BILLING = "BILLING"
    SCHEDULING = "SCHEDULING"
    SAFETY = "SAFETY"


class RegisteredAgent(BaseModel):
    """Metadata for a specialist agent registered with the supervisor."""
    agent_id: str
    name: str
    capabilities: List[AgentCapability]
    priority: int = 0


class RoutingDecision(BaseModel):
    """Result of the supervisor's routing decision."""
    selected_agent_id: str
    selected_agent_name: str
    reason: str
    confidence: float


class SupervisorAgentRouter:
    """
    Routes incoming clinical tasks to the best-fit specialist agent
    based on required capabilities and agent priority.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, RegisteredAgent] = {}

    def register_agent(self, agent: RegisteredAgent) -> None:
        """Register a specialist agent with the supervisor."""
        self._agents[agent.agent_id] = agent

    def route(self, required_capability: AgentCapability) -> RoutingDecision:
        """Select the highest-priority agent that has the required capability."""
        candidates = [
            a for a in self._agents.values()
            if required_capability in a.capabilities
        ]
        if not candidates:
            return RoutingDecision(
                selected_agent_id="NONE",
                selected_agent_name="Unresolved",
                reason=f"No agent registered with capability {required_capability.value}.",
                confidence=0.0,
            )

        best = max(candidates, key=lambda a: a.priority)
        return RoutingDecision(
            selected_agent_id=best.agent_id,
            selected_agent_name=best.name,
            reason=f"Agent '{best.name}' selected for {required_capability.value} (priority={best.priority}).",
            confidence=0.95,
        )

    @property
    def agent_count(self) -> int:
        """Return the number of registered agents."""
        return len(self._agents)


# =====================================================================
# 2. Plan-and-Execute Orchestrator
# =====================================================================

class PlanStep(BaseModel):
    """A single step in a clinical execution plan."""
    step_id: str = Field(default_factory=lambda: f"STEP-{uuid.uuid4().hex[:6]}")
    description: str
    required_capability: AgentCapability
    tool_name: Optional[str] = None
    tool_kwargs: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"
    result: Optional[str] = None


class ExecutionPlan(BaseModel):
    """A full multi-step clinical execution plan."""
    plan_id: str = Field(default_factory=lambda: f"PLAN-{uuid.uuid4().hex[:8]}")
    goal: str
    steps: List[PlanStep]
    overall_status: str = "PENDING"


class PlanAndExecuteOrchestrator:
    """
    Decomposes a complex clinical goal into ordered sub-tasks,
    routes each to the appropriate specialist agent via the supervisor,
    invokes tools from the registry, and records episodes in reflective memory.
    """

    def __init__(self, supervisor: SupervisorAgentRouter) -> None:
        self.supervisor = supervisor

    def plan(self, goal: str, steps: List[PlanStep]) -> ExecutionPlan:
        """Create an execution plan from a goal and ordered steps."""
        return ExecutionPlan(goal=goal, steps=steps)

    def execute(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Execute all steps in order, invoking tools and recording memory."""
        for step in plan.steps:
            step.status = "RUNNING"

            # Route to the best agent
            routing = self.supervisor.route(step.required_capability)

            # If a tool is specified, invoke it
            if step.tool_name and agent_tool_registry.get_schema(step.tool_name):
                try:
                    tool_result = agent_tool_registry.invoke(step.tool_name, **step.tool_kwargs)
                    step.result = f"[{routing.selected_agent_name}] Tool '{step.tool_name}' returned: {tool_result}"
                    step.status = "COMPLETED"
                    reward = 1.0
                except Exception as exc:
                    step.result = f"[{routing.selected_agent_name}] Tool '{step.tool_name}' failed: {exc}"
                    step.status = "FAILED"
                    reward = -1.0
            else:
                step.result = f"[{routing.selected_agent_name}] {step.description} — executed."
                step.status = "COMPLETED"
                reward = 0.5

            # Record episode in reflective memory
            agent_reflective_memory.record_episode(
                episode_id=step.step_id,
                agent_name=routing.selected_agent_name,
                action_taken=step.description,
                outcome=step.result or "",
                reward_signal=reward,
            )

        all_done = all(s.status == "COMPLETED" for s in plan.steps)
        plan.overall_status = "COMPLETED" if all_done else "PARTIAL_FAILURE"
        return plan


# ---------------------------------------------------------------------------
# Global singletons with pre-registered clinical agents
# ---------------------------------------------------------------------------
supervisor_router = SupervisorAgentRouter()

supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGT-TRIAGE-01", name="EDTriageAgent",
    capabilities=[AgentCapability.TRIAGE, AgentCapability.SAFETY], priority=10,
))
supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGT-PHARMA-01", name="PrescribingSafetyAgent",
    capabilities=[AgentCapability.PHARMACY, AgentCapability.SAFETY], priority=9,
))
supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGT-RAD-01", name="RadiologyPrereaderAgent",
    capabilities=[AgentCapability.RADIOLOGY], priority=8,
))
supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGT-DISCHARGE-01", name="DischargeSummarizerAgent",
    capabilities=[AgentCapability.DISCHARGE], priority=7,
))
supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGT-BILLING-01", name="BillingAgent",
    capabilities=[AgentCapability.BILLING], priority=6,
))
supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGT-SCHED-01", name="SchedulingAgent",
    capabilities=[AgentCapability.SCHEDULING], priority=5,
))

plan_and_execute_orchestrator = PlanAndExecuteOrchestrator(supervisor_router)
