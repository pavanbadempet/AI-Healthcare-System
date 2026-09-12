"""
Unit & Integration Tests for Peak Healthcare Data Engineering Capabilities:
- Bi-Temporal Event Sourcing & Zero-Leakage Point-in-Time (PIT) As-Of Joins
- Zero-Copy Streaming Kappa Architecture with Apache Arrow Columnar Memory
- Enforceable Enterprise Data Contracts & Schema Drift DLQ Quarantine
- (epsilon, delta)-Differential Privacy Synthetic EHR Cohort Synthesis
- Point-in-Time Feature Store with Automated Drift Monitoring (PSI, Wasserstein)
- FastAPI /v1/data-engineering/ REST Endpoints
"""

from datetime import datetime, timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.data_platform.bitemporal_engine import bitemporal_engine
from backend.data_platform.data_contracts import contract_enforcement_engine
from backend.data_platform.differential_privacy_engine import dp_synth_engine
from backend.data_platform.feature_drift_monitor import feature_drift_monitor
from backend.data_platform.kappa_streaming import kappa_streaming_engine
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. Bi-Temporal Event Sourcing Tests
# =====================================================================

def test_bitemporal_insert_and_dual_clocks():
    """Verify insertion sets valid_time and system_time with unbounded ends."""
    t_valid = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    t_sys = datetime(2026, 3, 1, 9, 30, tzinfo=timezone.utc)

    rec = bitemporal_engine.insert_clinical_event(
        record_id="REC-TEST-01",
        entity_id="PT-BITEMP-1",
        attribute_name="serum_creatinine",
        attribute_value=1.4,
        valid_time=t_valid,
        unit="mg/dL",
        system_time=t_sys,
    )
    assert rec.entity_id == "PT-BITEMP-1"
    assert rec.attribute_value == 1.4
    assert rec.valid_time_start == t_valid
    assert rec.system_time_start == t_sys
    assert rec.version == 1


def test_bitemporal_retroactive_amendment_and_as_of_query():
    """
    Verify retroactive correction closes superseded record in system-time,
    and query_as_of reconstructs past knowledge vs current knowledge.
    """
    t_event = datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc)
    t_initial_ingest = datetime(2026, 3, 2, 11, 0, tzinfo=timezone.utc)
    t_recalibration = datetime(2026, 3, 3, 15, 0, tzinfo=timezone.utc)

    # 1. Initial flawed lab result (e.g. 2.1 mg/dL)
    bitemporal_engine.insert_clinical_event(
        record_id="REC-LAB-OLD",
        entity_id="PT-AMEND-1",
        attribute_name="potassium",
        attribute_value=5.8,
        valid_time=t_event,
        system_time=t_initial_ingest,
    )

    # 2. Retroactive recalibration: lab was hemolyzed, corrected to 4.6 mg/dL on March 3
    old_rec, new_rec = bitemporal_engine.amend_clinical_event(
        entity_id="PT-AMEND-1",
        attribute_name="potassium",
        new_attribute_value=4.6,
        effective_valid_time=t_event,
        amendment_reason="Sample hemolysis correction",
        system_time=t_recalibration,
    )

    assert old_rec.system_time_end == t_recalibration
    assert new_rec.attribute_value == 4.6
    assert new_rec.version == 2

    # 3. Query AS OF SYSTEM TIME March 2 (before correction) -> Must see old 5.8
    past_slice = bitemporal_engine.query_as_of(
        entity_id="PT-AMEND-1",
        valid_time=t_event,
        system_time=datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc),
    )
    assert past_slice.features["potassium"] == 5.8
    assert past_slice.active_versions["potassium"] == 1

    # 4. Query AS OF SYSTEM TIME March 4 (after correction) -> Must see new 4.6
    current_slice = bitemporal_engine.query_as_of(
        entity_id="PT-AMEND-1",
        valid_time=t_event,
        system_time=datetime(2026, 3, 4, 12, 0, tzinfo=timezone.utc),
    )
    assert current_slice.features["potassium"] == 4.6
    assert current_slice.active_versions["potassium"] == 2


def test_bitemporal_point_in_time_feature_join_no_leakage():
    """Verify point-in-time join strictly filters future records."""
    t0 = datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 10, 18, 0, tzinfo=timezone.utc)

    bitemporal_engine.insert_clinical_event("R1", "PT-PIT-JOIN", "map", 70.0, t0, system_time=t0)
    bitemporal_engine.insert_clinical_event("R2", "PT-PIT-JOIN", "map", 62.0, t2, system_time=t2)

    # Query at decision point t1 (12:00) -> Cannot see the 18:00 MAP reading
    slices = bitemporal_engine.point_in_time_feature_join(
        entity_id="PT-PIT-JOIN",
        decision_timestamps=[t1],
        feature_names=["map"],
    )
    assert len(slices) == 1
    assert slices[0].features["map"] == 70.0
    assert slices[0].zero_leakage_verified is True


