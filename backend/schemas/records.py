"""Record domain schemas: health records, chat logs, audit logs."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, model_validator


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
    facility_id: Optional[int] = None
    admin_id: Optional[int] = None
    actor_user_id: Optional[int] = None
    target_user_id: Optional[int] = None
    action: str
    timestamp: datetime | str
    details: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def sync_admin_and_actor(cls, data: Any) -> Any:
        if isinstance(data, dict):
            admin_val = data.get("admin_id")
            actor_val = data.get("actor_user_id")
            if admin_val is not None and actor_val is None:
                data["actor_user_id"] = admin_val
            elif actor_val is not None and admin_val is None:
                data["admin_id"] = actor_val
        elif hasattr(data, "admin_id") or hasattr(data, "actor_user_id"):
            admin_val = getattr(data, "admin_id", None)
            actor_val = getattr(data, "actor_user_id", None)
            if admin_val is not None and actor_val is None:
                try:
                    setattr(data, "actor_user_id", admin_val)
                except Exception:
                    pass
            elif actor_val is not None and admin_val is None:
                try:
                    setattr(data, "admin_id", actor_val)
                except Exception:
                    pass
        return data

    @model_validator(mode="after")
    def populate_fallback_fields(self) -> "AuditLogResponse":
        if self.admin_id is not None and self.actor_user_id is None:
            self.actor_user_id = self.admin_id
        elif self.actor_user_id is not None and self.admin_id is None:
            self.admin_id = self.actor_user_id
        return self
