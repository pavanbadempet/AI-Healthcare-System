"""Appointment ORM model."""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base, SoftDeleteMixin


class Appointment(Base, SoftDeleteMixin):
    __tablename__ = "appointments"

    __table_args__ = (
        Index("idx_appointments_user_datetime", "user_id", "date_time"),
        CheckConstraint(
            "status IN ('Scheduled', 'Rescheduled', 'Completed', 'Cancelled')",
            name="check_appt_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Link to specific doctor
    specialist = Column(String)  # Keep for fallback name display
    date_time = Column(DateTime)
    reason = Column(Text)
    status = Column(String, default="Scheduled", index=True)  # Scheduled, Rescheduled, Completed, Cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="appointments", foreign_keys=[user_id])
    doctor = relationship("User", foreign_keys=[doctor_id])  # One-way relationship to doctor info
    facility = relationship("HospitalFacility")
