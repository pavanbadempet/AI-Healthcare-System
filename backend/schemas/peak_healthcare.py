"""
Pydantic Schemas for Peak Clinical Digital Twin, Pharmacogenomics, and Multi-Agent Council.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class OrganSystemTrajectory(BaseModel):
    """Longitudinal 10-year trajectory simulation for a specific organ system."""
    organ: str = Field(..., description="Target organ system: cardiovascular, renal, metabolic, hepatic, neuro")
    baseline_health_score: float = Field(..., ge=0.0, le=100.0, description="Baseline organ function index (0-100)")
    projected_score_without_intervention: List[float] = Field(..., description="Annual projected health score without intervention (Years 1-10)")
    projected_score_with_intervention: List[float] = Field(..., description="Annual projected health score with targeted intervention (Years 1-10)")
    relative_risk_reduction: float = Field(..., description="Calculated percentage risk reduction at year 10")
    key_drivers: List[str] = Field(default_factory=list, description="Primary physiological and biomarker drivers")


class DigitalTwinSimulationRequest(BaseModel):
    """Request to simulate 10-year clinical trajectory on a patient's digital twin."""
    patient_id: str
    age: float = Field(..., ge=0, le=120)
    gender: str = "unknown"
    bmi: float = 25.0
    systolic_bp: float = 120.0
    fasting_glucose: float = 95.0
    egfr: float = 90.0
    ldl_cholesterol: float = 100.0
    hba1c: float = 5.6
    smoking_status: str = "never"
    active_diagnoses: List[str] = Field(default_factory=list)
    proposed_interventions: List[str] = Field(default_factory=list, description="List of proposed pharmacological or lifestyle interventions")


class DigitalTwinSimulationResponse(BaseModel):
    """Full 10-year multi-organ digital twin simulation output."""
    patient_id: str
    simulation_horizon_years: int = 10
    cardiovascular: OrganSystemTrajectory
    renal: OrganSystemTrajectory
    metabolic: OrganSystemTrajectory
    hepatic: OrganSystemTrajectory
    overall_longevity_gain_years: float = Field(..., description="Estimated quality-adjusted life years (QALY) gained")
    top_recommended_pathway: str
    simulation_confidence_interval: str = "95% CI (Monte Carlo N=10,000)"


class PharmacogenomicProfile(BaseModel):
    """Patient pharmacogenomic gene variant profile."""
    patient_id: str
    cyp2d6_phenotype: str = Field(default="Normal Metabolizer (*1/*1)", description="CYP2D6 metabolic phenotype")
    cyp2c19_phenotype: str = Field(default="Rapid Metabolizer (*1/*17)", description="CYP2C19 metabolic phenotype")
    slco1b1_genotype: str = Field(default="Normal Function (*1a/*1a)", description="SLCO1B1 statin transport genotype")
    vkorc1_genotype: str = Field(default="G/G (Standard Warfarin Sensitivity)", description="VKORC1 sensitivity")
    hla_b5701_status: str = Field(default="Negative", description="HLA-B*5701 abacavir hypersensitivity")


class PharmacogenomicEvaluationRequest(BaseModel):
    """Request to evaluate drug metabolism and gene-drug interactions."""
    patient_id: str
    proposed_medications: List[str]
    genomic_profile: PharmacogenomicProfile


class DrugMetabolismReport(BaseModel):
    """Precision metabolism and dosage adjustment report for a specific drug."""
    drug_name: str
    relevant_gene: str
    metabolic_status: str
    clinical_implication: str
    recommended_dosage_adjustment: str
    adverse_reaction_risk: str
    cpic_guideline_level: str = "Level A (Actionable)"


class PharmacogenomicEvaluationResponse(BaseModel):
    """Comprehensive pharmacogenomic precision prescribing analysis."""
    patient_id: str
    total_drugs_analyzed: int
    evaluations: List[DrugMetabolismReport]
    has_critical_contraindications: bool


class SpecialistOpinion(BaseModel):
    """Individual clinical deliberation from an autonomous specialist agent."""
    specialist_role: str = Field(..., description="Role: Cardiologist, Endocrinologist, Nephrologist, Pharmacist, Patient Safety Officer")
    diagnostic_assessment: str
    recommended_actions: List[str]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    contraindication_flags: List[str] = Field(default_factory=list)


class ClinicalCouncilDeliberationRequest(BaseModel):
    """Request for autonomous multi-specialist medical council deliberation."""
    patient_id: str
    clinical_summary: str
    primary_symptoms: List[str]
    vitals_summary: Dict[str, Any]
    lab_results: Dict[str, Any]
    current_medications: List[str]


class ClinicalCouncilConsensusResponse(BaseModel):
    """Final unified consensus synthesized by the medical council."""
    patient_id: str
    council_session_id: str
    consensus_diagnosis: str
    consensus_confidence: float
    specialist_opinions: List[SpecialistOpinion]
    unified_care_plan: List[str]
    critical_safety_alerts: List[str]
    medical_disclaimer: str = "Autonomous Council Deliberation is for clinical decision support and requires physician sign-off."
