"""API Routes for Mission-Critical Frontier Backend Resilience.

Provides endpoints for adaptive latency-gradient concurrency control,
cryptographic idempotency execution, offline-first clinical CRDT synchronization,
and autonomous chaos mesh resilience.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from backend.resilience.adaptive_concurrency_limiter import (
    AdaptiveConcurrencyLimiter,
    TrafficPriority,
)
from backend.resilience.chaos_resilience_mesh import (
    AutonomousChaosMesh,
    ChaosFaultRule,
    ChaosFaultType,
    CircuitBreakerOpenError,
)
from backend.resilience.clinical_crdt_sync import (
    ClinicalPatientChartCRDT,
)
from backend.resilience.cryptographic_idempotency import (
    CryptographicIdempotencyEngine,
    IdempotencyConflictError,
    IdempotencyExecutionInProgressError,
    compute_request_fingerprint,
)
from backend.schemas.frontier_backend_resilience import (
    ChaosExecuteRequest,
    ChaosInjectRequest,
    ChaosStatusResponse,
    ConcurrencyEvaluateRequest,
    ConcurrencyEvaluateResponse,
    CrdtMutateRequest,
    CrdtMutateResponse,
    CrdtSyncRequest,
    CrdtSyncResponse,
    IdempotentExecuteRequest,
    IdempotentExecuteResponse,
)

logger = logging.getLogger("backend.frontier_backend_resilience")

router = APIRouter(
    prefix="/v1/resilience",
    tags=["Frontier Backend Resilience"],
)

# Global singleton instances for sandbox execution
adaptive_limiter = AdaptiveConcurrencyLimiter()
idempotency_engine = CryptographicIdempotencyEngine()
chaos_mesh = AutonomousChaosMesh()


@router.post("/concurrency/evaluate", response_model=ConcurrencyEvaluateResponse)
def evaluate_concurrency(req: ConcurrencyEvaluateRequest) -> ConcurrencyEvaluateResponse:
    """Evaluate admission under adaptive concurrency limits and update latency gradient."""
    try:
        priority = TrafficPriority(req.priority)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid traffic priority '{req.priority}'. Must be one of {[p.value for p in TrafficPriority]}",
        )

    admitted, reason, meta = adaptive_limiter.evaluate_admission(priority)

    if admitted and req.simulated_latency_ms is not None:
        adaptive_limiter.record_completion(req.simulated_latency_ms)

    metrics = adaptive_limiter.get_metrics()
    return ConcurrencyEvaluateResponse(
        admitted=admitted,
        reason=reason,
        current_limit=metrics.current_limit,
        inflight=metrics.inflight_requests,
        utilization=meta.get("utilization", 0.0),
        gradient=metrics.latency_gradient,
        metrics={
            "rtt_min_ms": metrics.rtt_min_ms,
            "rtt_current_ms": metrics.rtt_current_ms,
            "arrival_rate_rps": metrics.arrival_rate_rps,
            "estimated_littles_law_concurrency": metrics.estimated_littles_law_concurrency,
            "total_admitted": metrics.total_admitted,
            "total_shed": metrics.total_shed,
            "shed_by_priority": metrics.shed_by_priority,
        },
    )


@router.post("/idempotency/execute", response_model=IdempotentExecuteResponse)
def execute_idempotent_action(req: IdempotentExecuteRequest) -> IdempotentExecuteResponse:
    """Execute a mission-critical clinical action with deterministic exactly-once semantics."""
    path = f"/v1/resilience/actions/{req.action}"
    method = "POST"
    fingerprint = compute_request_fingerprint(req.idempotency_key, method, path, req.payload)

    def _execute() -> tuple[int, Dict[str, Any], Dict[str, str]]:
        # Deterministic simulation of clinical action execution
        action_result = {
            "action": req.action,
            "patient_id": req.patient_id,
            "status": "APPLIED_SUCCESSFULLY",
            "applied_payload": req.payload,
        }
        return 200, action_result, {"Content-Type": "application/json"}

    try:
        status_code, body, headers, is_replay = idempotency_engine.execute_idempotent(
            key=req.idempotency_key,
            method=method,
            path=path,
            payload=req.payload,
            execution_handler=_execute,
        )
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except IdempotencyExecutionInProgressError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )

    return IdempotentExecuteResponse(
        status="COMMITTED",
        idempotency_key=req.idempotency_key,
        fingerprint=fingerprint,
        is_replay=is_replay,
        result=body,
    )


@router.post("/crdt/mutate", response_model=CrdtMutateResponse)
def mutate_crdt_chart(req: CrdtMutateRequest) -> CrdtMutateResponse:
    """Apply an offline mutation to a decentralized patient chart CRDT."""
    if req.existing_chart:
        chart = ClinicalPatientChartCRDT.from_dict(req.existing_chart)
    else:
        chart = ClinicalPatientChartCRDT(patient_id=req.patient_id)

    op = req.operation.lower().strip()
    if op == "add_allergy":
        chart.add_allergy(req.entity, node_id=req.node_id)
    elif op == "remove_allergy":
        chart.remove_allergy(req.entity, node_id=req.node_id)
    elif op == "add_medication":
        chart.add_medication(req.entity, node_id=req.node_id)
    elif op == "remove_medication":
        chart.remove_medication(req.entity, node_id=req.node_id)
    elif op == "record_vital":
        chart.record_vital(req.entity, value=req.value, node_id=req.node_id, timestamp_us=req.timestamp_us)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported CRDT operation '{req.operation}'",
        )

    return CrdtMutateResponse(
        patient_id=chart.patient_id,
        chart_state=chart.to_dict(),
        snapshot=chart.snapshot(),
    )


@router.post("/crdt/merge-sync", response_model=CrdtSyncResponse)
def merge_sync_crdt(req: CrdtSyncRequest) -> CrdtSyncResponse:
    """Merge two divergent offline patient charts with commutative verification."""
    try:
        chart_a = ClinicalPatientChartCRDT.from_dict(req.replica_a)
        chart_b = ClinicalPatientChartCRDT.from_dict(req.replica_b)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CRDT wire format: {exc}",
        )

    if chart_a.patient_id != chart_b.patient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient ID mismatch: '{chart_a.patient_id}' vs '{chart_b.patient_id}'",
        )

    # Join-semilattice merge: A join B
    merged_ab = chart_a.merge(chart_b)
    # Verification of commutativity: B join A
    merged_ba = chart_b.merge(chart_a)

    snap_ab = merged_ab.snapshot()
    snap_ba = merged_ba.snapshot()

    # Verify identical snapshots regardless of merge direction
    is_commutative = (
        snap_ab["active_allergies"] == snap_ba["active_allergies"]
        and snap_ab["active_medications"] == snap_ba["active_medications"]
        and snap_ab["latest_vitals"] == snap_ba["latest_vitals"]
    )

    return CrdtSyncResponse(
        converged_chart=merged_ab.to_dict(),
        snapshot=snap_ab,
        is_commutative_verified=is_commutative,
    )


@router.post("/chaos/inject", response_model=ChaosStatusResponse)
def inject_chaos_rule(req: ChaosInjectRequest) -> ChaosStatusResponse:
    """Register an in-process chaos fault injection rule."""
    try:
        fault = ChaosFaultType(req.fault_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fault type '{req.fault_type}'. Valid: {[f.value for f in ChaosFaultType]}",
        )

    rule = ChaosFaultRule(
        fault_type=fault,
        probability=req.probability,
        delay_ms=req.delay_ms,
        error_message=req.error_message,
        target_endpoints=req.target_endpoints,
        enabled=req.enabled,
    )
    chaos_mesh.register_rule(req.rule_id, rule)

    return ChaosStatusResponse(
        status="RULE_REGISTERED",
        metrics=chaos_mesh.get_all_metrics(),
    )


@router.post("/chaos/execute-probe")
def execute_chaos_probe(req: ChaosExecuteRequest) -> Dict[str, Any]:
    """Execute a test call through a named circuit breaker."""
    breaker = chaos_mesh.get_or_create_breaker(name=req.breaker_name)

    def _service_call() -> str:
        if req.simulate_failure:
            raise RuntimeError("Synthetic downstream service failure")
        return "PRIMARY_SERVICE_SUCCESS"

    def _fallback_call() -> str:
        return "GRACEFUL_DEGRADATION_FALLBACK"

    fallback = _fallback_call if req.use_fallback else None

    try:
        result, used_fallback = breaker.execute(_service_call, fallback_fn=fallback)
        return {
            "status": "SUCCESS",
            "result": result,
            "used_fallback": used_fallback,
            "breaker_state": breaker.state.value,
            "metrics": breaker.get_metrics().__dict__,
        }
    except CircuitBreakerOpenError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/health")
def resilience_health() -> Dict[str, Any]:
    """Return comprehensive resilience operational telemetry."""
    concurrency_metrics = adaptive_limiter.get_metrics()
    return {
        "status": "HEALTHY",
        "concurrency_limiter": {
            "current_limit": concurrency_metrics.current_limit,
            "inflight": concurrency_metrics.inflight_requests,
            "rtt_min_ms": concurrency_metrics.rtt_min_ms,
            "rtt_current_ms": concurrency_metrics.rtt_current_ms,
            "gradient": concurrency_metrics.latency_gradient,
            "admitted_total": concurrency_metrics.total_admitted,
            "shed_total": concurrency_metrics.total_shed,
        },
        "idempotency_engine": {
            "active_records": idempotency_engine.count(),
        },
        "chaos_mesh": chaos_mesh.get_all_metrics(),
    }
