"""
User Settings Model
Store user preferences and API configurations
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserSettings(Base):
    """User settings and preferences"""
    
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # AI Configuration (Optional - for users who want their own keys)
    openai_api_key = Column(String(255), nullable=True)  # Encrypted
    gemini_api_key = Column(String(255), nullable=True)  # Encrypted
    preferred_ai_provider = Column(String(50), default="gemini-flash")  # gemini-flash, gpt4-vision
    
    # UI Preferences
    theme = Column(String(20), default="light")  # light, dark, auto
    language = Column(String(10), default="en")  # en, es, fr, etc.
    measurement_system = Column(String(20), default="metric")  # metric, imperial
    
    # Notification Preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    meal_reminders = Column(Boolean, default=True)
    weekly_summary = Column(Boolean, default=True)
    
    # Privacy Settings
    profile_visibility = Column(String(20), default="private")  # public, friends, private
    share_meals = Column(Boolean, default=False)
    share_recipes = Column(Boolean, default=False)
    
    # Dietary Preferences (stored as JSON)
    dietary_restrictions = Column(JSON, default=list)  # ["vegetarian", "gluten-free", ...]
    allergies = Column(JSON, default=list)  # ["peanuts", "dairy", ...]
    favorite_cuisines = Column(JSON, default=list)  # ["Italian", "Mexican", ...]
    disliked_foods = Column(JSON, default=list)  # ["olives", "mushrooms", ...]
    
    # Health Goals
    health_goals = Column(JSON, default=list)  # ["weight-loss", "muscle-gain", ...]
    daily_calorie_goal = Column(Integer, nullable=True)
    daily_protein_goal = Column(Integer, nullable=True)
    daily_carbs_goal = Column(Integer, nullable=True)
    daily_fat_goal = Column(Integer, nullable=True)
    
    # Additional Settings
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="YYYY-MM-DD")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id})>"
