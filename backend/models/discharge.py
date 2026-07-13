"""Discharge domain models: discharge summaries."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class DischargeSummary(Base):
    __tablename__ = "discharge_summaries"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    diagnosis_summary = Column(Text)
    hospital_course = Column(Text)
    medications = Column(Text, nullable=True)
    follow_up_plan = Column(Text, nullable=True)
    discharge_instructions = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft, finalized, amended
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finalized_at = Column(DateTime, nullable=True)

    facility = relationship("HospitalFacility")
    admission = relationship("Admission")
    encounter = relationship("Encounter")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