# =====================================================================
# 2. Zero-Copy Streaming Kappa Architecture Tests
# =====================================================================

def test_kappa_streaming_arrow_ingestion_and_cdc():
    """Verify zero-copy PyArrow ingestion and CDC Write-Ahead Log entries."""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    records = [
        {
            "patient_id": "PT-STREAM-01",
            "timestamp_epoch_ms": now_ms - 20000,
            "metric_name": "heart_rate",
            "metric_value": 78.0,
            "unit": "bpm",
            "device_id": "DEV-01",
        },
        {
            "patient_id": "PT-STREAM-01",
            "timestamp_epoch_ms": now_ms - 10000,
            "metric_name": "heart_rate",
            "metric_value": 82.0,
            "unit": "bpm",
            "device_id": "DEV-01",
        },
        {
            "patient_id": "PT-STREAM-01",
            "timestamp_epoch_ms": now_ms,
            "metric_name": "heart_rate",
            "metric_value": 88.0,
            "unit": "bpm",
            "device_id": "DEV-01",
        },
    ]

    batch = kappa_streaming_engine.ingest_batch_arrow(records, table_name="icu_telemetry")
    assert batch.num_rows == 3
    assert batch.num_columns == 6

    # Verify CDC WAL
    wal_entries = kappa_streaming_engine.replay_cdc_wal(from_lsn=0, limit=50)
    assert len(wal_entries) >= 3
    assert wal_entries[-1].table_name == "icu_telemetry"


def test_kappa_streaming_window_aggregates():
    """Verify sliding window mean, min, max, std and slope calculation."""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    pts = [
        {"patient_id": "PT-WIN-01", "timestamp_epoch_ms": now_ms - 60000, "metric_name": "map", "metric_value": 70.0, "unit": "mmHg", "device_id": "D1"},
        {"patient_id": "PT-WIN-01", "timestamp_epoch_ms": now_ms - 30000, "metric_name": "map", "metric_value": 75.0, "unit": "mmHg", "device_id": "D1"},
        {"patient_id": "PT-WIN-01", "timestamp_epoch_ms": now_ms, "metric_name": "map", "metric_value": 80.0, "unit": "mmHg", "device_id": "D1"},
    ]
    kappa_streaming_engine.ingest_batch_arrow(pts)

    agg = kappa_streaming_engine.compute_windowed_aggregates("PT-WIN-01", "map", window_duration_seconds=120)
    assert agg is not None
    assert agg.count == 3
    assert agg.mean == 75.0
    assert agg.min_val == 70.0
    assert agg.max_val == 80.0
    assert agg.slope_velocity > 0.0  # MAP is rising


# =====================================================================
# 3. Enforceable Enterprise Data Contracts Tests
# =====================================================================

def test_contract_validation_compliant_payload():
    """Verify compliant vital signs payload passes contract validation."""
    payload = {
        "patient_id": "PT-VITAL-01",
        "timestamp": "2026-09-12T12:00:00Z",
        "systolic_bp": 120.0,
        "diastolic_bp": 80.0,
        "heart_rate": 72.0,
        "spo2": 98.0,
    }
    res = contract_enforcement_engine.validate_payload("vitals_contract_v1", payload)
    assert res.is_valid is True
    assert res.quarantined is False
    assert len(res.violations) == 0


def test_contract_validation_breaking_violation_quarantined():
    """Verify missing required keys and out-of-bounds values are quarantined to DLQ."""
    corrupt_payload = {
        "patient_id": "PT-CORRUPT-01",
        "timestamp": "2026-09-12T12:00:00Z",
        # missing systolic_bp
        "diastolic_bp": 350.0,  # out of clinical range
        "heart_rate": "invalid_string_not_float",  # type mismatch
    }
    res = contract_enforcement_engine.validate_payload("vitals_contract_v1", corrupt_payload)
    assert res.is_valid is False
    assert res.quarantined is True
    assert res.quarantine_id is not None
    assert len(res.violations) >= 2

    # Check DLQ entry
    dlq_records = contract_enforcement_engine.get_quarantined_records()
    assert any(q.quarantine_id == res.quarantine_id for q in dlq_records)


# =====================================================================
# 4. Differential Privacy Synthetic EHR Tests
# =====================================================================

def test_differential_privacy_synthesis():
    """Verify synthetic cohort generation obeys privacy budget and covariance bounds."""
    report = dp_synth_engine.synthesize_cohort(
        cohort_id="COHORT-DP-TEST",
        n_patients=20,
        epsilon=1.0,
        delta=1e-5,
    )
    assert report.num_synthesized == 20
    assert len(report.synthetic_records) == 20
    assert report.empirical_covariance_preserved is True
    assert report.privacy_budget_status.epsilon_spent >= 1.0

    # Inspect a synthetic patient
    p0 = report.synthetic_records[0]
    assert 18.0 <= p0.age <= 95.0
    assert 50.0 <= p0.systolic_bp <= 220.0
    assert p0.gender in {"M", "F"}
    assert p0.primary_icd10 is not None


