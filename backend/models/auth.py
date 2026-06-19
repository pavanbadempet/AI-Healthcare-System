"""Authentication and user-related ORM models."""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base, SoftDeleteMixin


class User(Base, SoftDeleteMixin):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("role IN ('patient', 'doctor', 'nurse', 'pharmacist', 'billing', 'admin')", name="check_user_role"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    role = Column(String, default="patient")  # patient, doctor, nurse, pharmacist, billing, admin

    # Profile Data
    email = Column(String, nullable=True, unique=True, index=True)
    full_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    blood_type = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    existing_ailments = Column(Text, nullable=True)
    profile_picture = Column(Text, nullable=True)  # Base64 string
    about_me = Column(Text, nullable=True)  # Custom About Info

    # Lifestyle Data (The 4 Pillars)
    diet = Column(String, nullable=True)  # Vegan, Keto, etc.
    activity_level = Column(String, nullable=True)  # Sedentary, Active, etc.
    sleep_hours = Column(Float, nullable=True)
    stress_level = Column(String, nullable=True)  # Low, Medium, High

    # Privacy
    allow_data_collection = Column(Integer, default=1)  # 0=False, 1=True
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)

    # Subscription / Monetization
    plan_tier = Column(String, default="free")  # free, pro, clinic
    subscription_expiry = Column(DateTime, nullable=True)
    razorpay_customer_id = Column(String, nullable=True, index=True)

    # Doctor Specific
    consultation_fee = Column(Float, default=500.0)
    specialization = Column(String, nullable=True)

    # AI Memory
    psych_profile = Column(Text, nullable=True)  # Long term memory summary

    facility = relationship("HospitalFacility")
    health_records = relationship("HealthRecord", back_populates="owner")
    chat_logs = relationship("ChatLog", back_populates="owner")
    appointments = relationship("Appointment", back_populates="owner", foreign_keys="[Appointment.user_id]")
