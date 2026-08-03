"""
Unit tests for Spark 4.x Enterprise Engine:
- Spark Connect Decoupled Execution Manager
- Variant Data Type Handler (semi-structured FHIR JSON shredding)
- Python Data Source API v2 Interface
- Vectorized PyArrow Columnar Processing Engine
- Stateful RocksDB Structured Streaming Manager
"""

from backend.spark_engine import (
    SparkConnectConfig,
    StreamingStateConfig,
    spark4_data_source,
    spark4_streaming_manager,
    spark4_variant_handler,
    spark_connect_manager,
    vectorized_pyarrow_engine,
)


def test_spark_connect_manager_configuration():
    cfg = SparkConnectConfig(app_name="Test-Spark4", enable_ansi_sql=True)
    assert cfg.app_name == "Test-Spark4"
    assert cfg.enable_ansi_sql is True
    # In zero-config local environment without PySpark cluster, get_session returns None or Session
    session = spark_connect_manager.get_session()
    # Should execute without raising exceptions regardless of PySpark presence
    assert session is None or hasattr(session, "read")


def test_spark4_variant_handler_json_shredding():
    json_blob = '{"id": "FHIR-PATIENT-99", "name": "John Doe", "vital_hr": 88, "status": "ACTIVE"}'
    parsed = spark4_variant_handler.parse_variant_blob(json_blob, target_fields=["name", "vital_hr"])

    assert parsed.record_id == "FHIR-PATIENT-99"
    assert parsed.extracted_fields["name"] == "John Doe"
    assert parsed.extracted_fields["vital_hr"] == 88
    assert "status" not in parsed.extracted_fields


def test_spark4_data_source_v2_registration():
    spark4_data_source.register_schema("vitals_stream", "patient_id STRING, heart_rate INT")
    sample_data = [{"patient_id": "P1", "heart_rate": 75}]

    batch = spark4_data_source.read_batch(sample_data)
    assert len(batch) == 1
    assert batch[0]["patient_id"] == "P1"


def test_vectorized_pyarrow_columnar_stats():
    series = [70.0, 72.0, 75.0, 80.0, 68.0]
    stats = vectorized_pyarrow_engine.compute_columnar_stats(series)

    assert stats["min"] == 68.0
    assert stats["max"] == 80.0
    assert 72.0 <= stats["mean"] <= 74.0
    assert stats["std"] > 0.0


def test_spark4_streaming_manager_rocksdb_state_tracking():
    cfg = StreamingStateConfig(watermark_delay_seconds=15)
    assert cfg.watermark_delay_seconds == 15

    spark4_streaming_manager.track_query("patient_vitals_icu_stream")
    assert spark4_streaming_manager.active_query_count >= 1
