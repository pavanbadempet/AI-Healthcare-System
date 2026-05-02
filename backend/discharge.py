"""Discharge workflow: summaries, finalization, bed release, and metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import audit, auth, database, models, schemas
from .facility_scope import users_share_facility_context

router = APIRouter(prefix="/discharge", tags=["Discharge"])
DISCHARGE_FACILITY_MISMATCH_DETAIL = "Discharge resources must belong to the same facility"
DISCHARGE_FACILITY_ACCESS_DETAIL = "Discharge resource is outside the user's facility"


def _require_admin(current_user: models.User) -> None:
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")


def _require_doctor_or_admin(current_user: models.User) -> None:
    if not (auth.is_admin(current_user) or current_user.role == "doctor"):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")


def _get_patient(db: Session, patient_id: int) -> models.User:
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _get_admission(db: Session, admission_id: int) -> models.Admission:
    admission = db.query(models.Admission).filter(models.Admission.id == admission_id).first()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    return admission


def _get_summary(db: Session, summary_id: int) -> models.DischargeSummary:
    summary = db.query(models.DischargeSummary).filter(models.DischargeSummary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Discharge summary not found")
    return summary


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

    appointment = db.query(models.Appointment).filter(
        models.Appointment.user_id == patient_id,
        models.Appointment.doctor_id == doctor_id,
    ).first()
    return appointment is not None


def _ensure_doctor_can_access_patient(db: Session, current_user: models.User, patient_id: int) -> None:
    if auth.is_admin(current_user):
        patient = _get_patient(db, patient_id)
        _ensure_facility_access(current_user, patient.facility_id)
        return
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")
    if not _doctor_assigned_to_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")


def _resolve_discharge_facility_id(*entities: object | None) -> int | None:
    facility_ids = {
        getattr(entity, "facility_id", None)
        for entity in entities
        if entity is not None and getattr(entity, "facility_id", None) is not None
    }
    if len(facility_ids) > 1:
        raise HTTPException(status_code=400, detail=DISCHARGE_FACILITY_MISMATCH_DETAIL)
    return next(iter(facility_ids), None)


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(or_(facility_column == current_user.facility_id, facility_column.is_(None)))


def _ensure_facility_access(current_user: models.User, facility_id: int | None) -> None:
    if current_user.facility_id is None or facility_id is None:
        return
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=DISCHARGE_FACILITY_ACCESS_DETAIL)


def _validate_summary_context(
    db: Session,
    summary: schemas.DischargeSummaryCreate,
) -> tuple[models.User, models.Admission, models.Encounter | None]:
    patient = _get_patient(db, summary.patient_id)
    admission = _get_admission(db, summary.admission_id)
    if admission.patient_id != summary.patient_id:
        raise HTTPException(status_code=400, detail="Admission patient must match discharge summary patient")
    if summary.doctor_id is not None and admission.doctor_id not in (None, summary.doctor_id):
        raise HTTPException(status_code=400, detail="Admission doctor must match discharge summary doctor")
    encounter = None
    if summary.encounter_id is not None:
        encounter = db.query(models.Encounter).filter(models.Encounter.id == summary.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        if encounter.patient_id != summary.patient_id:
            raise HTTPException(status_code=400, detail="Encounter patient must match discharge summary patient")
        if admission.encounter_id != summary.encounter_id:
            raise HTTPException(status_code=400, detail="Admission encounter must match discharge summary encounter")
    return patient, admission, encounter


def _serialize_summary(summary: models.DischargeSummary) -> dict[str, Any]:
    return schemas.DischargeSummaryResponse.model_validate(summary).model_dump(mode="json")


@router.post("/summaries", response_model=schemas.DischargeSummaryResponse)
def create_discharge_summary(
    summary: schemas.DischargeSummaryCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_doctor_or_admin(current_user)
    patient, admission, encounter = _validate_summary_context(db, summary)
    _ensure_facility_access(current_user, admission.facility_id or patient.facility_id)
    doctor_id = summary.doctor_id if summary.doctor_id is not None else admission.doctor_id

    if current_user.role == "doctor":
        if doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Doctors can create only their own discharge summaries")
        _ensure_doctor_can_access_patient(db, current_user, summary.patient_id)

    existing = db.query(models.DischargeSummary).filter(
        models.DischargeSummary.admission_id == summary.admission_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Discharge summary already exists for admission")
    facility_id = _resolve_discharge_facility_id(current_user, patient, admission, encounter)

    db_summary = models.DischargeSummary(
        facility_id=facility_id,
        admission_id=summary.admission_id,
        encounter_id=summary.encounter_id,
        patient_id=summary.patient_id,
        doctor_id=doctor_id,
        diagnosis_summary=summary.diagnosis_summary,
        hospital_course=summary.hospital_course,
        medications=summary.medications,
        follow_up_plan=summary.follow_up_plan,
        discharge_instructions=summary.discharge_instructions,
        status="draft",
    )
    db.add(db_summary)
    db.add(models.CareEvent(
        facility_id=facility_id,
        patient_id=summary.patient_id,
        actor_user_id=current_user.id,
        encounter_id=summary.encounter_id,
        department_id=admission.department_id,
        event_type="DISCHARGE_SUMMARY_CREATED",
        title="Discharge summary created",
        summary="Clinician-authored discharge summary drafted for review.",
        severity="info",
    ))
    db.commit()
    db.refresh(db_summary)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=summary.patient_id,
        action="CREATE_DISCHARGE_SUMMARY",
        details={"resource_type": "discharge_summary", "resource_id": db_summary.id},
    )
    return db_summary


@router.put("/summaries/{summary_id}/finalize", response_model=schemas.DischargeSummaryResponse)
def finalize_discharge_summary(
    summary_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    summary = _get_summary(db, summary_id)
    _ensure_facility_access(current_user, summary.facility_id)
    _ensure_doctor_can_access_patient(db, current_user, summary.patient_id)
    if current_user.role != "doctor" and not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")

    if summary.status == "finalized":
        raise HTTPException(status_code=409, detail="Discharge summary is already finalized")

    now = datetime.now(timezone.utc)
    summary.status = "finalized"
    summary.finalized_at = summary.finalized_at or now

    admission = _get_admission(db, summary.admission_id)
    admission.status = "discharged"
    admission.discharged_at = admission.discharged_at or now

    if admission.bed_id is not None:
        bed = db.query(models.Bed).filter(models.Bed.id == admission.bed_id).first()
        if bed is not None:
            bed.status = "available"
            bed.current_patient_id = None

    if summary.encounter_id is not None:
        encounter = db.query(models.Encounter).filter(models.Encounter.id == summary.encounter_id).first()
        if encounter is not None:
            encounter.status = "closed"
            encounter.ended_at = encounter.ended_at or now

    db.add(models.CareEvent(
        facility_id=summary.facility_id,
        patient_id=summary.patient_id,
        actor_user_id=current_user.id,
        encounter_id=summary.encounter_id,
        department_id=admission.department_id,
        event_type="DISCHARGE_FINALIZED",
        title="Discharge finalized",
        summary="Admission was discharged after clinician finalization.",
        severity="info",
    ))
    db.commit()
    db.refresh(summary)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=summary.patient_id,
        action="FINALIZE_DISCHARGE_SUMMARY",
        details={"resource_type": "discharge_summary", "resource_id": summary.id},
    )
    return summary


@router.get("/patient/summaries", response_model=list[schemas.DischargeSummaryResponse])
def get_patient_discharge_summaries(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    return db.query(models.DischargeSummary).filter(
        models.DischargeSummary.patient_id == current_user.id,
        models.DischargeSummary.status == "finalized",
    ).order_by(models.DischargeSummary.finalized_at.desc()).all()


@router.get("/doctor/patients/{patient_id}/summaries")
def get_doctor_patient_discharge_summaries(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _ensure_doctor_can_access_patient(db, current_user, patient_id)
    summaries = db.query(models.DischargeSummary).filter(
        models.DischargeSummary.patient_id == patient_id,
    ).order_by(models.DischargeSummary.created_at.desc()).all()
    return {
        "patient_id": patient_id,
        "summaries": [_serialize_summary(summary) for summary in summaries],
        "clinical_safety_note": "Discharge summaries are clinician-authored records and require clinician finalization.",
    }


@router.get("/admin/metrics")
def get_discharge_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    summary_query = _scope_query_to_user_facility(
        db.query(models.DischargeSummary),
        models.DischargeSummary.facility_id,
        current_user,
    )
    active_admissions_query = _scope_query_to_user_facility(
        db.query(models.Admission).filter(models.Admission.status == "active"),
        models.Admission.facility_id,
        current_user,
    )
    discharged_admissions_query = _scope_query_to_user_facility(
        db.query(models.Admission).filter(models.Admission.status == "discharged"),
        models.Admission.facility_id,
        current_user,
    )
    summaries = summary_query.all()
    return {
        "total_summaries": len(summaries),
        "draft_summaries": sum(1 for summary in summaries if summary.status == "draft"),
        "finalized_summaries": sum(1 for summary in summaries if summary.status == "finalized"),
        "active_admissions": active_admissions_query.count(),
        "discharged_admissions": discharged_admissions_query.count(),
        "clinical_safety_note": "Discharge metrics support operations; clinicians remain responsible for discharge decisions.",
    }
