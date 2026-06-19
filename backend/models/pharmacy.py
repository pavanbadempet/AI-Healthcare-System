"""Pharmacy domain models: medication inventory, prescriptions, and dispensing."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base, SoftDeleteMixin


class MedicationInventory(Base):
    __tablename__ = "medication_inventory"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    medication_name = Column(String, index=True)
    strength = Column(String, nullable=True)
    form = Column(String, nullable=True)
    batch_number = Column(String, nullable=True, index=True)
    quantity_on_hand = Column(Float, default=0)
    reorder_level = Column(Float, default=0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")


class Prescription(Base, SoftDeleteMixin):
    __tablename__ = "prescriptions"

    __table_args__ = (
        Index("idx_prescriptions_patient_created", "patient_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    diagnosis_context = Column(Text, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    dispensed_at = Column(DateTime, nullable=True)

    facility = relationship("HospitalFacility")
    encounter = relationship("Encounter")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")
    dispense_records = relationship("DispenseRecord", back_populates="prescription")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), index=True)
    inventory_id = Column(Integer, ForeignKey("medication_inventory.id"), nullable=True)
    medication_name = Column(String)
    dosage = Column(String)
    frequency = Column(String)
    duration = Column(String)
    quantity_prescribed = Column(Float, default=1)
    quantity_dispensed = Column(Float, default=0)
    instructions = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, dispensed, partially_dispensed, cancelled

    prescription = relationship("Prescription", back_populates="items")
    inventory = relationship("MedicationInventory")
    dispense_records = relationship("DispenseRecord", back_populates="prescription_item")


class DispenseRecord(Base):
    __tablename__ = "dispense_records"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), index=True)
    prescription_item_id = Column(Integer, ForeignKey("prescription_items.id"), nullable=True, index=True)
    inventory_id = Column(Integer, ForeignKey("medication_inventory.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    dispensed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    quantity_dispensed = Column(Float, default=0)
    status = Column(String, default="dispensed")  # dispensed, returned, partial
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    prescription = relationship("Prescription", back_populates="dispense_records")
    prescription_item = relationship("PrescriptionItem", back_populates="dispense_records")
    inventory = relationship("MedicationInventory")
    patient = relationship("User", foreign_keys=[patient_id])
    dispensed_by = relationship("User", foreign_keys=[dispensed_by_id])
