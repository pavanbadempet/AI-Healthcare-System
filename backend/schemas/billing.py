"""Billing domain schemas: billable services, invoices, payments."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class BillableServiceCreate(BaseModel):
    service_code: str
    name: str
    service_type: str
    department_id: Optional[int] = None
    unit_price: float


class BillableServiceResponse(BillableServiceCreate):
    id: int
    facility_id: Optional[int] = None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InvoiceLineItemCreate(BaseModel):
    service_id: Optional[int] = None
    description: Optional[str] = None
    quantity: float = 1
    unit_price: Optional[float] = None


class InvoiceLineItemResponse(BaseModel):
    id: int
    invoice_id: int
    service_id: Optional[int] = None
    description: str
    quantity: float
    unit_price: float
    line_total: float
    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    patient_id: int
    encounter_id: Optional[int] = None
    admission_id: Optional[int] = None
    discount_amount: float = 0
    tax_amount: float = 0
    currency: Optional[str] = "INR"
    items: List[InvoiceLineItemCreate]


class InvoiceResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    encounter_id: Optional[int] = None
    admission_id: Optional[int] = None
    created_by_id: Optional[int] = None
    status: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    balance_amount: float
    currency: str
    created_at: datetime
    issued_at: datetime
    items: List[InvoiceLineItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class BillingPaymentCreate(BaseModel):
    amount: float
    payment_method: str
    reference_id: Optional[str] = None


class BillingPaymentResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    invoice_id: int
    patient_id: int
    collected_by_id: Optional[int] = None
    amount: float
    payment_method: str
    reference_id: Optional[str] = None
    status: str
    collected_at: datetime
    model_config = ConfigDict(from_attributes=True)
