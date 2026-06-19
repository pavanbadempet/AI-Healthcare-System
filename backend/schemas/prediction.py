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
    gender: Optional[int] = Field(None, description="0: Female, 1: Male")
    age: Optional[float] = Field(None, description="Age in years")
    hypertension: Optional[int] = Field(None, description="0: No, 1: Yes")
    heart_disease: Optional[int] = Field(None, description="0: No, 1: Yes")
    smoking_history: Optional[int] = Field(None, description="0: No, 1: Yes")
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    high_chol: Optional[int] = Field(None, description="0: No, 1: Yes")
    physical_activity: Optional[int] = Field(None, description="0: No, 1: Yes (Past 30 days)")
    general_health: Optional[int] = Field(None, description="1 (Excellent) to 5 (Poor)")


class HeartInput(BaseModel):
    """
    Schema for Heart Disease Prediction (Cleveland Dataset).
    Feature Logic: Focuses on Lab Reports and Clinical Vitals.
    """
    age: Optional[float] = Field(None, description="Age in years.")
    sex: Optional[int] = Field(None, description="0: Female, 1: Male")
    cp: Optional[int] = Field(None, description="Chest pain type (0-3)")
    trestbps: Optional[float] = Field(None, description="Resting blood pressure")
    chol: Optional[float] = Field(None, description="Serum cholesterol in mg/dl")
    fbs: Optional[int] = Field(None, description="Fasting blood sugar > 120 mg/dl (1/0)")
    restecg: Optional[int] = Field(None, description="Resting ECG results (0-2)")
    thalach: Optional[float] = Field(None, description="Maximum heart rate achieved")
    exang: Optional[int] = Field(None, description="Exercise induced angina (1/0)")
    oldpeak: Optional[float] = Field(None, description="ST depression induced by exercise")
    slope: Optional[int] = Field(None, description="Slope of the peak exercise ST segment (0-2)")
    ca: Optional[int] = Field(None, description="Number of major vessels (0-4)")
    thal: Optional[int] = Field(None, description="Thalassemia (1-3)")
    hdl: Optional[float] = Field(50.0, description="HDL Cholesterol in mg/dL (Default: 50.0)")
    smoker: Optional[int] = Field(0, description="0: Non-smoker, 1: Smoker (Default: 0)")
    hyp_treatment: Optional[int] = Field(0, description="0: Untreated, 1: Treated (Default: 0)")


class LiverInput(BaseModel):
    """Schema for Liver Disease Prediction (ILPD)."""
    age: Optional[float] = None
    gender: Optional[int] = None  # 0: Female, 1: Male
    total_bilirubin: Optional[float] = None
    direct_bilirubin: Optional[float] = None
    alkaline_phosphotase: Optional[float] = None
    alamine_aminotransferase: Optional[float] = None
    aspartate_aminotransferase: Optional[float] = None
    total_proteins: Optional[float] = None
    albumin: Optional[float] = None
    albumin_and_globulin_ratio: Optional[float] = None
    platelets: Optional[float] = Field(250.0, description="Platelets in 10^9/L (Default: 250.0)")


class KidneyInput(BaseModel):
    """Schema for Kidney Disease Prediction (24 Features)."""
    age: Optional[float] = None
    bp: Optional[float] = None
    sg: Optional[float] = None
    al: Optional[float] = None
    su: Optional[float] = None
    rbc: Optional[int] = None  # 0:Normal, 1:Abnormal
    pc: Optional[int] = None
    pcc: Optional[int] = None
    ba: Optional[int] = None
    bgr: Optional[float] = None
    bu: Optional[float] = None
    sc: Optional[float] = None
    sod: Optional[float] = None
    pot: Optional[float] = None
    hemo: Optional[float] = None
    pcv: Optional[float] = None
    wc: Optional[float] = None
    rc: Optional[float] = None
    htn: Optional[int] = None  # 1:Yes, 0:No
    dm: Optional[int] = None
    cad: Optional[int] = None
    appet: Optional[int] = None  # 0:Good, 1:Poor
    pe: Optional[int] = None
    ane: Optional[int] = None
    gender: Optional[int] = Field(1, description="0: Female, 1: Male (Default: 1)")


class LungInput(BaseModel):
    """Schema for Respiratory/Lung Health."""
    gender: Optional[int] = None  # 1:Male, 0:Female
    age: Optional[float] = None
    smoking: Optional[int] = None
    yellow_fingers: Optional[int] = None
    anxiety: Optional[int] = None
    peer_pressure: Optional[int] = None
    chronic_disease: Optional[int] = None
    fatigue: Optional[int] = None
    allergy: Optional[int] = None
    wheezing: Optional[int] = None
    alcohol: Optional[int] = None
    coughing: Optional[int] = None
    shortness_of_breath: Optional[int] = None
    swallowing_difficulty: Optional[int] = None
    chest_pain: Optional[int] = None
