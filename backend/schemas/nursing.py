"""Nursing domain schemas: nursing task creation, completion, responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NursingTaskCreate(BaseModel):
    patient_id: int
    assigned_nurse_id: Optional[int] = None
    encounter_id: Optional[int] = None
    admission_id: Optional[int] = None
    department_id: Optional[int] = None
    task_type: str
    title: str
    instructions: Optional[str] = None
    priority: Optional[str] = "routine"
    due_at: Optional[datetime] = None


class NursingTaskComplete(BaseModel):
    completion_note: Optional[str] = None


class NursingTaskResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    assigned_nurse_id: Optional[int] = None
    created_by_id: Optional[int] = None
    completed_by_id: Optional[int] = None
    encounter_id: Optional[int] = None
    admission_id: Optional[int] = None
    department_id: Optional[int] = None
    task_type: str
    title: str
    instructions: Optional[str] = None
    priority: str
    status: str
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_note: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