# =====================================================================
# 5. Point-in-Time Feature Store Drift Monitoring Tests
# =====================================================================

def test_feature_drift_normal_distribution():
    """Verify similar sample distribution produces normal PSI score (< 0.10)."""
    # Sample matching baseline egfr distribution (mean ~ 72, std ~ 18, n=100)
    rng = np.random.RandomState(42)
    curr_samples = rng.normal(loc=72.0, scale=18.0, size=100).tolist()
    report = feature_drift_monitor.audit_feature_drift("egfr", curr_samples)
    assert report.feature_name == "egfr"
    assert report.sample_size_current == 100
    assert report.drift_status in {"NORMAL", "MODERATE_SHIFT"}
    assert report.requires_retraining is False


def test_feature_drift_critical_alert():
    """Verify severely shifted sample distribution triggers critical drift alarm (PSI >= 0.25)."""
    # Severe renal failure shift (all eGFR < 20 mL/min vs baseline mean 72)
    shifted_samples = [12.0, 14.5, 11.0, 15.2, 13.8, 16.0, 10.5, 14.0, 12.5, 13.0]
    report = feature_drift_monitor.audit_feature_drift("egfr", shifted_samples)
    assert report.drift_status == "CRITICAL_DRIFT_ALERT"
    assert report.requires_retraining is True
    assert report.psi_score >= 0.25


# =====================================================================
# 6. FastAPI /v1/data-engineering/ REST Endpoints Tests
# =====================================================================

def test_api_bitemporal_insert_and_query(client: TestClient):
    insert_payload = {
        "record_id": "REC-API-01",
        "entity_id": "PT-API-DE-1",
        "attribute_name": "map",
        "attribute_value": 76.5,
        "valid_time_iso": "2026-05-01T10:00:00Z",
        "system_time_iso": "2026-05-01T10:05:00Z",
        "unit": "mmHg",
    }
    res_ins = client.post("/v1/data-engineering/bitemporal/insert", json=insert_payload)
    assert res_ins.status_code == 200
    data_ins = res_ins.json()
    assert data_ins["record_id"] == "REC-API-01"

    query_payload = {
        "entity_id": "PT-API-DE-1",
        "as_of_valid_time_iso": "2026-05-01T10:30:00Z",
        "as_of_system_time_iso": "2026-05-01T11:00:00Z",
    }
    res_query = client.post("/v1/data-engineering/bitemporal/as-of-query", json=query_payload)
    assert res_query.status_code == 200
    data_query = res_query.json()
    assert data_query["features"]["map"] == 76.5
    assert data_query["zero_leakage_verified"] is True


def test_api_streaming_batch_and_window(client: TestClient):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    batch_payload = {
        "table_name": "api_telemetry",
        "records": [
            {"patient_id": "PT-API-STREAM", "timestamp_epoch_ms": now_ms - 2000, "metric_name": "spo2", "metric_value": 98.0, "unit": "percent", "device_id": "PULSE_OX"},
            {"patient_id": "PT-API-STREAM", "timestamp_epoch_ms": now_ms, "metric_name": "spo2", "metric_value": 97.5, "unit": "percent", "device_id": "PULSE_OX"},
        ],
    }
    res_batch = client.post("/v1/data-engineering/streaming/ingest-batch", json=batch_payload)
    assert res_batch.status_code == 200
    assert res_batch.json()["zero_copy_success"] is True

    window_payload = {
        "patient_id": "PT-API-STREAM",
        "metric_name": "spo2",
        "window_duration_seconds": 60,
    }
    res_win = client.post("/v1/data-engineering/streaming/window-aggregates", json=window_payload)
    assert res_win.status_code == 200
    data_win = res_win.json()
    assert data_win["count"] == 2
    assert data_win["mean"] == 97.75


def test_api_contract_validation(client: TestClient):
    payload = {
        "contract_id": "vitals_contract_v1",
        "payload": {
            "patient_id": "PT-API-VAL",
            "timestamp": "2026-09-12T12:00:00Z",
            "systolic_bp": 122.0,
            "diastolic_bp": 78.0,
            "heart_rate": 68.0,
        },
    }
    res = client.post("/v1/data-engineering/contracts/validate", json=payload)
    assert res.status_code == 200
    assert res.json()["is_valid"] is True


def test_api_privacy_synthesize_cohort(client: TestClient):
    payload = {
        "cohort_id": "COHORT-API-SYNTH",
        "n_patients": 10,
        "epsilon": 0.5,
        "delta": 1e-5,
    }
    res = client.post("/v1/data-engineering/privacy/synthesize-cohort", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["num_synthesized"] == 10
    assert len(data["synthetic_records"]) == 10


def test_api_feature_drift_audit(client: TestClient):
    payload = {
        "feature_name": "map",
        "current_samples": [77.0, 78.5, 79.0, 76.0, 80.0, 77.5, 78.0],
    }
    res = client.post("/v1/data-engineering/features/drift-audit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["feature_name"] == "map"
    assert "psi_score" in data
