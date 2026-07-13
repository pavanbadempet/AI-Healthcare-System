"""Billing domain models: services, invoices, line items, and payments."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class BillableService(Base):
    __tablename__ = "billable_services"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    service_code = Column(String, unique=True, index=True)
    name = Column(String)
    service_type = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    unit_price = Column(Float, default=0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    department = relationship("Department")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="issued")  # issued, paid, partially_paid, voided, overdue
    subtotal = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    balance_amount = Column(Float, default=0)
    currency = Column(String, default="INR")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    created_by = relationship("User", foreign_keys=[created_by_id])
    items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("BillingPayment", back_populates="invoice")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), index=True)
    service_id = Column(Integer, ForeignKey("billable_services.id"), nullable=True)
    description = Column(String)
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0)
    line_total = Column(Float, default=0)

    invoice = relationship("Invoice", back_populates="items")
    service = relationship("BillableService")


class BillingPayment(Base):
    __tablename__ = "billing_payments"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    collected_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    amount = Column(Float, default=0)
    payment_method = Column(String)
    reference_id = Column(String, nullable=True)
    status = Column(String, default="collected")
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    invoice = relationship("Invoice", back_populates="payments")
    patient = relationship("User", foreign_keys=[patient_id])
    collected_by = relationship("User", foreign_keys=[collected_by_id])
