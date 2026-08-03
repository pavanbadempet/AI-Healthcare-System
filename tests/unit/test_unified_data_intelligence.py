"""
Unit tests for Unified Data Intelligence Platform:
- Clinical Feature Store
- Data Lineage Tracker
- Real-Time Streaming Analytics Engine
- Data Quality Gate
- Unified Query Fabric
"""

from backend.unified_data_intelligence import (
    ClinicalFeatureStore,
    StreamingAnalyticsEngine,
    data_lineage_tracker,
    data_quality_gate,
    unified_query_fabric,
)


def test_clinical_feature_store_upsert_and_versioning():
    store = ClinicalFeatureStore()
    v1 = store.upsert_feature("P-200", "rolling_hr_mean", 72.5)
    assert v1.version == 1

    v2 = store.upsert_feature("P-200", "rolling_hr_mean", 78.0)
    assert v2.version == 2

    latest = store.get_latest("P-200", "rolling_hr_mean")
    assert latest is not None
    assert latest.value == 78.0
    assert store.total_features == 1


def test_data_lineage_tracker_provenance_chain():
    src = data_lineage_tracker.register_node("HL7_ADT_Feed", "SOURCE")
    transform = data_lineage_tracker.register_node("Vitals_Normalizer", "TRANSFORM", upstream_ids=[src.node_id])
    sink = data_lineage_tracker.register_node("Feature_Store_Sink", "SINK", upstream_ids=[transform.node_id])

    chain = data_lineage_tracker.get_upstream_chain(sink.node_id)
    assert len(chain) == 3
    assert chain[0].name == "Feature_Store_Sink"
    assert chain[-1].name == "HL7_ADT_Feed"


def test_streaming_analytics_anomaly_detection():
    engine = StreamingAnalyticsEngine(window_size=10, z_threshold=2.0)
    # Ingest normal readings
    for hr in [72, 74, 70, 73, 71, 72, 74, 73, 71, 72]:
        engine.ingest("P-300", "heart_rate", float(hr))

    # Ingest anomalous spike
    spike = engine.ingest("P-300", "heart_rate", 150.0)
    assert spike.is_anomaly is True
    assert spike.severity in ("MEDIUM", "HIGH", "CRITICAL")
    assert spike.z_score > 2.0


def test_data_quality_gate_validation():
    good_record = {"patient_id": "P-400", "heart_rate": 80}
    assert data_quality_gate.gate_passes(good_record) is True

    bad_record_no_id = {"heart_rate": 80}
    assert data_quality_gate.gate_passes(bad_record_no_id) is False

    bad_record_hr = {"patient_id": "P-401", "heart_rate": 500}
    assert data_quality_gate.gate_passes(bad_record_hr) is False


def test_unified_query_fabric_federated_query():
    unified_query_fabric.register_domain(
        "vitals",
        lambda patient_id="": [{"patient_id": patient_id, "hr": 72, "spo2": 98}],
    )

    result = unified_query_fabric.query("vitals", patient_id="P-500")
    assert result.domain == "vitals"
    assert result.total_count == 1
    assert result.records[0]["patient_id"] == "P-500"
    assert result.query_time_ms >= 0

    empty = unified_query_fabric.query("nonexistent_domain")
    assert empty.total_count == 0
