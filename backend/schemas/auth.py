"""Auth domain schemas: tokens, user creation, profile updates."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .records import ChatLogResponse, HealthRecordResponse


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    """Schema for User Registration"""
    username: str
    password: str = Field(..., description="Must meet complexity requirements")
    email: str
    full_name: str
    dob: str = Field(..., description="YYYY-MM-DD format")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Full name cannot be empty or only spaces")
        if len(clean) < 2 or len(clean) > 100:
            raise ValueError("Full name must be between 2 and 100 characters")
        return clean

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        from datetime import date
        try:
            born = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Date of birth must be in YYYY-MM-DD format")

        if born > date.today():
            raise ValueError("Date of birth cannot be in the future")
        if born.year < 1900:
            raise ValueError("Date of birth must be after year 1900")
        return v


class UserResponse(BaseModel):
    """Schema for Public User Profile"""
    id: int
    username: str
    role: Optional[str] = "patient"
    full_name: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Schema for Updating User Details"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_type: Optional[str] = None
    existing_ailments: Optional[str] = None
    profile_picture: Optional[str] = None
    about_me: Optional[str] = None
    diet: Optional[str] = None
    activity_level: Optional[str] = None
    sleep_hours: Optional[float] = None
    stress_level: Optional[str] = None
    specialization: Optional[str] = None
    allow_data_collection: Optional[bool] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not clean:
            raise ValueError("Full name cannot be empty or only spaces")
        if len(clean) < 2 or len(clean) > 100:
            raise ValueError("Full name must be between 2 and 100 characters")
        return clean

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        from datetime import date
        try:
            born = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Date of birth must be in YYYY-MM-DD format")

        if born > date.today():
            raise ValueError("Date of birth cannot be in the future")
        if born.year < 1900:
            raise ValueError("Date of birth must be after year 1900")
        return v


class UserFullResponse(UserResponse):
    """Admin View: Includes sensitive health records and chat logs"""
    health_records: List[HealthRecordResponse] = []
    chat_logs: List[ChatLogResponse] = []


class ForgotPasswordRequest(BaseModel):
    """Schema for password reset request"""
    email: str


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password with token"""
    token: str
    new_password: str = Field(..., description="Must meet complexity requirements")

