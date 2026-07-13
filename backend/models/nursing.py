"""Nursing domain models: nursing tasks."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class NursingTask(Base):
    __tablename__ = "nursing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    assigned_nurse_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    task_type = Column(String)
    title = Column(String)
    instructions = Column(Text, nullable=True)
    priority = Column(String, default="routine")
    status = Column(String, default="assigned")
    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completion_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    assigned_nurse = relationship("User", foreign_keys=[assigned_nurse_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    department = relationship("Department")
