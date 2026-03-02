"""
Real-Time Telemetry WebSocket Endpoint

Streams live hospital operations data to the frontend dashboard.
In production, this would subscribe to HL7/FHIR ADT feeds, 
Redis pub/sub channels, or Kafka topics for real clinical data.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import random
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter()


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

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_census": active_census,
        "total_capacity": total_capacity,
        "system_latency_ms": random.randint(8, 22),
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
async def telemetry_stream(websocket: WebSocket):
    """WebSocket endpoint that streams real-time hospital telemetry."""
    await websocket.accept()
    logger.info("Telemetry client connected")
    try:
        while True:
            snapshot = _generate_telemetry_snapshot()
            await websocket.send_text(json.dumps(snapshot))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("Telemetry client disconnected")
    except Exception as e:
        logger.error(f"Telemetry stream error: {e}")
