"""Pydantic schemas for longitudinal (time-series) prediction endpoints.

Each schema represents a *sequence* of clinical visits for a single patient.
The list order is chronological — oldest visit first, most-recent visit last.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Per-visit feature records (one per disease domain)
# ---------------------------------------------------------------------------

class DiabetesVisit(BaseModel):
    """Single clinical visit record for diabetes risk features."""
    gender: Optional[int] = Field(None, description="0: Female, 1: Male")
    age: Optional[float] = Field(None, description="Age in years at time of visit")
    hypertension: Optional[int] = Field(None, description="0: No, 1: Yes")
    heart_disease: Optional[int] = Field(None, description="0: No, 1: Yes")
    smoking_history: Optional[int] = Field(None, description="0: No, 1: Yes")
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    high_chol: Optional[int] = Field(None, description="0: No, 1: Yes")
    physical_activity: Optional[int] = Field(None, description="0: No, 1: Yes (Past 30 days)")
    general_health: Optional[int] = Field(None, description="1 (Excellent) to 5 (Poor)")


class HeartVisit(BaseModel):
    """Single clinical visit record for heart disease risk features."""
    age: Optional[float] = Field(None, description="Age in years")
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


class LiverVisit(BaseModel):
    """Single clinical visit record for liver disease risk features."""
    age: Optional[float] = None
    gender: Optional[int] = None
    total_bilirubin: Optional[float] = None
    direct_bilirubin: Optional[float] = None
    alkaline_phosphotase: Optional[float] = None
    alamine_aminotransferase: Optional[float] = None
    aspartate_aminotransferase: Optional[float] = None
    total_proteins: Optional[float] = None
    albumin: Optional[float] = None
    albumin_globulin_ratio: Optional[float] = None


class KidneyVisit(BaseModel):
    """Single clinical visit record for kidney disease risk features."""
    age: Optional[float] = None
    blood_pressure: Optional[float] = None
    specific_gravity: Optional[float] = None
    albumin: Optional[float] = None
    sugar: Optional[float] = None
    blood_glucose_random: Optional[float] = None
    blood_urea: Optional[float] = None
    serum_creatinine: Optional[float] = None
    sodium: Optional[float] = None
    potassium: Optional[float] = None
    hemoglobin: Optional[float] = None
    packed_cell_volume: Optional[float] = None
    white_blood_cell_count: Optional[float] = None
    red_blood_cell_count: Optional[float] = None
    hypertension: Optional[int] = None
    diabetes_mellitus: Optional[int] = None
    appetite: Optional[int] = None
    pedal_edema: Optional[int] = None
    anemia: Optional[int] = None


# ---------------------------------------------------------------------------
# Sequence request wrappers
# ---------------------------------------------------------------------------

class LongitudinalDiabetesRequest(BaseModel):
    """Sequence of diabetes visits for temporal risk prediction."""
    patient_id: Optional[int] = Field(None, description="Patient ID for audit trail")
    visits: List[DiabetesVisit] = Field(
        ..., min_length=2,
        description="Chronological list of diabetes visit records (oldest → newest). Minimum 2 visits required.",
    )


class LongitudinalHeartRequest(BaseModel):
    """Sequence of heart visits for temporal risk prediction."""
    patient_id: Optional[int] = Field(None, description="Patient ID for audit trail")
    visits: List[HeartVisit] = Field(
        ..., min_length=2,
        description="Chronological list of heart visit records (oldest → newest). Minimum 2 visits required.",
    )


class LongitudinalLiverRequest(BaseModel):
    """Sequence of liver visits for temporal risk prediction."""
    patient_id: Optional[int] = Field(None, description="Patient ID for audit trail")
    visits: List[LiverVisit] = Field(
        ..., min_length=2,
        description="Chronological list of liver visit records (oldest → newest). Minimum 2 visits required.",
    )


class LongitudinalKidneyRequest(BaseModel):
    """Sequence of kidney visits for temporal risk prediction."""
    patient_id: Optional[int] = Field(None, description="Patient ID for audit trail")
    visits: List[KidneyVisit] = Field(
        ..., min_length=2,
        description="Chronological list of kidney visit records (oldest → newest). Minimum 2 visits required.",
    )


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class VisitAttention(BaseModel):
    """Attention weight for a single visit in the sequence."""
    visit_index: int = Field(..., description="0-indexed position in the visit sequence")
    weight: float = Field(..., description="Attention weight (0-1), higher = more influential")


class LongitudinalPredictionResponse(BaseModel):
    """Response from longitudinal temporal prediction endpoints."""
    condition: str = Field(..., description="Disease domain (diabetes, heart, liver, kidney)")
    risk_probability: float = Field(..., description="Predicted positive-class probability")
    risk_label: str = Field(..., description="LOW / MODERATE / HIGH / VERY HIGH")
    trend: str = Field(..., description="IMPROVING / STABLE / WORSENING based on visit trajectory")
    num_visits: int = Field(..., description="Number of visits in the input sequence")
    visit_attention: List[VisitAttention] = Field(
        ..., description="Per-visit attention weights showing which visits influenced the prediction most",
    )
    medical_disclaimer: str = Field(
        ..., description="Required medical disclaimer for AI-generated health advice",
    )
