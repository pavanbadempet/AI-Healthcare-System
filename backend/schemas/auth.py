"""Auth domain schemas: tokens, user creation, profile updates."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

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

