"""FastAPI Router for Level 14 Autonomous Multi-Agent Deliberative Clinical Consensus & Metacognitive HTN Orchestration OS."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from backend.agentic.dialectical_consensus import DialecticalConsensusEngine
from backend.agentic.htn_planner import HTNClinicalPlanner
from backend.agentic.invariant_execution_gate import PreActionInvariantGate
from backend.agentic.metacognitive_calibrator import MetacognitiveCalibrator
from backend.schemas.agentic import (
    AgenticHealthResponse,
    CalibrateMetacognitionRequest,
    DeliberationRequest,
    DeliberationResponse,
    ExecuteGatedActionRequest,
    GatedActionResponse,
    GeneratePlanRequest,
    MetacognitionResponse,
    PlanResponse,
    ReplanRequest,
)

logger = logging.getLogger("backend.agentic")

router = APIRouter(
    prefix="/v1/agentic",
    tags=["Autonomous Multi-Agent Deliberative Consensus & HTN Planning"],
)

# Global engine singletons
consensus_engine = DialecticalConsensusEngine()
htn_planner = HTNClinicalPlanner()
invariant_gate = PreActionInvariantGate()
metacognitive_calibrator = MetacognitiveCalibrator()


@router.post("/deliberate", response_model=DeliberationResponse)
def deliberate_clinical_consensus(req: DeliberationRequest) -> DeliberationResponse:
    """Execute multi-specialist virtual tumor board deliberation using Dung's abstract argumentation."""
    result = consensus_engine.deliberate(
        patient_id=req.patient_id,
        clinical_case=req.clinical_case,
    )
    return DeliberationResponse(**result)


@router.post("/htn/plan", response_model=PlanResponse)
def generate_htn_clinical_plan(req: GeneratePlanRequest) -> PlanResponse:
    """Decompose high-level medical goal into Hierarchical Task Network with precondition gates."""
    plan = htn_planner.generate_plan(
        patient_id=req.patient_id,
        goal=req.goal,
        initial_state=req.initial_state,
    )
    return PlanResponse(**plan.to_dict())


@router.post("/htn/replan", response_model=PlanResponse)
def reactive_replan_htn(req: ReplanRequest) -> PlanResponse:
    """Trigger reactive telemetry replanning upon sudden patient deterioration."""
    try:
        plan = htn_planner.reactive_replan(
            plan_id=req.plan_id,
            telemetry_interrupt=req.telemetry_interrupt,
        )
        return PlanResponse(**plan.to_dict())
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/htn/plan/{plan_id}", response_model=PlanResponse)
def get_htn_plan(plan_id: str) -> PlanResponse:
    """Retrieve existing Hierarchical Task Network plan."""
    plan = htn_planner.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found")
    return PlanResponse(**plan.to_dict())


@router.post("/gate/execute", response_model=GatedActionResponse)
def execute_gated_clinical_action(req: ExecuteGatedActionRequest) -> GatedActionResponse:
    """Evaluate proposed clinical action against deterministic safety invariants before execution."""
    res = invariant_gate.validate_and_execute(
        action_name=req.action_name,
        parameters=req.parameters,
        patient_profile=req.patient_profile,
    )
    return GatedActionResponse(**res.to_dict())


@router.get("/gate/audit", response_model=List[Dict[str, Any]])
def get_invariant_audit_log() -> List[Dict[str, Any]]:
    """Retrieve immutable audit trail of all invariant evaluations and blocked actions."""
    return invariant_gate.get_audit_log()


@router.post("/metacognition/calibrate", response_model=MetacognitionResponse)
def calibrate_epistemic_metacognition(req: CalibrateMetacognitionRequest) -> MetacognitionResponse:
    """Evaluate epistemic uncertainty, identify diagnostic gaps, and determine autonomous safety yield."""
    assessment = metacognitive_calibrator.evaluate_epistemic_confidence(
        clinical_claim=req.clinical_claim,
        available_evidence=req.available_evidence,
        missing_observations=req.missing_observations,
        acuity_level=req.acuity_level,
    )
    return MetacognitionResponse(**assessment.to_dict())


@router.get("/health", response_model=AgenticHealthResponse)
def get_agentic_health() -> AgenticHealthResponse:
    """Operational health check for the autonomous agentic orchestration layer."""
    return AgenticHealthResponse(
        status="HEALTHY",
        engine="AUTONOMOUS_DELIBERATIVE_METANET_AGENT_OS",
        deliberation_engine="DUNG_ABSTRACT_ARGUMENTATION_FRAMEWORK",
        planner_engine="HIERARCHICAL_TASK_NETWORK_REACTIVE_REPLANNER",
        invariant_gate="DETERMINISTIC_PRE_ACTION_SAFETY_BARRIER",
        metacognitive_calibrator="EPISTEMIC_UNCERTAINTY_SAFETY_YIELD",
    )
