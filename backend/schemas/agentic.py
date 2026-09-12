"""Pydantic schemas for Level 14 Autonomous Multi-Agent Deliberative Clinical Consensus & Metacognitive HTN Orchestration OS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DeliberationRequest(BaseModel):
    """Request to initiate Dung dialectical clinical consensus deliberation."""

    patient_id: str = Field(..., description="Target patient identifier")
    clinical_case: Dict[str, Any] = Field(..., description="Clinical case attributes (biomarkers, vitals, meds, directives)")


class DeliberationResponse(BaseModel):
    """Result of multi-specialist dialectical consensus deliberation."""

    session_id: str
    patient_id: str
    consensus_action: str
    rationale_summary: str
    grounded_consensus_arguments: List[Dict[str, Any]]
    defeated_arguments: List[Dict[str, Any]]
    attacks_evaluated: List[Dict[str, Any]]
    timestamp: str


class GeneratePlanRequest(BaseModel):
    """Request to decompose clinical goal into Hierarchical Task Network."""

    patient_id: str = Field(..., description="Target patient identifier")
    goal: str = Field(..., description="High-level clinical goal (e.g. SEPTIC_SHOCK_RESUSCITATION)")
    initial_state: Dict[str, Any] = Field(default_factory=dict, description="Initial patient physiological state")


class PlanResponse(BaseModel):
    """Complete HTN clinical execution tree."""

    plan_id: str
    patient_id: str
    goal: str
    compound_tasks: List[Dict[str, Any]]
    replanned_count: int
    replanning_history: List[Dict[str, Any]]
    created_at: str


class ReplanRequest(BaseModel):
    """Request to trigger dynamic reactive replanning on telemetry interrupt."""

    plan_id: str = Field(..., description="Target HTN plan ID")
    telemetry_interrupt: Dict[str, Any] = Field(..., description="New real-time telemetry (map, spo2, lactate, hr)")


class ExecuteGatedActionRequest(BaseModel):
    """Request to evaluate action against deterministic Pre-Action Invariants and execute."""

    action_name: str = Field(..., description="Clinical action name (e.g. prescribe_medication)")
    parameters: Dict[str, Any] = Field(..., description="Action parameters (drug, dose, route)")
    patient_profile: Dict[str, Any] = Field(..., description="Patient physiological profile (conditions, allergies, egfr, pregnant)")


class GatedActionResponse(BaseModel):
    """Result of invariant evaluation and sandboxed execution."""

    allowed: bool
    status: str
    action_name: str
    parameters: Dict[str, Any]
    violations: List[Dict[str, Any]]
    execution_output: Optional[Any] = None
    audit_token: Optional[str] = None
    timestamp: str


class CalibrateMetacognitionRequest(BaseModel):
    """Request to evaluate epistemic uncertainty and human escalation requirements."""

    clinical_claim: str = Field(..., description="Hypothesized diagnosis or proposed intervention")
    available_evidence: List[str] = Field(..., description="Documented clinical evidence backing the claim")
    missing_observations: List[str] = Field(..., description="Unobserved or pending critical diagnostic tests")
    acuity_level: str = Field("HIGH", description="CRITICAL, HIGH, MODERATE, LOW")


class MetacognitionResponse(BaseModel):
    """Epistemic uncertainty assessment and autonomous safety yield brief."""

    assessment_id: str
    clinical_claim: str
    epistemic_uncertainty: float
    safe_threshold: float
    autonomous_execution_permitted: bool
    yield_decision: str
    identified_knowledge_gaps: List[str]
    clinician_escalation_brief: Optional[Dict[str, Any]] = None
    timestamp: str


class AgenticHealthResponse(BaseModel):
    """Operational status of the autonomous agentic orchestration layer."""

    status: str = "HEALTHY"
    engine: str = "AUTONOMOUS_DELIBERATIVE_METANET_AGENT_OS"
    deliberation_engine: str = "DUNG_ABSTRACT_ARGUMENTATION_FRAMEWORK"
    planner_engine: str = "HIERARCHICAL_TASK_NETWORK_REACTIVE_REPLANNER"
    invariant_gate: str = "DETERMINISTIC_PRE_ACTION_SAFETY_BARRIER"
    metacognitive_calibrator: str = "EPISTEMIC_UNCERTAINTY_SAFETY_YIELD"
