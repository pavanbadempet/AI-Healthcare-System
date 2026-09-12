"""
Pydantic Schemas for Peak Healthcare Data Engineering Capabilities:
- Bi-Temporal Event Sourcing & Point-in-Time (PIT) As-Of Joins
- Zero-Copy Streaming Kappa Architecture with Apache Arrow
- Enforceable Enterprise Data Contracts & Schema Drift DLQ
- (epsilon, delta)-Differential Privacy Synthetic EHR Cohorts
- Point-in-Time Feature Store with Automated Drift Monitoring (PSI, Wasserstein)
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Bi-Temporal Event Sourcing ---
class BiTemporalInsertRequest(BaseModel):
    record_id: str = Field(..., description="Unique record identifier")
    entity_id: str = Field(..., description="Patient or subject identifier")
    attribute_name: str = Field(..., description="Clinical attribute name (e.g. serum_creatinine, map)")
    attribute_value: Any = Field(..., description="Clinical value")
    valid_time_iso: str = Field(..., description="ISO timestamp when observation physically occurred")
    unit: Optional[str] = Field(None, description="Physical unit of measurement")
    system_time_iso: Optional[str] = Field(None, description="Optional system transaction timestamp")


class BiTemporalRecordResponse(BaseModel):
    record_id: str
    entity_id: str
    attribute_name: str
    attribute_value: Any
    unit: Optional[str]
    valid_time_start: str
    valid_time_end: str
    system_time_start: str
    system_time_end: str
    version: int


class BiTemporalAsOfQueryRequest(BaseModel):
    entity_id: str = Field(..., description="Patient identifier")
    as_of_valid_time_iso: str = Field(..., description="Query valid time in reality")
    as_of_system_time_iso: str = Field(..., description="Query system transaction time")


class BiTemporalAsOfQueryResponse(BaseModel):
    entity_id: str
    as_of_valid_time: str
    as_of_system_time: str
    features: Dict[str, Any]
    active_versions: Dict[str, int]
    zero_leakage_verified: bool


class BiTemporalAmendRequest(BaseModel):
    entity_id: str = Field(..., description="Patient identifier")
    attribute_name: str = Field(..., description="Clinical attribute to amend")
    new_attribute_value: Any = Field(..., description="Corrected or recalibrated value")
    effective_valid_time_iso: str = Field(..., description="Valid time of the observation")
    amendment_reason: str = Field(..., description="Clinical rationale for retroactive correction")
    amended_by: str = Field("clinical_lab_system", description="User or system submitting correction")


# --- Zero-Copy Streaming Kappa Architecture ---
class TelemetryPointInput(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    timestamp_epoch_ms: int = Field(..., description="Epoch millisecond timestamp")
    metric_name: str = Field(..., description="Vital sign name (e.g. map, heart_rate, spo2)")
    metric_value: float = Field(..., description="Observed numeric reading")
    unit: str = Field(..., description="Unit of measurement")
    device_id: str = Field("BEDSIDE_MONITOR_01", description="Streaming telemetry device ID")


class StreamingBatchIngestRequest(BaseModel):
    table_name: str = Field("bedside_telemetry", description="Streaming target table")
    records: List[TelemetryPointInput] = Field(..., description="Batch of high-frequency telemetry points")


class StreamingBatchIngestResponse(BaseModel):
    ingested_count: int
    table_name: str
    arrow_num_columns: int
    zero_copy_success: bool


class StreamingWindowAggregateRequest(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    metric_name: str = Field(..., description="Telemetry metric name")
    window_duration_seconds: int = Field(300, ge=10, le=86400, description="Window size in seconds")
    window_type: str = Field("SLIDING", description="Window aggregation type (SLIDING or TUMBLING)")


class StreamingWindowAggregateResponse(BaseModel):
    patient_id: str
    metric_name: str
    window_type: str
    window_duration_seconds: int
    window_end_epoch_ms: int
    count: int
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    slope_velocity: float


# --- Enterprise Data Contracts ---
class ContractValidationRequest(BaseModel):
    contract_id: str = Field(..., description="Contract ID to validate against (e.g. vitals_contract_v1)")
    payload: Dict[str, Any] = Field(..., description="Incoming raw data payload from external source")


class ContractViolationSchema(BaseModel):
    field_name: str
    violation_type: str
    expected: str
    actual: str
    severity: str


class ContractValidationResponse(BaseModel):
    is_valid: bool
    contract_id: str
    dataset_name: str
    passed_fields: List[str]
    violations: List[ContractViolationSchema]
    quarantined: bool
    quarantine_id: Optional[str]
    drift_detected: bool
    new_uncontracted_fields: List[str]


# --- (epsilon, delta)-Differential Privacy ---
class DifferentialPrivacySynthesisRequest(BaseModel):
    cohort_id: str = Field(..., description="Synthetic cohort identifier")
    n_patients: int = Field(25, ge=1, le=500, description="Number of synthetic patient profiles to generate")
    epsilon: float = Field(1.0, ge=0.01, le=10.0, description="Privacy budget epsilon parameter")
    delta: float = Field(1e-5, ge=1e-9, le=1e-3, description="Privacy budget delta parameter")


class SyntheticPatientRecordSchema(BaseModel):
    synthetic_patient_id: str
    age: float
    gender: str
    systolic_bp: float
    diastolic_bp: float
    serum_creatinine: float
    egfr: float
    hba1c: float
    blood_glucose: float
    primary_icd10: str
    mace_risk_percent: float


class PrivacyBudgetStatusSchema(BaseModel):
    epsilon_budget: float
    delta_budget: float
    epsilon_spent: float
    delta_spent: float
    remaining_epsilon: float
    budget_exhausted: bool


class DifferentialPrivacySynthesisResponse(BaseModel):
    cohort_id: str
    num_synthesized: int
    epsilon_used: float
    delta_used: float
    privacy_mechanism: str
    empirical_covariance_preserved: bool
    synthetic_records: List[SyntheticPatientRecordSchema]
    privacy_budget_status: PrivacyBudgetStatusSchema


# --- Feature Store & Drift Monitoring ---
class FeatureDriftAuditRequest(BaseModel):
    feature_name: str = Field(..., description="Registered clinical feature name (e.g. egfr, map, lactate)")
    current_samples: List[float] = Field(..., description="Array of recently observed feature values")


class FeatureDriftAuditResponse(BaseModel):
    feature_name: str
    sample_size_baseline: int
    sample_size_current: int
    psi_score: float
    wasserstein_distance_score: float
    ks_statistic: float
    ks_p_value: float
    drift_status: str
    requires_retraining: bool
    recommended_action: str
    bucket_distributions: List[Dict[str, Any]]
