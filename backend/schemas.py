from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

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

class UserFullResponse(UserResponse):
    """Admin View: Includes sensitive health records and chat logs"""
    health_records: List[HealthRecordResponse] = []
    chat_logs: List[ChatLogResponse] = []



class AppointmentCreate(BaseModel):
    specialist: str
    date: str
    time: str
    reason: str

class AppointmentResponse(BaseModel):
    id: int
    specialist: str
    date_time: datetime
    reason: str
    status: str
    model_config = ConfigDict(from_attributes=True)

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
    Schema for Heart Disease Prediction (CDC BRFSS - 90%+ Accuracy).
    Feature Logic: Focuses on Risk Factors (History) rather than just current Vitals.
    """
    age: float = Field(..., description="Age in years.")
    gender: int = Field(..., description="0: Female, 1: Male")
    high_bp: int = Field(..., description="0: Normal, 1: High BP")
    high_chol: int = Field(..., description="0: Normal, 1: High Cholesterol")
    bmi: float = Field(..., description="Body Mass Index")
    smoker: int = Field(..., description="1 if smoked 100+ cigs in lifetime, else 0")
    stroke: int = Field(..., description="1 if history of stroke, else 0")
    diabetes: int = Field(..., description="0: No, 1: Pre-Diabetes or Diabetes")
    phys_activity: int = Field(..., description="1 if active in past 30 days, else 0")
    hvy_alcohol: int = Field(..., description="1 if heavy drinker (Men >14/wk, Women >7/wk), else 0")
    gen_hlth: int = Field(..., description="Self-rated health: 1 (Excellent) to 5 (Poor)")

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
