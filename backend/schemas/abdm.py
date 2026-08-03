"""
Pydantic Schemas for ABDM (Ayushman Bharat Digital Mission) Health ID & Consent Manager Sandbox.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ABHACreateRequest(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Aarav Sharma"})
    gender: str = Field("M", json_schema_extra={"example": "M"})
    year_of_birth: int = Field(1990, json_schema_extra={"example": 1990})
    mobile: str = Field(..., json_schema_extra={"example": "9876543210"})
    aadhaar_last4: Optional[str] = Field("1234", json_schema_extra={"example": "1234"})

class ABHAResponse(BaseModel):
    abha_number: str
    abha_address: str
    name: str
    status: str
    qr_code_token: str
    created_at: str

class ConsentArtifactCreate(BaseModel):
    patient_abha: str = Field(..., json_schema_extra={"example": "91-1234-5678-9012@sbx"})
    purpose: str = Field("CLINICAL_DIAGNOSIS", json_schema_extra={"example": "CLINICAL_DIAGNOSIS"})
    hi_types: List[str] = Field(["DiagnosticReport", "Prescription", "OPConsultation"])
    valid_until: str = Field("2026-12-31T23:59:59Z")

class ConsentArtifactResponse(BaseModel):
    consent_id: str
    patient_abha: str
    status: str
    purpose: str
    hi_types: List[str] = []
    granted_at: str
    valid_until: str
