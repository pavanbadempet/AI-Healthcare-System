"""Interoperability domain models: consent management, ABDM integration, and data exports."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class InteroperabilityConsent(Base):
    __tablename__ = "interoperability_consents"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    scope = Column(String, default="fhir_bundle_export")
    purpose = Column(Text)
    recipient_type = Column(String, default="care_team")
    status = Column(String, default="active")
    abdm_request_id = Column(String, nullable=True, index=True)
    abdm_consent_id = Column(String, nullable=True, index=True)
    abdm_status = Column(String, nullable=True)
    abdm_last_event_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])


class ABDMConsentEvent(Base):
    __tablename__ = "abdm_consent_events"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    local_consent_id = Column(Integer, ForeignKey("interoperability_consents.id"), nullable=True, index=True)
    abdm_request_id = Column(String, index=True)
    abdm_consent_id = Column(String, nullable=True, index=True)
    event_type = Column(String, default="consent_status")
    status = Column(String)
    local_consent_status = Column(String, nullable=True)
    hi_types = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)
    notification_at = Column(DateTime, nullable=True)
    payload_sha256 = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    local_consent = relationship("InteroperabilityConsent")


class InteroperabilityExportProfile(Base):
    __tablename__ = "interoperability_export_profiles"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    name = Column(String, index=True)
    partner_system = Column(String, nullable=True)
    resource_types = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    department = relationship("Department")
    created_by = relationship("User", foreign_keys=[created_by_id])


class InteroperabilityExport(Base):
    __tablename__ = "interoperability_exports"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    consent_id = Column(Integer, ForeignKey("interoperability_consents.id"), nullable=True)
    profile_id = Column(Integer, ForeignKey("interoperability_export_profiles.id"), nullable=True)
    export_type = Column(String, default="fhir_bundle")
    resource_count = Column(Integer, default=0)
    filter_summary = Column(Text, nullable=True)
    bundle_sha256 = Column(String, nullable=True)
    manifest_signature = Column(String, nullable=True)
    signature_algorithm = Column(String, default="HMAC-SHA256")
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    consent = relationship("InteroperabilityConsent")
    profile = relationship("InteroperabilityExportProfile")
