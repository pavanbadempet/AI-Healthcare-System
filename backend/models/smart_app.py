"""SMART on FHIR domain models: app registry and launch context."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class SmartApp(Base):
    """Registered SMART on FHIR application."""

    __tablename__ = "smart_apps"

    id = Column(Integer, primary_key=True, index=True)
    app_name = Column(String, unique=True, nullable=False)
    client_id = Column(String, unique=True, nullable=False, index=True)
    redirect_uri = Column(String, nullable=False)
    launch_url = Column(String, nullable=False)
    scopes = Column(String, default="launch/patient patient/*.read")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    launch_contexts = relationship("SmartLaunchContext", back_populates="app")


class SmartLaunchContext(Base):
    """Patient-scoped SMART launch context with short-lived auth tokens."""

    __tablename__ = "smart_launch_contexts"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("smart_apps.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    launch_token = Column(String, unique=True, nullable=False, index=True)
    auth_code = Column(String, nullable=True)
    scope = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    app = relationship("SmartApp", back_populates="launch_contexts")
    patient = relationship("User", foreign_keys=[patient_id])
    user = relationship("User", foreign_keys=[user_id])
