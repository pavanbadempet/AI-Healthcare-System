"""
Unit tests for the Unified Clinical Data + AI Platform:
- Open Table Format (ACID, time-travel, MERGE)
- Clinical Data Catalog & Governance
- Lakehouse SQL Engine
- MedFlow ETL Pipeline Orchestrator
- Agentic BI Engine
- Data & AI Apps Runtime
"""

from backend.data_platform.open_table_format import (
    OpenTableFormatEngine, TableSchema,
)
from backend.data_platform.data_catalog import (
    ClinicalDataCatalog, CatalogAsset, AssetType, DataClassification,
    ColumnMetadata, AccessPolicy,
)
from backend.data_platform.lakehouse_sql import LakehouseSQLEngine
from backend.data_platform.lakeflow import MedFlowOrchestrator
from backend.data_platform.agentic_bi import AgenticBIEngine
from backend.data_platform.data_apps import DataAIAppsRuntime, AppStatus


# ── Open Table Format ──────────────────────────────────────────────

def test_open_table_acid_insert_and_time_travel():
    engine = OpenTableFormatEngine()
    schema = TableSchema(columns={"patient_id": "str", "name": "str", "age": "int"})
    tbl = engine.create_table("patients_tt", schema)

    tbl.insert([
        {"patient_id": "P1", "name": "Alice", "age": 30},
        {"patient_id": "P2", "name": "Bob", "age": 45},
    ])
    assert tbl.current_version == 1
    assert tbl.row_count == 2

    # Time-travel: version 0 is empty
    assert len(tbl.read(version=0)) == 0
    assert len(tbl.read(version=1)) == 2


def test_open_table_merge_upsert():
    engine = OpenTableFormatEngine()
    schema = TableSchema(columns={"patient_id": "str", "name": "str", "age": "int"})
    tbl = engine.create_table("patients_merge", schema)

    tbl.insert([{"patient_id": "P1", "name": "Alice", "age": 30}])
    tbl.merge_upsert(
        [{"patient_id": "P1", "name": "Alice", "age": 31},
         {"patient_id": "P3", "name": "Charlie", "age": 50}],
        match_key="patient_id",
    )
    data = tbl.read()
    assert len(data) == 2
    assert any(r["age"] == 31 and r["patient_id"] == "P1" for r in data)
    assert any(r["patient_id"] == "P3" for r in data)


def test_open_table_delete_and_history():
    engine = OpenTableFormatEngine()
    schema = TableSchema(columns={"patient_id": "str", "name": "str", "age": "int"})
    tbl = engine.create_table("patients_del", schema)

    tbl.insert([
        {"patient_id": "P1", "name": "Alice", "age": 30},
        {"patient_id": "P2", "name": "Bob", "age": 45},
    ])
    tbl.delete("patient_id", "P1")
    assert tbl.row_count == 1
    assert tbl.read()[0]["patient_id"] == "P2"
    assert len(tbl.history()) == 2


# ── Clinical Data Catalog ──────────────────────────────────────────

def test_clinical_catalog_register_and_search():
    catalog = ClinicalDataCatalog()
    asset = CatalogAsset(
        catalog="healthcare", schema_name="clinical", name="vitals",
        asset_type=AssetType.TABLE, description="Patient vital signs",
        tags=["vitals", "real-time"], classification=DataClassification.PHI,
        columns=[
            ColumnMetadata(name="patient_id", data_type="STRING", classification=DataClassification.PII),
            ColumnMetadata(name="heart_rate", data_type="INT"),
        ],
    )
    catalog.register_asset(asset)
    assert catalog.total_assets == 1
    assert catalog.get_asset("healthcare", "clinical", "vitals") is not None

    results = catalog.search("vitals")
    assert len(results) == 1
    assert results[0].fully_qualified_name == "healthcare.clinical.vitals"


def test_clinical_catalog_access_policies():
    catalog = ClinicalDataCatalog()
    asset = CatalogAsset(
        catalog="healthcare", schema_name="clinical", name="labs",
        asset_type=AssetType.TABLE,
    )
    catalog.register_asset(asset)

    catalog.add_policy(AccessPolicy(
        asset_fqn="healthcare.clinical.labs",
        principal="dr_smith",
        allowed_columns=["test_name", "result"],
    ))

    assert catalog.check_access("healthcare.clinical.labs", "dr_smith", "test_name") is True
    assert catalog.check_access("healthcare.clinical.labs", "dr_smith", "ssn") is False
    assert catalog.check_access("healthcare.clinical.labs", "unknown_user") is False


# ── Lakehouse SQL Engine ───────────────────────────────────────────

def test_lakehouse_sql_select_and_where():
    from backend.data_platform.open_table_format import open_table_engine, TableSchema as TS
    schema = TS(columns={"id": "str", "dept": "str", "score": "int"})
    if "sql_test" not in open_table_engine.list_tables():
        tbl = open_table_engine.create_table("sql_test", schema)
        tbl.insert([
            {"id": "A", "dept": "cardio", "score": 90},
            {"id": "B", "dept": "neuro", "score": 85},
            {"id": "C", "dept": "cardio", "score": 95},
        ])

    sql_eng = LakehouseSQLEngine()
    result = sql_eng.execute("SELECT * FROM sql_test WHERE dept = 'cardio'")
    assert result.total_count == 2

    count_res = sql_eng.execute("SELECT COUNT(*) FROM sql_test")
    assert count_res.rows[0]["count"] == 3


# ── MedFlow Pipeline ─────────────────────────────────────────────

def test_medflow_pipeline_end_to_end():
    orch = MedFlowOrchestrator()
    pipe = orch.create_pipeline("vitals_etl")
    sink_data: list = []

    pipe.add_source("hl7_feed", lambda: [
        {"patient_id": "P1", "hr": 72},
        {"patient_id": "P2", "hr": 110},
    ])
    pipe.add_transform("flag_tachycardia", lambda data: [
        {**r, "tachycardia": r["hr"] > 100} for r in data
    ])
    pipe.add_sink("store_results", lambda data: (sink_data.extend(data), len(data))[1])

    run = pipe.execute()
    assert run.status == "COMPLETED"
    assert len(run.steps) == 3
    assert all(s.status.value == "COMPLETED" for s in run.steps)
    assert len(sink_data) == 2
    assert sink_data[1]["tachycardia"] is True


# ── Agentic BI Engine ──────────────────────────────────────────────

def test_agentic_bi_natural_language_query():
    bi = AgenticBIEngine()
    answer = bi.ask("how many patients are in sql_test", table="sql_test")
    assert answer.generated_sql != ""
    assert "COUNT" in answer.generated_sql
    assert answer.metrics.get("count", 0) >= 0


# ── Data & AI Apps Runtime ─────────────────────────────────────────

def test_data_apps_register_deploy_invoke():
    runtime = DataAIAppsRuntime()
    app = runtime.register_app(
        name="Renal Risk Calculator",
        handler=lambda creatinine=1.0, age=50: {"risk": "LOW" if creatinine < 1.5 else "HIGH"},
        description="Calculates renal risk from creatinine and age",
        app_type="ML_APP",
        input_schema={"creatinine": "float", "age": "int"},
        output_schema={"risk": "str"},
    )
    assert app.status == AppStatus.REGISTERED

    runtime.deploy(app.app_id)
    assert runtime.health_check(app.app_id)["healthy"] is True

    result = runtime.invoke(app.app_id, creatinine=0.9, age=45)
    assert result.status == "SUCCESS"
    assert result.output["risk"] == "LOW"

    runtime.stop(app.app_id)
    assert runtime.health_check(app.app_id)["healthy"] is False
