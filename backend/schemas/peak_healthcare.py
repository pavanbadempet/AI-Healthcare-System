"""
Pydantic Schemas for Peak Clinical Digital Twin, Pharmacogenomics, and Multi-Agent Council.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OrganSystemTrajectory(BaseModel):
    """Longitudinal 10-year trajectory simulation for a specific organ system."""
    organ: str = Field(..., description="Target organ system: cardiovascular, renal, metabolic, hepatic, neurovascular, pulmonary")
    baseline_health_score: float = Field(..., ge=0.0, le=100.0, description="Baseline organ function index (0-100)")
    projected_score_without_intervention: List[float] = Field(..., description="Annual projected health score without intervention (Years 1-10)")
    projected_score_with_intervention: List[float] = Field(..., description="Annual projected health score with targeted intervention (Years 1-10)")
    relative_risk_reduction: float = Field(..., description="Calculated percentage risk reduction at year 10")
    key_drivers: List[str] = Field(default_factory=list, description="Primary physiological and biomarker drivers")
    p10_confidence_bound: List[float] = Field(default_factory=list, description="10th percentile (optimistic) trajectory")
    p90_confidence_bound: List[float] = Field(default_factory=list, description="90th percentile (pessimistic) trajectory")
    projected_biomarkers: Dict[str, List[float]] = Field(default_factory=dict, description="Projected physical biomarkers in standard clinical units")


class DigitalTwinSimulationRequest(BaseModel):
    """Request to simulate 10-year clinical trajectory on a patient's digital twin."""
    patient_id: str
    age: float = Field(..., ge=0, le=120)
    gender: str = "unknown"
    bmi: float = 25.0
    systolic_bp: float = 120.0
    diastolic_bp: float = 80.0
    fasting_glucose: float = 95.0
    egfr: float = 90.0
    ldl_cholesterol: float = 100.0
    hba1c: float = 5.6
    smoking_status: str = "never"
    crp_mg_l: float = 1.0
    urine_albumin_creatinine_ratio: float = 30.0
    active_diagnoses: List[str] = Field(default_factory=list)
    proposed_interventions: List[str] = Field(default_factory=list, description="List of proposed pharmacological or lifestyle interventions")
    genomic_profile: Optional[Dict[str, Any]] = Field(default=None, description="Optional pharmacogenomic phenotype mapping")


class DigitalTwinSimulationResponse(BaseModel):
    """Full 10-year multi-organ digital twin simulation output."""
    patient_id: str
    simulation_horizon_years: int = 10
    cardiovascular: OrganSystemTrajectory
    renal: OrganSystemTrajectory
    metabolic: OrganSystemTrajectory
    hepatic: OrganSystemTrajectory
    neurovascular: Optional[OrganSystemTrajectory] = None
    pulmonary: Optional[OrganSystemTrajectory] = None
    overall_longevity_gain_years: float = Field(..., description="Estimated quality-adjusted life years (QALY) gained")
    top_recommended_pathway: str
    simulation_confidence_interval: str = "95% CI (Monte Carlo N=1,000 continuous RK45 ODE)"
    ten_year_mace_risk_untreated: float = Field(default=0.0, description="10-year major adverse cardiac event risk percentage without treatment")
    ten_year_mace_risk_treated: float = Field(default=0.0, description="10-year major adverse cardiac event risk percentage with treatment")
    biophysical_units: Dict[str, str] = Field(default_factory=dict, description="Units for projected biomarkers")


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


# =====================================================================
# Level 4 Autonomous Cyber-Physical Health OS Schemas
# =====================================================================

class TelemetryObservationVector(BaseModel):
    """Real-time streaming telemetry measurement vector for cybernetic assimilation."""
    heart_rate: float = Field(..., ge=20.0, le=250.0, description="Heart rate in beats per minute")
    mean_arterial_pressure: float = Field(..., ge=30.0, le=200.0, description="Mean arterial pressure (MAP) in mmHg")
    spo2: float = Field(..., ge=50.0, le=100.0, description="Pulse oximetry saturation percentage")
    blood_glucose: float = Field(..., ge=20.0, le=600.0, description="Instantaneous blood glucose in mg/dL")
    egfr_proxy: float = Field(..., ge=5.0, le=150.0, description="Real-time estimated renal filtration proxy (mL/min/1.73m^2)")
    observation_timestamp_utc: Optional[str] = None


class KalmanStateEstimate(BaseModel):
    """Posterior hidden physiological state and covariance estimated by the Unscented Kalman Filter."""
    estimated_organ_reserves: Dict[str, float] = Field(..., description="Estimated hidden reserve index (0-100) per organ")
    state_uncertainties_std: Dict[str, float] = Field(..., description="1-sigma uncertainty standard deviation per organ state")
    dynamic_decay_rates: Dict[str, float] = Field(..., description="Patient-adapted continuous biological decay rate constants (kappa_i)")
    filter_innovation_norm: float = Field(..., description="L2 norm of the Kalman innovation residual")
    system_stability_status: str = Field(..., description="Stability classification: STABLE, COMPENSATED_STRESS, CRITICAL_INSTABILITY")


class CyberneticAssimilationRequest(BaseModel):
    """Request to assimilate a new telemetry observation into the patient's continuous state space."""
    patient_id: str
    prior_state: Optional[Dict[str, float]] = Field(default=None, description="Prior hidden state vector (if None, initializes from population baseline)")
    prior_covariance: Optional[Dict[str, float]] = Field(default=None, description="Prior diagonal state covariance variances")
    observation: TelemetryObservationVector
    elapsed_time_hours: float = Field(default=1.0, ge=0.01, le=87600.0, description="Elapsed time delta since previous observation")
    active_interventions: List[str] = Field(default_factory=list, description="Active drug or lifestyle interventions during interval")


