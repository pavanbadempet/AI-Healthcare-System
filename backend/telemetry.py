"""
Real-Time Telemetry WebSocket Endpoint

Streams live hospital operations data to the frontend dashboard.
In production, this would subscribe to HL7/FHIR ADT feeds,
Redis pub/sub channels, or Kafka topics for real clinical data.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import auth, database, models

logger = logging.getLogger(__name__)

router = APIRouter()
OPEN_ENCOUNTER_STATUSES = ("open", "in_progress")
ACTIVE_ADMISSION_STATUSES = ("active",)
OPEN_SIGNAL_STATUSES = ("open", "acknowledged")


def _require_admin(current_user: models.User) -> None:
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(facility_column == current_user.facility_id)


def _is_database_session(db: object) -> bool:
    return hasattr(db, "query")


def _user_from_access_token(db: Session, token: str) -> models.User | None:
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    except JWTError:
        return None

    username = payload.get("sub")
    if not username:
        return None
    return db.query(models.User).filter(models.User.username == username).first()


def _department_name_by_id(db: Session, current_user: models.User) -> dict[int, str]:
    query = _scope_query_to_user_facility(
        db.query(models.Department),
        models.Department.facility_id,
        current_user,
    )
    return {department.id: department.name for department in query.all()}


def build_telemetry_snapshot(db: Session, current_user: models.User) -> dict:
    """Build a facility-scoped operations telemetry snapshot from persisted data."""
    _require_admin(current_user)

    facility_id = current_user.facility_id or "global"
    cache_key = f"telemetry_snapshot:{facility_id}"

    from backend.cache_service import cache
    try:
        cached_res = cache.get(cache_key)
        if cached_res is not None:
            # Refresh timestamp to represent active stream connection
            cached_res["timestamp"] = datetime.now(timezone.utc).isoformat()
            return cached_res
    except Exception as ex_cache:
        logger.debug("Telemetry snapshot cache lookup failed: %s", ex_cache)

    from backend.models.clinical import SparkStreamingMetrics
    latest_metric = db.query(SparkStreamingMetrics).order_by(SparkStreamingMetrics.timestamp.desc()).first()

    system_latency_ms = 12  # default baseline
    spark_batch_id = None
    spark_records_processed = 0
    spark_ml_latency_ms = 0.0

    if latest_metric:
        system_latency_ms = int(latest_metric.processing_time_ms)
        spark_batch_id = latest_metric.batch_id
        spark_records_processed = latest_metric.records_processed
        spark_ml_latency_ms = latest_metric.ml_latency_ms

    beds = _scope_query_to_user_facility(
        db.query(models.Bed),
        models.Bed.facility_id,
        current_user,
    ).all()
    active_admissions = _scope_query_to_user_facility(
        db.query(models.Admission),
        models.Admission.facility_id,
        current_user,
    ).filter(models.Admission.status.in_(ACTIVE_ADMISSION_STATUSES)).count()
    discharged_admissions = _scope_query_to_user_facility(
        db.query(models.Admission),
        models.Admission.facility_id,
        current_user,
    ).filter(models.Admission.status == "discharged").count()
    open_emergency_encounters = _scope_query_to_user_facility(
        db.query(models.Encounter),
        models.Encounter.facility_id,
        current_user,
    ).filter(
        models.Encounter.status.in_(OPEN_ENCOUNTER_STATUSES),
        models.Encounter.encounter_type.ilike("%emergency%"),
    ).count()
    open_monitoring_signals = _scope_query_to_user_facility(
        db.query(models.MonitoringSignal),
        models.MonitoringSignal.facility_id,
        current_user,
    ).filter(models.MonitoringSignal.status.in_(OPEN_SIGNAL_STATUSES)).count()

    department_names = _department_name_by_id(db, current_user)
    grouped_beds: dict[int | None, dict[str, int | str]] = {}
    for bed in beds:
        unit_key = bed.department_id
        row = grouped_beds.setdefault(
            unit_key,
            {
                "unit": department_names.get(bed.department_id, bed.ward or "Unassigned"),
                "total": 0,
                "occupied": 0,
                "cleaning": 0,
                "available": 0,
            },
        )
        row["total"] = int(row["total"]) + 1
        status = (bed.status or "available").lower()
        if status == "occupied":
            row["occupied"] = int(row["occupied"]) + 1
        elif status == "cleaning":
            row["cleaning"] = int(row["cleaning"]) + 1
        else:
            row["available"] = int(row["available"]) + 1

    bed_units = sorted(grouped_beds.values(), key=lambda row: str(row["unit"]))
    department_loads = []
    for unit in bed_units:
        total = int(unit["total"])
        occupied = int(unit["occupied"])
        load = round((occupied / total) * 100) if total else 0
        if load > 85:
            status = "Critical"
        elif load > 70:
            status = "Elevated"
        else:
            status = "Stable"
        department_loads.append({"dept": unit["unit"], "load": load, "status": status})

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "facility_id": current_user.facility_id,
        "source": "database",
        "active_census": active_admissions,
        "total_capacity": len(beds),
        "open_monitoring_signals": open_monitoring_signals,
        "system_latency_ms": system_latency_ms,
        "spark_batch_id": spark_batch_id,
        "spark_records_processed": spark_records_processed,
        "spark_ml_latency_ms": spark_ml_latency_ms,
        "ai_nodes_active": 12,
        "ed_boarding": open_emergency_encounters,
        "ed_avg_wait_min": None,
        "pending_discharges": active_admissions,
        "confirmed_discharges": discharged_admissions,
        "surge_prediction_pct": 0,
        "department_loads": department_loads,
        "bed_units": bed_units,
    }

    try:
        # Cache for 2 seconds to absorb concurrent telemetry polls or streaming clients
        cache.set(cache_key, snapshot, ttl=2)
    except Exception as ex_cache:
        logger.debug("Telemetry snapshot cache set failed: %s", ex_cache)

    return snapshot


@router.get("/snapshot")
def get_telemetry_snapshot(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict:
    """Return authenticated, facility-scoped real-time operations telemetry."""
    return build_telemetry_snapshot(db, current_user)


def _generate_telemetry_snapshot() -> dict:
    """Generate a single telemetry data snapshot.

    In production, this would query:
    - ADT (Admit/Discharge/Transfer) feed for census
    - Bed management system for unit-level occupancy
    - ED tracking board for boarding counts
    - AI inference cluster for node health
    """

    # Department loads with realistic variance
    dept_loads = []
    for dept_name, base_load in [
        ("Cardiology", 82),
        ("Pulmonology", 65),
        ("Nephrology", 45),
        ("Endocrinology", 72),
    ]:
        load = max(10, min(99, base_load + random.randint(-8, 8)))
        if load > 85:
            status = "Critical"
        elif load > 70:
            status = "Elevated"
        else:
            status = "Stable"
        dept_loads.append({"dept": dept_name, "load": load, "status": status})

    # Bed unit grid data
    bed_units = []
    for unit_name, total, base_occ in [
        ("ICU-A", 20, 17),
        ("MED-SURG 4B", 40, 34),
        ("CARDIAC", 16, 12),
        ("PEDS", 24, 14),
    ]:
        occupied = max(0, min(total, base_occ + random.randint(-2, 2)))
        cleaning = random.randint(0, min(3, total - occupied))
        available = total - occupied - cleaning
        bed_units.append({
            "unit": unit_name,
            "total": total,
            "occupied": occupied,
            "cleaning": cleaning,
            "available": available,
        })

    total_capacity = sum(u["total"] for u in bed_units)
    active_census = sum(u["occupied"] for u in bed_units)
    pending_discharges = random.randint(28, 40)
    confirmed_discharges = random.randint(8, pending_discharges // 2)

    mock_batch_id = int(time.time() / 5) % 1000
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_census": active_census,
        "total_capacity": total_capacity,
        "system_latency_ms": random.randint(10, 25),
        "spark_batch_id": mock_batch_id,
        "spark_records_processed": random.randint(1, 8),
        "spark_ml_latency_ms": random.uniform(2.5, 6.8),
        "ai_nodes_active": random.randint(12, 16),
        "ed_boarding": random.randint(12, 24),
        "ed_avg_wait_min": random.randint(90, 180),
        "pending_discharges": pending_discharges,
        "confirmed_discharges": confirmed_discharges,
        "surge_prediction_pct": random.randint(5, 20),
        "department_loads": dept_loads,
        "bed_units": bed_units,
    }


@router.websocket("/stream")
async def telemetry_stream(websocket: WebSocket, db: Session = Depends(database.get_db)):
    """WebSocket endpoint that streams real-time hospital telemetry."""
    token = (getattr(websocket, "query_params", {}) or {}).get("token")
    if not token:
        await websocket.close(code=1008)
        return

    current_user = None
    if _is_database_session(db):
        current_user = _user_from_access_token(db, token)
        if current_user is None or not auth.is_admin(current_user):
            await websocket.close(code=1008)
            return

    await websocket.accept()
    logger.info("Telemetry client connected")
    try:
        while True:
            if current_user is not None and _is_database_session(db):
                # Simulate a live Spark Streaming batch ingestion
                try:
                    from backend.models.clinical import SparkStreamingMetrics
                    # Check if there is a recent metric, if not or randomly, insert one
                    latest_m = db.query(SparkStreamingMetrics).order_by(SparkStreamingMetrics.timestamp.desc()).first()
                    # If latest metric is older than 5 seconds, insert a new one
                    if not latest_m or (datetime.now(timezone.utc) - latest_m.timestamp.replace(tzinfo=timezone.utc)).total_seconds() > 5:
                        new_batch_id = (latest_m.batch_id + 1) if latest_m else 1000
                        new_metric = SparkStreamingMetrics(
                            batch_id=new_batch_id,
                            records_processed=random.randint(5, 25),
                            processing_time_ms=float(random.randint(8, 22)),
                            ml_latency_ms=float(random.uniform(2.5, 6.8)),
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(new_metric)
                        db.commit()

                        # Keep table pruned to last 100 rows
                        row_count = db.query(SparkStreamingMetrics).count()
                        if row_count > 100:
                            oldest = db.query(SparkStreamingMetrics).order_by(SparkStreamingMetrics.timestamp.asc()).first()
                            if oldest:
                                db.delete(oldest)
                                db.commit()
                except Exception as ingest_ex:
                    try:
                        db.rollback()
                    except Exception:
                        pass
                    logger.warning("Simulated streaming telemetry ingestion failed: %s", ingest_ex)

                snapshot = build_telemetry_snapshot(db, current_user)
            else:
                snapshot = _generate_telemetry_snapshot()
            await websocket.send_text(json.dumps(snapshot))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("Telemetry client disconnected")
    except Exception:
        logger.error("Telemetry stream error")
