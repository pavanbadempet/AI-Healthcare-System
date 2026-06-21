"""Hospital billing workflow: services, invoices, payments, and metrics."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import audit, auth, database, models, schemas

router = APIRouter(prefix="/billing", tags=["Billing"])

BILLING_ROLES = {"billing", "cashier", "billing_staff"}
BILLING_FACILITY_MISMATCH_DETAIL = "Billing resources must belong to the same facility"
BILLING_FACILITY_ACCESS_DETAIL = "Billing resource is outside the user's facility"


def _is_billing_staff(current_user: models.User) -> bool:
    return (current_user.role or "").lower() in BILLING_ROLES


def _require_billing_or_admin(current_user: models.User) -> None:
    if not (auth.is_admin(current_user) or _is_billing_staff(current_user)):
        raise HTTPException(status_code=403, detail="Billing or admin privileges required")


def _get_patient(db: Session, patient_id: int) -> models.User:
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _get_service(db: Session, service_id: int) -> models.BillableService:
    service = db.query(models.BillableService).filter(models.BillableService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Billable service not found")
    return service


def _get_invoice(db: Session, invoice_id: int) -> models.Invoice:
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


def _resolve_billing_facility_id(*entities: object | None) -> int | None:
    facility_ids = {
        getattr(entity, "facility_id", None)
        for entity in entities
        if entity is not None and getattr(entity, "facility_id", None) is not None
    }
    if len(facility_ids) > 1:
        raise HTTPException(status_code=400, detail=BILLING_FACILITY_MISMATCH_DETAIL)
    return next(iter(facility_ids), None)


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(or_(facility_column == current_user.facility_id, facility_column.is_(None)))


def _ensure_facility_access(current_user: models.User, facility_id: int | None) -> None:
    if current_user.facility_id is None or facility_id is None:
        return
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=BILLING_FACILITY_ACCESS_DETAIL)


def _validate_context(
    db: Session,
    invoice: schemas.InvoiceCreate,
) -> tuple[models.Encounter | None, models.Admission | None]:
    encounter = None
    if invoice.encounter_id is not None:
        encounter = db.query(models.Encounter).filter(models.Encounter.id == invoice.encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        if encounter.patient_id != invoice.patient_id:
            raise HTTPException(status_code=400, detail="Encounter patient must match invoice patient")

    admission = None
    if invoice.admission_id is not None:
        admission = db.query(models.Admission).filter(models.Admission.id == invoice.admission_id).first()
        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")
        if admission.patient_id != invoice.patient_id:
            raise HTTPException(status_code=400, detail="Admission patient must match invoice patient")
        if encounter is not None and admission.encounter_id != encounter.id:
            raise HTTPException(status_code=400, detail="Admission encounter must match invoice encounter")
    return encounter, admission


def _round_money(value: float) -> float:
    return round(float(value), 2)


def _serialize_invoice(invoice: models.Invoice) -> dict[str, Any]:
    return schemas.InvoiceResponse.model_validate(invoice).model_dump(mode="json")


@router.post("/services", response_model=schemas.BillableServiceResponse)
def create_billable_service(
    service: schemas.BillableServiceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_billing_or_admin(current_user)
    if service.unit_price < 0:
        raise HTTPException(status_code=400, detail="Service price cannot be negative")
    if service.department_id is not None:
        department = db.query(models.Department).filter(models.Department.id == service.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
    else:
        department = None
    facility_id = _resolve_billing_facility_id(current_user, department)

    existing = db.query(models.BillableService).filter(
        models.BillableService.service_code == service.service_code,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Billable service already exists")

    db_service = models.BillableService(
        facility_id=facility_id,
        service_code=service.service_code,
        name=service.name,
        service_type=service.service_type,
        department_id=service.department_id,
        unit_price=service.unit_price,
        status="active",
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=None,
        facility_id=db_service.facility_id,
        action="CREATE_BILLABLE_SERVICE",
        details={"resource_type": "billable_service", "resource_id": db_service.id},
    )
    return db_service


@router.get("/services", response_model=list[schemas.BillableServiceResponse])
def list_billable_services(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_billing_or_admin(current_user)
    query = _scope_query_to_user_facility(
        db.query(models.BillableService),
        models.BillableService.facility_id,
        current_user,
    )
    return query.order_by(models.BillableService.name.asc()).all()


@router.post("/invoices", response_model=schemas.InvoiceResponse)
def create_invoice(
    invoice: schemas.InvoiceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_billing_or_admin(current_user)
    patient = _get_patient(db, invoice.patient_id)
    encounter, admission = _validate_context(db, invoice)

    if not invoice.items:
        raise HTTPException(status_code=400, detail="Invoice must include at least one item")
    if invoice.discount_amount < 0 or invoice.tax_amount < 0:
        raise HTTPException(status_code=400, detail="Invoice adjustments cannot be negative")

    prepared_items: list[dict[str, Any]] = []
    services: list[models.BillableService] = []
    subtotal = 0.0
    for item in invoice.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Invoice item quantity must be positive")
        service = _get_service(db, item.service_id) if item.service_id is not None else None
        if service is not None:
            services.append(service)
        unit_price = item.unit_price if item.unit_price is not None else (service.unit_price if service else None)
        if unit_price is None:
            raise HTTPException(status_code=400, detail="Invoice item unit price is required")
        if unit_price < 0:
            raise HTTPException(status_code=400, detail="Invoice item unit price cannot be negative")
        description = item.description or (service.name if service else None)
        if not description:
            raise HTTPException(status_code=400, detail="Invoice item description is required")
        line_total = _round_money(item.quantity * unit_price)
        subtotal = _round_money(subtotal + line_total)
        prepared_items.append({
            "service_id": item.service_id,
            "description": description,
            "quantity": item.quantity,
            "unit_price": _round_money(unit_price),
            "line_total": line_total,
        })

    total_amount = _round_money(subtotal - invoice.discount_amount + invoice.tax_amount)
    if total_amount < 0:
        raise HTTPException(status_code=400, detail="Invoice total cannot be negative")
    facility_id = _resolve_billing_facility_id(current_user, patient, encounter, admission, *services)

    db_invoice = models.Invoice(
        facility_id=facility_id,
        patient_id=invoice.patient_id,
        encounter_id=invoice.encounter_id,
        admission_id=invoice.admission_id,
        created_by_id=current_user.id,
        status="issued",
        subtotal=subtotal,
        discount_amount=_round_money(invoice.discount_amount),
        tax_amount=_round_money(invoice.tax_amount),
        total_amount=total_amount,
        paid_amount=0,
        balance_amount=total_amount,
        currency=(invoice.currency or "INR").upper(),
    )
    db.add(db_invoice)
    db.flush()
    for prepared in prepared_items:
        db.add(models.InvoiceLineItem(invoice_id=db_invoice.id, **prepared))

    db.add(models.CareEvent(
        facility_id=facility_id,
        patient_id=invoice.patient_id,
        actor_user_id=current_user.id,
        encounter_id=invoice.encounter_id,
        event_type="INVOICE_ISSUED",
        title="Invoice issued",
        summary="Billing invoice issued for hospital services.",
        severity="info",
    ))
    db.commit()
    db.refresh(db_invoice)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=invoice.patient_id,
        action="CREATE_INVOICE",
        details={
            "resource_type": "invoice",
            "resource_id": db_invoice.id,
            "item_count": len(prepared_items),
        },
    )
    return _get_invoice(db, db_invoice.id)


@router.get("/patient/invoices", response_model=list[schemas.InvoiceResponse])
def get_patient_invoices(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    return db.query(models.Invoice).filter(
        models.Invoice.patient_id == current_user.id
    ).order_by(models.Invoice.created_at.desc()).all()


@router.get("/admin/invoices", response_model=list[schemas.InvoiceResponse])
def list_invoices(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_billing_or_admin(current_user)
    query = _scope_query_to_user_facility(
        db.query(models.Invoice),
        models.Invoice.facility_id,
        current_user,
    )
    return query.order_by(models.Invoice.created_at.desc()).all()


@router.post("/invoices/{invoice_id}/payments")
def record_invoice_payment(
    invoice_id: int,
    payment: schemas.BillingPaymentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_billing_or_admin(current_user)
    invoice = _get_invoice(db, invoice_id)
    _ensure_facility_access(current_user, invoice.facility_id)
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")
    if payment.amount > invoice.balance_amount:
        raise HTTPException(status_code=400, detail="Payment amount exceeds invoice balance")

    db_payment = models.BillingPayment(
        facility_id=invoice.facility_id,
        invoice_id=invoice.id,
        patient_id=invoice.patient_id,
        collected_by_id=current_user.id,
        amount=_round_money(payment.amount),
        payment_method=payment.payment_method,
        reference_id=payment.reference_id,
        status="collected",
    )
    invoice.paid_amount = _round_money(invoice.paid_amount + payment.amount)
    invoice.balance_amount = _round_money(invoice.total_amount - invoice.paid_amount)
    invoice.status = "paid" if invoice.balance_amount <= 0 else "partially_paid"
    if invoice.balance_amount <= 0:
        invoice.balance_amount = 0

    db.add(db_payment)
    db.add(models.CareEvent(
        facility_id=invoice.facility_id,
        patient_id=invoice.patient_id,
        actor_user_id=current_user.id,
        encounter_id=invoice.encounter_id,
        event_type="PAYMENT_RECORDED",
        title="Payment recorded",
        summary="Payment was recorded against a billing invoice.",
        severity="info",
    ))
    db.commit()
    db.refresh(db_payment)
    refreshed_invoice = _get_invoice(db, invoice.id)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=invoice.patient_id,
        action="RECORD_INVOICE_PAYMENT",
        details={
            "resource_type": "invoice",
            "resource_id": invoice.id,
            "payment_id": db_payment.id,
        },
    )
    return {
        "payment": schemas.BillingPaymentResponse.model_validate(db_payment).model_dump(mode="json"),
        "invoice": _serialize_invoice(refreshed_invoice),
    }


@router.get("/admin/metrics")
def get_billing_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_billing_or_admin(current_user)
    invoice_query = _scope_query_to_user_facility(
        db.query(models.Invoice),
        models.Invoice.facility_id,
        current_user,
    )
    payment_query = _scope_query_to_user_facility(
        db.query(models.BillingPayment),
        models.BillingPayment.facility_id,
        current_user,
    )
    service_query = _scope_query_to_user_facility(
        db.query(models.BillableService),
        models.BillableService.facility_id,
        current_user,
    )
    invoices = invoice_query.all()
    payments = payment_query.all()
    return {
        "total_services": service_query.count(),
        "total_invoices": len(invoices),
        "issued_invoices": sum(1 for invoice in invoices if invoice.status == "issued"),
        "partially_paid_invoices": sum(1 for invoice in invoices if invoice.status == "partially_paid"),
        "paid_invoices": sum(1 for invoice in invoices if invoice.status == "paid"),
        "total_billed": _round_money(sum(invoice.total_amount for invoice in invoices)),
        "total_collected": _round_money(sum(payment.amount for payment in payments)),
        "outstanding_balance": _round_money(sum(invoice.balance_amount for invoice in invoices)),
        "operations_note": "Billing metrics support cashier and administrator workflows; finance teams verify collections.",
    }


@router.get("/estimate")
def get_procedure_cost_estimate(
    procedure_type: str,
    insurance_provider: str | None = None,
    region: str = "US",
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    proc_lower = procedure_type.lower()

    facility_fee = 100.0
    doctor_fee = 150.0
    lab_fee = 50.0

    if "mri" in proc_lower or "magnetic" in proc_lower:
        facility_fee = 850.0
        doctor_fee = 350.0
        lab_fee = 200.0
    elif "blood" in proc_lower or "panel" in proc_lower or "lab" in proc_lower:
        facility_fee = 45.0
        doctor_fee = 60.0
        lab_fee = 95.0
    elif "cardiac" in proc_lower or "ekg" in proc_lower or "ecg" in proc_lower:
        facility_fee = 200.0
        doctor_fee = 250.0
        lab_fee = 75.0
    elif "consult" in proc_lower or "visit" in proc_lower:
        facility_fee = 50.0
        doctor_fee = 150.0
        lab_fee = 0.0

    # Regional currency & pricing mapping
    reg_upper = region.upper()
    if reg_upper == "IN":
        currency = "INR"
        currency_symbol = "₹"
        multiplier = 10.0
        pricing_model = "Indian CGHS Reimbursement Standard"
    elif reg_upper == "UK":
        currency = "GBP"
        currency_symbol = "£"
        multiplier = 0.8
        pricing_model = "UK NHS Private Costing Reference"
    elif reg_upper == "EU":
        currency = "EUR"
        currency_symbol = "€"
        multiplier = 0.9
        pricing_model = "European Healthcare Standard Tariffs"
    else:
        currency = "USD"
        currency_symbol = "$"
        multiplier = 1.0
        pricing_model = "Medicare Relative Value Units (RVU) Standard"

    facility_fee *= multiplier
    doctor_fee *= multiplier
    lab_fee *= multiplier

    gross_total = facility_fee + doctor_fee + lab_fee
    coverage_percentage = 0.0
    copay = gross_total

    if insurance_provider:
        ins_lower = insurance_provider.lower()
        if "blue" in ins_lower or "bcbs" in ins_lower:
            coverage_percentage = 80.0
            copay = gross_total * 0.20
        elif "medicare" in ins_lower:
            coverage_percentage = 90.0
            copay = gross_total * 0.10
        elif "aetna" in ins_lower:
            coverage_percentage = 75.0
            copay = gross_total * 0.25
        else:
            coverage_percentage = 50.0
            copay = gross_total * 0.50

    facility_fee = round(facility_fee, 2)
    doctor_fee = round(doctor_fee, 2)
    lab_fee = round(lab_fee, 2)
    gross_total = round(gross_total, 2)
    copay = round(copay, 2)
    insurance_covered = round(gross_total - copay, 2)

    return {
        "procedure_type": procedure_type,
        "insurance_provider": insurance_provider or "Self-Pay / Cash",
        "region": region,
        "currency": currency,
        "currency_symbol": currency_symbol,
        "breakdown": {
            "facility_fee": facility_fee,
            "doctor_fee": doctor_fee,
            "lab_fee": lab_fee
        },
        "gross_total": gross_total,
        "coverage_percentage": coverage_percentage,
        "insurance_covered": insurance_covered,
        "patient_responsibility": copay,
        "pricing_model": pricing_model,
        "message": f"Procedure cost estimate compiled for {procedure_type} in {region} under {insurance_provider or 'Self-Pay'}."
    }
