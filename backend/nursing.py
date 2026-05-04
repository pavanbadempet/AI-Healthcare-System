"""Nursing workflow: task assignment, completion, staff views, and metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import audit, auth, database, models, schemas
from .facility_scope import users_share_facility_context

router = APIRouter(prefix="/nursing", tags=["Nursing"])
NURSING_FACILITY_MISMATCH_DETAIL = "Nursing resources must belong to the same facility"
NURSING_FACILITY_ACCESS_DETAIL = "Nursing resource is outside the user's facility"


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


def _get_nurse(db: Session, nurse_id: int | None) -> models.User | None:
    if nurse_id is None:
        return None
    nurse = db.query(models.User).filter(
        models.User.id == nurse_id,
        models.User.role == "nurse",
    ).first()
    if not nurse:
        raise HTTPException(status_code=404, detail="Nurse not found")
    return nurse


def _get_task(db: Session, task_id: int) -> models.NursingTask:
    task = db.query(models.NursingTask).filter(models.NursingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Nursing task not found")
    return task


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


def _resolve_nursing_facility_id(*entities: object | None) -> int | None:
    facility_ids = {
        getattr(entity, "facility_id", None)
        for entity in entities
        if entity is not None and getattr(entity, "facility_id", None) is not None
    }
    if len(facility_ids) > 1:
        raise HTTPException(status_code=400, detail=NURSING_FACILITY_MISMATCH_DETAIL)
    return next(iter(facility_ids), None)


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(or_(facility_column == current_user.facility_id, facility_column.is_(None)))


def _ensure_facility_access(current_user: models.User, facility_id: int | None) -> None:
    if current_user.facility_id is None or facility_id is None:
        return
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=NURSING_FACILITY_ACCESS_DETAIL)


def _validate_context(
    db: Session,
    task: schemas.NursingTaskCreate,
) -> tuple[
    models.User,
    models.User | None,
    models.Encounter | None,
    models.Admission | None,
    models.Department | None,
]:
    patient = _get_patient(db, task.patient_id)
    nurse = _get_nurse(db, task.assigned_nurse_id)

    department = None
    if task.department_id is not None:
        department = db.query(models.Department).filter(models.Department.id == task.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")

    encounter = None
    if task.encounter_id is not None:
        encounter = db.query(models.Encounter).filter(models.Encounter.id == task.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        if encounter.patient_id != task.patient_id:
            raise HTTPException(status_code=400, detail="Encounter patient must match nursing task patient")
        if task.department_id is not None and encounter.department_id != task.department_id:
            raise HTTPException(status_code=400, detail="Encounter department must match nursing task department")

    admission = None
    if task.admission_id is not None:
        admission = db.query(models.Admission).filter(models.Admission.id == task.admission_id).first()
        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")
        if admission.patient_id != task.patient_id:
            raise HTTPException(status_code=400, detail="Admission patient must match nursing task patient")
        if task.encounter_id is not None and admission.encounter_id != task.encounter_id:
            raise HTTPException(status_code=400, detail="Admission encounter must match nursing task encounter")
        if task.department_id is not None and admission.department_id != task.department_id:
            raise HTTPException(status_code=400, detail="Admission department must match nursing task department")
    return patient, nurse, encounter, admission, department


def _serialize_task(task: models.NursingTask) -> dict[str, Any]:
    return schemas.NursingTaskResponse.model_validate(task).model_dump(mode="json")


@router.post("/tasks", response_model=schemas.NursingTaskResponse)
def create_nursing_task(
    task: schemas.NursingTaskCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_doctor_or_admin(current_user)
    patient, nurse, encounter, admission, department = _validate_context(db, task)
    _ensure_facility_access(current_user, patient.facility_id)
    if current_user.role == "doctor":
        _ensure_doctor_can_access_patient(db, current_user, task.patient_id)
    facility_id = _resolve_nursing_facility_id(
        current_user,
        patient,
        nurse,
        encounter,
        admission,
        department,
    )

    db_task = models.NursingTask(
        facility_id=facility_id,
        patient_id=task.patient_id,
        assigned_nurse_id=task.assigned_nurse_id,
        created_by_id=current_user.id,
        encounter_id=task.encounter_id,
        admission_id=task.admission_id,
        department_id=task.department_id,
        task_type=task.task_type,
        title=task.title,
        instructions=task.instructions,
        priority=task.priority or "routine",
        due_at=task.due_at,
        status="assigned",
    )
    db.add(db_task)
    db.add(models.CareEvent(
        facility_id=facility_id,
        patient_id=task.patient_id,
        actor_user_id=current_user.id,
        encounter_id=task.encounter_id,
        department_id=task.department_id,
        event_type="NURSING_TASK_CREATED",
        title="Nursing task created",
        summary="Nursing task assigned for care team follow-up.",
        severity="info",
    ))
    db.commit()
    db.refresh(db_task)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=task.patient_id,
        action="CREATE_NURSING_TASK",
        details={
            "resource_type": "nursing_task",
            "resource_id": db_task.id,
            "task_type": task.task_type,
        },
    )
    return db_task


@router.get("/nurse/tasks", response_model=list[schemas.NursingTaskResponse])
def get_nurse_tasks(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "nurse" and not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Nurse or admin privileges required")
    query = db.query(models.NursingTask)
    if current_user.role == "nurse":
        query = query.filter(models.NursingTask.assigned_nurse_id == current_user.id)
    query = _scope_query_to_user_facility(query, models.NursingTask.facility_id, current_user)
    return query.order_by(models.NursingTask.created_at.desc()).all()


@router.put("/tasks/{task_id}/complete", response_model=schemas.NursingTaskResponse)
def complete_nursing_task(
    task_id: int,
    completion: schemas.NursingTaskComplete,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = _get_task(db, task_id)
    _ensure_facility_access(current_user, task.facility_id)
    if auth.is_admin(current_user):
        pass
    elif current_user.role == "nurse":
        if task.assigned_nurse_id != current_user.id:
            raise HTTPException(status_code=403, detail="Nurse is not assigned to this task")
    else:
        raise HTTPException(status_code=403, detail="Nurse or admin privileges required")

    if task.status == "completed":
        raise HTTPException(status_code=409, detail="Nursing task is already completed")

    task.status = "completed"
    task.completed_by_id = current_user.id
    task.completed_at = datetime.now(timezone.utc)
    task.completion_note = completion.completion_note
    db.add(models.CareEvent(
        facility_id=task.facility_id,
        patient_id=task.patient_id,
        actor_user_id=current_user.id,
        encounter_id=task.encounter_id,
        department_id=task.department_id,
        event_type="NURSING_TASK_COMPLETED",
        title="Nursing task completed",
        summary="Nursing task completed and recorded for care team review.",
        severity="info",
    ))
    db.commit()
    db.refresh(task)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=task.patient_id,
        action="COMPLETE_NURSING_TASK",
        details={"resource_type": "nursing_task", "resource_id": task.id},
    )
    return task


@router.get("/patient/tasks", response_model=list[schemas.NursingTaskResponse])
def get_patient_nursing_tasks(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    return db.query(models.NursingTask).filter(
        models.NursingTask.patient_id == current_user.id
    ).order_by(models.NursingTask.created_at.desc()).all()


@router.get("/doctor/patients/{patient_id}/tasks")
def get_doctor_patient_nursing_tasks(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _ensure_doctor_can_access_patient(db, current_user, patient_id)
    tasks = db.query(models.NursingTask).filter(
        models.NursingTask.patient_id == patient_id
    ).order_by(models.NursingTask.created_at.desc()).all()
    return {
        "patient_id": patient_id,
        "tasks": [_serialize_task(task) for task in tasks],
        "clinical_safety_note": "Nursing tasks support care coordination and require staff completion.",
    }


@router.get("/admin/metrics")
def get_nursing_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    task_query = _scope_query_to_user_facility(
        db.query(models.NursingTask),
        models.NursingTask.facility_id,
        current_user,
    )
    tasks = task_query.all()
    tasks_by_type: dict[str, int] = {}
    for task in tasks:
        tasks_by_type[task.task_type] = tasks_by_type.get(task.task_type, 0) + 1
    return {
        "total_tasks": len(tasks),
        "assigned_tasks": sum(1 for task in tasks if task.status == "assigned"),
        "completed_tasks": sum(1 for task in tasks if task.status == "completed"),
        "overdue_tasks": sum(
            1 for task in tasks
            if task.status != "completed" and task.due_at is not None and task.due_at < datetime.now(timezone.utc)
        ),
        "tasks_by_type": tasks_by_type,
        "operations_note": "Nursing metrics support care coordination; clinical accountability remains with licensed staff.",
    }
