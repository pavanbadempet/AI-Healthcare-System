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
    role = Column(String, default="patient") # patient, doctor, nurse, pharmacist, billing, admin
    
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
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    
    # Subscription / Monetization
    plan_tier = Column(String, default="free") # free, pro, clinic
    subscription_expiry = Column(DateTime, nullable=True)
    razorpay_customer_id = Column(String, nullable=True)
    
    # Doctor Specific
    consultation_fee = Column(Float, default=500.0)
    specialization = Column(String, nullable=True)
    
    # AI Memory
    psych_profile = Column(Text, nullable=True) # Long term memory summary

    facility = relationship("HospitalFacility")
    health_records = relationship("HealthRecord", back_populates="owner")
    chat_logs = relationship("ChatLog", back_populates="owner")
    appointments = relationship("Appointment", back_populates="owner", foreign_keys="[Appointment.user_id]")


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
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    target_user_id = Column(Integer) # Keep generic or link, but generic is safer if user deleted
    action = Column(String) # VIEW_FULL, DELETE, BAN
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    details = Column(String, nullable=True)

    facility = relationship("HospitalFacility")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Link to specific doctor
    specialist = Column(String) # Keep for fallback name display
    date_time = Column(DateTime)
    reason = Column(Text)
    status = Column(String, default="Scheduled") # Scheduled, Completed, Cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="appointments", foreign_keys=[user_id])
    doctor = relationship("User", foreign_keys=[doctor_id]) # One-way relationship to doctor info
    facility = relationship("HospitalFacility")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    name = Column(String, unique=True, index=True)
    department_type = Column(String) # OPD, IPD, Emergency, Diagnostics, Pharmacy
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")


class HospitalFacility(Base):
    __tablename__ = "hospital_facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    facility_type = Column(String, default="hospital")
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Bed(Base):
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    bed_number = Column(String, index=True)
    ward = Column(String, nullable=True)
    status = Column(String, default="available") # available, occupied, maintenance
    current_patient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
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
    encounter_type = Column(String) # OPD, IPD, Emergency
    reason = Column(Text, nullable=True)
    priority = Column(String, default="routine")
    status = Column(String, default="open")
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


class ClinicalOrder(Base):
    __tablename__ = "clinical_orders"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    order_type = Column(String) # lab, radiology, pharmacy, procedure, nursing
    title = Column(String)
    priority = Column(String, default="routine")
    status = Column(String, default="ordered")
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


class VitalObservation(Base):
    __tablename__ = "vital_observations"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    source = Column(String, default="manual") # manual, device, patient_reported
    heart_rate = Column(Float, nullable=True)
    systolic_bp = Column(Float, nullable=True)
    diastolic_bp = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    respiratory_rate = Column(Float, nullable=True)
    observed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])
    encounter = relationship("Encounter")
    department = relationship("Department")


class MonitoringSignal(Base):
    __tablename__ = "monitoring_signals"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    vital_observation_id = Column(Integer, ForeignKey("vital_observations.id"), nullable=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    signal_type = Column(String)
    severity = Column(String, default="info")
    title = Column(String)
    summary = Column(Text)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    vital_observation = relationship("VitalObservation")
    encounter = relationship("Encounter")
    department = relationship("Department")


class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("clinical_orders.id"), index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    result_type = Column(String) # lab, radiology, diagnostic
    title = Column(String)
    summary = Column(Text)
    abnormal_flag = Column(Integer, default=0)
    status = Column(String, default="final")
    review_status = Column(String, default="pending_review")
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


class Prescription(Base):
    __tablename__ = "prescriptions"

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
    status = Column(String, default="pending")

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
    status = Column(String, default="dispensed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    prescription = relationship("Prescription", back_populates="dispense_records")
    prescription_item = relationship("PrescriptionItem", back_populates="dispense_records")
    inventory = relationship("MedicationInventory")
    patient = relationship("User", foreign_keys=[patient_id])
    dispensed_by = relationship("User", foreign_keys=[dispensed_by_id])


class BillableService(Base):
    __tablename__ = "billable_services"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    service_code = Column(String, unique=True, index=True)
    name = Column(String)
    service_type = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    unit_price = Column(Float, default=0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    department = relationship("Department")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="issued")
    subtotal = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    balance_amount = Column(Float, default=0)
    currency = Column(String, default="INR")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    created_by = relationship("User", foreign_keys=[created_by_id])
    items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("BillingPayment", back_populates="invoice")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), index=True)
    service_id = Column(Integer, ForeignKey("billable_services.id"), nullable=True)
    description = Column(String)
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0)
    line_total = Column(Float, default=0)

    invoice = relationship("Invoice", back_populates="items")
    service = relationship("BillableService")


