"""Pydantic v2 model serializers for clinical inference endpoints."""
from pydantic import BaseModel, Field
from typing import List, Optional

class VitalSignReading(BaseModel):
    loinc_code: str
    value: float
    unit: str

class ClinicalInferenceRequest(BaseModel):
    patient_id: str
    vitals: List[VitalSignReading] = Field(default_factory=list)
    confidence_level: Optional[float] = 0.95
