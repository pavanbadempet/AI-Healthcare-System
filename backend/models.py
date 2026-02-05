from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    role = Column(String, default="patient") # patient, doctor, admin
    
    # Profile Data
    email = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    blood_type = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    existing_ailments = Column(Text, nullable=True)
    profile_picture = Column(Text, nullable=True) # Base64 string
    about_me = Column(Text, nullable=True) # Custom About Info
    
    # Lifestyle Data (The 4 Pillars)
    diet = Column(String, nullable=True) # Vegan, Keto, etc.
    activity_level = Column(String, nullable=True) # Sedentary, Active, etc.
    sleep_hours = Column(Float, nullable=True)
    stress_level = Column(String, nullable=True) # Low, Medium, High
    
    # Privacy
    allow_data_collection = Column(Integer, default=1) # 0=False, 1=True
    
    # Subscription / Monetization
    plan_tier = Column(String, default="free") # free, pro, clinic
    subscription_expiry = Column(DateTime, nullable=True)
    razorpay_customer_id = Column(String, nullable=True)
    
    # Doctor Specific
    consultation_fee = Column(Float, default=500.0)
    
    # AI Memory
    psych_profile = Column(Text, nullable=True) # Long term memory summary

    health_records = relationship("HealthRecord", back_populates="owner")
    chat_logs = relationship("ChatLog", back_populates="owner")
    appointments = relationship("Appointment", back_populates="owner")


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    record_type = Column(String) # 'diabetes', 'heart', 'liver'
    data = Column(Text) # JSON string of input data
    prediction = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="health_records")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String) # 'user' or 'assistant'
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="chat_logs")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    target_user_id = Column(Integer) # Keep generic or link, but generic is safer if user deleted
    action = Column(String) # VIEW_FULL, DELETE, BAN
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    details = Column(String, nullable=True)

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Link to specific doctor
    specialist = Column(String) # Keep for fallback name display
    date_time = Column(DateTime)
    reason = Column(Text)
    status = Column(String, default="Scheduled") # Scheduled, Completed, Cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="appointments")
