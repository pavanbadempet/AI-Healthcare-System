"""Hospital domain schemas: facilities, departments, beds, encounters, admissions."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FacilityCreate(BaseModel):
    name: str
    facility_type: str = "hospital"
    country: Optional[str] = None
    region: Optional[str] = None


class FacilityResponse(FacilityCreate):
    id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    facility_id: Optional[int] = None
    name: str
    department_type: str
    location: Optional[str] = None
    description: Optional[str] = None


class DepartmentResponse(DepartmentCreate):
    id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BedCreate(BaseModel):
    department_id: int
    bed_number: str
    ward: Optional[str] = None
    status: Optional[str] = "available"


class BedResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    department_id: int
    bed_number: str
    ward: Optional[str] = None
    status: str
    current_patient_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EncounterCreate(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    encounter_type: str
    reason: Optional[str] = None
    priority: Optional[str] = "routine"


class EncounterResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    encounter_type: str
    reason: Optional[str] = None
    priority: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AdmissionCreate(BaseModel):
    encounter_id: int
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    bed_id: Optional[int] = None
    admitted_at: Optional[datetime] = None
    reason: Optional[str] = None


class AdmissionResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    encounter_id: int
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    bed_id: Optional[int] = None
    admitted_at: datetime
    discharged_at: Optional[datetime] = None
    reason: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)
