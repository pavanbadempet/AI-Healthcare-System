"""Appointment ORM model."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to specific doctor
    specialist = Column(String)  # Keep for fallback name display
    date_time = Column(DateTime)
    reason = Column(Text)
    status = Column(String, default="Scheduled")  # Scheduled, Completed, Cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="appointments", foreign_keys=[user_id])
    doctor = relationship("User", foreign_keys=[doctor_id])  # One-way relationship to doctor info
    facility = relationship("HospitalFacility")
