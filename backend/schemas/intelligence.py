"""Clinical Intelligence domain schemas: alerts, insights, explainability."""
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class ClinicalAlertResponse(BaseModel):
    """Serialised clinical alert."""

    id: int
    patient_id: int
    alert_type: str
    severity: str
    message: str
    source_event_id: Optional[str] = None
    is_acknowledged: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledgeRequest(BaseModel):
    """Empty body — presence of the request triggers acknowledgement."""

    pass


class PatientInsightResponse(BaseModel):
    """Serialised patient insight."""

    id: int
    patient_id: int
    insight_type: str
    content: str  # JSON text
    model_version: Optional[str] = None
    disclaimer: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExplainabilityResponse(BaseModel):
    """SHAP-style feature-importance explanation for a prediction."""

    prediction_id: int
    model_name: str
    feature_importances: Dict[str, float]
    explanation_text: str
