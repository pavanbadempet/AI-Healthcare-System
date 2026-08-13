"""
Pydantic Schemas for 4-Stage Multi-Objective Clinical Recommendation Engine.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PatientContext(BaseModel):
    """Real-time patient demographic, clinical, and physiological context."""
    patient_id: str = Field(..., description="Unique Patient Identifier (MRN or UUID)")
    age: float = Field(..., ge=0, le=120, description="Patient age in years")
    gender: str = Field(default="unknown", description="Patient gender (male, female, other)")
    bmi: Optional[float] = Field(default=None, ge=10, le=80, description="Body Mass Index")
    systolic_bp: Optional[float] = Field(default=None, description="Systolic Blood Pressure (mmHg)")
    diastolic_bp: Optional[float] = Field(default=None, description="Diastolic Blood Pressure (mmHg)")
    fasting_glucose: Optional[float] = Field(default=None, description="Fasting Blood Glucose (mg/dL)")
    hba1c: Optional[float] = Field(default=None, description="HbA1c percentage")
    primary_conditions: List[str] = Field(default_factory=list, description="Active ICD-10 or clinical diagnoses")
    allergies: List[str] = Field(default_factory=list, description="Known patient allergies and intolerances")
    current_medications: List[str] = Field(default_factory=list, description="Active medication names or RxNorm codes")
    recent_interactions: List[str] = Field(default_factory=list, description="Recent user interactions or clicked topics")


class RecommendationRequest(BaseModel):
    """Incoming request to the 4-stage recommendation engine."""
    patient_context: PatientContext
    domain: str = Field(default="clinical_intervention", description="Domain: clinical_intervention, lifestyle_pathway, clinical_trial")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of final recommendations to return")
    diversity_lambda: float = Field(default=0.7, ge=0.0, le=1.0, description="MMR trade-off factor (1.0 = pure relevance, 0.0 = max diversity)")
    enable_exploration: bool = Field(default=True, description="Enable Contextual Bandit exploration via Thompson Sampling")


class CandidateItem(BaseModel):
    """Raw candidate entity retrieved in Stage 1."""
    item_id: str
    title: str
    category: str
    description: str
    evidence_level: str = "Level 1A"
    contraindications: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    similarity_score: float = 0.0


class RankedRecommendation(BaseModel):
    """Fully scored, diversified, and safety-verified recommendation."""
    rank: int
    item_id: str
    title: str
    category: str
    description: str
    evidence_level: str
    predicted_efficacy: float = Field(..., ge=0.0, le=1.0, description="Predicted clinical efficacy score")
    safety_score: float = Field(..., ge=0.0, le=1.0, description="Predicted safety score (1.0 - adverse probability)")
    adherence_likelihood: float = Field(..., ge=0.0, le=1.0, description="Predicted patient compliance likelihood")
    composite_score: float = Field(..., description="Multi-objective calibrated rank score")
    diversity_score: float = Field(..., description="Maximal Marginal Relevance penalty applied")
    is_explored: bool = Field(default=False, description="Whether selected via Thompson Sampling exploration")
    rationale: str = Field(default="", description="Clinical AI justification for the recommendation")


class RecommendationResponse(BaseModel):
    """Final output response from the 4-stage recommendation engine."""
    patient_id: str
    domain: str
    total_candidates_retrieved: int
    total_ranked_candidates: int
    latency_ms: float
    recommendations: List[RankedRecommendation]
    medical_disclaimer: str = "AI-generated recommendations are for clinical decision support only and must be validated by a licensed clinician."


class FeedbackEvent(BaseModel):
    """Feedback event for Thompson Sampling bandit learning and delayed outcome tracking."""
    patient_id: str
    item_id: str
    action: str = Field(..., description="Action: impression, click, accept, decline, completed")
    outcome_value: float = Field(default=1.0, ge=0.0, le=1.0, description="Reward signal (1.0 for positive, 0.0 for negative)")
    time_delay_hours: Optional[float] = Field(default=0.0, description="Time elapsed before outcome observed")
