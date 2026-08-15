"""
FastAPI Router for Peak Healthcare Capabilities:
- Clinical Digital Twin (10-Year Multi-Organ Trajectory Simulation)
- Precision Pharmacogenomics (CPIC Gene-Drug Prescribing)
- Autonomous Multi-Specialist Clinical Consensus Council
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.agents.clinical_consensus_council import clinical_council
from backend.clinical_digital_twin import digital_twin_engine
from backend.precision_pharmacogenomics import pharmacogenomics_engine
from backend.schemas.peak_healthcare import (
    ClinicalCouncilConsensusResponse,
    ClinicalCouncilDeliberationRequest,
    DigitalTwinSimulationRequest,
    DigitalTwinSimulationResponse,
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
