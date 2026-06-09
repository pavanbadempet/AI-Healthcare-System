"""Prediction domain schemas: prediction review and ML model inputs."""
from typing import Optional

from pydantic import BaseModel, Field


class PredictionReviewCreate(BaseModel):
    patient_id: int
    prediction_type: str
    decision: str
    clinical_use_category: Optional[str] = "clinician_review"
    model_card_id: Optional[str] = None
    prediction_reference_id: Optional[str] = None
    review_note: Optional[str] = None


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
    gender: int  # 0: Female, 1: Male
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
    rbc: int  # 0:Normal, 1:Abnormal
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
    htn: int  # 1:Yes, 0:No
    dm: int
    cad: int
    appet: int  # 0:Good, 1:Poor
    pe: int
    ane: int


class LungInput(BaseModel):
    """Schema for Respiratory/Lung Health."""
    gender: int  # 1:Male, 0:Female
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
