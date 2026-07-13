"""Discharge domain schemas: discharge summaries."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DischargeSummaryCreate(BaseModel):
    admission_id: int
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis_summary: str
    hospital_course: str
    medications: Optional[str] = None
    follow_up_plan: Optional[str] = None
    discharge_instructions: Optional[str] = None


class DischargeSummaryResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    admission_id: int
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis_summary: str
    hospital_course: str
    medications: Optional[str] = None
    follow_up_plan: Optional[str] = None
    discharge_instructions: Optional[str] = None
    status: str
    created_at: datetime
    finalized_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
