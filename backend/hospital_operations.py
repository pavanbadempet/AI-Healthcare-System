"""Hospital operations core: departments, encounters, admissions, orders, timelines."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import audit, auth, database, models, schemas

router = APIRouter(prefix="/hospital", tags=["Hospital Operations"])

ACTIVE_ADMISSION_STATUSES = ("active",)
OPEN_ORDER_STATUSES = ("ordered", "in_progress")
OPEN_ENCOUNTER_STATUSES = ("open", "in_progress")
HOSPITAL_FACILITY_ACCESS_DETAIL = "Hospital resource is outside the user's facility"


def _require_admin(current_user: models.User) -> None:
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")


def _require_doctor_or_admin(current_user: models.User) -> None:
    if not (auth.is_admin(current_user) or current_user.role == "doctor"):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(facility_column == current_user.facility_id)


def _ensure_facility_access(current_user: models.User, facility_id: int | None) -> None:
    if current_user.facility_id is None or facility_id is None:
        return
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=HOSPITAL_FACILITY_ACCESS_DETAIL)


def _get_user(db: Session, user_id: int, *, role: str | None = None) -> models.User:
    query = db.query(models.User).filter(models.User.id == user_id)
    if role:
        query = query.filter(models.User.role == role)
    user = query.first()
    if not user:
        label = f"{role.title()} " if role else ""
        raise HTTPException(status_code=404, detail=f"{label}User not found")
    return user


def _get_department(db: Session, department_id: int | None) -> models.Department | None:
    if department_id is None:
        return None
    department = db.query(models.Department).filter(models.Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


def _get_facility(db: Session, facility_id: int | None) -> models.HospitalFacility | None:
    if facility_id is None:
        return None
    facility = db.query(models.HospitalFacility).filter(models.HospitalFacility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility


def _get_encounter(db: Session, encounter_id: int | None) -> models.Encounter | None:
    if encounter_id is None:
        return None
    encounter = db.query(models.Encounter).filter(models.Encounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return encounter


def _resolve_facility_id(detail: str, *entities: object | None) -> int | None:
    facility_ids = {
        getattr(entity, "facility_id", None)
        for entity in entities
        if entity is not None and getattr(entity, "facility_id", None) is not None
    }
    if len(facility_ids) > 1:
        raise HTTPException(status_code=400, detail=detail)
    return next(iter(facility_ids), None)


def _event(
    db: Session,
    *,
    patient_id: int,
    actor_user_id: int | None,
    event_type: str,
    title: str,
    encounter_id: int | None = None,
    department_id: int | None = None,
    summary: str | None = None,
    severity: str = "info",
    facility_id: int | None = None,
) -> models.CareEvent:
    care_event = models.CareEvent(
        facility_id=facility_id,
        patient_id=patient_id,
        actor_user_id=actor_user_id,
        encounter_id=encounter_id,
        department_id=department_id,
        event_type=event_type,
        title=title,
        summary=summary,
        severity=severity,
    )
    db.add(care_event)
    return care_event


def _serialize_patient(user: models.User) -> dict[str, Any]:
    return {
        "patient_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
    }


@router.post("/facilities", response_model=schemas.FacilityResponse)
def create_facility(
    facility: schemas.FacilityCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_admin(current_user)
    if current_user.facility_id is not None:
        raise HTTPException(status_code=403, detail=HOSPITAL_FACILITY_ACCESS_DETAIL)
    existing = db.query(models.HospitalFacility).filter(models.HospitalFacility.name == facility.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Facility already exists")

    db_facility = models.HospitalFacility(**facility.model_dump(), status="active")
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=None,
        facility_id=db_facility.id,
        action="CREATE_FACILITY",
        details={"resource_type": "hospital_facility", "resource_id": db_facility.id},
    )
    return db_facility


@router.get("/facilities", response_model=list[schemas.FacilityResponse])
def list_facilities(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_admin(current_user)
    query = _scope_query_to_user_facility(
        db.query(models.HospitalFacility),
        models.HospitalFacility.id,
        current_user,
    )
    return query.order_by(models.HospitalFacility.name.asc()).all()


@router.post("/departments", response_model=schemas.DepartmentResponse)
def create_department(
    department: schemas.DepartmentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_admin(current_user)
    department_data = department.model_dump()
    if department_data["facility_id"] is None and current_user.facility_id is not None:
        department_data["facility_id"] = current_user.facility_id
    _ensure_facility_access(current_user, department_data["facility_id"])
    existing = db.query(models.Department).filter(models.Department.name == department_data["name"]).first()
    if existing:
        raise HTTPException(status_code=409, detail="Department already exists")
    _get_facility(db, department_data["facility_id"])

    db_department = models.Department(**department_data, status="active")
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=None,
        facility_id=db_department.facility_id,
        action="CREATE_DEPARTMENT",
        details={"resource_type": "department", "resource_id": db_department.id},
    )
    return db_department


@router.get("/departments", response_model=list[schemas.DepartmentResponse])
def list_departments(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = _scope_query_to_user_facility(
        db.query(models.Department),
        models.Department.facility_id,
        current_user,
    )
    return query.order_by(models.Department.name.asc()).all()


@router.post("/beds", response_model=schemas.BedResponse)
def create_bed(
    bed: schemas.BedCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_admin(current_user)
    department = _get_department(db, bed.department_id)
    _ensure_facility_access(current_user, department.facility_id if department else None)
    db_bed = models.Bed(**bed.model_dump(), facility_id=department.facility_id if department else None)
    db.add(db_bed)
    db.commit()
    db.refresh(db_bed)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=None,
        facility_id=db_bed.facility_id,
        action="CREATE_BED",
        details={"resource_type": "bed", "resource_id": db_bed.id},
    )
    return db_bed


@router.get("/beds", response_model=list[schemas.BedResponse])
def list_beds(
    status: str | None = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = _scope_query_to_user_facility(
        db.query(models.Bed),
        models.Bed.facility_id,
        current_user,
    )
    if status:
        query = query.filter(models.Bed.status == status)
    return query.order_by(models.Bed.bed_number.asc()).all()


@router.post("/encounters", response_model=schemas.EncounterResponse)
def create_encounter(
    encounter: schemas.EncounterCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_doctor_or_admin(current_user)
    patient = _get_user(db, encounter.patient_id, role="patient")
    doctor = None
    if encounter.doctor_id is not None:
        doctor = _get_user(db, encounter.doctor_id, role="doctor")
    elif current_user.role == "doctor":
        doctor = current_user
    department = _get_department(db, encounter.department_id)

    if current_user.role == "doctor" and encounter.doctor_id not in (None, current_user.id):
        raise HTTPException(status_code=403, detail="Doctors can only open their own encounters")

    doctor_id = encounter.doctor_id if encounter.doctor_id is not None else (
        current_user.id if current_user.role == "doctor" else None
    )
    facility_id = _resolve_facility_id(
        "Encounter participants must belong to the same facility",
        patient,
        doctor,
        department,
    )
    _ensure_facility_access(current_user, facility_id)
    db_encounter = models.Encounter(
        facility_id=facility_id,
        patient_id=encounter.patient_id,
        doctor_id=doctor_id,
        department_id=encounter.department_id,
        encounter_type=encounter.encounter_type,
        reason=encounter.reason,
        priority=encounter.priority or "routine",
        status="open",
    )
    db.add(db_encounter)
    db.flush()
    _event(
        db,
        patient_id=db_encounter.patient_id,
        actor_user_id=current_user.id,
        encounter_id=db_encounter.id,
        department_id=db_encounter.department_id,
        facility_id=db_encounter.facility_id,
        event_type="ENCOUNTER_OPENED",
        title=f"{db_encounter.encounter_type} encounter opened",
        summary="Clinician-reviewed workflow encounter opened",
    )
    db.commit()
    db.refresh(db_encounter)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=db_encounter.patient_id,
        action="CREATE_ENCOUNTER",
        details={
            "resource_type": "encounter",
            "resource_id": db_encounter.id,
            "encounter_type": db_encounter.encounter_type,
        },
    )
    return db_encounter


@router.post("/admissions", response_model=schemas.AdmissionResponse)
def create_admission(
    admission: schemas.AdmissionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_doctor_or_admin(current_user)
    encounter = _get_encounter(db, admission.encounter_id)
    patient = _get_user(db, admission.patient_id, role="patient")
    doctor = None
    if admission.doctor_id is not None:
        doctor = _get_user(db, admission.doctor_id, role="doctor")
    department = _get_department(db, admission.department_id)
    if encounter.patient_id != admission.patient_id:
        raise HTTPException(status_code=400, detail="Admission patient must match encounter")
    if current_user.role == "doctor" and admission.doctor_id not in (None, current_user.id):
        raise HTTPException(status_code=403, detail="Doctors can only create their own admissions")

    doctor_id = admission.doctor_id if admission.doctor_id is not None else (
        current_user.id if current_user.role == "doctor" else encounter.doctor_id
    )
    if doctor is None and doctor_id is not None:
        doctor = _get_user(db, doctor_id, role="doctor")
    if doctor_id is not None and encounter.doctor_id not in (None, doctor_id):
        raise HTTPException(status_code=400, detail="Admission doctor must match encounter doctor")

    existing_active_admission = db.query(models.Admission).filter(
        models.Admission.patient_id == admission.patient_id,
        models.Admission.status.in_(ACTIVE_ADMISSION_STATUSES),
    ).first()
    if existing_active_admission:
        raise HTTPException(status_code=409, detail="Patient already has an active admission")

    bed = None
    if admission.bed_id is not None:
        bed = db.query(models.Bed).filter(models.Bed.id == admission.bed_id).first()
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")
        if admission.department_id is not None and bed.department_id != admission.department_id:
            raise HTTPException(status_code=400, detail="Admission bed must belong to admission department")
        if bed.status == "occupied":
            raise HTTPException(status_code=409, detail="Bed is already occupied")
    facility_id = _resolve_facility_id(
        "Admission participants must belong to the same facility",
        encounter,
        patient,
        doctor,
        department,
        bed,
    )
    _ensure_facility_access(current_user, facility_id)

    db_admission = models.Admission(
        facility_id=facility_id,
        encounter_id=admission.encounter_id,
        patient_id=admission.patient_id,
        doctor_id=doctor_id,
        department_id=admission.department_id,
        bed_id=admission.bed_id,
        admitted_at=admission.admitted_at or datetime.now(timezone.utc),
        reason=admission.reason,
        status="active",
    )
    db.add(db_admission)
    if bed is not None:
        bed.status = "occupied"
        bed.current_patient_id = admission.patient_id
    _event(
        db,
        patient_id=admission.patient_id,
        actor_user_id=current_user.id,
        encounter_id=admission.encounter_id,
        department_id=admission.department_id,
        facility_id=facility_id,
        event_type="ADMISSION_CREATED",
        title="Admission created",
        summary="Patient admitted for clinician-managed care",
    )
    db.commit()
    db.refresh(db_admission)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=admission.patient_id,
        action="CREATE_ADMISSION",
        details={"resource_type": "admission", "resource_id": db_admission.id},
    )
    return db_admission


@router.post("/orders", response_model=schemas.ClinicalOrderResponse)
def create_order(
    order: schemas.ClinicalOrderCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_doctor_or_admin(current_user)
    patient = _get_user(db, order.patient_id, role="patient")
    doctor = None
    if order.doctor_id is not None:
        doctor = _get_user(db, order.doctor_id, role="doctor")
    elif current_user.role == "doctor":
        doctor = current_user
    encounter = _get_encounter(db, order.encounter_id)
    department = _get_department(db, order.department_id)
    if encounter is not None and encounter.patient_id != order.patient_id:
        raise HTTPException(status_code=400, detail="Order patient must match encounter")
    if current_user.role == "doctor" and order.doctor_id not in (None, current_user.id):
        raise HTTPException(status_code=403, detail="Doctors can only create their own orders")

    doctor_id = order.doctor_id if order.doctor_id is not None else (
        current_user.id if current_user.role == "doctor" else None
    )
    if current_user.role == "doctor" and encounter is None:
        raise HTTPException(status_code=400, detail="Doctor orders must be linked to an encounter")
    if encounter is not None and doctor_id is not None and encounter.doctor_id not in (None, doctor_id):
        raise HTTPException(status_code=400, detail="Order doctor must match encounter doctor")
    facility_id = _resolve_facility_id(
        "Order participants must belong to the same facility",
        encounter,
        patient,
        doctor,
        department,
    )
    _ensure_facility_access(current_user, facility_id)

    db_order = models.ClinicalOrder(
        facility_id=facility_id,
        encounter_id=order.encounter_id,
        patient_id=order.patient_id,
        doctor_id=doctor_id,
        department_id=order.department_id,
        order_type=order.order_type,
        title=order.title,
        priority=order.priority or "routine",
        notes=order.notes,
        status="ordered",
    )
    db.add(db_order)
    db.flush()
    _event(
        db,
        patient_id=order.patient_id,
        actor_user_id=current_user.id,
        encounter_id=order.encounter_id,
        department_id=order.department_id,
        facility_id=facility_id,
        event_type="ORDER_CREATED",
        title=f"{order.order_type.title()} order created",
        summary="Department workflow order created for clinician review",
    )
    db.commit()
    db.refresh(db_order)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=order.patient_id,
        action="CREATE_CLINICAL_ORDER",
        details={
            "resource_type": "clinical_order",
            "resource_id": db_order.id,
            "order_type": order.order_type,
        },
    )
    return db_order


@router.get("/patient/timeline", response_model=schemas.PatientTimelineResponse)
def get_patient_timeline(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    patient_id = current_user.id
    encounters = db.query(models.Encounter).filter(
        models.Encounter.patient_id == patient_id
    ).order_by(models.Encounter.started_at.desc()).all()
    admissions = db.query(models.Admission).filter(
        models.Admission.patient_id == patient_id
    ).order_by(models.Admission.admitted_at.desc()).all()
    orders = db.query(models.ClinicalOrder).filter(
        models.ClinicalOrder.patient_id == patient_id
    ).order_by(models.ClinicalOrder.created_at.desc()).all()
    events = db.query(models.CareEvent).filter(
        models.CareEvent.patient_id == patient_id
    ).order_by(models.CareEvent.created_at.asc()).all()
    return {
        "encounters": encounters,
        "admissions": admissions,
        "orders": orders,
        "events": events,
    }


@router.get("/doctor/patients")
def get_doctor_patients(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[dict[str, Any]]:
    if current_user.role != "doctor" and not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")

    query = db.query(models.Encounter)
    if current_user.role == "doctor":
        query = query.filter(models.Encounter.doctor_id == current_user.id)
    encounters = query.order_by(models.Encounter.started_at.desc()).all()

    panel: dict[int, dict[str, Any]] = {}
    for encounter in encounters:
        patient = encounter.patient
        row = panel.setdefault(
            encounter.patient_id,
            {
                **_serialize_patient(patient),
                "latest_encounter_id": encounter.id,
                "latest_encounter_type": encounter.encounter_type,
                "latest_status": encounter.status,
                "open_orders": 0,
                "active_admissions": 0,
            },
        )
        if encounter.started_at and encounter.id == row["latest_encounter_id"]:
            row["latest_encounter_type"] = encounter.encounter_type
            row["latest_status"] = encounter.status

    for patient_id, row in panel.items():
        order_query = db.query(models.ClinicalOrder).filter(
            models.ClinicalOrder.patient_id == patient_id,
            models.ClinicalOrder.status.in_(OPEN_ORDER_STATUSES),
        )
        admission_query = db.query(models.Admission).filter(
            models.Admission.patient_id == patient_id,
            models.Admission.status.in_(ACTIVE_ADMISSION_STATUSES),
        )
        if current_user.role == "doctor":
            order_query = order_query.filter(models.ClinicalOrder.doctor_id == current_user.id)
            admission_query = admission_query.filter(models.Admission.doctor_id == current_user.id)
        row["open_orders"] = order_query.count()
        row["active_admissions"] = admission_query.count()

    return list(panel.values())


@router.get("/doctor/insights")
def get_doctor_insights(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    if current_user.role != "doctor" and not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")

    encounter_query = db.query(models.Encounter).filter(models.Encounter.status.in_(OPEN_ENCOUNTER_STATUSES))
    order_query = db.query(models.ClinicalOrder).filter(models.ClinicalOrder.status.in_(OPEN_ORDER_STATUSES))
    admission_query = db.query(models.Admission).filter(models.Admission.status.in_(ACTIVE_ADMISSION_STATUSES))
    if current_user.role == "doctor":
        encounter_query = encounter_query.filter(models.Encounter.doctor_id == current_user.id)
        order_query = order_query.filter(models.ClinicalOrder.doctor_id == current_user.id)
        admission_query = admission_query.filter(models.Admission.doctor_id == current_user.id)

    open_orders = order_query.count()
    active_admissions = admission_query.count()
    open_encounters = encounter_query.count()
    return {
        "open_encounters": open_encounters,
        "open_orders": open_orders,
        "active_admissions": active_admissions,
        "insights": [
            "Review open orders before closing encounters" if open_orders else "No open department orders",
            "Check admitted patients during rounds" if active_admissions else "No active admissions assigned",
            "Clinician review remains required for all AI-assisted signals",
        ],
    }


@router.get("/admin/operations")
def get_admin_operations(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    facility_query = _scope_query_to_user_facility(
        db.query(models.HospitalFacility),
        models.HospitalFacility.id,
        current_user,
    )
    department_query = _scope_query_to_user_facility(
        db.query(models.Department),
        models.Department.facility_id,
        current_user,
    )
    bed_query = _scope_query_to_user_facility(
        db.query(models.Bed),
        models.Bed.facility_id,
        current_user,
    )
    encounter_query = _scope_query_to_user_facility(
        db.query(models.Encounter),
        models.Encounter.facility_id,
        current_user,
    )
    admission_query = _scope_query_to_user_facility(
        db.query(models.Admission),
        models.Admission.facility_id,
        current_user,
    )
    order_query = _scope_query_to_user_facility(
        db.query(models.ClinicalOrder),
        models.ClinicalOrder.facility_id,
        current_user,
    )
    encounters = encounter_query.all()
    encounters_by_type: dict[str, int] = {}
    for encounter in encounters:
        encounters_by_type[encounter.encounter_type] = encounters_by_type.get(encounter.encounter_type, 0) + 1

    orders = order_query.all()
    orders_by_type: dict[str, int] = {}
    for order in orders:
        orders_by_type[order.order_type] = orders_by_type.get(order.order_type, 0) + 1

    return {
        "total_facilities": facility_query.count(),
        "total_departments": department_query.count(),
        "total_beds": bed_query.count(),
        "occupied_beds": bed_query.filter(models.Bed.status == "occupied").count(),
        "open_encounters": encounter_query.filter(models.Encounter.status.in_(OPEN_ENCOUNTER_STATUSES)).count(),
        "active_admissions": admission_query.filter(models.Admission.status.in_(ACTIVE_ADMISSION_STATUSES)).count(),
        "open_orders": order_query.filter(models.ClinicalOrder.status.in_(OPEN_ORDER_STATUSES)).count(),
        "encounters_by_type": encounters_by_type,
        "orders_by_type": orders_by_type,
        "clinical_safety_note": "Operational insights support clinicians and administrators; doctors make final clinical decisions.",
    }


@router.get("/triage-queue")
def get_triage_queue(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    # Require doctor, nurse or admin
    if not (auth.is_admin(current_user) or (current_user.role or "").lower() in ["doctor", "nurse"]):
        raise HTTPException(status_code=403, detail="Clinical staff privileges required")

    # Fetch patients in the system
    patients = db.query(models.User).filter(
        models.User.role == "patient"
    ).all()

    triage_queue = []
    for patient in patients:
        latest_vital = db.query(models.VitalObservation).filter(
            models.VitalObservation.patient_id == patient.id
        ).order_by(models.VitalObservation.observed_at.desc()).first()

        esi_score = 5
        reason = "Normal vital signs."

        if latest_vital:
            hr = latest_vital.heart_rate or 72.0
            sbp = latest_vital.systolic_bp or 120.0
            spo2 = latest_vital.spo2 or 98.0
            temp = latest_vital.temperature_c or 37.0

            # ESI 1: Immediate resuscitation
            if spo2 < 85.0 or hr < 40 or hr > 160:
                esi_score = 1
                reason = f"Immediate resuscitation needed: critical SpO2 ({spo2}%) or HR ({hr} bpm)."
            # ESI 2: High risk
            elif sbp > 180.0 or sbp < 90.0 or hr > 120 or temp > 39.5 or temp < 35.0 or spo2 < 90.0:
                esi_score = 2
                reason = f"High-risk situation: abnormal vitals (BP {sbp} mmHg, HR {hr} bpm, SpO2 {spo2}%)."
            # ESI 3: Urgent
            elif spo2 < 95.0 or sbp > 140.0 or sbp < 100.0 or hr > 100 or temp > 38.0 or temp < 36.0:
                esi_score = 3
                reason = "Urgent: moderate vital sign alterations."
            # ESI 4: Semi-urgent
            elif sbp > 130.0 or hr > 90:
                esi_score = 4
                reason = "Semi-urgent: minor vital sign alterations."

        if latest_vital:
            triage_queue.append({
                "patient_id": patient.id,
                "full_name": patient.full_name or patient.username,
                "esi_level": esi_score,
                "vital_summary": f"HR: {latest_vital.heart_rate} bpm, BP: {latest_vital.systolic_bp}/{latest_vital.diastolic_bp} mmHg, SpO2: {latest_vital.spo2}%, Temp: {latest_vital.temperature_c}°C",
                "triage_reason": reason,
                "observed_at": latest_vital.observed_at.isoformat() if latest_vital.observed_at else None
            })

    # Sort queue: ESI level ascending, then patient ID
    triage_queue.sort(key=lambda x: (x["esi_level"], x["patient_id"]))

    return {
        "queue": triage_queue,
        "total_waiting": len(triage_queue),
        "critical_count": sum(1 for p in triage_queue if p["esi_level"] <= 2),
        "clinical_safety_note": "ESI triage scores are automated clinical decision-support aids; clinicians perform final physical triage evaluations."
    }
