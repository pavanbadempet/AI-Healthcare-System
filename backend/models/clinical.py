"""Clinical order, care event, vital observation, monitoring signal, and diagnostic result ORM models."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from ..database import Base, SoftDeleteMixin


class ClinicalOrder(Base):
    __tablename__ = "clinical_orders"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    order_type = Column(String)  # lab, radiology, pharmacy, procedure, nursing
    title = Column(String)
    priority = Column(String, default="routine")  # routine, urgent, stat
    status = Column(String, default="ordered")  # ordered, in_progress, completed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    facility = relationship("HospitalFacility")
    encounter = relationship("Encounter")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    department = relationship("Department")


class CareEvent(Base):
    __tablename__ = "care_events"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    event_type = Column(String)
    title = Column(String)
    summary = Column(Text, nullable=True)
    severity = Column(String, default="info")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    actor = relationship("User", foreign_keys=[actor_user_id])
    encounter = relationship("Encounter")
    department = relationship("Department")


class VitalObservation(Base, SoftDeleteMixin):
    __tablename__ = "vital_observations"

    __table_args__ = (
        UniqueConstraint("patient_id", "observed_at", name="uq_vital_obs_patient_observed"),
        Index("idx_vital_obs_patient_observed", "patient_id", "observed_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    source = Column(String, default="manual")  # manual, device, patient_reported
    heart_rate = Column(Float, nullable=True)
    systolic_bp = Column(Float, nullable=True)
    diastolic_bp = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    respiratory_rate = Column(Float, nullable=True)
    blood_glucose = Column(Float, nullable=True)
    observed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])
    encounter = relationship("Encounter")
    department = relationship("Department")


class MonitoringSignal(Base):
    __tablename__ = "monitoring_signals"

    __table_args__ = (
        UniqueConstraint(
            "vital_observation_id",
            "signal_type",
            name="uq_monitoring_signal_vital_type",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    vital_observation_id = Column(Integer, ForeignKey("vital_observations.id"), nullable=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    signal_type = Column(String)
    severity = Column(String, default="info")  # info, warning, critical
    title = Column(String)
    summary = Column(Text)
    status = Column(String, default="open", index=True)  # open, acknowledged, resolved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    vital_observation = relationship("VitalObservation")
    encounter = relationship("Encounter")
    department = relationship("Department")


class DiagnosticResult(Base, SoftDeleteMixin):
    __tablename__ = "diagnostic_results"

    __table_args__ = (
        Index("idx_diagnostic_res_patient_created", "patient_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("clinical_orders.id"), index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    result_type = Column(String)  # lab, radiology, diagnostic
    title = Column(String)
    summary = Column(Text)
    abnormal_flag = Column(Integer, default=0)  # 0=normal, 1=abnormal
    status = Column(String, default="final")  # preliminary, final, corrected
    review_status = Column(String, default="pending_review")  # pending_review, reviewed, needs_follow_up, withheld
    review_note = Column(Text, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    order = relationship("ClinicalOrder")
    encounter = relationship("Encounter")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    department = relationship("Department")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])


class SparkStreamingMetrics(Base):
    __tablename__ = "spark_streaming_metrics"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, nullable=False)
    records_processed = Column(Integer, nullable=False)
    processing_time_ms = Column(Float, nullable=False)
    ml_latency_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

