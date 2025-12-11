"""
Forecast Health - User Models
Core user, health profile, and preferences models
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, Float, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


# Enums
class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    FAMILY = "family"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    PAUSED = "paused"


class GenderType(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class User(Base):
    """Core user account model"""
    __tablename__ = "users"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(GenderType), nullable=True)
    
    # Subscription
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(100), unique=True, nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    
    # Settings
    timezone = Column(String(50), default="Australia/Melbourne", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    notification_settings = Column(JSON, default={}, nullable=False)
    
    # Tracking
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    health_profile = relationship("UserHealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UserHealthProfile(Base):
    """User's health profile and conditions"""
    __tablename__ = "user_health_profiles"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Physical Measurements
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    waist_circumference_cm = Column(Float, nullable=True)
    
    # Medical History
    diagnosed_conditions = Column(ARRAY(String), default=[], nullable=False)
    family_history_diabetes = Column(Boolean, default=False, nullable=False)
    current_medications = Column(JSON, default=[], nullable=False)
    
    # Lab Values
    hba1c_percentage = Column(Float, nullable=True)
    fasting_glucose_mmol = Column(Float, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    lab_values_date = Column(Date, nullable=True)
    
    # Lifestyle
    physical_activity_hours_week = Column(Float, nullable=True)
    sleep_hours_avg = Column(Float, nullable=True)
    stress_level = Column(Integer, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="health_profile")
    
    @property
    def bmi(self):
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None
    
    def __repr__(self):
        return f"<UserHealthProfile(user_id={self.user_id})>"


class UserPreferences(Base):
    """User's dietary and lifestyle preferences"""
    __tablename__ = "user_preferences"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Dietary
    dietary_restrictions = Column(ARRAY(String), default=[], nullable=False)
    cuisine_preferences = Column(ARRAY(String), default=[], nullable=False)
    disliked_ingredients = Column(ARRAY(String), default=[], nullable=False)
    
    # Meal Planning
    cooking_skill = Column(String(20), default="intermediate", nullable=False)
    max_cooking_time_minutes = Column(Integer, default=60, nullable=False)
    household_size = Column(Integer, default=1, nullable=False)
    
    # Health Goals
    health_goals = Column(ARRAY(String), default=[], nullable=False)
    target_daily_calories = Column(Integer, nullable=True)
    target_macros = Column(JSON, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"
