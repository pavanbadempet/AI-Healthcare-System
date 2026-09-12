"""
Pydantic Schemas for Level 8 Frontier Clinical AI & Neuro-Symbolic Reasoning:
- Multi-Agent Clinical Consensus Delphi Swarm with Adversarial Falsification
- Neuro-Symbolic Clinical Ontology Reasoner & Axiomatic Proof Engine
- Clinical Semantic Uncertainty & Epistemic Hallucination Guard
- Medical Tree-of-Thoughts (Med-ToT) with Expected Value of Diagnostic Information (EVDI)
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Multi-Agent Delphi Swarm Schemas
# ---------------------------------------------------------------------------

class CognitiveBiasAlertSchema(BaseModel):
    bias_type: str = Field(..., description="Type of cognitive trap detected")
    description: str = Field(..., description="Clinical explanation of bias risk")
    high_acuity_mimickers: List[str] = Field(..., description="Dangerous mimicker diagnoses to rule out")
    falsification_tests: List[str] = Field(..., description="Required objective tests to falsify bias")


class DelphiSwarmRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient record identifier")
    symptoms: List[str] = Field(..., description="Presenting symptoms and clinical signs")
    vitals: Dict[str, Any] = Field(default_factory=dict, description="Objective vitals measurements")
    labs: Dict[str, Any] = Field(default_factory=dict, description="Current laboratory values")
    current_medications: List[str] = Field(default_factory=list, description="Active medication list")
    max_rounds: int = Field(default=3, description="Maximum Delphi consensus rounds")


class DelphiSwarmResponse(BaseModel):
    consensus_reached: bool = Field(..., description="Whether panel achieved Kendall concordance threshold")
    final_kendall_w: float = Field(..., description="Kendall's coefficient of concordance (0 to 1)")
    rounds_executed: int = Field(..., description="Number of deliberation rounds completed")
    primary_unified_diagnosis: str = Field(..., description="Synthesized working diagnosis")
    calibrated_consensus_confidence: float = Field(..., description="Mean calibrated specialist confidence")
    dissenting_opinions: List[str] = Field(..., description="Explicit preserved minority/adversarial challenges")
    cognitive_bias_warnings: List[CognitiveBiasAlertSchema] = Field(..., description="Detected cognitive biases")
    prioritized_care_plan: List[str] = Field(..., description="Consensus recommended interventions")
    mandatory_falsification_tests: List[str] = Field(..., description="Adversarial tests required before closure")
    timestamp_iso: str = Field(..., description="Deliberation completion timestamp")


# ---------------------------------------------------------------------------
# 2. Neuro-Symbolic Clinical Reasoner Schemas
# ---------------------------------------------------------------------------

class NeurosymbolicProofRequest(BaseModel):
    patient_profile: Dict[str, Any] = Field(..., description="Structured patient profile with labs, PGx, conditions")
    proposed_medications_and_actions: List[str] = Field(..., description="Candidate clinical interventions to verify")


class NeurosymbolicProofResponse(BaseModel):
    is_provably_safe: bool = Field(..., description="Whether proposed plan is mathematically consistent with medical axioms")
    proof_token: str = Field(..., description="Cryptographic proof token")
    verified_axioms_evaluated: int = Field(..., description="Number of formal axioms checked")
    active_premises: List[str] = Field(..., description="Symbolic clinical logic predicates extracted")
    unsat_core_violations: List[str] = Field(..., description="Unsatisfiable core detailing violated medical rules")
    remedial_clinical_actions: List[str] = Field(..., description="Guideline-directed safe substitutions")
    formal_proof_trace: List[str] = Field(..., description="Step-by-step logic deduction log")
    timestamp_iso: str = Field(..., description="Verification timestamp")


# ---------------------------------------------------------------------------
# 3. Clinical Semantic Uncertainty Schemas
# ---------------------------------------------------------------------------

class SemanticClusterSchema(BaseModel):
    cluster_id: str = Field(..., description="Cluster identifier")
    canonical_concept: str = Field(..., description="Normalized medical entity")
    member_statements: List[str] = Field(..., description="Equivalence class trajectory members")
    probability_weight: float = Field(..., description="Cluster empirical probability")
    cluster_entropy_contribution: float = Field(..., description="Entropy contribution of this cluster")


class VerificationFactorSchema(BaseModel):
    claim_statement: str = Field(..., description="High-entropy clinical claim")
    verification_question: str = Field(..., description="Targeted falsification sub-question")
    evidence_source: str = Field(..., description="Medical knowledge authority")
    verification_status: str = Field(..., description="Verification verdict")
    rationale: str = Field(..., description="Detailed verification context")


class SemanticUncertaintyRequest(BaseModel):
    candidate_trajectories: List[str] = Field(..., description="Candidate clinical diagnostic reasoning strings")
    baseline_patient_entropy: float = Field(default=0.20, description="Inherent patient biological noise baseline")


class SemanticUncertaintyResponse(BaseModel):
    semantic_entropy: float = Field(..., description="Farquhar semantic entropy across candidate paths")
    is_epistemically_safe: bool = Field(..., description="Whether semantic entropy is below safety ceiling")
    entropy_threshold: float = Field(..., description="Configured maximum permissible entropy")
    uncertainty_decomposition: Dict[str, float] = Field(..., description="Epistemic vs aleatoric percentage split")
    semantic_clusters: List[SemanticClusterSchema] = Field(..., description="Identified semantic equivalence clusters")
    hallucination_risk_level: str = Field(..., description="Risk tier: LOW, MODERATE, or CRITICAL_HALLUCINATION_HAZARD")
    chain_of_verification_plan: List[VerificationFactorSchema] = Field(..., description="Chain-of-Verification sub-questions")
    timestamp_iso: str = Field(..., description="Analysis timestamp")


# ---------------------------------------------------------------------------
# 4. Medical Tree-of-Thoughts (Med-ToT) Schemas
# ---------------------------------------------------------------------------

class DiagnosticEvaluationNodeSchema(BaseModel):
    test_id: str = Field(..., description="Catalog identifier")
    test_name: str = Field(..., description="Clinical test or imaging study")
    modality: str = Field(..., description="Diagnostic modality")
    expected_entropy_reduction: float = Field(..., description="Expected bits of diagnostic entropy reduction")
    expected_value_of_information: float = Field(..., description="Calculated EVDI score")
    composite_utility_score: float = Field(..., description="Net utility factoring radiation, cost, and time")
    turnaround_time_minutes: int = Field(..., description="Time to results in minutes")
    radiation_burden_msv: float = Field(..., description="Ionizing radiation in mSv")
    pareto_rank: int = Field(..., description="Pareto efficiency ranking")
    clinical_rationale: str = Field(..., description="Clinical yield justification")


class MedTotPlannerRequest(BaseModel):
    differential_diagnosis_probabilities: Dict[str, float] = Field(..., description="Differential probability distribution")
    patient_contraindications: List[str] = Field(default_factory=list, description="Patient specific contraindications")


class MedTotPlannerResponse(BaseModel):
    initial_differential_entropy: float = Field(..., description="Shannon entropy of prior differential distribution")
    primary_suspected_diagnosis: str = Field(..., description="Highest prior probability pathology")
    prior_probabilities: Dict[str, float] = Field(..., description="Normalized prior distribution")
    ranked_diagnostic_actions: List[DiagnosticEvaluationNodeSchema] = Field(..., description="Ranked diagnostic tests")
    recommended_immediate_next_test: str = Field(..., description="Pareto-optimal next diagnostic test to order")
    expected_post_test_entropy: float = Field(..., description="Residual entropy after executing top test")
    composite_efficiency_gain_pct: float = Field(..., description="Percentage entropy reduction")
    timestamp_iso: str = Field(..., description="Plan generation timestamp")
