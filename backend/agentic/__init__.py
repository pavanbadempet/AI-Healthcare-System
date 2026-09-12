"""Level 14 Autonomous Multi-Agent Deliberative Clinical Consensus & Metacognitive HTN Orchestration OS.

Exposes:
- DialecticalConsensusEngine: Dung's abstract argumentation framework for multi-specialist clinical consensus.
- HTNClinicalPlanner: Hierarchical task networks with reactive telemetry replanning in sub-5ms.
- PreActionInvariantGate: Deterministic 5-category medical safety barrier preventing unsafe tool calls.
- MetacognitiveCalibrator: Epistemic uncertainty calibration and autonomous human clinician escalation.
"""

from backend.agentic.dialectical_consensus import (
    ArgumentAttack,
    ClinicalArgument,
    DialecticalConsensusEngine,
    DungArgumentationFramework,
    SpecialistRole,
)
from backend.agentic.htn_planner import (
    CompoundClinicalTask,
    HTNClinicalPlan,
    HTNClinicalPlanner,
    PrimitiveClinicalAction,
    TaskStatus,
)
from backend.agentic.invariant_execution_gate import (
    InvariantExecutionResult,
    InvariantType,
    InvariantViolation,
    PreActionInvariantGate,
)
from backend.agentic.metacognitive_calibrator import (
    MetacognitiveAssessment,
    MetacognitiveCalibrator,
)

__all__ = [
    "DialecticalConsensusEngine",
    "DungArgumentationFramework",
    "ClinicalArgument",
    "ArgumentAttack",
    "SpecialistRole",
    "HTNClinicalPlanner",
    "HTNClinicalPlan",
    "CompoundClinicalTask",
    "PrimitiveClinicalAction",
    "TaskStatus",
    "PreActionInvariantGate",
    "InvariantExecutionResult",
    "InvariantViolation",
    "InvariantType",
    "MetacognitiveCalibrator",
    "MetacognitiveAssessment",
]
