"""
Unit & API integration tests for Unified Data + AI Platform & Multi-Agent Supervisor FastAPI routes.
"""

from fastapi.testclient import TestClient

from backend.data_platform.open_table_format import TableSchema, open_table_engine
from backend.main import app

client = TestClient(app)


def test_api_lakehouse_sql_execute():
    # Ensure sample table exists for testing
    if "sql_test" not in open_table_engine.list_tables():
        schema = TableSchema(columns={"id": "str", "dept": "str", "score": "int"})
        tbl = open_table_engine.create_table("sql_test", schema)
        tbl.insert([{"id": "A", "dept": "cardio", "score": 90}])

    res = client.post("/api/v1/data-platform/sql/execute", json={
        "sql": "SELECT COUNT(*) FROM sql_test",
    })
    assert res.status_code == 200
    body = res.json()
    assert "columns" in body
    assert "rows" in body
    assert body["total_count"] >= 1


def test_api_catalog_search():
    res = client.get("/api/v1/data-platform/catalog/search?query=vitals")
    assert res.status_code == 200
    body = res.json()
    assert "query" in body
    assert "assets" in body


def test_api_agentic_bi_ask():
    res = client.post("/api/v1/data-platform/bi/ask", json={
        "question": "how many records in sql_test",
        "table": "sql_test",
    })
    assert res.status_code == 200
    body = res.json()
    assert "generated_sql" in body
    assert "answer" in body


def test_api_spark_variant_shred():
    res = client.post("/api/v1/data-platform/spark/variant-shred", json={
        "raw_json": '{"id": "V-100", "hr": 99, "status": "ACTIVE"}',
        "target_fields": ["hr"],
    })
    assert res.status_code == 200
    body = res.json()
    assert body["record_id"] == "V-100"
    assert body["extracted_fields"]["hr"] == 99


def test_api_data_apps_list():
    res = client.get("/api/v1/data-platform/apps/list")
    assert res.status_code == 200
    body = res.json()
    assert "total" in body
    assert "apps" in body


def test_api_supervisor_agent_route():
    res = client.post("/api/v1/data-platform/agents/route", json={
        "capability": "TRIAGE",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["selected_agent_id"].startswith("AG")
    assert body["confidence"] > 0.0


def test_api_plan_and_execute_orchestration():
    res = client.post("/api/v1/data-platform/agents/plan-and-execute", json={
        "goal": "Evaluate ED Patient Risk & Dosage",
        "steps": [
            {
                "description": "Perform ED Triage Risk Assessment",
                "required_capability": "TRIAGE",
            },
            {
                "description": "Verify Pharmacy Dosage Safety",
                "required_capability": "PHARMACY",
            },
        ],
    })
    assert res.status_code == 200
    body = res.json()
    assert body["overall_status"] == "COMPLETED"
    assert len(body["steps"]) == 2