class BillingPayment(Base):
    __tablename__ = "billing_payments"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    collected_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    amount = Column(Float, default=0)
    payment_method = Column(String)
    reference_id = Column(String, nullable=True)
    status = Column(String, default="collected")
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    invoice = relationship("Invoice", back_populates="payments")
    patient = relationship("User", foreign_keys=[patient_id])
    collected_by = relationship("User", foreign_keys=[collected_by_id])


class DischargeSummary(Base):
    __tablename__ = "discharge_summaries"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    diagnosis_summary = Column(Text)
    hospital_course = Column(Text)
    medications = Column(Text, nullable=True)
    follow_up_plan = Column(Text, nullable=True)
    discharge_instructions = Column(Text, nullable=True)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finalized_at = Column(DateTime, nullable=True)

    facility = relationship("HospitalFacility")
    admission = relationship("Admission")
    encounter = relationship("Encounter")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])


class NursingTask(Base):
    __tablename__ = "nursing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    assigned_nurse_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    task_type = Column(String)
    title = Column(String)
    instructions = Column(Text, nullable=True)
    priority = Column(String, default="routine")
    status = Column(String, default="assigned")
    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completion_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    assigned_nurse = relationship("User", foreign_keys=[assigned_nurse_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    encounter = relationship("Encounter")
    admission = relationship("Admission")
    department = relationship("Department")


class InteroperabilityConsent(Base):
    __tablename__ = "interoperability_consents"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    scope = Column(String, default="fhir_bundle_export")
    purpose = Column(Text)
    recipient_type = Column(String, default="care_team")
    status = Column(String, default="active")
    abdm_request_id = Column(String, nullable=True, index=True)
    abdm_consent_id = Column(String, nullable=True, index=True)
    abdm_status = Column(String, nullable=True)
    abdm_last_event_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])


class ABDMConsentEvent(Base):
    __tablename__ = "abdm_consent_events"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    local_consent_id = Column(Integer, ForeignKey("interoperability_consents.id"), nullable=True, index=True)
    abdm_request_id = Column(String, index=True)
    abdm_consent_id = Column(String, nullable=True, index=True)
    event_type = Column(String, default="consent_status")
    status = Column(String)
    local_consent_status = Column(String, nullable=True)
    hi_types = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)
    notification_at = Column(DateTime, nullable=True)
    payload_sha256 = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    local_consent = relationship("InteroperabilityConsent")


class InteroperabilityExportProfile(Base):
    __tablename__ = "interoperability_export_profiles"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    name = Column(String, index=True)
    partner_system = Column(String, nullable=True)
    resource_types = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    department = relationship("Department")
    created_by = relationship("User", foreign_keys=[created_by_id])


class InteroperabilityExport(Base):
    __tablename__ = "interoperability_exports"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    consent_id = Column(Integer, ForeignKey("interoperability_consents.id"), nullable=True)
    profile_id = Column(Integer, ForeignKey("interoperability_export_profiles.id"), nullable=True)
    export_type = Column(String, default="fhir_bundle")
    resource_count = Column(Integer, default=0)
    filter_summary = Column(Text, nullable=True)
    bundle_sha256 = Column(String, nullable=True)
    manifest_signature = Column(String, nullable=True)
    signature_algorithm = Column(String, default="HMAC-SHA256")
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("HospitalFacility")
    patient = relationship("User", foreign_keys=[patient_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    consent = relationship("InteroperabilityConsent")
    profile = relationship("InteroperabilityExportProfile")
