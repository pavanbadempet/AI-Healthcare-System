"""Role-aware care event feeds for operational dashboards."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from . import auth, database, models, schemas
from .facility_scope import users_share_facility_context

router = APIRouter(prefix="/events", tags=["Care Events"])
CARE_EVENT_FACILITY_ACCESS_DETAIL = "Care event resource is outside the user's facility"


def _require_admin(current_user: models.User) -> None:
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")


def _scope_events_to_admin_facility(query, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(models.CareEvent.facility_id == current_user.facility_id)


def _ensure_admin_can_access_patient(db: Session, current_user: models.User, patient_id: int) -> None:
    if current_user.facility_id is None:
        return
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.facility_id != current_user.facility_id:
        raise HTTPException(status_code=403, detail=CARE_EVENT_FACILITY_ACCESS_DETAIL)


def _doctor_assigned_to_patient(db: Session, doctor_id: int, patient_id: int) -> bool:
    if not users_share_facility_context(db, doctor_id, patient_id):
        return False

    admission = db.query(models.Admission).filter(
        models.Admission.patient_id == patient_id,
        models.Admission.doctor_id == doctor_id,
    ).first()
    if admission:
        return True

    encounter = db.query(models.Encounter).filter(
        models.Encounter.patient_id == patient_id,
        models.Encounter.doctor_id == doctor_id,
    ).first()
    if encounter:
        return True

    order = db.query(models.ClinicalOrder).filter(
        models.ClinicalOrder.patient_id == patient_id,
        models.ClinicalOrder.doctor_id == doctor_id,
    ).first()
    if order:
        return True

    appointment = db.query(models.Appointment).filter(
        models.Appointment.user_id == patient_id,
        models.Appointment.doctor_id == doctor_id,
    ).first()
    return appointment is not None


def _ensure_doctor_can_access_patient(db: Session, current_user: models.User, patient_id: int) -> None:
    if auth.is_admin(current_user):
        _ensure_admin_can_access_patient(db, current_user, patient_id)
        return
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")
    if not _doctor_assigned_to_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")


def _serialize_event(event: models.CareEvent) -> dict[str, Any]:
    return schemas.CareEventResponse.model_validate(event).model_dump(mode="json")


def _event_feed(events: list[models.CareEvent]) -> dict[str, Any]:
    return {
        "events": [_serialize_event(event) for event in events],
        "next_after_id": max((event.id for event in events), default=None),
    }


def _apply_cursor(query, after_id: int | None, limit: int):
    if after_id is not None:
        query = query.filter(models.CareEvent.id > after_id)
    return query.order_by(models.CareEvent.id.asc()).limit(limit)


@router.get("/patient/feed")
def get_patient_event_feed(
    after_id: int | None = Query(None, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    query = db.query(models.CareEvent).filter(models.CareEvent.patient_id == current_user.id)
    return _event_feed(_apply_cursor(query, after_id, limit).all())


@router.get("/doctor/patients/{patient_id}/feed")
def get_doctor_patient_event_feed(
    patient_id: int,
    after_id: int | None = Query(None, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _ensure_doctor_can_access_patient(db, current_user, patient_id)
    query = db.query(models.CareEvent).filter(models.CareEvent.patient_id == patient_id)
    payload = _event_feed(_apply_cursor(query, after_id, limit).all())
    payload["patient_id"] = patient_id
    payload["clinical_safety_note"] = "Care events are operational records and do not replace clinician review."
    return payload


@router.get("/admin/recent")
def get_admin_recent_events(
    after_id: int | None = Query(None, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    query = _scope_events_to_admin_facility(db.query(models.CareEvent), current_user)
    return _event_feed(_apply_cursor(query, after_id, limit).all())


@router.get("/admin/patients/{patient_id}/feed")
def get_admin_patient_event_feed(
    patient_id: int,
    after_id: int | None = Query(None, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    _ensure_admin_can_access_patient(db, current_user, patient_id)
    query = _scope_events_to_admin_facility(
        db.query(models.CareEvent),
        current_user,
    ).filter(models.CareEvent.patient_id == patient_id)
    payload = _event_feed(_apply_cursor(query, after_id, limit).all())
    payload["patient_id"] = patient_id
    payload["clinical_safety_note"] = "Care events are operational records and do not replace clinician review."
    return payload


@router.get("/admin/metrics")
def get_admin_event_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    events = _scope_events_to_admin_facility(db.query(models.CareEvent), current_user).all()
    events_by_type: dict[str, int] = {}
    events_by_severity: dict[str, int] = {}
    for event in events:
        events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
        events_by_severity[event.severity] = events_by_severity.get(event.severity, 0) + 1
    return {
        "total_events": len(events),
        "events_by_type": events_by_type,
        "events_by_severity": events_by_severity,
        "operations_note": "Care event metrics support operational dashboards and do not represent clinical diagnoses.",
    }
