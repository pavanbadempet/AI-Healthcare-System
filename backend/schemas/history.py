"""Pydantic schemas for Level 12 Bi-Temporal Event-Sourced Clinical History & Time-Travel OS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BiTemporalRecordSchema(BaseModel):
    """Schema for an ISO/IEC 9075:2011 bi-temporal fact."""

    record_id: str
    entity_type: str
    entity_id: str
    patient_id: str
    valid_from: str
    valid_to: Optional[str] = None
    transaction_from: str
    transaction_to: Optional[str] = None
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BiTemporalInsertRequest(BaseModel):
    """Request to insert or correct a bi-temporal clinical observation."""

    entity_type: str = Field(..., description="diagnosis, medication, vital, allergy, lab")
    entity_id: str = Field(..., description="Unique entity ID")
    patient_id: str = Field(..., description="Patient identifier")
    valid_from: str = Field(..., description="ISO 8601 clinical occurrence start")
    valid_to: Optional[str] = Field(None, description="ISO 8601 clinical occurrence end (None if open)")
    payload: Dict[str, Any] = Field(..., description="Clinical fact payload")
    transaction_time: Optional[str] = Field(None, description="Optional override for system transaction time")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BiTemporalQueryRequest(BaseModel):
    """Request for dual-axis as-of temporal query."""

    valid_time: str = Field(..., description="Target clinical reality time (ISO 8601)")
    transaction_time: str = Field(..., description="Target system knowledge time (ISO 8601)")
    entity_type: Optional[str] = Field(None, description="Optional entity type filter")


class AppendEventRequest(BaseModel):
    """Request to append an immutable domain event."""

    patient_id: str = Field(..., description="Patient identifier")
    event_type: str = Field(..., description="Clinical domain event type")
    payload: Dict[str, Any] = Field(..., description="Domain event payload")
    valid_time: Optional[str] = Field(None, description="Clinical occurrence timestamp (ISO 8601)")
    node_id: Optional[str] = Field(None, description="Originating node/ambulance/ward ID")
    intent_id: Optional[str] = Field(None, description="Optional link to clinical intent record")
    timestamp: Optional[str] = Field(None, description="Optional system transaction timestamp")
    incoming_clock: Optional[Dict[str, int]] = Field(None, description="Incoming vector clock for distributed merge")


class EventResponseSchema(BaseModel):
    """Response containing appended domain event details."""

    event_id: str
    patient_id: str
    event_type: str
    timestamp: str
    valid_time: str
    node_id: str
    vector_clock: Dict[str, int]
    causal_sequence: int
    payload: Dict[str, Any]
    intent_id: Optional[str] = None
    prev_hash: Optional[str] = None
    event_hash: str
    status: str = "EVENT_COMMITTED"


class ChartProjectionResponse(BaseModel):
    """Deterministic mathematical fold projection of patient chart."""

    patient_id: str
    admitted: bool
    admission: Optional[Dict[str, Any]] = None
    conditions: Dict[str, Any]
    medications: Dict[str, Any]
    vitals: List[Dict[str, Any]]
    allergies: Dict[str, Any]
    labs: Dict[str, Any]
    event_count: int
    as_of_time: Optional[str] = None
    last_event_hash: Optional[str] = None
    chain_verified: bool = True


class TemporalDiffRequest(BaseModel):
    """Request to compute structural differential between two clinical milestones."""

    t1: str = Field(..., description="Baseline time (ISO 8601)")
    t2: str = Field(..., description="Comparison time (ISO 8601)")
    by_valid_time: bool = Field(False, description="Whether to diff by Valid Time instead of Transaction Time")


class TemporalDiffResponse(BaseModel):
    """Response containing structural state differences and clinical narrative."""

    patient_id: str
    t1_label: str
    t2_label: str
    added: Dict[str, List[Any]]
    modified: Dict[str, List[Any]]
    resolved_or_revoked: Dict[str, List[Any]]
    new_vitals_count: int
    new_vitals: List[Dict[str, Any]]
    clinical_narrative: List[str]
    total_structural_changes: int


class RecordIntentRequest(BaseModel):
    """Request to log structured clinical justification and attribution."""

    patient_id: str = Field(..., description="Patient identifier")
    category: str = Field(..., description="Standardized clinical motivation category")
    rationale: str = Field(..., description="Detailed clinical justification")
    clinician_id: str = Field(..., description="Primary clinician ID")
    clinician_name: str = Field(..., description="Primary clinician full name")
    role: str = Field(..., description="Clinician role e.g. ATTENDING_PHYSICIAN")
    evidence: Optional[List[Dict[str, str]]] = Field(None, description="Diagnostic evidence linkages")


class CountersignIntentRequest(BaseModel):
    """Request for Four-Eye dual signoff countersignature."""

    clinician_id: str = Field(..., description="Countersigning clinician ID")
    clinician_name: str = Field(..., description="Countersigning clinician full name")
    role: str = Field(..., description="Role e.g. CLINICAL_PHARMACIST")


class IntentResponseSchema(BaseModel):
    """Response containing clinical intent record and quorum status."""

    intent_id: str
    patient_id: str
    category: str
    rationale: str
    primary_clinician: Dict[str, Any]
    countersignatures: List[Dict[str, Any]]
    evidence_links: List[Dict[str, Any]]
    is_quorum_verified: bool
    created_at: str


class HistoryHealthResponse(BaseModel):
    """Operational status of history tracking and temporal subsystems."""

    status: str = "HEALTHY"
    engine: str = "BI_TEMPORAL_EVENT_SOURCED_TIME_TRAVEL_OS"
    total_events: int
    total_patients_tracked: int
    bitemporal_records: int
    intents_recorded: int
