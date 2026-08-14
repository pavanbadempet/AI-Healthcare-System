from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ClickstreamEventInput(BaseModel):
    session_id: str
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    url: Optional[str] = None

class ClickstreamEventResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    session_id: str
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
