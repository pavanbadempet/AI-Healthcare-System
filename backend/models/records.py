"""Health records, chat logs, and audit log ORM models."""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from ..database import Base, SoftDeleteMixin, get_encryption_key


class HealthRecord(Base, SoftDeleteMixin):
    __tablename__ = "health_records"

    __table_args__ = (
        Index("idx_health_records_user_timestamp", "user_id", "timestamp"),
        CheckConstraint("record_type IN ('diabetes', 'heart', 'liver', 'kidney', 'lungs')", name="check_health_record_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    record_type = Column(String)  # 'diabetes', 'heart', 'liver'
    data = Column(StringEncryptedType(Text, get_encryption_key, AesEngine, 'pkcs5'))  # JSON string of input data (Encrypted)
    prediction = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="health_records")


class ChatLog(Base, SoftDeleteMixin):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="chat_logs")


class AuditLog(Base, SoftDeleteMixin):
    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("idx_audit_logs_admin_timestamp", "admin_id", "timestamp"),
        Index("idx_audit_logs_target_timestamp", "target_user_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), index=True)
    target_user_id = Column(Integer)  # Keep generic or link, but generic is safer if user deleted
    action = Column(String)  # VIEW_FULL, DELETE, BAN
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    details = Column(String, nullable=True)

    facility = relationship("HospitalFacility")
    admin = relationship("User", foreign_keys=[admin_id], backref="audit_logs_created")
