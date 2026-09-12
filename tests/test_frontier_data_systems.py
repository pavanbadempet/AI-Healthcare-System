"""
Unit & Integration Tests for Level 6 Frontier Data Systems & Cryptography:
- Cryptographic Zero-Knowledge ETL Provenance (zk-ETL Merkle DAGs)
- Secure Multi-Party Computation (SMPC) & Commutative Diffie-Hellman PSI
- SIMD Vectorized Columnar Execution Engine (PyArrow SIMD Kernels)
- Autonomous Storage Graph & Z-Order Space-Filling Partitioner
- FastAPI /v1/data-systems/ REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.data_platform.autonomous_storage_graph import autonomous_storage_graph
from backend.data_platform.simd_vector_engine import ColumnarPredicate, simd_engine
from backend.data_platform.smpc_private_join import smpc_engine
from backend.data_platform.zk_etl_lineage import zk_etl_engine
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. Zero-Knowledge ETL Provenance Tests
# =====================================================================

def test_zk_etl_merkle_tree_consistency():
    """Verify Merkle root determinism and sensitivity to single-bit changes."""
    records_1 = [
        {"patient_id": "P001", "vital": 120, "code": "I10"},
        {"patient_id": "P002", "vital": 135, "code": "E11"},
        {"patient_id": "P003", "vital": 110, "code": "J45"},
    ]
    records_2 = [
        {"patient_id": "P001", "vital": 120, "code": "I10"},
        {"patient_id": "P002", "vital": 136, "code": "E11"},  # Tampered vital
        {"patient_id": "P003", "vital": 110, "code": "J45"},
    ]

    root_1, leaves_1 = zk_etl_engine.build_merkle_tree(records_1)
    root_1_repeat, _ = zk_etl_engine.build_merkle_tree(records_1)
    root_2, leaves_2 = zk_etl_engine.build_merkle_tree(records_2)

    assert root_1 == root_1_repeat, "Merkle root must be deterministic"
    assert root_1 != root_2, "Tampered record must produce completely distinct Merkle root"
    assert len(leaves_1) == 3
    assert leaves_1[1] != leaves_2[1]


def test_zk_etl_proof_generation_and_verification():
    """Verify cryptographic proof generation and tamper detection."""
    bronze_records = [
        {"raw_id": "B-101", "source": "HL7_FEED", "val": 98.6},
        {"raw_id": "B-102", "source": "HL7_FEED", "val": 101.4},
    ]
    silver_records = [
        {"patient_id": "P-101", "temp_f": 98.6, "fever": False},
        {"patient_id": "P-102", "temp_f": 101.4, "fever": True},
    ]

    receipt = zk_etl_engine.generate_etl_proof(
        transformation_name="normalize_vitals_stage",
        input_records=bronze_records,
        output_records=silver_records,
        pipeline_stage="BRONZE_TO_SILVER",
    )

    assert receipt.proof_token.startswith("PROOF-ETL-")
    assert receipt.num_input_records == 2
    assert receipt.num_output_records == 2

    # Verification with legitimate datasets
    valid, msg = zk_etl_engine.verify_etl_proof(
        proof_token=receipt.proof_token,
        claimed_input_records=bronze_records,
        claimed_output_records=silver_records,
    )
    assert valid is True
    assert "Output dataset authentic" in msg

    # Verification fails on forged/tampered output
    tampered_silver = [
        {"patient_id": "P-101", "temp_f": 98.6, "fever": False},
        {"patient_id": "P-102", "temp_f": 101.4, "fever": False},  # Forged flag
    ]
    valid_bad, msg_bad = zk_etl_engine.verify_etl_proof(
        proof_token=receipt.proof_token,
        claimed_input_records=bronze_records,
        claimed_output_records=tampered_silver,
    )
    assert valid_bad is False
    assert "Output Merkle root mismatch" in msg_bad


def test_zk_etl_api_endpoints(client):
    """Verify FastAPI /zk-etl/prove and /zk-etl/verify endpoints."""
    in_recs = [{"id": "A1", "status": "active"}]
    out_recs = [{"id": "A1", "status": "active", "curated": True}]

    # 1. Prove
    res_prove = client.post(
        "/v1/data-systems/zk-etl/prove",
        json={
            "transformation_name": "test_curation",
            "pipeline_stage": "BRONZE_TO_SILVER",
            "input_records": in_recs,
            "output_records": out_recs,
        },
    )
    assert res_prove.status_code == 201
    data_prove = res_prove.json()
    token = data_prove["proof_token"]
    assert token.startswith("PROOF-ETL-")

    # 2. Verify
    res_verify = client.post(
        "/v1/data-systems/zk-etl/verify",
        json={
            "proof_token": token,
            "claimed_input_records": in_recs,
            "claimed_output_records": out_recs,
        },
    )
    assert res_verify.status_code == 200
    assert res_verify.json()["verified"] is True


# =====================================================================
# 2. SMPC & Private Set Intersection Tests
# =====================================================================

def test_smpc_commutative_dh_psi():
    """Verify Private Set Intersection correctly finds shared cohort without identifier leakage."""
    cohort_hospital_alpha = [f"PT-{i:04d}" for i in range(1, 11)]  # PT-0001 to PT-0010
    cohort_hospital_beta = [f"PT-{i:04d}" for i in range(6, 16)]   # PT-0006 to PT-0015
    # Expected overlap: PT-0006, PT-0007, PT-0008, PT-0009, PT-0010 (5 patients)

    result = smpc_engine.compute_psi(
        identifiers_a=cohort_hospital_alpha,
        identifiers_b=cohort_hospital_beta,
    )

    assert result.intersection_size == 5
    assert result.cohort_alpha_size == 10
    assert result.cohort_beta_size == 10
    # Jaccard = 5 / 15 = 0.3333
    assert pytest.approx(result.jaccard_similarity, abs=1e-2) == 0.3333
    assert len(result.matched_double_blinded_tokens) == 5


def test_smpc_additive_secret_sharing_aggregation():
    """Verify 2-party additive secret sharing computes exact federated mean and sum."""
    egfr_alpha = [85.5, 92.0, 74.2, 60.1, 105.0]
    egfr_beta = [55.4, 48.0, 70.3, 88.2, 91.5]

    expected_sum = sum(egfr_alpha) + sum(egfr_beta)
    expected_mean = expected_sum / (len(egfr_alpha) + len(egfr_beta))

    agg = smpc_engine.federated_additive_secret_share_aggregate(
        values_a=egfr_alpha,
        values_b=egfr_beta,
    )

    assert agg["total_records"] == 10
    assert pytest.approx(agg["federated_sum"], abs=1e-2) == expected_sum
    assert pytest.approx(agg["federated_mean"], abs=1e-2) == expected_mean
    assert agg["zero_leakage_guarantee"] is True


def test_smpc_api_endpoints(client):
    """Verify FastAPI /smpc/private-join and /smpc/secret-share-aggregate endpoints."""
    # 1. PSI Endpoint
    res_psi = client.post(
        "/v1/data-systems/smpc/private-join",
        json={
            "identifiers_a": ["ABC", "DEF", "GHI"],
            "identifiers_b": ["XYZ", "DEF", "UVW"],
        },
    )
    assert res_psi.status_code == 200
    data_psi = res_psi.json()
    assert data_psi["intersection_size"] == 1
    assert data_psi["cohort_alpha_size"] == 3

    # 2. Secret Share Aggregate Endpoint
    res_ss = client.post(
        "/v1/data-systems/smpc/secret-share-aggregate",
        json={
            "values_a": [10.0, 20.0],
            "values_b": [30.0, 40.0],
        },
    )
    assert res_ss.status_code == 200
    data_ss = res_ss.json()
    assert data_ss["federated_sum"] == 100.0
    assert data_ss["federated_mean"] == 25.0


# =====================================================================
# 3. SIMD Vector Execution Engine Tests
# =====================================================================

def test_simd_multi_predicate_filtering_and_aggregates():
    """Verify PyArrow SIMD multi-predicate filtering and columnar aggregations."""
    records = [
        {"patient_id": f"P-{i}", "age": 50 + i, "systolic_bp": 110 + (i * 5), "ward": "ICU" if i % 2 == 0 else "WARD"}
        for i in range(20)
    ]

    table = simd_engine.create_record_batch(records)
    preds = [
        ColumnarPredicate(column="age", operator=">=", value=60),
        ColumnarPredicate(column="systolic_bp", operator="<=", value=180),
        ColumnarPredicate(column="ward", operator="==", value="ICU"),
    ]

    filtered_table, metrics = simd_engine.evaluate_predicates(table, preds)
    assert metrics.total_records_scanned == 20
    assert metrics.matched_records > 0
    assert metrics.filter_latency_microseconds >= 0.0

    # Aggregates
    aggs = simd_engine.compute_columnar_aggregates(filtered_table, ["age", "systolic_bp", "ward"])
    assert "age" in aggs
    assert aggs["age"]["mean"] >= 60.0
    assert "median" in aggs["age"]
    assert "ward" in aggs
    assert aggs["ward"]["count"] == metrics.matched_records


def test_simd_api_endpoint(client):
    """Verify FastAPI /simd/execute endpoint."""
    records = [
        {"patient_id": "P1", "age": 72, "egfr": 42.0},
        {"patient_id": "P2", "age": 45, "egfr": 95.0},
        {"patient_id": "P3", "age": 68, "egfr": 38.5},
    ]

    res = client.post(
        "/v1/data-systems/simd/execute",
        json={
            "records": records,
            "predicates": [
                {"column": "age", "operator": ">=", "value": 60},
                {"column": "egfr", "operator": "<", "value": 50.0},
            ],
            "aggregate_columns": ["age", "egfr"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["filtered_records"]) == 2
    assert data["metrics"]["matched_records"] == 2
    assert "egfr" in data["aggregates"]
    assert data["aggregates"]["egfr"]["min"] == 38.5


# =====================================================================
# 4. Autonomous Storage Graph & Z-Order Tests
# =====================================================================

def test_autonomous_storage_graph_affinity():
    """Verify storage access profiling and dimension recommendation."""
    autonomous_storage_graph.record_query(
        query_id="Q-001",
        columns=["age", "admission_timestamp", "icd10_code"],
        predicates={"age": ">65"},
        rows_scanned=5000,
        rows_returned=200,
        execution_time_ms=12.5,
    )
    autonomous_storage_graph.record_query(
        query_id="Q-002",
        columns=["age", "admission_timestamp", "systolic_bp"],
        predicates={"age": ">50"},
        rows_scanned=5000,
        rows_returned=800,
        execution_time_ms=15.0,
    )

    graph = autonomous_storage_graph.get_affinity_graph()
    assert graph["total_queries_analyzed"] >= 2
    assert graph["columns_tracked"] >= 3

    keys = autonomous_storage_graph.recommend_clustering_keys(max_dimensions=2)
    assert len(keys) == 2
    assert "age" in keys or "admission_timestamp" in keys


def test_storage_z_order_encoding_and_pruning_simulation():
    """Verify Z-order bit-interleaving and physical block pruning simulation."""
    records = [
        {"id": 1, "age": 20, "sys_bp": 110},
        {"id": 2, "age": 80, "sys_bp": 160},
        {"id": 3, "age": 30, "sys_bp": 120},
        {"id": 4, "age": 70, "sys_bp": 150},
    ]
    z_records = autonomous_storage_graph.compute_dataset_z_order(records, ["age", "sys_bp"])
    assert len(z_records) == 4
    for r in z_records:
        assert "_z_order_code" in r

    plan = autonomous_storage_graph.simulate_io_pruning(
        num_records=100_000,
        block_size=1_000,
        dimension_columns=["age", "sys_bp"],
        selectivity_per_dim=0.20,
    )
    assert plan.estimated_io_pruning_pct > 50.0
    assert plan.simulated_blocks_scanned < plan.simulated_blocks_total


def test_storage_api_endpoints_and_health(client):
    """Verify FastAPI storage endpoints and subsystem health check."""
    # 1. Profile query access
    res_prof = client.post(
        "/v1/data-systems/storage/profile-access",
        json={
            "query_id": "API-Q-1",
            "columns_referenced": ["age", "lab_crp"],
            "filter_predicates": {"lab_crp": ">10"},
            "rows_scanned": 1000,
            "rows_returned": 50,
            "execution_time_ms": 5.2,
        },
    )
    assert res_prof.status_code == 200
    assert res_prof.json()["status"] == "RECORDED"

    # 2. Get affinity graph
    res_graph = client.get("/v1/data-systems/storage/affinity-graph")
    assert res_graph.status_code == 200
    assert res_graph.json()["total_queries_analyzed"] >= 1

    # 3. Optimize Z-order
    res_opt = client.post(
        "/v1/data-systems/storage/optimize-zorder",
        json={
            "num_records": 50_000,
            "block_size": 1_000,
            "dimension_columns": ["age", "lab_crp"],
        },
    )
    assert res_opt.status_code == 200
    assert res_opt.json()["estimated_io_pruning_pct"] > 50.0

    # 4. Health
    res_health = client.get("/v1/data-systems/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "HEALTHY"
    assert res_health.json()["subsystems"]["zk_etl_lineage"] == "ACTIVE"
