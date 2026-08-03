"""
AI Healthcare System — Unified Data + AI Platform API Router.

Exposes REST endpoints for:
- Lakehouse SQL Query execution
- Clinical Data Catalog search & access checks
- MedFlow declarative ETL pipeline runs
- Agentic BI natural language analytics
- Spark 4.x Variant JSON shredding & Spark Connect session status
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from backend.data_platform.lakehouse_sql import lakehouse_sql_engine
from backend.data_platform.data_catalog import clinical_data_catalog, AssetType
from backend.data_platform.lakeflow import medflow_orchestrator
from backend.data_platform.agentic_bi import agentic_bi_engine
from backend.data_platform.data_apps import data_ai_apps_runtime
from backend.spark_engine import spark4_variant_handler, spark_connect_manager

router = APIRouter(prefix="/api/v1/data-platform", tags=["Unified Data Platform"])


# =====================================================================
# Request & Response Schemas
# =====================================================================

class SQLExecuteRequest(BaseModel):
    sql: str
    warehouse_id: Optional[str] = "clinical-warehouse-01"


class BIAskRequest(BaseModel):
    question: str
    table: Optional[str] = "sql_test"


class VariantShredRequest(BaseModel):
    raw_json: str
    target_fields: List[str] = Field(default_factory=list)


# =====================================================================
# Endpoints
# =====================================================================

@router.post("/sql/execute")
def execute_lakehouse_sql(req: SQLExecuteRequest) -> Dict[str, Any]:
    """Execute SQL query over Lakehouse ACID tables."""
    try:
        res = lakehouse_sql_engine.execute(req.sql)
        return {
            "columns": res.columns,
            "rows": res.rows,
            "total_count": res.total_count,
            "profile": res.profile.model_dump(),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/catalog/search")
def search_catalog(
    query: str = Query(..., min_length=1),
    asset_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Search Clinical Data Catalog assets."""
    atype = AssetType(asset_type) if asset_type else None
    results = clinical_data_catalog.search(query, asset_type=atype)
    return {
        "query": query,
        "results_count": len(results),
        "assets": [a.model_dump() for a in results],
    }


@router.post("/bi/ask")
def ask_agentic_bi(req: BIAskRequest) -> Dict[str, Any]:
    """Answer natural language BI question using AI BI Engine."""
    try:
        ans = agentic_bi_engine.ask(req.question, table=req.table or "sql_test")
        return ans.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/spark/variant-shred")
def shred_variant_json(req: VariantShredRequest) -> Dict[str, Any]:
    """Parse & shred semi-structured JSON using Spark 4.x Variant Engine."""
    try:
        shredded = spark4_variant_handler.parse_variant_blob(req.raw_json, req.target_fields)
        return shredded.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/apps/list")
def list_data_apps() -> Dict[str, Any]:
    """List registered Data & AI Apps."""
    apps = data_ai_apps_runtime.list_apps()
    return {"total": len(apps), "apps": [a.model_dump() for a in apps]}
