"""
Unit tests for Polars, DuckDB, and Apache Iceberg / Delta Lake multi-format engines.
"""

from backend.data_platform.multi_format_exporter import (
    OpenTableSpec,
    multi_format_exporter,
)
from backend.data_platform.polars_duckdb_engine import (
    polars_duckdb_engine,
)


def test_polars_duckdb_engine_filtering():
    records = [
        {"patient_id": "P101", "dept": "cardiology", "hr": 78},
        {"patient_id": "P102", "dept": "neurology", "hr": 82},
        {"patient_id": "P103", "dept": "cardiology", "hr": 95},
    ]

    res = polars_duckdb_engine.execute_polars_pipeline(records, "dept", "cardiology")
    assert res.record_count == 2
    assert res.engine_used in ("POLARS_RUST", "PYTHON_FALLBACK")
    assert len(res.rows) == 2


def test_duckdb_sql_execution():
    records = [
        {"patient_id": "P101", "hr": 78},
        {"patient_id": "P102", "hr": 110},
        {"patient_id": "P103", "hr": 65},
    ]

    sql = "SELECT * FROM vitals WHERE hr > 70"
    res = polars_duckdb_engine.execute_duckdb_sql(sql, table_name="vitals", records=records)
    assert res.engine_used in ("DUCKDB_VECTORIZED", "PYTHON_FALLBACK")
    assert res.record_count >= 1


def test_iceberg_manifest_exporter():
    cols = {"patient_id": "string", "heart_rate": "int", "timestamp": "long"}
    pkeys = ["patient_id"]

    manifest = multi_format_exporter.generate_iceberg_manifest(
        table_name="patient_vitals_iceberg",
        columns=cols,
        partition_keys=pkeys,
        location="s3://healthcare-lakehouse",
    )

    assert manifest.table_spec == OpenTableSpec.APACHE_ICEBERG
    assert len(manifest.schema_fields) == 3
    assert manifest.partition_specs[0].name == "patient_id"


def test_delta_manifest_exporter():
    cols = {"patient_id": "string", "glucose": "double"}
    delta_meta = multi_format_exporter.generate_delta_manifest(
        table_name="labs_delta",
        columns=cols,
        location="s3://healthcare-lakehouse",
    )

    assert "commitInfo" in delta_meta
    assert "metaData" in delta_meta
    assert delta_meta["metaData"]["format"]["provider"] == "parquet"
