"""Appointment domain schemas: appointment creation, responses, doctor info."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AppointmentCreate(BaseModel):
    doctor_id: Optional[int] = None  # Link to real doctor
    specialist: str  # Fallback name
    date: str
    time: str
    reason: str


class AppointmentResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    user_id: int  # Vital for Admin/Doctor visibility
    doctor_id: Optional[int] = None
    specialist: str
    date_time: datetime
    reason: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class DoctorResponse(BaseModel):
    id: int
    full_name: str
    specialization: str = "General Physician"  # Default for now if not in DB
    consultation_fee: float
    profile_picture: Optional[str] = None
