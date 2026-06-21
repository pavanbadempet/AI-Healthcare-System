"""Clinical domain schemas: orders, care events, vitals, monitoring, diagnostics."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from .hospital import AdmissionResponse, EncounterResponse


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
    blood_glucose: Optional[float] = None
    observed_at: Optional[datetime] = None

    @field_validator("heart_rate")
    @classmethod
    def validate_heart_rate(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 20 or v > 250):
            raise ValueError("Heart rate must be between 20 and 250 bpm")
        return v

    @field_validator("systolic_bp")
    @classmethod
    def validate_systolic_bp(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 40 or v > 300):
            raise ValueError("Systolic blood pressure must be between 40 and 300 mmHg")
        return v

    @field_validator("diastolic_bp")
    @classmethod
    def validate_diastolic_bp(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 20 or v > 200):
            raise ValueError("Diastolic blood pressure must be between 20 and 200 mmHg")
        return v

    @field_validator("spo2")
    @classmethod
    def validate_spo2(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v > 100):
            raise ValueError("SpO2 oxygen saturation must be between 0 and 100%")
        return v

    @field_validator("temperature_c")
    @classmethod
    def validate_temperature_c(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 30.0 or v > 45.0):
            raise ValueError("Temperature must be between 30.0 and 45.0 °C")
        return v

    @field_validator("respiratory_rate")
    @classmethod
    def validate_respiratory_rate(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 4 or v > 80):
            raise ValueError("Respiratory rate must be between 4 and 80 breaths/min")
        return v


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
    blood_glucose: Optional[float] = None
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
