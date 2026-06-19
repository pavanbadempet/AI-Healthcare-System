"""Record domain schemas: health records, chat logs, audit logs."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class AuditLogResponse(BaseModel):
    id: int
    facility_id: int | None = None
    actor_user_id: int | None = None
    target_user_id: int | None = None
    action: str
    timestamp: datetime | str
    details: str
