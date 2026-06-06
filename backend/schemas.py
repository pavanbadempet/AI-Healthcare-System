from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Authentication & User Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    """Schema for User Registration"""
    username: str
    password: str = Field(..., description="Must meet complexity requirements")
    email: str
    full_name: str
    dob: str = Field(..., description="YYYY-MM-DD format")

class UserResponse(BaseModel):
    """Schema for Public User Profile"""
    id: int
    username: str
    role: Optional[str] = "patient"
    full_name: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserProfileUpdate(BaseModel):
    """Schema for Updating User Details"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_type: Optional[str] = None
    existing_ailments: Optional[str] = None
    profile_picture: Optional[str] = None
    about_me: Optional[str] = None
    diet: Optional[str] = None
    activity_level: Optional[str] = None
    sleep_hours: Optional[float] = None
    stress_level: Optional[str] = None
    specialization: Optional[str] = None
    allow_data_collection: Optional[bool] = None

class HealthRecordResponse(BaseModel):
    id: int
    record_type: str
    prediction: str
    timestamp: datetime
    data: str
    model_config = ConfigDict(from_attributes=True)

class ChatLogResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    actor_user_id: Optional[int] = None
    target_user_id: Optional[int] = None
    action: str
    timestamp: datetime | str
    details: str


class UserFullResponse(UserResponse):
    """Admin View: Includes sensitive health records and chat logs"""
    health_records: List[HealthRecordResponse] = []
    chat_logs: List[ChatLogResponse] = []




class AppointmentCreate(BaseModel):
    doctor_id: Optional[int] = None # Link to real doctor
    specialist: str # Fallback name
    date: str
    time: str
    reason: str

class AppointmentResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    user_id: int # Vital for Admin/Doctor visibility
    doctor_id: Optional[int] = None
    specialist: str
    date_time: datetime
    reason: str
    status: str
    model_config = ConfigDict(from_attributes=True)

class DoctorResponse(BaseModel):
    id: int
    full_name: str
    specialization: str = "General Physician" # Default for now if not in DB
    consultation_fee: float
    profile_picture: Optional[str] = None

# --- Hospital Operations Schemas ---

class FacilityCreate(BaseModel):
    name: str
    facility_type: str = "hospital"
    country: Optional[str] = None
    region: Optional[str] = None


class FacilityResponse(FacilityCreate):
    id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    facility_id: Optional[int] = None
    name: str
    department_type: str
    location: Optional[str] = None
    description: Optional[str] = None


class DepartmentResponse(DepartmentCreate):
    id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BedCreate(BaseModel):
    department_id: int
    bed_number: str
    ward: Optional[str] = None
    status: Optional[str] = "available"


class BedResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    department_id: int
    bed_number: str
    ward: Optional[str] = None
    status: str
    current_patient_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EncounterCreate(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    encounter_type: str
    reason: Optional[str] = None
    priority: Optional[str] = "routine"


class EncounterResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    encounter_type: str
    reason: Optional[str] = None
    priority: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AdmissionCreate(BaseModel):
    encounter_id: int
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    bed_id: Optional[int] = None
    admitted_at: Optional[datetime] = None
    reason: Optional[str] = None


class AdmissionResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    encounter_id: int
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    bed_id: Optional[int] = None
    admitted_at: datetime
    discharged_at: Optional[datetime] = None
    reason: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class ClinicalOrderCreate(BaseModel):
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    order_type: str
    title: str
    priority: Optional[str] = "routine"
    notes: Optional[str] = None


class ClinicalOrderResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    order_type: str
    title: str
    priority: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class CareEventResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    actor_user_id: Optional[int] = None
    encounter_id: Optional[int] = None
    department_id: Optional[int] = None
    event_type: str
    title: str
    summary: Optional[str] = None
    severity: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PatientTimelineResponse(BaseModel):
    encounters: List[EncounterResponse]
    admissions: List[AdmissionResponse]
    orders: List[ClinicalOrderResponse]
    events: List[CareEventResponse]


class VitalObservationCreate(BaseModel):
    patient_id: int
    encounter_id: Optional[int] = None
    department_id: Optional[int] = None
    source: Optional[str] = "manual"
    heart_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    spo2: Optional[float] = None
    temperature_c: Optional[float] = None
    respiratory_rate: Optional[float] = None
    observed_at: Optional[datetime] = None


class VitalObservationResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    recorded_by_id: Optional[int] = None
    encounter_id: Optional[int] = None
    department_id: Optional[int] = None
    source: str
    heart_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    spo2: Optional[float] = None
    temperature_c: Optional[float] = None
    respiratory_rate: Optional[float] = None
    observed_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MonitoringSignalResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    vital_observation_id: Optional[int] = None
    encounter_id: Optional[int] = None
    department_id: Optional[int] = None
    signal_type: str
    severity: str
    title: str
    summary: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VitalSubmissionResponse(BaseModel):
    vital: VitalObservationResponse
    signals: List[MonitoringSignalResponse]


class DiagnosticResultCreate(BaseModel):
    order_id: int
    result_type: str
    title: str
    summary: str
    abnormal_flag: Optional[bool] = False
    status: Optional[str] = "final"


class DiagnosticReviewUpdate(BaseModel):
    review_status: Optional[str] = "reviewed"
    review_note: Optional[str] = None


class DiagnosticResultResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    order_id: int
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    result_type: str
    title: str
    summary: str
    abnormal_flag: bool
    status: str
    review_status: str
    review_note: Optional[str] = None
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MedicationInventoryCreate(BaseModel):
    medication_name: str
    strength: Optional[str] = None
    form: Optional[str] = None
    batch_number: Optional[str] = None
    quantity_on_hand: float = 0
    reorder_level: float = 0


class MedicationInventoryResponse(MedicationInventoryCreate):
    id: int
    facility_id: Optional[int] = None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PrescriptionItemCreate(BaseModel):
    inventory_id: Optional[int] = None
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    quantity_prescribed: float = 1
    instructions: Optional[str] = None


class PrescriptionItemResponse(BaseModel):
    id: int
    prescription_id: int
    inventory_id: Optional[int] = None
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    quantity_prescribed: float
    quantity_dispensed: float
    instructions: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class PrescriptionCreate(BaseModel):
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis_context: Optional[str] = None
    items: List[PrescriptionItemCreate]


class PrescriptionResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis_context: Optional[str] = None
    status: str
    created_at: datetime
    dispensed_at: Optional[datetime] = None
    items: List[PrescriptionItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class DispenseItemCreate(BaseModel):
    prescription_item_id: int
    quantity_dispensed: float


class DispensePrescriptionCreate(BaseModel):
    items: List[DispenseItemCreate]


class DispenseRecordResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    prescription_id: int
    prescription_item_id: Optional[int] = None
    inventory_id: Optional[int] = None
    patient_id: int
    dispensed_by_id: Optional[int] = None
    quantity_dispensed: float
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BillableServiceCreate(BaseModel):
    service_code: str
    name: str
    service_type: str
    department_id: Optional[int] = None
    unit_price: float


class BillableServiceResponse(BillableServiceCreate):
    id: int
    facility_id: Optional[int] = None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InvoiceLineItemCreate(BaseModel):
    service_id: Optional[int] = None
    description: Optional[str] = None
    quantity: float = 1
    unit_price: Optional[float] = None


class InvoiceLineItemResponse(BaseModel):
    id: int
    invoice_id: int
    service_id: Optional[int] = None
    description: str
    quantity: float
    unit_price: float
    line_total: float
    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    patient_id: int
    encounter_id: Optional[int] = None
    admission_id: Optional[int] = None
    discount_amount: float = 0
    tax_amount: float = 0
    currency: Optional[str] = "INR"
    items: List[InvoiceLineItemCreate]


class InvoiceResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    encounter_id: Optional[int] = None
    admission_id: Optional[int] = None
    created_by_id: Optional[int] = None
    status: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    balance_amount: float
    currency: str
    created_at: datetime
    issued_at: datetime
    items: List[InvoiceLineItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class BillingPaymentCreate(BaseModel):
    amount: float
    payment_method: str
    reference_id: Optional[str] = None


class BillingPaymentResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    invoice_id: int
    patient_id: int
    collected_by_id: Optional[int] = None
    amount: float
    payment_method: str
    reference_id: Optional[str] = None
    status: str
    collected_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DischargeSummaryCreate(BaseModel):
    admission_id: int
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis_summary: str
    hospital_course: str
    medications: Optional[str] = None
    follow_up_plan: Optional[str] = None
    discharge_instructions: Optional[str] = None


class DischargeSummaryResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    admission_id: int
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis_summary: str
    hospital_course: str
    medications: Optional[str] = None
    follow_up_plan: Optional[str] = None
    discharge_instructions: Optional[str] = None
    status: str
    created_at: datetime
    finalized_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class NursingTaskCreate(BaseModel):
    patient_id: int
    assigned_nurse_id: Optional[int] = None
    encounter_id: Optional[int] = None
    admission_id: Optional[int] = None
    department_id: Optional[int] = None
    task_type: str
    title: str
    instructions: Optional[str] = None
    priority: Optional[str] = "routine"
    due_at: Optional[datetime] = None


class NursingTaskComplete(BaseModel):
    completion_note: Optional[str] = None


class NursingTaskResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    assigned_nurse_id: Optional[int] = None
    created_by_id: Optional[int] = None
    completed_by_id: Optional[int] = None
    encounter_id: Optional[int] = None
    admission_id: Optional[int] = None
    department_id: Optional[int] = None
    task_type: str
    title: str
    instructions: Optional[str] = None
    priority: str
    status: str
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_note: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InteroperabilityConsentCreate(BaseModel):
    scope: str = "fhir_bundle_export"
    purpose: str
    recipient_type: str = "care_team"
    expires_at: Optional[datetime] = None


class InteroperabilityConsentResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    granted_by_id: Optional[int] = None
    revoked_by_id: Optional[int] = None
    scope: str
    purpose: str
    recipient_type: str
    status: str
    abdm_request_id: Optional[str] = None
    abdm_consent_id: Optional[str] = None
    abdm_status: Optional[str] = None
    abdm_last_event_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    standards_note: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class InteroperabilityExportProfileCreate(BaseModel):
    name: str
    partner_system: Optional[str] = None
    resource_types: Optional[List[str]] = None
    department_id: Optional[int] = None
    status: Optional[str] = "active"


class InteroperabilityExportProfileResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    name: str
    partner_system: Optional[str] = None
    resource_types: Optional[List[str]] = None
    department_id: Optional[int] = None
    created_by_id: Optional[int] = None
    status: str
    created_at: datetime
    standards_note: Optional[str] = None


class InteroperabilityExportResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    patient_id: int
    requested_by_id: Optional[int] = None
    consent_id: Optional[int] = None
    profile_id: Optional[int] = None
    export_type: str
    resource_count: int
    filter_summary: Optional[str] = None
    bundle_sha256: Optional[str] = None
    manifest_signature: Optional[str] = None
    signature_algorithm: Optional[str] = "HMAC-SHA256"
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ABDMConsentRequestCreate(BaseModel):
    patient_id: int
    patient_abha_address: str = Field(..., min_length=3, max_length=255)
    purpose_code: str = "CAREMGT"
    hi_types: Optional[List[str]] = None
    date_from: datetime
    date_to: datetime
    data_erase_at: datetime
    hip_id: Optional[str] = None
    care_context_reference: Optional[str] = None
    submit: bool = False


class ABDMConsentCallbackCreate(BaseModel):
    patient_id: Optional[int] = None
    local_consent_id: Optional[int] = None
    abdm_request_id: str = Field(..., min_length=1, max_length=128)
    abdm_consent_id: Optional[str] = Field(default=None, max_length=128)
    status: str = Field(..., min_length=1, max_length=32)
    hi_types: Optional[List[str]] = None
    event_type: Optional[str] = Field(default="consent_status", max_length=128)
    notification_at: Optional[datetime] = None
    error_code: Optional[str] = Field(default=None, max_length=128)

    model_config = ConfigDict(extra="forbid")


class ABDMConsentCallbackResponse(BaseModel):
    source: str
    event_id: int
    facility_id: Optional[int] = None
    patient_id: Optional[int] = None
    local_consent_id: Optional[int] = None
    abdm_request_id: str
    abdm_consent_id: Optional[str] = None
    event_type: str
    status: str
    local_consent_status: str
    hi_types: List[str]
    error_code: Optional[str] = None
    notification_at: Optional[str] = None
    payload_sha256: str
    raw_payload_stored: bool


class PredictionReviewCreate(BaseModel):
    patient_id: int
    prediction_type: str
    decision: str
    clinical_use_category: Optional[str] = "clinician_review"
    model_card_id: Optional[str] = None
    prediction_reference_id: Optional[str] = None
    review_note: Optional[str] = None

# --- Prediction Schemas ---

class DiabetesInput(BaseModel):
    """Schema for Diabetes Prediction (BRFSS 2015 Big Data)"""
    gender: int = Field(..., description="0: Female, 1: Male")
    age: float = Field(..., description="Age in years")
    hypertension: int = Field(..., description="0: No, 1: Yes")
    heart_disease: int = Field(..., description="0: No, 1: Yes")
    smoking_history: int = Field(..., description="0: No, 1: Yes")
    bmi: float = Field(..., description="Body Mass Index")
    high_chol: int = Field(..., description="0: No, 1: Yes")
    physical_activity: int = Field(..., description="0: No, 1: Yes (Past 30 days)")
    general_health: int = Field(..., description="1 (Excellent) to 5 (Poor)")

class HeartInput(BaseModel):
    """
    Schema for Heart Disease Prediction (Cleveland Dataset).
    Feature Logic: Focuses on Lab Reports and Clinical Vitals.
    """
    age: float = Field(..., description="Age in years.")
    sex: int = Field(..., description="0: Female, 1: Male")
    cp: int = Field(..., description="Chest pain type (0-3)")
    trestbps: float = Field(..., description="Resting blood pressure")
    chol: float = Field(..., description="Serum cholesterol in mg/dl")
    fbs: int = Field(..., description="Fasting blood sugar > 120 mg/dl (1/0)")
    restecg: int = Field(..., description="Resting ECG results (0-2)")
    thalach: float = Field(..., description="Maximum heart rate achieved")
    exang: int = Field(..., description="Exercise induced angina (1/0)")
    oldpeak: float = Field(..., description="ST depression induced by exercise")
    slope: int = Field(..., description="Slope of the peak exercise ST segment (0-2)")
    ca: int = Field(..., description="Number of major vessels (0-4)")
    thal: int = Field(..., description="Thalassemia (1-3)")

class LiverInput(BaseModel):
    """Schema for Liver Disease Prediction (ILPD)."""
    age: float
    gender: int # 0: Female, 1: Male
    total_bilirubin: float
    direct_bilirubin: float
    alkaline_phosphotase: float
    alamine_aminotransferase: float
    aspartate_aminotransferase: float
    total_proteins: float
    albumin: float
    albumin_and_globulin_ratio: float

class KidneyInput(BaseModel):
    """Schema for Kidney Disease Prediction (24 Features)."""
    age: float
    bp: float
    sg: float
    al: float
    su: float
    rbc: int # 0:Normal, 1:Abnormal
    pc: int
    pcc: int
    ba: int
    bgr: float
    bu: float
    sc: float
    sod: float
    pot: float
    hemo: float
    pcv: float
    wc: float
    rc: float
    htn: int # 1:Yes, 0:No
    dm: int
    cad: int
    appet: int # 0:Good, 1:Poor
    pe: int
    ane: int

class LungInput(BaseModel):
    """Schema for Respiratory/Lung Health."""
    gender: int # 1:Male, 0:Female
    age: float
    smoking: int
    yellow_fingers: int
    anxiety: int
    peer_pressure: int
    chronic_disease: int
    fatigue: int
    allergy: int
    wheezing: int
    alcohol: int
    coughing: int
    shortness_of_breath: int
    swallowing_difficulty: int
    chest_pain: int
