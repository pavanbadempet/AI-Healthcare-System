"""SMART on FHIR domain schemas: app registration and launch context."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SmartAppCreate(BaseModel):
    """Payload to register a new SMART on FHIR application."""

    app_name: str
    redirect_uri: str
    launch_url: str
    scopes: str = "launch/patient patient/*.read"


class SmartAppResponse(BaseModel):
    """Serialised SMART app returned to clients."""

    id: int
    app_name: str
    client_id: str
    redirect_uri: str
    launch_url: str
    scopes: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SmartLaunchRequest(BaseModel):
    """Request to create a patient-scoped launch context."""

    app_id: int
    patient_id: int


class SmartLaunchResponse(BaseModel):
    """Short-lived launch context returned after a SMART launch."""

    launch_token: str
    auth_code: str
    scope: str
    expires_at: datetime
