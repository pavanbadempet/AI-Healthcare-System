"""Interoperability domain schemas: consent management, ABDM integration, data exports."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InteroperabilityConsentCreate(BaseModel):
    scope: str = "fhir_bundle_export"
    purpose: str
    recipient_type: str = "care_team"
    expires_at: Optional[datetime] = None


class InteroperabilityConsentResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    granted_by_id: Optional[int] = None
    revoked_by_id: Optional[int] = None
    scope: str
    purpose: str
    recipient_type: str
    status: str
    abdm_request_id: Optional[str] = None
    abdm_consent_id: Optional[str] = None
    abdm_status: Optional[str] = None
    abdm_last_event_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    standards_note: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class InteroperabilityExportProfileCreate(BaseModel):
    name: str
    partner_system: Optional[str] = None
    resource_types: Optional[List[str]] = None
    department_id: Optional[int] = None
    status: Optional[str] = "active"


class InteroperabilityExportProfileResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    name: str
    partner_system: Optional[str] = None
    resource_types: Optional[List[str]] = None
    department_id: Optional[int] = None
    created_by_id: Optional[int] = None
    status: str
    created_at: datetime
    standards_note: Optional[str] = None


class InteroperabilityExportResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    requested_by_id: Optional[int] = None
    consent_id: Optional[int] = None
    profile_id: Optional[int] = None
    export_type: str
    resource_count: int
    filter_summary: Optional[str] = None
    bundle_sha256: Optional[str] = None
    manifest_signature: Optional[str] = None
    signature_algorithm: Optional[str] = "HMAC-SHA256"
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ABDMConsentRequestCreate(BaseModel):
    patient_id: int
    patient_abha_address: str = Field(..., min_length=3, max_length=255)
    purpose_code: str = "CAREMGT"
    hi_types: Optional[List[str]] = None
    date_from: datetime
    date_to: datetime
    data_erase_at: datetime
    hip_id: Optional[str] = None
    care_context_reference: Optional[str] = None
    submit: bool = False


class ABDMConsentCallbackCreate(BaseModel):
    patient_id: Optional[int] = None
    local_consent_id: Optional[int] = None
    abdm_request_id: str = Field(..., min_length=1, max_length=128)
    abdm_consent_id: Optional[str] = Field(default=None, max_length=128)
    status: str = Field(..., min_length=1, max_length=32)
    hi_types: Optional[List[str]] = None
    event_type: Optional[str] = Field(default="consent_status", max_length=128)
    notification_at: Optional[datetime] = None
    error_code: Optional[str] = Field(default=None, max_length=128)

    model_config = ConfigDict(extra="forbid")


class ABDMConsentCallbackResponse(BaseModel):
    source: str
    event_id: int
    facility_id: Optional[int] = None
    patient_id: Optional[int] = None
    local_consent_id: Optional[int] = None
    abdm_request_id: str
    abdm_consent_id: Optional[str] = None
    event_type: str
    status: str
    local_consent_status: str
    hi_types: List[str]
    error_code: Optional[str] = None
    notification_at: Optional[str] = None
    payload_sha256: str
    raw_payload_stored: bool
