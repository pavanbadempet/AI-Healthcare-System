"""Clinical Intelligence domain models: alerts and AI-driven patient insights."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class ClinicalAlert(Base):
    """Severity-tagged clinical alert tied to a patient."""

    __tablename__ = "clinical_alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    alert_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False)  # CRITICAL | WARNING | INFO
    message = Column(Text, nullable=False)
    source_event_id = Column(String, nullable=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("User", foreign_keys=[patient_id])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])


class PatientInsight(Base):
    """AI-generated patient insight (risk summary or trend analysis)."""

    __tablename__ = "patient_insights"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    insight_type = Column(String, nullable=False)  # risk_summary | trend_analysis
    content = Column(Text, nullable=False)  # JSON
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("User", foreign_keys=[patient_id])
