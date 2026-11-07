"""Prediction domain schemas: prediction review and ML model inputs."""
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class PredictionReviewCreate(BaseModel):
    patient_id: int
    prediction_type: str
    model_prediction: str = ""
    clinician_agree: bool = True
    revised_diagnosis: Optional[str] = None
    notes: Optional[str] = None

    # Bidirectional parity fields for Python legacy endpoints & audit logs
    decision: Optional[str] = None
    clinical_use_category: Optional[str] = "clinician_review"
    model_card_id: Optional[str] = None
    prediction_reference_id: Optional[str] = None
    review_note: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def harmonize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Harmonize decision and clinician_agree
            decision = data.get("decision")
            clinician_agree = data.get("clinician_agree")
            if decision is None and clinician_agree is not None:
                data["decision"] = "accepted" if clinician_agree else "overridden"
            elif decision is not None and clinician_agree is None:
                data["clinician_agree"] = str(decision).strip().lower() in {
                    "accepted", "agree", "approved", "true", "1"
                }
            elif decision is None and clinician_agree is None:
                data["decision"] = "accepted"
                data["clinician_agree"] = True

            # Harmonize notes and review_note
            notes = data.get("notes")
            review_note = data.get("review_note")
            if notes is None and review_note is not None:
                data["notes"] = review_note
            elif review_note is None and notes is not None:
                data["review_note"] = notes

            # Ensure model_prediction is at least empty string if missing
            if data.get("model_prediction") is None:
                data["model_prediction"] = ""
        return data


class DiabetesInput(BaseModel):
    """Schema for Diabetes Prediction (BRFSS 2015 Big Data). Aligned with Rust DiabetesInput."""
    hypertension: float = Field(..., description="0: No, 1: Yes")
    high_chol: float = Field(..., description="0: No, 1: Yes")
    bmi: float = Field(..., description="Body Mass Index")
    smoking_history: float = Field(..., description="0: No, 1: Yes")
    heart_disease: float = Field(..., description="0: No, 1: Yes")
    physical_activity: float = Field(..., description="0: No, 1: Yes (Past 30 days)")
    general_health: float = Field(..., description="1 (Excellent) to 5 (Poor)")
    gender: float = Field(..., description="0: Female, 1: Male")
    age: float = Field(..., description="Age in years")


class HeartInput(BaseModel):
    """
    Schema for Heart Disease Prediction (Cleveland Dataset).
    Mirrors rust_gateway/src/ml/predictors.rs:HeartInput with the 13 required features,
    while maintaining optional clinical features (hdl, smoker, hyp_treatment) with defaults.
    """
    age: float = Field(..., description="Age in years.")
    sex: float = Field(..., description="0: Female, 1: Male")
    cp: float = Field(..., description="Chest pain type (0-3)")
    trestbps: float = Field(..., description="Resting blood pressure")
    chol: float = Field(..., description="Serum cholesterol in mg/dl")
    fbs: float = Field(..., description="Fasting blood sugar > 120 mg/dl (1/0)")
    restecg: float = Field(..., description="Resting ECG results (0-2)")
    thalach: float = Field(..., description="Maximum heart rate achieved")
    exang: float = Field(..., description="Exercise induced angina (1/0)")
    oldpeak: float = Field(..., description="ST depression induced by exercise")
    slope: float = Field(..., description="Slope of the peak exercise ST segment (0-2)")
    ca: float = Field(..., description="Number of major vessels (0-4)")
    thal: float = Field(..., description="Thalassemia (1-3)")
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
    """Schema for Kidney Disease Prediction (24 Features). Aligned with Rust KidneyInput."""
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
    is_female: Optional[bool] = Field(None, description="True: Female, False: Male (Rust parity)")

    @model_validator(mode="before")
    @classmethod
    def harmonize_gender_and_is_female(cls, data: Any) -> Any:
        if isinstance(data, dict):
            is_female = data.get("is_female")
            gender = data.get("gender")
            if is_female is not None and gender is None:
                data["gender"] = 0 if is_female else 1
            elif gender is not None and is_female is None:
                data["is_female"] = bool(gender == 0)
        return data


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


