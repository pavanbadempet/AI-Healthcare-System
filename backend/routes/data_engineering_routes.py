"""
FastAPI Router for Enterprise Healthcare Data Engineering Platform:
- OMOP CDM v5.4 Relational Transformations
- Declarative Great Expectations Quality Gates & Quarantine Management
- Delta Lake Time-Travel, Change Data Feed (CDF), and ACID Rollback
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.data_platform.omop_cdm_engine import omop_engine
from backend.data_platform.data_quality_gates import data_quality_gate
from backend.data_platform.delta_time_travel import delta_time_travel

router = APIRouter(prefix="/v1/lakehouse", tags=["Lakehouse Data Engineering"])


class RawPatientPayload(BaseModel):
    patient_id: str
    year_of_birth: int = 1975
    gender: str = "male"
    conditions: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    vitals: Dict[str, Any] = Field(default_factory=dict)


class QualityAuditRequest(BaseModel):
    records: List[Dict[str, Any]]


class TimeTravelRequest(BaseModel):
    table_name: str = "workspace.healthcare_silver.patients"
    target_version: int = 0


class RestoreTableRequest(BaseModel):
    table_name: str = "workspace.healthcare_silver.patients"
    target_version: int = 0


@router.post("/omop/transform", summary="Transform FHIR / EHR Payload to OMOP CDM v5.4")
def transform_to_omop(payload: RawPatientPayload) -> Dict[str, Any]:
    """
    Transforms raw clinical payload into standardized OMOP CDM tables
    (PERSON, VISIT_OCCURRENCE, CONDITION_OCCURRENCE, DRUG_EXPOSURE, MEASUREMENT).
    """
    try:
        return omop_engine.transform_patient_bundle(payload.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OMOP CDM transformation failed: {str(e)}"
        )


@router.post("/quality/audit", summary="Execute Great Expectations Quality Gate & Quarantine Routing")
def audit_data_quality(req: QualityAuditRequest) -> Dict[str, Any]:
    """
    Validates batch against clinical expectation suites, routing dirty records to Quarantine.
    """
    try:
        clean, quarantined, summary = data_quality_gate.validate_and_partition_batch(req.records)
        return {
            "summary": summary,
            "clean_sample": clean[:5],
            "quarantined_sample": quarantined[:5]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data quality audit failed: {str(e)}"
        )


@router.get("/delta/history", summary="Inspect Delta Lake Commit Log & History")
def get_delta_history(table_name: str = Query("workspace.healthcare_silver.patients")) -> List[Dict[str, Any]]:
    """Retrieves chronological commit log for a Delta Lake table."""
    try:
        return delta_time_travel.get_table_history(table_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch table history: {str(e)}"
        )


@router.post("/delta/time-travel", summary="Query Delta Lake Snapshot at Historical Version")
def time_travel_query(req: TimeTravelRequest) -> Dict[str, Any]:
    """Queries a Delta table as of a specific version number."""
    try:
        return delta_time_travel.query_as_of_version(req.table_name, req.target_version)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delta time travel query failed: {str(e)}"
        )


@router.post("/delta/restore", summary="Execute ACID Table Rollback / Restore")
def restore_table(req: RestoreTableRequest) -> Dict[str, Any]:
    """Restores a Delta Lake table to a previous commit version with HIPAA audit logging."""
    try:
        return delta_time_travel.restore_table_to_version(req.table_name, req.target_version)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Table restore failed: {str(e)}"
        )


@router.get("/delta/cdf", summary="Read Delta Lake Change Data Feed (CDF) Stream")
def read_change_data_feed(
    table_name: str = Query("workspace.healthcare_silver.patients"),
    start_version: int = Query(0),
    end_version: int = Query(2)
) -> List[Dict[str, Any]]:
    """Fetches Change Data Feed (CDF) CDC records between two commit versions."""
    try:
        return delta_time_travel.compute_change_data_feed(table_name, start_version, end_version)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CDF stream read failed: {str(e)}"
        )
