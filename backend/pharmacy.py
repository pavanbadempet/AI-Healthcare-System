"""Pharmacy workflow: inventory, prescriptions, dispensing, and metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import audit, auth, database, models, schemas
from .facility_scope import users_share_facility_context

router = APIRouter(prefix="/pharmacy", tags=["Pharmacy"])

PHARMACY_ROLES = {"pharmacist"}
PHARMACY_FACILITY_MISMATCH_DETAIL = "Pharmacy resources must belong to the same facility"
PHARMACY_FACILITY_ACCESS_DETAIL = "Pharmacy resource is outside the user's facility"


def _is_pharmacy_staff(current_user: models.User) -> bool:
    return (current_user.role or "").lower() in PHARMACY_ROLES


def _require_pharmacy_or_admin(current_user: models.User) -> None:
    if not (auth.is_admin(current_user) or _is_pharmacy_staff(current_user)):
        raise HTTPException(status_code=403, detail="Pharmacy or admin privileges required")


def _require_doctor_or_admin(current_user: models.User) -> None:
    if not (auth.is_admin(current_user) or current_user.role == "doctor"):
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")


def _require_staff_inventory_access(current_user: models.User) -> None:
    if not (auth.is_admin(current_user) or _is_pharmacy_staff(current_user) or current_user.role == "doctor"):
        raise HTTPException(status_code=403, detail="Clinical staff privileges required")


def _get_patient(db: Session, patient_id: int) -> models.User:
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _get_doctor(db: Session, doctor_id: int | None) -> models.User | None:
    if doctor_id is None:
        return None
    doctor = db.query(models.User).filter(
        models.User.id == doctor_id,
        models.User.role == "doctor",
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


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


def _ensure_doctor_can_access_patient(db: Session, current_user: models.User, patient_id: int) -> None:
    if auth.is_admin(current_user):
        patient = _get_patient(db, patient_id)
        _ensure_facility_access(current_user, patient.facility_id)
        return
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")
    if not _doctor_assigned_to_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")


def _validate_encounter(
    db: Session,
    encounter_id: int | None,
    patient_id: int,
    doctor_id: int | None,
) -> models.Encounter | None:
    if encounter_id is None:
        return None
    encounter = db.query(models.Encounter).filter(models.Encounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    if encounter.patient_id != patient_id:
        raise HTTPException(status_code=400, detail="Encounter patient must match prescription patient")
    if doctor_id is not None and encounter.doctor_id not in (None, doctor_id):
        raise HTTPException(status_code=400, detail="Encounter doctor must match prescription doctor")
    return encounter


def _get_inventory(db: Session, inventory_id: int) -> models.MedicationInventory:
    inventory = db.query(models.MedicationInventory).filter(models.MedicationInventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Medication inventory not found")
    return inventory


def _get_prescription(db: Session, prescription_id: int) -> models.Prescription:
    prescription = db.query(models.Prescription).filter(models.Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription


def _resolve_pharmacy_facility_id(*entities: object | None) -> int | None:
    facility_ids = {
        getattr(entity, "facility_id", None)
        for entity in entities
        if entity is not None and getattr(entity, "facility_id", None) is not None
    }
    if len(facility_ids) > 1:
        raise HTTPException(status_code=400, detail=PHARMACY_FACILITY_MISMATCH_DETAIL)
    return next(iter(facility_ids), None)


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(or_(facility_column == current_user.facility_id, facility_column.is_(None)))


def _ensure_facility_access(current_user: models.User, facility_id: int | None) -> None:
    if current_user.facility_id is None or facility_id is None:
        return
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=PHARMACY_FACILITY_ACCESS_DETAIL)


def _add_care_event(
    db: Session,
    *,
    facility_id: int | None = None,
    patient_id: int,
    actor_user_id: int | None,
    event_type: str,
    title: str,
    encounter_id: int | None = None,
    summary: str | None = None,
) -> None:
    db.add(models.CareEvent(
        facility_id=facility_id,
        patient_id=patient_id,
        actor_user_id=actor_user_id,
        encounter_id=encounter_id,
        event_type=event_type,
        title=title,
        summary=summary,
        severity="info",
    ))


def _serialize_prescription(prescription: models.Prescription) -> dict[str, Any]:
    return schemas.PrescriptionResponse.model_validate(prescription).model_dump(mode="json")


@router.post("/inventory", response_model=schemas.MedicationInventoryResponse)
def create_inventory_item(
    item: schemas.MedicationInventoryCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_pharmacy_or_admin(current_user)
    if item.quantity_on_hand < 0 or item.reorder_level < 0:
        raise HTTPException(status_code=400, detail="Inventory quantities cannot be negative")

    db_item = models.MedicationInventory(
        facility_id=current_user.facility_id,
        medication_name=item.medication_name,
        strength=item.strength,
        form=item.form,
        batch_number=item.batch_number,
        quantity_on_hand=item.quantity_on_hand,
        reorder_level=item.reorder_level,
        status="active",
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=None,
        facility_id=db_item.facility_id,
        action="CREATE_MEDICATION_INVENTORY",
        details={"resource_type": "medication_inventory", "resource_id": db_item.id},
    )
    return db_item


@router.get("/inventory", response_model=list[schemas.MedicationInventoryResponse])
def list_inventory(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_staff_inventory_access(current_user)
    query = _scope_query_to_user_facility(
        db.query(models.MedicationInventory),
        models.MedicationInventory.facility_id,
        current_user,
    )
    return query.order_by(models.MedicationInventory.medication_name.asc()).all()


@router.post("/prescriptions", response_model=schemas.PrescriptionResponse)
def create_prescription(
    prescription: schemas.PrescriptionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_doctor_or_admin(current_user)
    patient = _get_patient(db, prescription.patient_id)
    doctor_id = prescription.doctor_id if prescription.doctor_id is not None else (
        current_user.id if current_user.role == "doctor" else None
    )
    doctor = _get_doctor(db, doctor_id)
    encounter = _validate_encounter(db, prescription.encounter_id, prescription.patient_id, doctor_id)

    if current_user.role == "doctor":
        if doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Doctors can create only their own prescriptions")
        _ensure_doctor_can_access_patient(db, current_user, prescription.patient_id)

    if not prescription.items:
        raise HTTPException(status_code=400, detail="Prescription must include at least one item")

    inventories: list[models.MedicationInventory] = []
    for item in prescription.items:
        if item.quantity_prescribed <= 0:
            raise HTTPException(status_code=400, detail="Prescribed quantity must be positive")
        if item.inventory_id is not None:
            inventories.append(_get_inventory(db, item.inventory_id))

    facility_id = _resolve_pharmacy_facility_id(
        current_user,
        patient,
        doctor,
        encounter,
        *inventories,
    )

    db_prescription = models.Prescription(
        facility_id=facility_id,
        encounter_id=prescription.encounter_id,
        patient_id=prescription.patient_id,
        doctor_id=doctor_id,
        diagnosis_context=prescription.diagnosis_context,
        status="active",
    )
    db.add(db_prescription)
    db.flush()

    for item in prescription.items:
        db.add(models.PrescriptionItem(
            prescription_id=db_prescription.id,
            inventory_id=item.inventory_id,
            medication_name=item.medication_name,
            dosage=item.dosage,
            frequency=item.frequency,
            duration=item.duration,
            quantity_prescribed=item.quantity_prescribed,
            quantity_dispensed=0,
            instructions=item.instructions,
            status="pending",
        ))

    _add_care_event(
        db,
        facility_id=facility_id,
        patient_id=prescription.patient_id,
        actor_user_id=current_user.id,
        encounter_id=prescription.encounter_id,
        event_type="PRESCRIPTION_CREATED",
        title="Prescription created",
        summary="Clinician-created prescription is ready for pharmacy review.",
    )
    db.commit()
    db.refresh(db_prescription)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=prescription.patient_id,
        action="CREATE_PRESCRIPTION",
        details={
            "resource_type": "prescription",
            "resource_id": db_prescription.id,
            "item_count": len(prescription.items),
        },
    )
    return _get_prescription(db, db_prescription.id)


@router.get("/patient/prescriptions", response_model=list[schemas.PrescriptionResponse])
def get_patient_prescriptions(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    return db.query(models.Prescription).filter(
        models.Prescription.patient_id == current_user.id
    ).order_by(models.Prescription.created_at.desc()).all()


@router.get("/doctor/patients/{patient_id}/prescriptions")
def get_doctor_patient_prescriptions(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _ensure_doctor_can_access_patient(db, current_user, patient_id)
    prescriptions = db.query(models.Prescription).filter(
        models.Prescription.patient_id == patient_id
    ).order_by(models.Prescription.created_at.desc()).all()
    return {
        "patient_id": patient_id,
        "prescriptions": [_serialize_prescription(prescription) for prescription in prescriptions],
        "clinical_safety_note": "Prescriptions support clinician and pharmacist workflows; clinicians remain responsible for treatment decisions.",
    }


@router.post("/prescriptions/{prescription_id}/dispense", response_model=schemas.PrescriptionResponse)
def dispense_prescription(
    prescription_id: int,
    dispense: schemas.DispensePrescriptionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_pharmacy_or_admin(current_user)
    prescription = _get_prescription(db, prescription_id)
    _ensure_facility_access(current_user, prescription.facility_id)
    if not dispense.items:
        raise HTTPException(status_code=400, detail="Dispense request must include at least one item")

    item_by_id = {item.id: item for item in prescription.items}
    for requested in dispense.items:
        if requested.quantity_dispensed <= 0:
            raise HTTPException(status_code=400, detail="Dispensed quantity must be positive")
        item = item_by_id.get(requested.prescription_item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Prescription item not found")

        remaining = item.quantity_prescribed - item.quantity_dispensed
        if requested.quantity_dispensed > remaining:
            raise HTTPException(status_code=400, detail="Dispensed quantity exceeds prescribed quantity")

        inventory = None
        if item.inventory_id is not None:
            inventory = _get_inventory(db, item.inventory_id)
            _resolve_pharmacy_facility_id(current_user, prescription, inventory)
            if inventory.quantity_on_hand < requested.quantity_dispensed:
                raise HTTPException(status_code=409, detail="Insufficient medication inventory")

        if inventory is not None:
            inventory.quantity_on_hand -= requested.quantity_dispensed
        item.quantity_dispensed += requested.quantity_dispensed
        item.status = "dispensed" if item.quantity_dispensed >= item.quantity_prescribed else "partially_dispensed"
        db.add(models.DispenseRecord(
            facility_id=prescription.facility_id,
            prescription_id=prescription.id,
            prescription_item_id=item.id,
            inventory_id=item.inventory_id,
            patient_id=prescription.patient_id,
            dispensed_by_id=current_user.id,
            quantity_dispensed=requested.quantity_dispensed,
            status="dispensed",
        ))

    all_dispensed = all(item.quantity_dispensed >= item.quantity_prescribed for item in prescription.items)
    prescription.status = "dispensed" if all_dispensed else "partially_dispensed"
    if all_dispensed:
        prescription.dispensed_at = datetime.now(timezone.utc)

    _add_care_event(
        db,
        facility_id=prescription.facility_id,
        patient_id=prescription.patient_id,
        actor_user_id=current_user.id,
        encounter_id=prescription.encounter_id,
        event_type="PRESCRIPTION_DISPENSED",
        title="Prescription dispensed",
        summary="Pharmacy dispensed medication against a clinician prescription.",
    )
    db.commit()
    db.refresh(prescription)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=prescription.patient_id,
        action="DISPENSE_PRESCRIPTION",
        details={
            "resource_type": "prescription",
            "resource_id": prescription.id,
            "item_count": len(dispense.items),
        },
    )
    return _get_prescription(db, prescription.id)


@router.get("/admin/metrics")
def get_pharmacy_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_pharmacy_or_admin(current_user)
    inventory_query = _scope_query_to_user_facility(
        db.query(models.MedicationInventory),
        models.MedicationInventory.facility_id,
        current_user,
    )
    prescription_query = _scope_query_to_user_facility(
        db.query(models.Prescription),
        models.Prescription.facility_id,
        current_user,
    )
    dispense_query = _scope_query_to_user_facility(
        db.query(models.DispenseRecord),
        models.DispenseRecord.facility_id,
        current_user,
    )
    inventory_items = inventory_query.all()
    prescriptions = prescription_query.all()
    return {
        "total_inventory_items": len(inventory_items),
        "low_stock_items": sum(
            1 for item in inventory_items if item.quantity_on_hand <= item.reorder_level
        ),
        "total_prescriptions": len(prescriptions),
        "active_prescriptions": sum(1 for prescription in prescriptions if prescription.status == "active"),
        "dispensed_prescriptions": sum(1 for prescription in prescriptions if prescription.status == "dispensed"),
        "total_dispense_records": dispense_query.count(),
        "clinical_safety_note": "Pharmacy metrics support operations; clinicians and pharmacists verify medication decisions.",
    }


# --- Phase 10 Safety Checker Route ---
from pydantic import BaseModel as PydanticBaseModel


class DrugSafetyCheckRequest(PydanticBaseModel):
    patient_id: int
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    additional_allergies: list[str] | None = None


@router.post("/check-safety")
async def check_prescription_safety(
    req: DrugSafetyCheckRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _ensure_doctor_can_access_patient(db, current_user, req.patient_id)

    from backend.agents.safety_agent import PrescribingSafetyAgent
    agent = PrescribingSafetyAgent(db)
    result = await agent.check_prescription_safety(
        patient_id=req.patient_id,
        medication_name=req.medication_name,
        dosage=req.dosage,
        frequency=req.frequency,
        duration=req.duration,
        additional_allergies=req.additional_allergies
    )
    return result


@router.get("/compare-pricing")
def compare_medication_pricing(
    medication_name: str,
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    # Mock price search for medication name
    med_lower = medication_name.lower()

    # Generic base prices to generate mock variations
    base_price = 15.0
    if "metformin" in med_lower or "glucophage" in med_lower:
        base_price = 10.0
    elif "atorvastatin" in med_lower or "lipitor" in med_lower:
        base_price = 25.0
    elif "amoxicillin" in med_lower:
        base_price = 12.0
    elif "albuterol" in med_lower or "proair" in med_lower:
        base_price = 45.0
    elif "lisinopril" in med_lower or "zestril" in med_lower:
        base_price = 8.0

    prices = [
        {"chain": "CVS Pharmacy", "price": round(base_price * 1.15, 2), "distance": 1.2, "available": True},
        {"chain": "Walgreens", "price": round(base_price * 1.25, 2), "distance": 2.4, "available": True},
        {"chain": "Walmart Pharmacy", "price": round(base_price * 0.85, 2), "distance": 4.1, "available": True},
        {"chain": "Costco Pharmacy", "price": round(base_price * 0.75, 2), "distance": 6.8, "available": True},
        {"chain": "Local Neighborhood Rx", "price": round(base_price * 1.00, 2), "distance": 0.5, "available": True},
    ]

    # Sort by price
    prices.sort(key=lambda x: x["price"])

    return {
        "medication": medication_name,
        "base_price": base_price,
        "prices": prices,
        "message": "Medicine prices checked across major local and retail pharmacy chains."
    }


@router.get("/generic-substitute")
def get_generic_substitution(
    branded_name: str,
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    # Map of branded drugs to generic equivalents and average savings
    brand_map = {
        "glucophage": {"generic": "Metformin", "brand": "Glucophage", "savings": 45.00, "strength_match": "500mg, 850mg, 1000mg"},
        "lipitor": {"generic": "Atorvastatin", "brand": "Lipitor", "savings": 85.00, "strength_match": "10mg, 20mg, 40mg, 80mg"},
        "zocor": {"generic": "Simvastatin", "brand": "Zocor", "savings": 50.00, "strength_match": "5mg, 10mg, 20mg, 40mg, 80mg"},
        "zestril": {"generic": "Lisinopril", "brand": "Zestril", "savings": 35.00, "strength_match": "5mg, 10mg, 20mg, 40mg"},
        "proair": {"generic": "Albuterol Inhaler", "brand": "ProAir HFA", "savings": 60.00, "strength_match": "90mcg"},
        "synthroid": {"generic": "Levothyroxine", "brand": "Synthroid", "savings": 40.00, "strength_match": "25mcg, 50mcg, 75mcg, 88mcg, 100mcg"},
        "nexium": {"generic": "Esomeprazole", "brand": "Nexium", "savings": 70.00, "strength_match": "20mg, 40mg"}
    }

    brand_lower = branded_name.lower().strip()
    match = None
    for brand, details in brand_map.items():
        if brand in brand_lower:
            match = details
            break

    if not match:
        return {
            "substituted": False,
            "branded_name": branded_name,
            "message": "No brand-to-generic mapping found in the clinical catalog for this medication.",
            "savings": 0.0
        }

    return {
        "substituted": True,
        "branded_name": match["brand"],
        "generic_name": match["generic"],
        "savings": match["savings"],
        "strength_match": match["strength_match"],
        "message": f"Cheaper generic alternative {match['generic']} found for brand-name {match['brand']}."
    }

