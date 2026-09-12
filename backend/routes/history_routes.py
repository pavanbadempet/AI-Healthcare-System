"""FastAPI Router for Level 12 Bi-Temporal Event-Sourced Clinical History & Time-Travel OS."""

from __future__ import annotations

import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.history.bitemporal_engine import BiTemporalEngine
from backend.history.clinical_event_store import ClinicalEventStore
from backend.history.clinical_intent_tracker import ClinicalIntentTracker
from backend.history.temporal_diff_engine import TemporalDiffEngine
from backend.schemas.history import (
    AppendEventRequest,
    BiTemporalInsertRequest,
    BiTemporalQueryRequest,
    BiTemporalRecordSchema,
    ChartProjectionResponse,
    CountersignIntentRequest,
    EventResponseSchema,
    HistoryHealthResponse,
    IntentResponseSchema,
    RecordIntentRequest,
    TemporalDiffRequest,
    TemporalDiffResponse,
)

logger = logging.getLogger("backend.history")

router = APIRouter(
    prefix="/v1/history",
    tags=["History & Time-Travel"],
)

# Global engine singletons for history subsystem
event_store = ClinicalEventStore()
bitemporal_engine = BiTemporalEngine()
intent_tracker = ClinicalIntentTracker()
diff_engine = TemporalDiffEngine(event_store)


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime.datetime]:
    """Parse ISO 8601 string to UTC datetime."""
    if not dt_str:
        return None
    try:
        # Replace trailing Z with +00:00 for fromisoformat compatibility
        clean_str = dt_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(clean_str)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ISO 8601 timestamp: '{dt_str}'. Error: {exc}",
        ) from exc


@router.post("/events/append", response_model=EventResponseSchema)
def append_event(req: AppendEventRequest) -> EventResponseSchema:
    """Append an immutable clinical domain event to the patient's event stream."""
    v_time = _parse_iso(req.valid_time)
    t_time = _parse_iso(req.timestamp)

    event = event_store.append(
        patient_id=req.patient_id,
        event_type=req.event_type,
        payload=req.payload,
        valid_time=v_time,
        node_id=req.node_id,
        intent_id=req.intent_id,
        timestamp=t_time,
        incoming_clock=req.incoming_clock,
    )

    return EventResponseSchema(
        event_id=event.event_id,
        patient_id=event.patient_id,
        event_type=event.event_type.value,
        timestamp=event.timestamp.isoformat(),
        valid_time=event.valid_time.isoformat(),
        node_id=event.node_id,
        vector_clock=event.vector_clock,
        causal_sequence=event.causal_sequence,
        payload=event.payload,
        intent_id=event.intent_id,
        prev_hash=event.prev_hash,
        event_hash=event.event_hash,
        status="EVENT_COMMITTED",
    )


@router.get("/patient/{patient_id}/as-of", response_model=ChartProjectionResponse)
def get_patient_chart_as_of(
    patient_id: str,
    as_of_time: Optional[str] = Query(None, description="ISO 8601 target timepoint"),
    by_valid_time: bool = Query(False, description="Filter by clinical valid time instead of record time"),
) -> ChartProjectionResponse:
    """Deterministic mathematical fold projection of patient chart as-of a specific timestamp."""
    cutoff = _parse_iso(as_of_time)
    chart = event_store.project_patient_chart(
        patient_id=patient_id,
        as_of_time=cutoff,
        by_valid_time=by_valid_time,
    )
    chain_ok = event_store.verify_event_chain(patient_id)

    return ChartProjectionResponse(
        patient_id=chart["patient_id"],
        admitted=chart["admitted"],
        admission=chart["admission"],
        conditions=chart["conditions"],
        medications=chart["medications"],
        vitals=chart["vitals"],
        allergies=chart["allergies"],
        labs=chart["labs"],
        event_count=chart["event_count"],
        as_of_time=chart["as_of_time"],
        last_event_hash=chart["last_event_hash"],
        chain_verified=chain_ok,
    )


@router.get("/patient/{patient_id}/timeline", response_model=List[EventResponseSchema])
def get_patient_timeline(
    patient_id: str,
    as_of_time: Optional[str] = Query(None, description="ISO 8601 cutoff"),
    by_valid_time: bool = Query(False, description="Filter by valid time"),
) -> List[EventResponseSchema]:
    """Retrieve full chronological event stream for a patient."""
    cutoff = _parse_iso(as_of_time)
    events = event_store.get_events(
        patient_id=patient_id,
        as_of_time=cutoff,
        by_valid_time=by_valid_time,
    )

    return [
        EventResponseSchema(
            event_id=ev.event_id,
            patient_id=ev.patient_id,
            event_type=ev.event_type.value,
            timestamp=ev.timestamp.isoformat(),
            valid_time=ev.valid_time.isoformat(),
            node_id=ev.node_id,
            vector_clock=ev.vector_clock,
            causal_sequence=ev.causal_sequence,
            payload=ev.payload,
            intent_id=ev.intent_id,
            prev_hash=ev.prev_hash,
            event_hash=ev.event_hash,
            status="EVENT_COMMITTED",
        )
        for ev in events
    ]


