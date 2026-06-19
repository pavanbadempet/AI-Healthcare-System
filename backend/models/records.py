"""Health records, chat logs, and audit log ORM models."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    record_type = Column(String)  # 'diabetes', 'heart', 'liver'
    data = Column(Text)  # JSON string of input data
    prediction = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="health_records")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="chat_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), index=True)
    target_user_id = Column(Integer)  # Keep generic or link, but generic is safer if user deleted
    action = Column(String)  # VIEW_FULL, DELETE, BAN
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    details = Column(String, nullable=True)

    facility = relationship("HospitalFacility")
