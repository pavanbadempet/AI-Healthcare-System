"""Tests for Frontier Backend Resilience and High-Availability Distributed Systems.

Verifies:
1. Adaptive latency-gradient concurrency limiter and priority load shedder.
2. Cryptographic idempotency engine with deterministic replay and tamper conflict rejection.
3. Offline-first clinical CRDT synchronization (ORSet, LWWRegister, VectorClock).
4. Autonomous chaos mesh and 3-state sliding-window circuit breaker.
5. FastAPI /v1/resilience endpoints.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.resilience.adaptive_concurrency_limiter import (
    AdaptiveConcurrencyLimiter,
    TrafficPriority,
)
from backend.resilience.chaos_resilience_mesh import (
    AutonomousChaosMesh,
    ChaosFaultRule,
    ChaosFaultType,
    CircuitState,
    SlidingWindowCircuitBreaker,
    SyntheticChaosError,
)
from backend.resilience.clinical_crdt_sync import (
    ClinicalPatientChartCRDT,
    ORSet,
)
from backend.resilience.cryptographic_idempotency import (
    CryptographicIdempotencyEngine,
    IdempotencyConflictError,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# =========================================================================
# 1. Adaptive Concurrency Limiter & Latency-Gradient Tests
# =========================================================================

def test_adaptive_concurrency_limiter_gradient_and_shedding():
    limiter = AdaptiveConcurrencyLimiter(
        min_concurrency=5.0,
        max_concurrency=50.0,
        initial_concurrency=10.0,
        smoothing_factor=0.5,
        beta=1.0,
        rtt_tolerance=1.2,
    )

    # Base state
    assert limiter.current_limit == 10.0
    assert limiter.inflight == 0

    # Admit normal clinical query
    admitted, reason, meta = limiter.evaluate_admission(TrafficPriority.CLINICAL_QUERY)
    assert admitted is True
    assert reason == "ADMITTED_CLINICAL"
    assert limiter.inflight == 1

    # Record healthy low-latency completion (5ms)
    limiter.record_completion(5.0)
    assert limiter.inflight == 0

    # Record multiple healthy completions to establish low RTT_min
    for _ in range(5):
        limiter.record_completion(5.0)

    # Now simulate severe latency spike (50ms)
    limiter.record_completion(50.0)
    metrics = limiter.get_metrics()
    assert metrics.rtt_min_ms <= 5.0
    assert metrics.latency_gradient < 1.0  # Gradient signals congestion

    # Test load-shedding tiers under controlled limit of 10.0
    limiter.current_limit = 10.0
    limiter._inflight = 7  # 70% of limit (10.0)
    # Background analytics should be shed at >60%
    bg_admitted, bg_reason, _ = limiter.evaluate_admission(TrafficPriority.BACKGROUND_ANALYTICS)
    assert bg_admitted is False
    assert bg_reason == "SHED_BACKGROUND_CONGESTION"

    # Clinical query should still be admitted at 70%
    cq_admitted, cq_reason, _ = limiter.evaluate_admission(TrafficPriority.CLINICAL_QUERY)
    assert cq_admitted is True
    limiter._inflight -= 1

    # Critical actuation should be admitted even at 100% capacity due to reserve headroom
    limiter._inflight = 10
    crit_admitted, crit_reason, _ = limiter.evaluate_admission(TrafficPriority.CRITICAL_ACTUATION)
    assert crit_admitted is True
    assert crit_reason == "ADMITTED_CRITICAL_RESERVE"


def test_adaptive_concurrency_limiter_guard_context_manager():
    limiter = AdaptiveConcurrencyLimiter(initial_concurrency=10.0)
    with limiter.guard(TrafficPriority.CLINICAL_QUERY) as (admitted, reason, _):
        assert admitted is True
        time.sleep(0.005)

    assert limiter.inflight == 0
    metrics = limiter.get_metrics()
    assert metrics.total_admitted >= 1


# =========================================================================
# 2. Cryptographic Idempotency Tests
# =========================================================================

def test_cryptographic_idempotency_replay_and_tamper_detection():
    engine = CryptographicIdempotencyEngine(default_ttl_seconds=3600)
    key = "order-tx-99981"
    method = "POST"
    path = "/v1/clinical/orders"
    payload = {"patient_id": "P-101", "drug": "Furosemide", "dose_mg": 40}

    execution_count = 0

    def mock_order_handler():
        nonlocal execution_count
        execution_count += 1
        return 200, {"order_id": "ORD-001", "status": "DISPENSED"}, {"X-Custom": "Test"}

    # First execution: primary execution
    code1, body1, headers1, is_replay1 = engine.execute_idempotent(
        key=key, method=method, path=path, payload=payload, execution_handler=mock_order_handler
    )
    assert code1 == 200
    assert is_replay1 is False
    assert execution_count == 1
    assert body1["order_id"] == "ORD-001"
    assert headers1["X-Idempotent-Replay"] == "false"

    # Second execution with identical payload: replay cached deterministic result
    code2, body2, headers2, is_replay2 = engine.execute_idempotent(
        key=key, method=method, path=path, payload=payload, execution_handler=mock_order_handler
    )
    assert code2 == 200
    assert is_replay2 is True
    assert execution_count == 1  # Handler NOT called again
    assert body2["order_id"] == "ORD-001"
    assert headers2["X-Idempotent-Replay"] == "true"

    # Third execution with mutated payload under the same key: must raise tamper conflict
    mutated_payload = {"patient_id": "P-101", "drug": "Furosemide", "dose_mg": 80}  # Altered dose!
    with pytest.raises(IdempotencyConflictError) as exc_info:
        engine.execute_idempotent(
            key=key, method=method, path=path, payload=mutated_payload, execution_handler=mock_order_handler
        )
    assert "Idempotency conflict" in str(exc_info.value)
    assert execution_count == 1


# =========================================================================
# 3. Clinical CRDT Synchronization Tests
# =========================================================================

def test_orset_add_remove_and_merge():
    set_a = ORSet()
    set_b = ORSet()

    # Node A adds Penicillin
    set_a.add("Penicillin")
    assert "Penicillin" in set_a.read()

    # Node B adds Aspirin and Penicillin
    set_b.add("Aspirin")
    set_b.add("Penicillin")

    # Node A removes Penicillin (removes only tags observed on A)
    set_a.remove("Penicillin")
    assert "Penicillin" not in set_a.read()

    # Merge A join B and B join A (Commutativity test)
    merged_ab = set_a.merge(set_b)
    merged_ba = set_b.merge(set_a)

    # In ORSet, concurrent add on B wins over remove on A because tag on B was not yet seen by A
    assert "Penicillin" in merged_ab.read()
    assert "Aspirin" in merged_ab.read()
    assert merged_ab.read() == merged_ba.read()


def test_clinical_patient_chart_crdt_convergence():
    # Simulate two disconnected ambulances mutating the same patient chart
    patient_id = "PT-ICU-882"
    amb_1 = ClinicalPatientChartCRDT(patient_id=patient_id)
    amb_2 = ClinicalPatientChartCRDT(patient_id=patient_id)

    # Ambulance 1 records allergies and vitals
    amb_1.add_allergy("Sulfa", node_id="AMB-01")
    amb_1.record_vital("heart_rate", 92, node_id="AMB-01", timestamp_us=1000)
    amb_1.record_vital("systolic_bp", 125, node_id="AMB-01", timestamp_us=1000)

    # Ambulance 2 records medications and newer vitals
    amb_2.add_medication("Epinephrine", node_id="AMB-02")
    amb_2.record_vital("heart_rate", 118, node_id="AMB-02", timestamp_us=2000)  # Newer timestamp wins

    # Merge in both directions
    merged_1_2 = amb_1.merge(amb_2)
    merged_2_1 = amb_2.merge(amb_1)

    snap_1_2 = merged_1_2.snapshot()
    snap_2_1 = merged_2_1.snapshot()

    assert snap_1_2 == snap_2_1
    assert "Sulfa" in snap_1_2["active_allergies"]
    assert "Epinephrine" in snap_1_2["active_medications"]
    assert snap_1_2["latest_vitals"]["heart_rate"] == 118  # LWW resolution
    assert snap_1_2["latest_vitals"]["systolic_bp"] == 125


# =========================================================================
# 4. Chaos Resilience Mesh & Circuit Breaker Tests
# =========================================================================

def test_sliding_window_circuit_breaker_tripping_and_healing():
    breaker = SlidingWindowCircuitBreaker(
        name="test_breaker",
        failure_threshold_rate=0.5,
        window_size=6,
        cooldown_seconds=0.1,  # Fast cooldown for testing
        half_open_trial_count=2,
    )

    assert breaker.state == CircuitState.CLOSED

    def failing_call():
        raise RuntimeError("Service down")

    def success_call():
        return "SUCCESS"

    def fallback_call():
        return "FALLBACK"

    # Execute 3 failures to trip the 50% threshold
    for _ in range(3):
        res, used_fb = breaker.execute(failing_call, fallback_fn=fallback_call)
        assert res == "FALLBACK"
        assert used_fb is True

    # Circuit should now be OPEN
    assert breaker.state == CircuitState.OPEN

    # While OPEN, fails fast or returns fallback
    res, used_fb = breaker.execute(success_call, fallback_fn=fallback_call)
    assert res == "FALLBACK"
    assert used_fb is True

    # Wait for cooldown to expire
    time.sleep(0.15)
    # State transitions to HALF_OPEN
    assert breaker.state == CircuitState.HALF_OPEN

    # 2 trial successes heal the circuit
    breaker.execute(success_call)
    breaker.execute(success_call)
    assert breaker.state == CircuitState.CLOSED


def test_autonomous_chaos_mesh_rules():
    mesh = AutonomousChaosMesh()
    rule = ChaosFaultRule(
        fault_type=ChaosFaultType.TRANSIENT_ERROR,
        probability=1.0,
        error_message="Chaos injection test",
    )
    mesh.register_rule("rule-01", rule)

    with pytest.raises(SyntheticChaosError) as exc_info:
        mesh.evaluate_chaos_interception("/v1/test")
    assert "Chaos injection test" in str(exc_info.value)

    mesh.clear_rules()
    assert mesh.evaluate_chaos_interception("/v1/test") is None


# =========================================================================
# 5. FastAPI Endpoints Integration Tests (/v1/resilience/)
# =========================================================================

def test_api_concurrency_evaluate(client: TestClient):
    resp = client.post(
        "/v1/resilience/concurrency/evaluate",
        json={"priority": "CLINICAL_QUERY", "simulated_latency_ms": 12.5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["admitted"] is True
    assert "current_limit" in data
    assert "gradient" in data


def test_api_idempotency_execute_and_conflict(client: TestClient):
    key = f"test-idemp-{int(time.time() * 1000)}"
    payload = {"patient_id": "P-404", "order": "Morphine", "dosage": "5mg"}

    # 1. Primary execution
    resp1 = client.post(
        "/v1/resilience/idempotency/execute",
        json={
            "idempotency_key": key,
            "action": "administer_narcotics",
            "patient_id": "P-404",
            "payload": payload,
        },
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["is_replay"] is False
    assert data1["status"] == "COMMITTED"

    # 2. Replay execution
    resp2 = client.post(
        "/v1/resilience/idempotency/execute",
        json={
            "idempotency_key": key,
            "action": "administer_narcotics",
            "patient_id": "P-404",
            "payload": payload,
        },
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["is_replay"] is True

    # 3. Conflict on payload mutation
    resp3 = client.post(
        "/v1/resilience/idempotency/execute",
        json={
            "idempotency_key": key,
            "action": "administer_narcotics",
            "patient_id": "P-404",
            "payload": {"patient_id": "P-404", "order": "Morphine", "dosage": "50mg"},  # Tampered
        },
    )
    assert resp3.status_code == 409


def test_api_crdt_mutate_and_merge_sync(client: TestClient):
    # Mutate on Ambulance Node A
    mut_a = client.post(
        "/v1/resilience/crdt/mutate",
        json={
            "patient_id": "PT-SYNC-01",
            "node_id": "NODE-AMB-A",
            "operation": "add_allergy",
            "entity": "Latex",
        },
    )
    assert mut_a.status_code == 200
    chart_a = mut_a.json()["chart_state"]

    # Mutate on Clinic Node B
    mut_b = client.post(
        "/v1/resilience/crdt/mutate",
        json={
            "patient_id": "PT-SYNC-01",
            "node_id": "NODE-CLINIC-B",
            "operation": "add_medication",
            "entity": "Amoxicillin",
        },
    )
    assert mut_b.status_code == 200
    chart_b = mut_b.json()["chart_state"]

    # Merge sync
    sync_resp = client.post(
        "/v1/resilience/crdt/merge-sync",
        json={"replica_a": chart_a, "replica_b": chart_b},
    )
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["is_commutative_verified"] is True
    assert "Latex" in sync_data["snapshot"]["active_allergies"]
    assert "Amoxicillin" in sync_data["snapshot"]["active_medications"]


def test_api_chaos_probe_and_health(client: TestClient):
    probe_resp = client.post(
        "/v1/resilience/chaos/execute-probe",
        json={"breaker_name": "api_test_breaker", "simulate_failure": False, "use_fallback": True},
    )
    assert probe_resp.status_code == 200
    assert probe_resp.json()["status"] == "SUCCESS"

    health_resp = client.get("/v1/resilience/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "HEALTHY"
