"""
Pydantic Schemas for Advanced Clinical Intelligence Systems:
- Conformal Prediction (Distribution-free uncertainty intervals & adaptive prediction sets)
- Survival Analysis & Competing Risks (Kaplan-Meier, Cox Proportional Hazards, CIF)
- Polypharmacy Graph Interaction Network (Multi-relational DDI & high-order synergies)
- Marked Temporal Point Process (Multivariate Hawkes process for arrival cascades)
- Safe Offline Reinforcement Learning (Batch-Constrained DTR optimization)
- Topological Data Analysis (Vietoris-Rips persistent homology & Betti curves)
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Conformal Prediction ---
class ConformalIntervalRequest(BaseModel):
    target_name: str = Field(..., description="Biomarker target name (egfr, map, hba1c, lactate)")
    point_estimate: float = Field(..., description="Point prediction from clinical ML or digital twin")
    confidence_level: float = Field(0.95, ge=0.5, le=0.999, description="Target marginal coverage probability (1 - alpha)")
    local_spread_factor: Optional[float] = Field(None, description="Optional heteroscedastic scale factor")
    custom_calibration_residuals: Optional[List[float]] = Field(None, description="Optional custom nonconformity residuals")


class ConformalIntervalResponse(BaseModel):
    target_name: str
    point_estimate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float
    interval_width: float
    method: str
    finite_sample_guaranteed: bool


class ConformalClassificationRequest(BaseModel):
    candidate_probabilities: Dict[str, float] = Field(
        ...,
        description="Predicted class probabilities from clinical classifier",
    )
    confidence_level: float = Field(0.95, ge=0.5, le=0.999, description="Target coverage probability")


class ConformalClassificationResponse(BaseModel):
    diagnostic_category: str
    prediction_set: List[str]
    confidence_level: float
    set_cardinality: int
    class_probabilities: Dict[str, float]
    ambiguity_flag: bool


# --- Survival Analysis ---
class PatientSurvivalRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    condition: str = Field(..., description="Condition key (heart_failure, ckd_progression, sepsis_30d)")
    age: float = Field(..., ge=18.0, le=120.0, description="Patient age in years")
    biomarkers: Dict[str, float] = Field(
        default_factory=dict,
        description="Baseline laboratory and physiological biomarker values",
    )
    active_therapies: List[str] = Field(
        default_factory=list,
        description="List of active pharmacotherapies",
    )


class SurvivalCurvePointSchema(BaseModel):
    time_months: float
    survival_probability: float
    lower_ci: float
    upper_ci: float
    n_at_risk: int
    n_events: int


class PatientSurvivalResponse(BaseModel):
    patient_id: str
    condition: str
    median_survival_months: Optional[float]
    survival_probabilities: Dict[str, float]
    competing_risk_probabilities: Dict[str, float]
    individual_hazard_ratio: float
    risk_tier: str
    survival_curve: List[SurvivalCurvePointSchema]


# --- Polypharmacy Graph Interaction Network ---
class PolypharmacyEvaluationRequest(BaseModel):
    patient_id: Optional[str] = Field(None, description="Optional patient identifier")
    drug_list: List[str] = Field(
        ...,
        description="List of active medications to evaluate for pairwise and high-order synergies",
    )


class DrugInteractionEdgeSchema(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
    interaction_type: str
    mechanism: str
    clinical_risk: str
    confidence_score: float
    recommended_action: str


class HighOrderSynergySchema(BaseModel):
    involved_drugs: List[str]
    synergy_name: str
    synergy_type: str
    severity: str
    mechanism: str
    organ_risk: str
    mitigation_strategy: str


class PolypharmacyEvaluationResponse(BaseModel):
    regimen: List[str]
    num_drugs: int
    regimen_toxicity_index: float
    highest_severity: str
    pairwise_interactions: List[DrugInteractionEdgeSchema]
    high_order_synergies: List[HighOrderSynergySchema]
    safer_substitutions: Dict[str, List[str]]
    is_contraindicated: bool


# --- Marked Temporal Point Process ---
class ClinicalEventInputSchema(BaseModel):
    timestamp_hours: float = Field(..., description="Timestamp in hours relative to observation start")
    event_type: str = Field(..., description="Clinical event category identifier")
    severity_mark: float = Field(1.0, ge=0.1, le=10.0, description="Magnitude / mark of event severity")


class ProjectedArrivalSchema(BaseModel):
    simulated_arrival_hour: float
    hours_from_now: float
    predicted_event_type: str
    probability_confidence: float


class TemporalForecastRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    current_time_hours: float = Field(..., description="Current observation timeline in hours")
    history: List[ClinicalEventInputSchema] = Field(
        ...,
        description="Chronological series of past adverse events",
    )


class TemporalForecastResponse(BaseModel):
    patient_id: str
    current_time_hours: float
    instantaneous_intensities: Dict[str, float]
    dominant_near_term_threat: str
    expected_time_to_next_event_hours: float
    horizon_event_probabilities: Dict[str, float]
    branching_ratio_spectral_radius: float
    system_is_subcritical: bool
    simulated_next_arrivals: List[ProjectedArrivalSchema]


# --- Safe Offline RL Treatment Optimizer ---
class ClinicalStateInputSchema(BaseModel):
    map_mmhg: float = Field(..., description="Mean Arterial Pressure in mmHg")
    heart_rate_bpm: float = Field(..., description="Heart Rate in beats per minute")
    lactate_mmol_l: float = Field(..., description="Serum Lactate in mmol/L")
    serum_creatinine: float = Field(..., description="Serum Creatinine in mg/dL")
    urine_output_ml_kg_hr: float = Field(..., description="Urine Output in mL/kg/hr")
    blood_glucose_mg_dl: float = Field(..., description="Blood Glucose in mg/dL")


class RlOptimizationRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    state: ClinicalStateInputSchema
    current_vasopressor_dose: float = Field(0.0, description="Current Norepinephrine infusion dose")
    current_fluid_rate: float = Field(100.0, description="Current crystalloid infusion rate")
    current_insulin_rate: float = Field(0.0, description="Current regular insulin infusion rate")


class RlOptimizationResponse(BaseModel):
    patient_id: str
    recommended_action_id: int
    recommended_action_label: str
    norepinephrine_dose_mcg_kg_min: float
    iv_fluid_rate_ml_hr: float
    insulin_rate_units_hr: float
    expected_q_value: float
    standard_of_care_q_value: float
    expected_counterfactual_gain: float
    top_candidate_actions: List[Dict[str, Any]]
    clinical_rationale: str
    safety_interlock_cleared: bool


# --- Topological Phenotyping (Persistent Homology) ---
class TopologicalAnalysisRequest(BaseModel):
    cohort_id: str = Field(..., description="Cohort or patient group identifier")
    patient_feature_matrix: List[List[float]] = Field(
        ...,
        description="N x D matrix of patient phenotypic features (e.g. MAP, lactate, eGFR, glucose)",
    )
    feature_names: Optional[List[str]] = Field(None, description="Optional feature column labels")


class PersistenceIntervalSchema(BaseModel):
    homology_dimension: int
    birth: float
    death: float
    lifetime: float
    is_essential: bool


class BettiProfilePointSchema(BaseModel):
    filtration_radius: float
    beta_0: int
    beta_1: int


class TopologicalAnalysisResponse(BaseModel):
    cohort_id: str
    num_samples: int
    dimension: int
    persistent_entropy: float
    num_distinct_subtypes: int
    identified_subtypes: List[Dict[str, Any]]
    h0_persistence: List[PersistenceIntervalSchema]
    h1_persistence: List[PersistenceIntervalSchema]
    betti_curves: List[BettiProfilePointSchema]
    dominant_topological_feature: str
