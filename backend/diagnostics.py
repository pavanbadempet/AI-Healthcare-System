"""Diagnostics result lifecycle for lab and radiology workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import audit, auth, database, models, schemas
from .facility_scope import users_share_facility_context

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])

DIAGNOSTIC_ORDER_TYPES = {"lab", "radiology", "diagnostic", "imaging"}
ORDER_RESULT_TYPE_ALIASES = {
    "diagnostic": DIAGNOSTIC_ORDER_TYPES,
    "imaging": {"imaging", "radiology"},
    "radiology": {"radiology", "imaging"},
}
ALLOWED_DIAGNOSTIC_REVIEW_STATUSES = {"reviewed", "needs_follow_up", "withheld"}
PATIENT_VISIBLE_REVIEW_STATUSES = {"reviewed", "needs_follow_up"}
DIAGNOSTIC_FACILITY_ACCESS_DETAIL = "Diagnostic resource is outside the user's facility"


def _require_doctor_or_admin(current_user: models.User) -> None:
    if not (auth.is_admin(current_user) or current_user.role == "doctor"):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")


def _require_admin(current_user: models.User) -> None:
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")


def _doctor_assigned_to_patient(db: Session, doctor_id: int, patient_id: int) -> bool:
    if not users_share_facility_context(db, doctor_id, patient_id):
        return False

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


def _get_order(db: Session, order_id: int) -> models.ClinicalOrder:
    order = db.query(models.ClinicalOrder).filter(models.ClinicalOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Clinical order not found")
    if (order.order_type or "").lower() not in DIAGNOSTIC_ORDER_TYPES:
        raise HTTPException(status_code=400, detail="Order is not a diagnostic workflow")
    return order


def _get_patient(db: Session, patient_id: int) -> models.User:
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _get_result(db: Session, result_id: int) -> models.DiagnosticResult:
    result = db.query(models.DiagnosticResult).filter(models.DiagnosticResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Diagnostic result not found")
    return result


def _ensure_doctor_can_access_patient(db: Session, current_user: models.User, patient_id: int) -> None:
    if auth.is_admin(current_user):
        patient = _get_patient(db, patient_id)
        _ensure_facility_access(current_user, patient.facility_id)
        return
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")
    if not _doctor_assigned_to_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this diagnostic result")


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(or_(facility_column == current_user.facility_id, facility_column.is_(None)))


def _ensure_facility_access(current_user: models.User, facility_id: int | None) -> None:
    if current_user.facility_id is None or facility_id is None:
        return
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=DIAGNOSTIC_FACILITY_ACCESS_DETAIL)


def _result_to_dict(result: models.DiagnosticResult) -> dict[str, Any]:
    return schemas.DiagnosticResultResponse.model_validate(result).model_dump(mode="json")


def _ensure_result_type_matches_order(order: models.ClinicalOrder, result_type: str) -> str:
    order_type = (order.order_type or "").strip().lower()
    normalized_result_type = (result_type or "").strip().lower()
    allowed_result_types = ORDER_RESULT_TYPE_ALIASES.get(order_type, {order_type})
    if normalized_result_type not in allowed_result_types:
        raise HTTPException(status_code=400, detail="Diagnostic result type must match order type")
    return normalized_result_type


@router.post("/results", response_model=schemas.DiagnosticResultResponse)
def post_diagnostic_result(
    result: schemas.DiagnosticResultCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_doctor_or_admin(current_user)
    order = _get_order(db, result.order_id)
    _ensure_facility_access(current_user, order.facility_id)
    _ensure_doctor_can_access_patient(db, current_user, order.patient_id)
    result_type = _ensure_result_type_matches_order(order, result.result_type)

    db_result = models.DiagnosticResult(
        facility_id=order.facility_id,
        order_id=order.id,
        encounter_id=order.encounter_id,
        patient_id=order.patient_id,
        doctor_id=order.doctor_id,
        department_id=order.department_id,
        result_type=result_type,
        title=result.title,
        summary=result.summary,
        abnormal_flag=1 if result.abnormal_flag else 0,
        status=result.status or "final",
        review_status="pending_review",
    )
    db.add(db_result)
    db.flush()

    order.status = "completed"
    order.completed_at = datetime.now(timezone.utc)
    db.add(models.CareEvent(
        facility_id=order.facility_id,
        patient_id=order.patient_id,
        actor_user_id=current_user.id,
        encounter_id=order.encounter_id,
        department_id=order.department_id,
        event_type="DIAGNOSTIC_RESULT_POSTED",
        title="Diagnostic result posted",
        summary="A diagnostic result was posted and is pending clinician review.",
        severity="warning" if result.abnormal_flag else "info",
    ))
    db.commit()
    db.refresh(db_result)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=order.patient_id,
        action="POST_DIAGNOSTIC_RESULT",
        details={
            "resource_type": "diagnostic_result",
            "resource_id": db_result.id,
            "order_id": order.id,
            "result_type": result.result_type,
        },
    )
    return db_result


@router.get("/patient/results", response_model=list[schemas.DiagnosticResultResponse])
def get_patient_results(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    return db.query(models.DiagnosticResult).filter(
        models.DiagnosticResult.patient_id == current_user.id,
        models.DiagnosticResult.review_status.in_(PATIENT_VISIBLE_REVIEW_STATUSES),
    ).order_by(models.DiagnosticResult.created_at.desc()).all()


@router.get("/doctor/patients/{patient_id}/results")
def get_doctor_patient_results(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _ensure_doctor_can_access_patient(db, current_user, patient_id)
    results = db.query(models.DiagnosticResult).filter(
        models.DiagnosticResult.patient_id == patient_id
    ).order_by(models.DiagnosticResult.created_at.desc()).all()
    return {
        "patient_id": patient_id,
        "results": [_result_to_dict(result) for result in results],
        "clinical_safety_note": "Diagnostic results require clinician review and are not AI diagnoses.",
    }


@router.put("/results/{result_id}/review", response_model=schemas.DiagnosticResultResponse)
def review_diagnostic_result(
    result_id: int,
    review: schemas.DiagnosticReviewUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = _get_result(db, result_id)
    _ensure_facility_access(current_user, result.facility_id)
    _ensure_doctor_can_access_patient(db, current_user, result.patient_id)
    if current_user.role != "doctor" and not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")

    review_status = (review.review_status or "reviewed").strip().lower()
    if review_status not in ALLOWED_DIAGNOSTIC_REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid diagnostic review status")

    result.review_status = review_status
    result.review_note = review.review_note
    result.reviewed_by_id = current_user.id
    result.reviewed_at = datetime.now(timezone.utc)
    db.add(models.CareEvent(
        facility_id=result.facility_id,
        patient_id=result.patient_id,
        actor_user_id=current_user.id,
        encounter_id=result.encounter_id,
        department_id=result.department_id,
        event_type="DIAGNOSTIC_RESULT_REVIEWED",
        title="Diagnostic result reviewed",
        summary="A clinician reviewed the diagnostic result.",
        severity="info",
    ))
    db.commit()
    db.refresh(result)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=result.patient_id,
        action="REVIEW_DIAGNOSTIC_RESULT",
        details={
            "resource_type": "diagnostic_result",
            "resource_id": result.id,
            "review_status": result.review_status,
        },
    )
    return result


@router.get("/admin/metrics")
def get_diagnostics_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    result_query = _scope_query_to_user_facility(
        db.query(models.DiagnosticResult),
        models.DiagnosticResult.facility_id,
        current_user,
    )
    results = result_query.all()
    results_by_type: dict[str, int] = {}
    results_by_status: dict[str, int] = {}
    for result in results:
        results_by_type[result.result_type] = results_by_type.get(result.result_type, 0) + 1
        results_by_status[result.review_status] = results_by_status.get(result.review_status, 0) + 1

    return {
        "total_results": len(results),
        "pending_review": sum(1 for result in results if result.review_status == "pending_review"),
        "abnormal_results": sum(1 for result in results if bool(result.abnormal_flag)),
        "results_by_type": results_by_type,
        "results_by_status": results_by_status,
        "clinical_safety_note": "Diagnostics metrics support operations; clinicians interpret results and make care decisions.",
    }


# --- Phase 10 Itch Upgrades: At-Home Lab Kits ---
from pydantic import BaseModel as PydanticBaseModel


class LabKitOrderRequest(PydanticBaseModel):
    patient_id: int
    kit_type: str
    shipping_address: str


@router.post("/lab-kits")
def order_lab_kit(
    req: LabKitOrderRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    if current_user.role == "patient" and current_user.id != req.patient_id:
        raise HTTPException(status_code=403, detail="Patients can only order kits for themselves")

    db_order = models.ClinicalOrder(
        facility_id=current_user.facility_id or 1,
        patient_id=req.patient_id,
        doctor_id=current_user.id if current_user.role == "doctor" else None,
        order_type="lab",
        title=f"At-Home Lab Kit - {req.kit_type}",
        priority="routine",
        status="ordered",
        notes=f"Shipping Address: {req.shipping_address}. Status tracking: ordered -> shipped -> delivered -> results_uploaded."
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    db.add(models.CareEvent(
        facility_id=db_order.facility_id,
        patient_id=req.patient_id,
        actor_user_id=current_user.id,
        event_type="LAB_KIT_ORDERED",
        title=f"At-home {req.kit_type} kit ordered",
        summary=f"Diagnostic kit was requested. Shipping to: {req.shipping_address}.",
        severity="info"
    ))
    db.commit()

    return {
        "order_id": db_order.id,
        "patient_id": req.patient_id,
        "kit_type": req.kit_type,
        "status": "ordered",
        "shipping_address": req.shipping_address,
        "estimated_delivery": "3-5 business days",
        "message": f"Successfully ordered at-home {req.kit_type} diagnostic kit."
    }


@router.get("/lab-kits/{patient_id}")
def get_lab_kits(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Patients can only check their own kits")

    orders = db.query(models.ClinicalOrder).filter(
        models.ClinicalOrder.patient_id == patient_id,
        models.ClinicalOrder.order_type == "lab",
        models.ClinicalOrder.title.like("At-Home Lab Kit -%")
    ).all()

    kits_list = []
    for order in orders:
        kit_type = order.title.replace("At-Home Lab Kit - ", "")
        tracking_status = "ordered"
        tracking_number = f"1Z999AA1012345{order.id}"

        if order.status == "completed":
            tracking_status = "results_uploaded"
        elif order.status == "in_progress":
            tracking_status = "shipped"
        else:
            tracking_status = "ordered"

        kits_list.append({
            "kit_id": order.id,
            "kit_type": kit_type,
            "ordered_at": order.created_at.isoformat() if order.created_at else None,
            "tracking_status": tracking_status,
            "tracking_number": tracking_number,
            "carrier": "UPS Mail Innovations",
            "notes": order.notes
        })

    return {
        "patient_id": patient_id,
        "kits": kits_list,
        "total_kits": len(kits_list),
        "clinical_safety_note": "At-home diagnostic test kits support remote patient monitoring; clinical decisions are made upon physician review of uploaded lab reports."
    }
