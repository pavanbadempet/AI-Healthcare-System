"""Pydantic schemas for Level 13 Clinical Version Control, Care Protocol Branching & Simulation OS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateBranchRequest(BaseModel):
    """Request to create an isolated patient simulation branch."""

    patient_id: str = Field(..., description="Target patient ID")
    branch_name: str = Field(..., description="Descriptive branch name (e.g. sim-regimen-a)")
    author_id: str = Field(..., description="Clinician user ID creating the branch")
    author_name: str = Field(..., description="Clinician name")
    purpose: str = Field(..., description="Clinical hypothesis or simulation intent")


class BranchResponse(BaseModel):
    """Metadata describing a simulation workspace."""

    branch_id: str
    patient_id: str
    branch_name: str
    author_id: str
    author_name: str
    purpose: str
    created_at: str
    status: str
    branch_events_count: int


class MutateBranchRequest(BaseModel):
    """Request to record a simulated clinical action on a branch."""

    event_type: str = Field(..., description="Domain event type (e.g. MedicationPrescribed)")
    payload: Dict[str, Any] = Field(..., description="Simulated order/prescription parameters")
    valid_time: Optional[str] = Field(None, description="Optional clinical valid time (ISO 8601)")


class BranchStateResponse(BaseModel):
    """Hypothetical projected patient state in a simulation workspace."""

    branch_id: str
    patient_id: str
    branch_name: str
    simulated_event_count: int
    conditions: Dict[str, Any]
    medications: Dict[str, Any]
    vitals: List[Dict[str, Any]]
    allergies: Dict[str, Any]
    labs: Dict[str, Any]


class MergeBranchRequest(BaseModel):
    """Request to execute 3-way merge from simulation branch to trunk."""

    merging_clinician_id: str = Field(..., description="Clinician ID approving the merge")
    merging_clinician_name: str = Field(..., description="Clinician full name")
    allow_conflict_override: bool = Field(False, description="Whether to override detected conflicts")


class MergeBranchResponse(BaseModel):
    """Result of 3-way merge operation."""

    success: bool
    status: str
    branch_id: str
    patient_id: Optional[str] = None
    applied_events_count: int = 0
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts_overridden: int = 0
    merged_chart: Optional[Dict[str, Any]] = None


class CreateProtocolRequest(BaseModel):
    """Request to create a new clinical care protocol."""

    protocol_id: str = Field(..., description="Unique protocol ID")
    title: str = Field(..., description="Protocol title")
    version: str = Field(..., description="SemVer version (e.g. 1.0.0)")
    steps: List[Dict[str, Any]] = Field(..., description="Ordered clinical actions")
    author_id: str = Field(..., description="Authoring clinician or committee ID")


class ProtocolResponse(BaseModel):
    """Care protocol definition and lifecycle status."""

    protocol_id: str
    title: str
    version: str
    status: str
    canary_units: List[str]
    approvers: List[str]
    steps: List[Dict[str, Any]]
    created_at: str
    updated_at: str


class TransitionProtocolRequest(BaseModel):
    """Request to advance protocol lifecycle stage."""

    version: str = Field(..., description="Protocol SemVer string")
    target_status: str = Field(..., description="IN_REVIEW, STAGED, ACTIVE, DEPRECATED, RETIRED")
    user_id: str = Field(..., description="Approving clinician/committee member ID")
    canary_units: Optional[List[str]] = Field(None, description="Units for canary rollout (e.g. ['NEURO_ICU'])")


class ProtocolDiffResponse(BaseModel):
    """Structural differential between two protocol versions."""

    protocol_id: str
    v1: str
    v2: str
    added_steps: List[Dict[str, Any]]
    removed_steps: List[Dict[str, Any]]
    modified_steps: List[Dict[str, Any]]


class RegisterTriadRequest(BaseModel):
    """Request to register a Model-Data-Code cryptographic triad."""

    model_id: str = Field(..., description="Model identifier")
    weights_digest: str = Field(..., description="SHA-256 digest of weights binary")
    dataset_digest: str = Field(..., description="SHA-256 Merkle root of training dataset")
    code_commit_hash: str = Field(..., description="Git commit hash of pipeline")
    framework: str = Field("PyTorch", description="Framework name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TriadResponse(BaseModel):
    """Model-Data-Code triad manifest."""

    triad_id: str
    model_id: str
    weights_digest: str
    dataset_digest: str
    code_commit_hash: str
    framework: str
    triad_signature: str
    registered_at: str


class AttestInferenceRequest(BaseModel):
    """Request to issue cryptographic attestation for AI inference."""

    patient_id: str = Field(..., description="Patient identifier")
    prediction_id: str = Field(..., description="Prediction identifier")
    triad_id: str = Field(..., description="Lineage triad reference")
    input_features: Dict[str, Any] = Field(..., description="Inference input feature dictionary")
    output_prediction: Dict[str, Any] = Field(..., description="Prediction output payload")


class AttestationResponse(BaseModel):
    """Signed inference certificate."""

    attestation_id: str
    patient_id: str
    prediction_id: str
    triad_id: str
    input_features_hash: str
    output_prediction: Dict[str, Any]
    attestation_hash: str
    timestamp: str


class VerifyProvenanceResponse(BaseModel):
    """Provenance verification result."""

    valid: bool
    attestation_id: str
    patient_id: Optional[str] = None
    prediction_id: Optional[str] = None
    triad: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    verified_at: Optional[str] = None


class ScanDeprecationsResponse(BaseModel):
    """Medical code deprecation scan and proposed migration patch."""

    patient_id: str
    target_release: str
    findings: List[Dict[str, Any]]
    migration_patch: Optional[Dict[str, Any]] = None


class VersioningHealthResponse(BaseModel):
    """Operational status of the clinical version control subsystem."""

    status: str = "HEALTHY"
    engine: str = "CLINICAL_VCS_SIMULATION_OS"
    active_branches: int
    registered_protocols: int
    model_triads: int
