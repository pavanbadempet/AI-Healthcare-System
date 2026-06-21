"""Federated Learning domain schemas: feedback, sync, and audit."""
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class ModelFeedbackCreate(BaseModel):
    """Clinician submits a correction for a model prediction."""

    patient_id: int
    model_name: str
    input_features: dict
    prediction_result: dict
    corrected_label: str


class ModelFeedbackResponse(BaseModel):
    """Serialised feedback record."""

    id: int
    patient_id: int
    model_name: str
    input_features: str  # stored as JSON text
    prediction_result: str  # stored as JSON text
    corrected_label: str
    clinician_id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FederatedSyncRequest(BaseModel):
    """Parameters for a differential-privacy federated sync."""

    model_name: str
    epsilon: float = 1.0
    sensitivity: float = 1.0


class FederatedSyncResponse(BaseModel):
    """Result of a federated DP sync run."""

    sync_run_id: str
    records_synced: int
    epsilon_consumed: float
    noisy_gradients: Dict[str, float]
    status: str


class FederatedSyncAuditResponse(BaseModel):
    """Serialised sync audit record."""

    id: int
    sync_run_id: str
    node_id: str
    model_name: str
    records_synced: int
    epsilon_consumed: float
    delta_consumed: float
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
