"""Pharmacy domain schemas: medication inventory, prescriptions, dispensing."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class MedicationInventoryCreate(BaseModel):
    medication_name: str
    strength: Optional[str] = None
    form: Optional[str] = None
    batch_number: Optional[str] = None
    quantity_on_hand: float = 0
    reorder_level: float = 0


class MedicationInventoryResponse(MedicationInventoryCreate):
    id: int
    facility_id: Optional[int] = None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PrescriptionItemCreate(BaseModel):
    inventory_id: Optional[int] = None
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    quantity_prescribed: float = 1
    instructions: Optional[str] = None


class PrescriptionItemResponse(BaseModel):
    id: int
    prescription_id: int
    inventory_id: Optional[int] = None
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    quantity_prescribed: float
    quantity_dispensed: float
    instructions: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class PrescriptionCreate(BaseModel):
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis_context: Optional[str] = None
    items: List[PrescriptionItemCreate]


class PrescriptionResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis_context: Optional[str] = None
    status: str
    created_at: datetime
    dispensed_at: Optional[datetime] = None
    items: List[PrescriptionItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class DispenseItemCreate(BaseModel):
    prescription_item_id: int
    quantity_dispensed: float


class DispensePrescriptionCreate(BaseModel):
    items: List[DispenseItemCreate]


class DispenseRecordResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    prescription_id: int
    prescription_item_id: Optional[int] = None
    inventory_id: Optional[int] = None
    patient_id: int
    dispensed_by_id: Optional[int] = None
    quantity_dispensed: float
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
