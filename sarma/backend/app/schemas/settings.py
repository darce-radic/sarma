"""
User Settings Schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class UserSettingsBase(BaseModel):
    """Base user settings schema"""
    
    # AI Configuration
    openai_api_key: Optional[str] = Field(None, description="User's OpenAI API key (encrypted)")
    gemini_api_key: Optional[str] = Field(None, description="User's Gemini API key (encrypted)")
    preferred_ai_provider: str = Field("gemini-flash", description="Preferred AI provider")
    
    # UI Preferences
    theme: str = Field("light", description="UI theme")
    language: str = Field("en", description="Language code")
    measurement_system: str = Field("metric", description="Measurement system")
    
    # Notifications
    email_notifications: bool = True
    push_notifications: bool = True
    meal_reminders: bool = True
    weekly_summary: bool = True
    
    # Privacy
    profile_visibility: str = Field("private", description="Profile visibility")
    share_meals: bool = False
    share_recipes: bool = False
    
    # Dietary Preferences
    dietary_restrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    favorite_cuisines: List[str] = Field(default_factory=list)
    disliked_foods: List[str] = Field(default_factory=list)
    
    # Health Goals
    health_goals: List[str] = Field(default_factory=list)
    daily_calorie_goal: Optional[int] = None
    daily_protein_goal: Optional[int] = None
    daily_carbs_goal: Optional[int] = None
    daily_fat_goal: Optional[int] = None
    
    # Other
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"


class UserSettingsCreate(UserSettingsBase):
    """Create user settings"""
    pass


class UserSettingsUpdate(BaseModel):
    """Update user settings (all fields optional)"""
    
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    preferred_ai_provider: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    measurement_system: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    meal_reminders: Optional[bool] = None
    weekly_summary: Optional[bool] = None
    profile_visibility: Optional[str] = None
    share_meals: Optional[bool] = None
    share_recipes: Optional[bool] = None
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    favorite_cuisines: Optional[List[str]] = None
    disliked_foods: Optional[List[str]] = None
    health_goals: Optional[List[str]] = None
    daily_calorie_goal: Optional[int] = None
    daily_protein_goal: Optional[int] = None
    daily_carbs_goal: Optional[int] = None
    daily_fat_goal: Optional[int] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None


class UserSettingsResponse(UserSettingsBase):
    """User settings response"""
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    # Mask API keys in response (show only first/last few chars)
    openai_api_key: Optional[str] = Field(None, description="Masked API key")
    gemini_api_key: Optional[str] = Field(None, description="Masked API key")
    
    class Config:
        from_attributes = True


class TestAPIKeyRequest(BaseModel):
    """Test API key request"""
    provider: str = Field(..., description="AI provider to test (gemini or openai)")
    api_key: str = Field(..., description="API key to test")


class TestAPIKeyResponse(BaseModel):
    """Test API key response"""
    success: bool
    provider: str
    message: str
    response_time_ms: Optional[int] = None
