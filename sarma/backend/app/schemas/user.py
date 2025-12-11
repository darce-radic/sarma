"""
Forecast Health - User Schemas
Pydantic models for request/response validation
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


class UserUpdate(BaseModel):
    """User profile update request"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class HealthProfileUpdate(BaseModel):
    """Health profile update request"""
    height_cm: Optional[float] = Field(None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(None, gt=0, lt=500)
    waist_circumference_cm: Optional[float] = Field(None, gt=0, lt=300)
    diagnosed_conditions: Optional[List[str]] = None
    family_history_diabetes: Optional[bool] = None
    current_medications: Optional[List[dict]] = None
    physical_activity_hours_week: Optional[float] = Field(None, ge=0, le=168)
    sleep_hours_avg: Optional[float] = Field(None, ge=0, le=24)
    stress_level: Optional[int] = Field(None, ge=1, le=10)


class PreferencesUpdate(BaseModel):
    """User preferences update request"""
    dietary_restrictions: Optional[List[str]] = None
    cuisine_preferences: Optional[List[str]] = None
    disliked_ingredients: Optional[List[str]] = None
    cooking_skill: Optional[str] = None
    max_cooking_time_minutes: Optional[int] = Field(None, gt=0)
    household_size: Optional[int] = Field(None, gt=0, le=20)
    health_goals: Optional[List[str]] = None
    target_daily_calories: Optional[int] = Field(None, gt=0)
    target_macros: Optional[dict] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class HealthProfileResponse(BaseModel):
    """Health profile response"""
    height_cm: Optional[float]
    weight_kg: Optional[float]
    waist_circumference_cm: Optional[float]
    diagnosed_conditions: List[str]
    family_history_diabetes: bool
    current_medications: List[dict]
    hba1c_percentage: Optional[float]
    fasting_glucose_mmol: Optional[float]
    blood_pressure_systolic: Optional[int]
    blood_pressure_diastolic: Optional[int]
    physical_activity_hours_week: Optional[float]
    bmi: Optional[float]
    
    class Config:
        from_attributes = True


class PreferencesResponse(BaseModel):
    """User preferences response"""
    dietary_restrictions: List[str]
    cuisine_preferences: List[str]
    disliked_ingredients: List[str]
    cooking_skill: str
    max_cooking_time_minutes: int
    household_size: int
    health_goals: List[str]
    target_daily_calories: Optional[int]
    target_macros: Optional[dict]
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription info response"""
    tier: str
    status: str
    current_period_end: Optional[datetime]


class UserResponse(BaseModel):
    """Complete user profile response"""
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    phone_number: Optional[str]
    email_verified: bool
    onboarding_completed: bool
    created_at: datetime
    subscription: SubscriptionResponse
    health_profile: Optional[HealthProfileResponse]
    preferences: Optional[PreferencesResponse]
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response (login/register)"""
    user: UserResponse
    tokens: TokenResponse
