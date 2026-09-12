"""Pydantic schemas for Frontier Backend Resilience and High-Availability Distributed Systems."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConcurrencyEvaluateRequest(BaseModel):
    """Request to evaluate admission under adaptive concurrency limits."""
    priority: str = Field(
        default="CLINICAL_QUERY",
        description="Traffic tier: CRITICAL_ACTUATION, CLINICAL_QUERY, or BACKGROUND_ANALYTICS",
    )
    simulated_latency_ms: Optional[float] = Field(
        default=10.0,
        ge=0.1,
        description="Simulated or observed latency in ms to record upon completion",
    )


class ConcurrencyEvaluateResponse(BaseModel):
    """Admission decision and current concurrency telemetry."""
    admitted: bool
    reason: str
    current_limit: float
    inflight: int
    utilization: float
    gradient: float
    metrics: Dict[str, Any]


class IdempotentExecuteRequest(BaseModel):
    """Request for exactly-once idempotent execution."""
    idempotency_key: str = Field(..., min_length=1, description="Client idempotency key")
    action: str = Field(..., description="Action name (e.g. administer_medication, process_billing)")
    patient_id: str = Field(..., description="Patient identifier")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary action payload")


class IdempotentExecuteResponse(BaseModel):
    """Deterministic result of idempotent execution."""
    status: str
    idempotency_key: str
    fingerprint: str
    is_replay: bool
    result: Dict[str, Any]


class CrdtMutateRequest(BaseModel):
    """Request to apply a local offline mutation to a patient chart CRDT."""
    patient_id: str
    node_id: str
    operation: str = Field(..., description="add_allergy, remove_allergy, add_medication, remove_medication, record_vital")
    entity: str = Field(..., description="Allergen, medication name, or vital parameter name")
    value: Optional[Any] = Field(default=None, description="Value for vital records")
    timestamp_us: Optional[int] = Field(default=None, description="Optional microsecond timestamp")
    existing_chart: Optional[Dict[str, Any]] = Field(default=None, description="Existing wire CRDT state if any")


class CrdtMutateResponse(BaseModel):
    """Resulting mutated CRDT state and human-readable snapshot."""
    patient_id: str
    chart_state: Dict[str, Any]
    snapshot: Dict[str, Any]


class CrdtSyncRequest(BaseModel):
    """Request to merge two divergent offline CRDT replicas."""
    replica_a: Dict[str, Any] = Field(..., description="Wire state of replica A")
    replica_b: Dict[str, Any] = Field(..., description="Wire state of replica B")


class CrdtSyncResponse(BaseModel):
    """Converged CRDT state after join-semilattice merge."""
    converged_chart: Dict[str, Any]
    snapshot: Dict[str, Any]
    is_commutative_verified: bool


class ChaosInjectRequest(BaseModel):
    """Configuration to inject chaos fault rules."""
    rule_id: str
    fault_type: str = Field(..., description="LATENCY_SPIKE, TRANSIENT_ERROR, DEADLOCK, DROP_PACKET")
    probability: float = Field(default=1.0, ge=0.0, le=1.0)
    delay_ms: float = Field(default=0.0, ge=0.0)
    error_message: str = "Synthetic fault injected by chaos mesh"
    target_endpoints: List[str] = Field(default_factory=list)
    enabled: bool = True


class ChaosExecuteRequest(BaseModel):
    """Trigger a call through a named circuit breaker to test fault handling."""
    breaker_name: str = "clinical_service_breaker"
    simulate_failure: bool = False
    use_fallback: bool = True


class ChaosStatusResponse(BaseModel):
    """Status report of all chaos rules and circuit breakers."""
    status: str
    metrics: Dict[str, Any]
