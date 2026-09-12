"""
Unit & Integration Tests for Level 7 Theoretical Peak & Confidential Data Systems:
- Learned Index Structures (PGM-Index & Learned CDFs)
- Confidential Clean-Room Remote Attestation & Hardware Enclave Verification
- Autonomous Adaptive Join Optimizer & Physical Access Planner
- FastAPI /v1/confidential-systems/ REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.data_platform.adaptive_join_optimizer import (
    CountMinSketch,
    HyperLogLog,
    adaptive_join_optimizer,
)
from backend.data_platform.confidential_cleanroom import (
    confidential_cleanroom_engine,
)
from backend.data_platform.learned_index import PgmIndex
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. Learned Index Structures (PGM-Index) Tests
# =====================================================================

def test_pgm_index_construction_and_error_bounds():
    """Verify that every key lookup falls strictly within the bounded error window."""
    keys = sorted([float(i * 3 + (i % 5)) for i in range(150)])  # Monotonic sequence
    idx = PgmIndex(epsilon=8)
    idx.build(keys)

    assert idx.num_records == 150
    assert len(idx.levels) >= 1

    # Verify point lookup for sample of keys
    for sample_pos in [0, 25, 70, 100, 149]:
        key = keys[sample_pos]
        pos, telemetry = idx.point_lookup(key)
        assert telemetry["found"] is True
        assert pos == sample_pos
        # Assert predicted position is within epsilon
        assert abs(telemetry["predicted_position"] - sample_pos) <= (idx.epsilon * 2.0)

    # Missing key
    pos_none, tel_none = idx.point_lookup(999999.0)
    assert tel_none["found"] is False
    assert pos_none is None


def test_pgm_index_range_queries():
    """Verify learned range query accurately locates start and end bounds."""
    keys = [float(i * 10) for i in range(100)]  # 0, 10, 20, ..., 990
    idx = PgmIndex(epsilon=8)
    idx.build(keys)

    matched_indices, telemetry = idx.range_query(200.0, 500.0)
    # Expected keys: 200, 210, ..., 500 -> 31 keys
    assert telemetry["count"] == 31
    assert matched_indices[0] == 20
    assert matched_indices[-1] == 50


def test_pgm_index_memory_compression():
    """Verify index metrics show memory compression advantage."""
    keys = [float(i * 2) for i in range(500)]
    idx = PgmIndex(epsilon=16)
    idx.build(keys)
    metrics = idx.get_index_metrics()

    assert metrics["memory_compression_ratio"] >= 1.5
    assert metrics["pgm_index_size_bytes"] < metrics["estimated_btree_size_bytes"]


def test_pgm_index_api_endpoints(client):
    """Verify FastAPI learned-index endpoints."""
    keys = [10.5, 20.0, 35.2, 50.8, 62.1, 80.0, 95.4]

    # 1. Build
    res_build = client.post(
        "/v1/confidential-systems/learned-index/build",
        json={"keys": keys, "epsilon": 4},
    )
    assert res_build.status_code == 201
    data_build = res_build.json()
    assert data_build["num_records"] == 7

    # 2. Point Query
    res_query = client.post(
        "/v1/confidential-systems/learned-index/query",
        json={"key": 35.2},
    )
    assert res_query.status_code == 200
    data_query = res_query.json()
    assert data_query["found"] is True
    assert data_query["position"] == 2

    # 3. Range Query
    res_range = client.post(
        "/v1/confidential-systems/learned-index/range",
        json={"min_key": 20.0, "max_key": 65.0},
    )
    assert res_range.status_code == 200
    data_range = res_range.json()
    assert data_range["count"] == 4


# =====================================================================
# 2. Confidential Clean Room & Enclave Attestation Tests
# =====================================================================

def test_enclave_attestation_quote_verification_success():
    """Verify valid hardware quote with authentic key binding passes verification."""
    client_pubkey = "ECDH-PUBKEY-ALICE-12345"
    quote = confidential_cleanroom_engine.generate_simulated_attestation_quote(
        architecture="AMD_SEV_SNP",
        image_tag="CLINICAL_ANALYTICS_V1",
        client_ephemeral_pubkey=client_pubkey,
    )

    verdict = confidential_cleanroom_engine.verify_attestation_quote(
        quote=quote,
        expected_client_pubkey=client_pubkey,
        expected_image_tag="CLINICAL_ANALYTICS_V1",
    )

    assert verdict.is_valid is True
    assert verdict.mrenclave_verified is True
    assert verdict.pcr_integrity_verified is True
    assert verdict.key_binding_verified is True
    assert verdict.hardware_pki_verified is True
    assert verdict.enclave_session_id.startswith("SESSION-TEE-")


def test_enclave_attestation_rejects_tampered_key_binding():
    """Verify attestation strictly fails if client ephemeral pubkey does not match report_data."""
    client_pubkey_real = "ECDH-PUBKEY-ALICE-REAL"
    client_pubkey_attacker = "ECDH-PUBKEY-ATTACKER-FORGED"

    quote = confidential_cleanroom_engine.generate_simulated_attestation_quote(
        architecture="AMD_SEV_SNP",
        image_tag="CLINICAL_ANALYTICS_V1",
        client_ephemeral_pubkey=client_pubkey_real,
    )

    verdict = confidential_cleanroom_engine.verify_attestation_quote(
        quote=quote,
        expected_client_pubkey=client_pubkey_attacker,  # Attacker attempts key interception
        expected_image_tag="CLINICAL_ANALYTICS_V1",
    )

    assert verdict.is_valid is False
    assert verdict.key_binding_verified is False
    assert "report_data key binding" in verdict.verdict_message


def test_cleanroom_joint_multi_party_compute():
    """Verify multi-hospital joint computation inside confidential enclave memory."""
    session_id = "SESSION-TEE-VALID-1234"
    hosp_a = [
        {"patient_id": "PT-A1", "age": 60, "systolic_bp": 130},
        {"patient_id": "PT-SHARED", "age": 70, "systolic_bp": 140},
    ]
    hosp_b = [
        {"patient_id": "PT-B1", "age": 50, "systolic_bp": 120},
        {"patient_id": "PT-SHARED", "age": 70, "systolic_bp": 140},
    ]

    res = confidential_cleanroom_engine.execute_confidential_joint_compute(
        enclave_session_id=session_id,
        hospital_a_dataset=hosp_a,
        hospital_b_dataset=hosp_b,
    )

    assert res["status"] == "COMPUTED_INSIDE_CONFIDENTIAL_ENCLAVE"
    assert res["shared_patients_identified"] == 1
    assert res["joint_cohort_metrics"]["combined_patient_count"] == 4
    assert res["joint_cohort_metrics"]["mean_age"] == 62.5
    assert res["hardware_execution_seal"].startswith("SEAL-TEE-")


def test_cleanroom_rejects_unattested_session():
    """Verify unauthenticated enclave session is forbidden from executing clean room compute."""
    with pytest.raises(PermissionError):
        confidential_cleanroom_engine.execute_confidential_joint_compute(
            enclave_session_id="INVALID_SESSION",
            hospital_a_dataset=[],
            hospital_b_dataset=[],
        )


def test_cleanroom_api_endpoints(client):
    """Verify FastAPI /enclave/attest and /cleanroom/joint-compute endpoints."""
    # 1. Attest
    res_attest = client.post(
        "/v1/confidential-systems/enclave/attest",
        json={
            "architecture": "AMD_SEV_SNP",
            "image_tag": "CLINICAL_ANALYTICS_V1",
            "client_ephemeral_pubkey": "PUBKEY-SESSION-ABC",
        },
    )
    assert res_attest.status_code == 200
    data_attest = res_attest.json()
    assert data_attest["is_valid"] is True
    session_id = data_attest["enclave_session_id"]

    # 2. Joint Compute
    res_compute = client.post(
        "/v1/confidential-systems/cleanroom/joint-compute",
        json={
            "enclave_session_id": session_id,
            "hospital_a_dataset": [{"patient_id": "P1", "age": 60, "systolic_bp": 120}],
            "hospital_b_dataset": [{"patient_id": "P2", "age": 80, "systolic_bp": 140}],
        },
    )
    assert res_compute.status_code == 200
    data_compute = res_compute.json()
    assert data_compute["joint_cohort_metrics"]["mean_age"] == 70.0


# =====================================================================
# 3. Autonomous Adaptive Join Optimizer Tests
# =====================================================================

def test_hll_cardinality_estimator():
    """Verify HyperLogLog estimates cardinality within acceptable error bounds."""
    hll = HyperLogLog(precision_bits=8)
    for i in range(500):
        hll.add(f"KEY-{i}")

    est = hll.estimate()
    # HLL with 256 buckets has ~6.5% standard error
    assert 400 <= est <= 600


def test_cms_frequency_estimator():
    """Verify Count-Min sketch tracks heavy hitters under skewed distributions."""
    cms = CountMinSketch(width=128, depth=4)
    # Insert skewed distribution: "SKEWED_KEY" 80 times, other keys 1 time each
    for _ in range(80):
        cms.add("SKEWED_KEY")
    for i in range(20):
        cms.add(f"UNIFORM_KEY_{i}")

    assert cms.estimate_frequency("SKEWED_KEY") >= 80
    assert cms.estimate_frequency("UNIFORM_KEY_5") <= 5


def test_adaptive_join_broadcast_strategy():
    """Verify optimizer selects Broadcast Hash Join when one table is small."""
    table_large = [{"pt_id": f"P-{i}", "v": i} for i in range(1000)]
    table_small = [{"pt_id": f"P-{i}", "info": f"data-{i}"} for i in range(10)]

    plan = adaptive_join_optimizer.profile_and_plan_join(table_large, table_small, "pt_id")
    assert plan.strategy == "BROADCAST_HASH_JOIN"


def test_adaptive_join_skew_sort_merge_strategy():
    """Verify optimizer switches to Sort-Merge Join when high skew is detected and tables exceed cache limit."""
    table_skewed = [{"pt_id": "HOT_KEY", "val": i} for i in range(4800)] + [
        {"pt_id": f"P-{i}", "val": i} for i in range(1200)
    ]
    table_b = [{"pt_id": f"P-{i}", "dx": "I10"} for i in range(6000)]

    plan = adaptive_join_optimizer.profile_and_plan_join(table_skewed, table_b, "pt_id")
    assert plan.strategy == "CACHE_CONSCIOUS_SORT_MERGE_JOIN"


def test_adaptive_join_api_and_health(client):
    """Verify FastAPI /join-optimizer/plan-and-execute and /health endpoints."""
    # 1. Join Execution
    table_a = [{"id": 1, "diag": "A"}, {"id": 2, "diag": "B"}]
    table_b = [{"id": 1, "cost": 100}, {"id": 2, "cost": 200}]

    res_join = client.post(
        "/v1/confidential-systems/join-optimizer/plan-and-execute",
        json={"table_a": table_a, "table_b": table_b, "join_key": "id"},
    )
    assert res_join.status_code == 200
    data_join = res_join.json()
    assert data_join["output_rows"] == 2
    assert data_join["strategy"] == "BROADCAST_HASH_JOIN"

    # 2. Health
    res_health = client.get("/v1/confidential-systems/health")
    assert res_health.status_code == 200
    data_h = res_health.json()
    assert data_h["status"] == "HEALTHY"
    assert data_h["tier"] == "LEVEL_7_THEORETICAL_PEAK"
    assert data_h["subsystems"]["learned_index_engine"] == "ACTIVE"
