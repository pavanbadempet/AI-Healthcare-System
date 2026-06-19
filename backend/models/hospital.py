"""Hospital facility, department, bed, encounter, and admission ORM models."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class HospitalFacility(Base):
    __tablename__ = "hospital_facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    facility_type = Column(String, default="hospital")
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    name = Column(String, unique=True, index=True)
    department_type = Column(String)  # OPD, IPD, Emergency, Diagnostics, Pharmacy
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")


class Bed(Base):
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    bed_number = Column(String, index=True)
    ward = Column(String, nullable=True)
    status = Column(String, default="available")  # available, occupied, maintenance
    current_patient_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    department = relationship("Department")
    current_patient = relationship("User", foreign_keys=[current_patient_id])


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    encounter_type = Column(String)  # OPD, IPD, Emergency
    reason = Column(Text, nullable=True)
    priority = Column(String, default="routine")  # routine, urgent, emergency
    status = Column(String, default="open")  # open, closed, cancelled
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    department = relationship("Department")


class Admission(Base):
    __tablename__ = "admissions"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    bed_id = Column(Integer, ForeignKey("beds.id"), nullable=True)
    admitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    discharged_at = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String, default="active")

    facility = relationship("HospitalFacility")
    encounter = relationship("Encounter")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    department = relationship("Department")
    bed = relationship("Bed")
