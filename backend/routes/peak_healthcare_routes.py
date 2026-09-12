"""
FastAPI Router for Peak Healthcare Capabilities:
- Clinical Digital Twin (10-Year Multi-Organ Trajectory Simulation)
- Precision Pharmacogenomics (CPIC Gene-Drug Prescribing)
- Autonomous Multi-Specialist Clinical Consensus Council
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.agents.clinical_consensus_council import clinical_council
from backend.causal_engine import causal_engine
from backend.clinical_cybernetics import cybernetics_engine
from backend.clinical_digital_twin import digital_twin_engine
from backend.clinical_guardrails import clinical_guardrails
from backend.multimodal_fusion import multimodal_engine
from backend.precision_pharmacogenomics import pharmacogenomics_engine
from backend.schemas.peak_healthcare import (
    CausalCounterfactualRequest,
    CausalCounterfactualResponse,
    ClinicalCouncilConsensusResponse,
    ClinicalCouncilDeliberationRequest,
    CyberneticAssimilationRequest,
    CyberneticAssimilationResponse,
    DigitalTwinSimulationRequest,
    DigitalTwinSimulationResponse,
    FormalSafetyVerificationRequest,
    FormalSafetyVerificationResponse,
    MultimodalEmbeddingResponse,
    MultimodalPatientProfile,
    PharmacogenomicEvaluationRequest,
    PharmacogenomicEvaluationResponse,
)

logger = logging.getLogger("backend.peak_healthcare_routes")

router = APIRouter(prefix="/v1", tags=["Peak Healthcare Intelligence"])


@router.post("/digital-twin/simulate", response_model=DigitalTwinSimulationResponse, summary="Simulate 10-Year Multi-Organ Clinical Trajectory")
def simulate_digital_twin(request: DigitalTwinSimulationRequest) -> DigitalTwinSimulationResponse:
    """
    Executes continuous state-space simulation of a patient's digital twin across 10 years
    for Cardiovascular, Renal, Metabolic, and Hepatic organ systems.
    """
    try:
        return digital_twin_engine.simulate_10_year_trajectory(request)
    except Exception as e:
        logger.error("Digital twin simulation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Digital twin simulation failed: {str(e)}"
        )


@router.post("/pharmacogenomics/evaluate", response_model=PharmacogenomicEvaluationResponse, summary="Evaluate CPIC Precision Pharmacogenomics")
def evaluate_pharmacogenomics(request: PharmacogenomicEvaluationRequest) -> PharmacogenomicEvaluationResponse:
    """
    Cross-references patient CYP2D6, CYP2C19, SLCO1B1, and HLA alleles to provide actionable CPIC Level A dosing guidance.
    """
    try:
        return pharmacogenomics_engine.evaluate(request)
    except Exception as e:
        logger.error("Pharmacogenomic evaluation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pharmacogenomic evaluation failed: {str(e)}"
        )


@router.post("/clinical-council/deliberate", response_model=ClinicalCouncilConsensusResponse, summary="Deliberate Complex Cases with Multi-Specialist AI Council")
def deliberate_clinical_council(request: ClinicalCouncilDeliberationRequest) -> ClinicalCouncilConsensusResponse:
    """
    Spawns an autonomous multi-specialist medical council (Cardiology, Endocrinology, Nephrology, Pharmacy, Safety)
    to deliberate and synthesize a unified, evidence-based care plan.
    """
    try:
        return clinical_council.deliberate_and_synthesize(request)
    except Exception as e:
        logger.error("Clinical council deliberation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clinical council deliberation failed: {str(e)}"
        )


@router.post("/cybernetics/assimilate", response_model=CyberneticAssimilationResponse, summary="Assimilate Streaming Telemetry into Digital Twin via UKF")
def assimilate_cybernetic_telemetry(request: CyberneticAssimilationRequest) -> CyberneticAssimilationResponse:
    """
    Ingests real-time streaming telemetry (HR, MAP, SpO2, Glucose, eGFR proxy) and executes
    an Unscented Kalman Filter assimilation step to estimate hidden multi-organ reserves and parameter drift.
    """
    try:
        return cybernetics_engine.assimilate_telemetry(request)
    except Exception as e:
        logger.error("Cybernetic assimilation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cybernetic assimilation failed: {str(e)}"
        )


@router.post("/causal/counterfactual", response_model=CausalCounterfactualResponse, summary="Evaluate Causal Counterfactual Trajectory via do-Calculus")
def evaluate_causal_counterfactual(request: CausalCounterfactualRequest) -> CausalCounterfactualResponse:
    """
    Evaluates Pearl Level-3 Structural Causal Models (SCMs) with do-calculus to infer
    individual treatment effects (ITE) and counterfactual trajectories under targeted interventions.
    """
    try:
        return causal_engine.evaluate_counterfactual(request)
    except Exception as e:
        logger.error("Causal counterfactual evaluation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Causal counterfactual evaluation failed: {str(e)}"
        )


@router.post("/safety/verify-regimen", response_model=FormalSafetyVerificationResponse, summary="Formally Prove Medication Safety Invariants")
def verify_safety_regimen(request: FormalSafetyVerificationRequest) -> FormalSafetyVerificationResponse:
    """
    Mathematically verifies physiological safety bounds, renal clearance floors, hyperkalemia gates,
    and cumulative QTc prolongation to formally certify or reject a proposed pharmacotherapeutic regimen.
    """
    try:
        return clinical_guardrails.verify_regimen(request)
    except Exception as e:
        logger.error("Formal safety verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Formal safety verification failed: {str(e)}"
        )


@router.post("/multimodal/embed-patient", response_model=MultimodalEmbeddingResponse, summary="Project Multimodal Patient State into Unified Latent Manifold")
def embed_multimodal_patient(request: MultimodalPatientProfile) -> MultimodalEmbeddingResponse:
    """
    Projects heterogeneous vitals, diagnostic tokens, pharmacogenomic variants, and imaging features
    into a unified 128-dimensional clinical latent space to discover matched phenotypic cohorts.
    """
    try:
        return multimodal_engine.embed_patient(request)
    except Exception as e:
        logger.error("Multimodal embedding failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multimodal embedding failed: {str(e)}"
        )