class MultiOrganInput(BaseModel):
    """Unified schema for Multi-Organ Risk Assessment (union of all 5 inputs)"""
    # Demographics
    gender: Optional[int] = Field(None, description="0: Female, 1: Male")
    age: Optional[float] = Field(None, description="Age in years")

    # Lifestyle & Common Markers
    smoking: Optional[int] = Field(None, description="0: No, 1: Yes")
    physical_activity: Optional[int] = Field(None, description="0: No, 1: Yes")
    alcohol: Optional[int] = Field(None, description="0: No, 1: Yes")
    general_health: Optional[int] = Field(None, description="1 (Excellent) to 5 (Poor)")
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    glucose: Optional[float] = Field(None, description="Blood glucose level")
    hba1c: Optional[float] = Field(None, description="HbA1c level")

    # Cardiovascular
    hypertension: Optional[int] = Field(None, description="0: No, 1: Yes")
    heart_disease: Optional[int] = Field(None, description="0: No, 1: Yes")
    cp: Optional[int] = Field(None, description="Chest pain type (0-3)")
    trestbps: Optional[float] = Field(None, description="Resting blood pressure")
    chol: Optional[float] = Field(None, description="Serum cholesterol in mg/dl")
    fbs: Optional[int] = Field(None, description="Fasting blood sugar > 120 mg/dl (1/0)")
    restecg: Optional[int] = Field(None, description="Resting ECG results (0-2)")
    thalach: Optional[float] = Field(None, description="Maximum heart rate achieved")
    exang: Optional[int] = Field(None, description="Exercise induced angina (1/0)")
    oldpeak: Optional[float] = Field(None, description="ST depression induced by exercise")
    slope: Optional[int] = Field(None, description="Slope of peak exercise ST segment")
    ca: Optional[int] = Field(None, description="Number of major vessels (0-4)")
    thal: Optional[int] = Field(None, description="Thalassemia (1-3)")
    hdl: Optional[float] = Field(50.0, description="HDL Cholesterol")
    hyp_treatment: Optional[int] = Field(0, description="0: Untreated, 1: Treated")

    # Hepatic / Liver
    total_bilirubin: Optional[float] = None
    direct_bilirubin: Optional[float] = None
    alkaline_phosphotase: Optional[float] = None
    alamine_aminotransferase: Optional[float] = None
    aspartate_aminotransferase: Optional[float] = None
    total_proteins: Optional[float] = None
    albumin: Optional[float] = None
    albumin_and_globulin_ratio: Optional[float] = None
    platelets: Optional[float] = Field(250.0, description="Platelets in 10^9/L (Default: 250.0)")

    # Renal / Kidney
    bp: Optional[float] = None
    sg: Optional[float] = None
    al: Optional[float] = None
    su: Optional[float] = None
    rbc: Optional[int] = None
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
    htn: Optional[int] = None
    dm: Optional[int] = None
    cad: Optional[int] = None
    appet: Optional[int] = None
    pe: Optional[int] = None
    ane: Optional[int] = None

    # Lungs / Pulmonary
    yellow_fingers: Optional[int] = None
    anxiety: Optional[int] = None
    peer_pressure: Optional[int] = None
    chronic_disease: Optional[int] = None
    fatigue: Optional[int] = None
    allergy: Optional[int] = None
    wheezing: Optional[int] = None
    coughing: Optional[int] = None
    shortness_of_breath: Optional[int] = None
    swallowing_difficulty: Optional[int] = None
    chest_pain: Optional[int] = None


class StrokeInput(BaseModel):
    """Schema for Stroke Risk Prediction (Cerebrovascular risk)"""
    gender: Optional[int] = Field(None, description="0: Female, 1: Male")
    age: Optional[float] = Field(None, description="Age in years")
    hypertension: Optional[int] = Field(None, description="0: No, 1: Yes")
    heart_disease: Optional[int] = Field(None, description="0: No, 1: Yes")
    smoking: Optional[int] = Field(None, description="0: No, 1: Yes")
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    glucose: Optional[float] = Field(None, description="Average blood glucose level")
