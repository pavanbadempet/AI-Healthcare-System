"""
FastAPI Router for Level 8 Frontier Clinical AI & Neuro-Symbolic Reasoning:
- Multi-Agent Clinical Consensus Delphi Swarm with Adversarial Falsification
- Neuro-Symbolic Clinical Ontology Reasoner & Axiomatic Proof Engine
- Clinical Semantic Uncertainty & Epistemic Hallucination Guard
- Medical Tree-of-Thoughts (Med-ToT) with Expected Value of Diagnostic Information (EVDI)
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from backend.ai_engine.adversarial_delphi_swarm import delphi_swarm_engine
from backend.ai_engine.clinical_semantic_uncertainty import semantic_uncertainty_engine
from backend.ai_engine.medical_tree_of_thoughts import medical_tot_engine
from backend.ai_engine.neurosymbolic_clinical_reasoner import neurosymbolic_reasoner
from backend.schemas.frontier_clinical_ai import (
    CognitiveBiasAlertSchema,
    DelphiSwarmRequest,
    DelphiSwarmResponse,
    DiagnosticEvaluationNodeSchema,
    MedTotPlannerRequest,
    MedTotPlannerResponse,
    NeurosymbolicProofRequest,
    NeurosymbolicProofResponse,
    SemanticClusterSchema,
    SemanticUncertaintyRequest,
    SemanticUncertaintyResponse,
    VerificationFactorSchema,
)

logger = logging.getLogger("backend.frontier_clinical_ai_routes")

router = APIRouter(prefix="/v1/clinical-ai", tags=["Frontier Clinical AI & Neuro-Symbolic Reasoning"])


# ---------------------------------------------------------------------------
# 1. Multi-Agent Delphi Swarm Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/delphi-swarm/deliberate",
    response_model=DelphiSwarmResponse,
    summary="Execute Multi-Round Clinical Delphi Consensus with Adversarial Falsification",
)
def deliberate_delphi_swarm(payload: DelphiSwarmRequest) -> DelphiSwarmResponse:
    """
    Executes an iterative consensus deliberation among Internist, Pharmacologist, Intensivist,
    and Adversarial Skeptic agents, tracking Kendall concordance and eliminating cognitive traps.
    """
    try:
        patient_case = {
            "patient_id": payload.patient_id,
            "symptoms": payload.symptoms,
            "vitals": payload.vitals,
            "labs": payload.labs,
            "current_medications": payload.current_medications,
        }
        res = delphi_swarm_engine.execute_delphi_deliberation(
            patient_case=patient_case,
            max_rounds=payload.max_rounds,
        )
        return DelphiSwarmResponse(
            consensus_reached=res.consensus_reached,
            final_kendall_w=res.final_kendall_w,
            rounds_executed=res.rounds_executed,
            primary_unified_diagnosis=res.primary_unified_diagnosis,
            calibrated_consensus_confidence=res.calibrated_consensus_confidence,
            dissenting_opinions=res.dissenting_opinions,
            cognitive_bias_warnings=[
                CognitiveBiasAlertSchema(
                    bias_type=b.bias_type,
                    description=b.description,
                    high_acuity_mimickers=b.high_acuity_mimickers,
                    falsification_tests=b.falsification_tests,
                )
                for b in res.cognitive_bias_warnings
            ],
            prioritized_care_plan=res.prioritized_care_plan,
            mandatory_falsification_tests=res.mandatory_falsification_tests,
            timestamp_iso=res.timestamp_iso,
        )
    except Exception as e:
        logger.error(f"Delphi swarm deliberation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delphi swarm deliberation error: {str(e)}",
        )


# ---------------------------------------------------------------------------
# 2. Neuro-Symbolic Clinical Reasoner Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/neurosymbolic/verify-plan",
    response_model=NeurosymbolicProofResponse,
    summary="Verify Clinical Plan via First-Order Logic & CPIC/FDA Medical Axioms",
)
def verify_clinical_plan(payload: NeurosymbolicProofRequest) -> NeurosymbolicProofResponse:
    """
    Formally proves the safety of proposed medications and interventions against a compiled
    axiomatic ontology, returning a cryptographic proof certificate or minimal UnsatCore.
    """
    try:
        cert = neurosymbolic_reasoner.verify_treatment_plan(
            patient_profile=payload.patient_profile,
            proposed_medications_and_actions=payload.proposed_medications_and_actions,
        )
        return NeurosymbolicProofResponse(
            is_provably_safe=cert.is_provably_safe,
            proof_token=cert.proof_token,
            verified_axioms_evaluated=cert.verified_axioms_evaluated,
            active_premises=cert.active_premises,
            unsat_core_violations=cert.unsat_core_violations,
            remedial_clinical_actions=cert.remedial_clinical_actions,
            formal_proof_trace=cert.formal_proof_trace,
            timestamp_iso=cert.timestamp_iso,
        )
    except Exception as e:
        logger.error(f"Neuro-symbolic verification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Neuro-symbolic verification error: {str(e)}",
        )


# ---------------------------------------------------------------------------
# 3. Clinical Semantic Uncertainty Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/uncertainty/semantic-entropy",
    response_model=SemanticUncertaintyResponse,
    summary="Compute Semantic Entropy & Generate Chain-of-Verification Plan",
)
def evaluate_semantic_uncertainty(payload: SemanticUncertaintyRequest) -> SemanticUncertaintyResponse:
    """
    Clusters candidate clinical reasoning trajectories into semantic equivalence classes,
    calculates Farquhar semantic entropy, and decomposes epistemic vs aleatoric uncertainty.
    """
    try:
        profile = semantic_uncertainty_engine.evaluate_semantic_entropy(
            candidate_trajectories=payload.candidate_trajectories,
            baseline_patient_entropy=payload.baseline_patient_entropy,
        )
        return SemanticUncertaintyResponse(
            semantic_entropy=profile.semantic_entropy,
            is_epistemically_safe=profile.is_epistemically_safe,
            entropy_threshold=profile.entropy_threshold,
            uncertainty_decomposition=profile.uncertainty_decomposition,
            semantic_clusters=[
                SemanticClusterSchema(
                    cluster_id=c.cluster_id,
                    canonical_concept=c.canonical_concept,
                    member_statements=c.member_statements,
                    probability_weight=c.probability_weight,
                    cluster_entropy_contribution=c.cluster_entropy_contribution,
                )
                for c in profile.semantic_clusters
            ],
            hallucination_risk_level=profile.hallucination_risk_level,
            chain_of_verification_plan=[
                VerificationFactorSchema(
                    claim_statement=v.claim_statement,
                    verification_question=v.verification_question,
                    evidence_source=v.evidence_source,
                    verification_status=v.verification_status,
                    rationale=v.rationale,
                )
                for v in profile.chain_of_verification_plan
            ],
            timestamp_iso=profile.timestamp_iso,
        )
    except Exception as e:
        logger.error(f"Semantic uncertainty evaluation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic uncertainty error: {str(e)}",
        )


# ---------------------------------------------------------------------------
# 4. Medical Tree-of-Thoughts (Med-ToT) Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/med-tot/optimal-diagnostic-path",
    response_model=MedTotPlannerResponse,
    summary="Search Medical Tree-of-Thoughts & Rank Tests by Expected Value of Information",
)
def optimize_diagnostic_pathway(payload: MedTotPlannerRequest) -> MedTotPlannerResponse:
    """
    Performs tree search over candidate diagnostic actions, computing Expected Value of
    Diagnostic Information (EVDI) and selecting the Pareto-optimal sequence of workup tests.
    """
    try:
        plan = medical_tot_engine.optimize_diagnostic_pathway(
            differential_diagnosis_probabilities=payload.differential_diagnosis_probabilities,
            patient_contraindications=payload.patient_contraindications,
        )
        return MedTotPlannerResponse(
            initial_differential_entropy=plan.initial_differential_entropy,
            primary_suspected_diagnosis=plan.primary_suspected_diagnosis,
            prior_probabilities=plan.prior_probabilities,
            ranked_diagnostic_actions=[
                DiagnosticEvaluationNodeSchema(
                    test_id=n.test_id,
                    test_name=n.test_name,
                    modality=n.modality,
                    expected_entropy_reduction=n.expected_entropy_reduction,
                    expected_value_of_information=n.expected_value_of_information,
                    composite_utility_score=n.composite_utility_score,
                    turnaround_time_minutes=n.turnaround_time_minutes,
                    radiation_burden_msv=n.radiation_burden_msv,
                    pareto_rank=n.pareto_rank,
                    clinical_rationale=n.clinical_rationale,
                )
                for n in plan.ranked_diagnostic_actions
            ],
            recommended_immediate_next_test=plan.recommended_immediate_next_test,
            expected_post_test_entropy=plan.expected_post_test_entropy,
            composite_efficiency_gain_pct=plan.composite_efficiency_gain_pct,
            timestamp_iso=plan.timestamp_iso,
        )
    except Exception as e:
        logger.error(f"Med-ToT pathway optimization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Med-ToT optimization error: {str(e)}",
        )


@router.get("/health", summary="Health Check for Frontier Clinical AI Systems")
def health_check() -> Dict[str, Any]:
    """
    Subsystem readiness and clinical reasoning safety status.
    """
    return {
        "status": "HEALTHY",
        "tier": "LEVEL_8_UNIFIED_CLINICAL_INTELLIGENCE_OS",
        "subsystems": {
            "delphi_swarm_engine": "ACTIVE",
            "neurosymbolic_reasoner": "ACTIVE",
            "semantic_uncertainty_engine": "ACTIVE",
            "medical_tot_engine": "ACTIVE",
        },
        "reasoning_frameworks": [
            "Med-Delphi-Adversarial-Consensus",
            "FOL-SMT-Axiomatic-Prover",
            "Farquhar-Semantic-Entropy-CoVe",
            "POMDP-Tree-of-Thoughts-EVDI",
        ],
    }
