"""Federated Learning domain models: clinician feedback and sync audit."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class ModelFeedback(Base):
    """Clinician correction on a model prediction for federated retraining."""

    __tablename__ = "model_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    model_name = Column(String, nullable=False, index=True)
    input_features = Column(Text, nullable=False)  # JSON
    prediction_result = Column(Text, nullable=False)  # JSON
    corrected_label = Column(String, nullable=False)
    clinician_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, default="pending_sync")  # pending_sync | synced
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("User", foreign_keys=[patient_id])
    clinician = relationship("User", foreign_keys=[clinician_id])


class FederatedSyncAudit(Base):
    """Audit trail for a differential-privacy federated sync run."""

    __tablename__ = "federated_sync_audits"

    id = Column(Integer, primary_key=True, index=True)
    sync_run_id = Column(String, unique=True, nullable=False, index=True)
    node_id = Column(String, nullable=False)
    model_name = Column(String, nullable=False, index=True)
    records_synced = Column(Integer, nullable=False, default=0)
    epsilon_consumed = Column(Float, nullable=False, default=0.0)
    delta_consumed = Column(Float, nullable=False, default=0.0)
    status = Column(String, nullable=False)  # completed | failed | rejected
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