class CyberneticAssimilationResponse(BaseModel):
    """Real-time cybernetic assimilation result with updated state and instability alerts."""
    patient_id: str
    posterior_estimate: KalmanStateEstimate
    hemodynamic_instability_detected: bool
    recommended_sampling_interval_sec: int = Field(default=60, description="Adaptive closed-loop sampling frequency")
    clinical_alert: Optional[str] = None


class CausalCounterfactualRequest(BaseModel):
    """Request for Pearl Level-3 Structural Causal Model counterfactual trajectory estimation."""
    patient_id: str
    age: float = Field(..., ge=18, le=120)
    baseline_egfr: float = Field(..., ge=5, le=150)
    baseline_sbp: float = Field(..., ge=70, le=240)
    baseline_hba1c: float = Field(..., ge=4.0, le=16.0)
    bmi: float = Field(..., ge=12.0, le=65.0)
    factual_treatment: str = Field(..., description="Actual treatment received (e.g. standard_of_care, acei_arb)")
    factual_10yr_mace_percent: float = Field(..., ge=0.0, le=100.0, description="Observed or baseline factual 10-year MACE risk")
    factual_egfr_slope_per_year: float = Field(..., description="Observed annual eGFR decline slope (mL/min/1.73m^2/yr)")
    counterfactual_intervention: str = Field(..., description="Target counterfactual do(X=x) intervention (e.g. sglt2i_plus_glp1)")


class CausalCounterfactualResponse(BaseModel):
    """Causal counterfactual deduction comparing factual vs do-calculus outcomes."""
    patient_id: str
    counterfactual_intervention: str
    individual_treatment_effect_mace: float = Field(..., description="Estimated Individual Treatment Effect (ITE) on 10-yr MACE risk percentage reduction")
    individual_treatment_effect_egfr_slope: float = Field(..., description="Estimated ITE on slowing annual eGFR decline (mL/min/yr preserved)")
    counterfactual_10yr_mace_percent: float = Field(..., description="Projected MACE risk under do(X=x)")
    counterfactual_egfr_slope_per_year: float = Field(..., description="Projected annual eGFR decline slope under do(X=x)")
    average_treatment_effect_ate: float = Field(..., description="Population Average Treatment Effect (ATE) for reference cohort")
    e_value_sensitivity: float = Field(..., description="VanderWeele & Ding E-value: minimum confounding strength needed to overturn causal effect")
    causal_graph_provenance: str = "Structural Causal Model (SCM) via Doubly Robust G-Computation"


class FormalSafetyVerificationRequest(BaseModel):
    """Request to mathematically prove physiological safety invariants for a proposed regimen."""
    patient_id: str
    proposed_medications: List[str]
    egfr: float = Field(..., ge=5.0, le=150.0)
    serum_potassium: float = Field(..., ge=2.0, le=8.0, description="Serum potassium in mEq/L")
    systolic_bp: float = Field(..., ge=60.0, le=250.0)
    diastolic_bp: float = Field(..., ge=30.0, le=150.0)
    qtc_interval_ms: float = Field(default=420.0, ge=300.0, le=650.0, description="Baseline baseline corrected QT interval in ms")
    fib4_score: float = Field(default=1.2, ge=0.1, le=15.0, description="FIB-4 liver fibrosis index")
    active_diagnoses: List[str] = Field(default_factory=list)


class FormalSafetyVerificationResponse(BaseModel):
    """Formal mathematical verification output certifying patient regimen safety."""
    patient_id: str
    verification_status: str = Field(..., description="Status: PROVEN_SAFE, CONDITIONAL_SAFE, REJECTED_LETHAL_VIOLATION")
    safety_proof_token: str = Field(..., description="Cryptographic/deterministic formal audit token")
    invariants_evaluated: int
    violated_invariants: List[str] = Field(default_factory=list)
    mathematical_rationale: List[str] = Field(default_factory=list)
    safe_auto_clamped_alternatives: Dict[str, str] = Field(default_factory=dict)
    is_safe_to_administer: bool


class MultimodalPatientProfile(BaseModel):
    """Cross-modal patient profile for unified latent coordinate projection."""
    patient_id: str
    age: float
    gender: str = "unknown"
    vitals_vector: Dict[str, float] = Field(..., description="Key numerical vitals and lab biomarkers")
    diagnostic_codes: List[str] = Field(default_factory=list, description="Active ICD-10 or SNOMED clinical codes")
    genomic_variants: Dict[str, str] = Field(default_factory=dict, description="Key pharmacogenomic alleles (CYP2D6, CYP2C19, etc.)")
    morphological_features: Dict[str, float] = Field(default_factory=dict, description="Imaging/waveform features (e.g. cardiothoracic_ratio, lvef, qtc_ms)")


class MultimodalEmbeddingResponse(BaseModel):
    """Unified 128-dimensional clinical latent coordinate embedding."""
    patient_id: str
    embedding_dimension: int = 128
    latent_coordinate_vector: List[float] = Field(..., description="Normalized 128-dimensional clinical manifold coordinate")
    latent_manifold_stability_index: float = Field(..., ge=0.0, le=1.0, description="Manifold stability score (1.0 = highly stable homeostasis)")
    nearest_phenotypic_cohort: str
    cohort_euclidean_distance: float