@router.post("/patient/{patient_id}/diff", response_model=TemporalDiffResponse)
def diff_patient_chronology(
    patient_id: str,
    req: TemporalDiffRequest,
) -> TemporalDiffResponse:
    """Compute semantic structural delta between two milestones in a patient's trajectory."""
    t1_dt = _parse_iso(req.t1)
    t2_dt = _parse_iso(req.t2)

    if not t1_dt or not t2_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both t1 and t2 timestamps are required",
        )

    delta = diff_engine.diff_patient_at_times(
        patient_id=patient_id,
        t1=t1_dt,
        t2=t2_dt,
        by_valid_time=req.by_valid_time,
    )

    return TemporalDiffResponse(
        patient_id=patient_id,
        t1_label=delta["t1_label"],
        t2_label=delta["t2_label"],
        added=delta["added"],
        modified=delta["modified"],
        resolved_or_revoked=delta["resolved_or_revoked"],
        new_vitals_count=delta["new_vitals_count"],
        new_vitals=delta["new_vitals"],
        clinical_narrative=delta["clinical_narrative"],
        total_structural_changes=delta["total_structural_changes"],
    )


@router.post("/bitemporal/insert", response_model=BiTemporalRecordSchema)
def insert_bitemporal_record(req: BiTemporalInsertRequest) -> BiTemporalRecordSchema:
    """Assert a dual-axis bi-temporal observation."""
    v_from = _parse_iso(req.valid_from)
    v_to = _parse_iso(req.valid_to)
    t_time = _parse_iso(req.transaction_time)

    if not v_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="valid_from timestamp is required",
        )

    rec = bitemporal_engine.insert(
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        patient_id=req.patient_id,
        valid_from=v_from,
        valid_to=v_to,
        payload=req.payload,
        transaction_time=t_time,
        metadata=req.metadata,
    )

    return BiTemporalRecordSchema(**rec.to_dict())


@router.post("/bitemporal/query", response_model=List[BiTemporalRecordSchema])
def query_bitemporal_as_of(
    patient_id: str = Query(..., description="Target patient"),
    req: BiTemporalQueryRequest = ...,
) -> List[BiTemporalRecordSchema]:
    """Query clinical truth as-of valid_time according to EHR system knowledge at transaction_time."""
    vt = _parse_iso(req.valid_time)
    tt = _parse_iso(req.transaction_time)

    if not vt or not tt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both valid_time and transaction_time are required",
        )

    records = bitemporal_engine.query_as_of(
        patient_id=patient_id,
        valid_time=vt,
        transaction_time=tt,
        entity_type=req.entity_type,
    )

    return [BiTemporalRecordSchema(**r.to_dict()) for r in records]


@router.post("/intents", response_model=IntentResponseSchema)
def record_clinical_intent(req: RecordIntentRequest) -> IntentResponseSchema:
    """Record structured clinical justification, attribution signature, and evidence."""
    intent = intent_tracker.record_intent(
        patient_id=req.patient_id,
        category=req.category,
        rationale=req.rationale,
        clinician_id=req.clinician_id,
        clinician_name=req.clinician_name,
        role=req.role,
        evidence=req.evidence,
    )

    return IntentResponseSchema(**intent.to_dict())


@router.post("/intents/{intent_id}/countersign", response_model=IntentResponseSchema)
def countersign_intent(
    intent_id: str,
    req: CountersignIntentRequest,
) -> IntentResponseSchema:
    """Add Four-Eye dual signoff countersignature."""
    try:
        intent = intent_tracker.add_countersignature(
            intent_id=intent_id,
            clinician_id=req.clinician_id,
            clinician_name=req.clinician_name,
            role=req.role,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intent record '{intent_id}' not found",
        )

    return IntentResponseSchema(**intent.to_dict())


@router.get("/patient/{patient_id}/intents", response_model=List[IntentResponseSchema])
def get_patient_intents(patient_id: str) -> List[IntentResponseSchema]:
    """Retrieve all structured clinical intent rationales for a patient."""
    intents = intent_tracker.get_patient_intents(patient_id)
    return [IntentResponseSchema(**i.to_dict()) for i in intents]


@router.get("/health", response_model=HistoryHealthResponse)
def get_history_health() -> HistoryHealthResponse:
    """Retrieve operational status of the History and Time-Travel subsystem."""
    total_events = sum(len(evs) for evs in event_store._events.values())
    total_patients = len(event_store._events)
    bitemporal_count = len(bitemporal_engine._records)
    intents_count = len(intent_tracker._intents)

    return HistoryHealthResponse(
        status="HEALTHY",
        engine="BI_TEMPORAL_EVENT_SOURCED_TIME_TRAVEL_OS",
        total_events=total_events,
        total_patients_tracked=total_patients,
        bitemporal_records=bitemporal_count,
        intents_recorded=intents_count,
    )
