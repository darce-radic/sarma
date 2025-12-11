"""
Meal Tracking and Photo Analysis Models
"""
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Index, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import enum

from app.core.database import Base


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    BEVERAGE = "beverage"
    OTHER = "other"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MealPhoto(Base):
    """AI-analyzed meal photos"""
    __tablename__ = "meal_photos"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Photo data
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # User context
    meal_type: Mapped[MealType] = mapped_column(SQLEnum(MealType), nullable=False)
    eaten_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # AI Analysis
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False
    )
    ai_description: Mapped[Optional[str]] = mapped_column(Text)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float)  # 0-1
    detected_foods: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    
    # Nutritional analysis summary
    total_calories: Mapped[Optional[float]] = mapped_column(Float)
    total_protein_g: Mapped[Optional[float]] = mapped_column(Float)
    total_carbs_g: Mapped[Optional[float]] = mapped_column(Float)
    total_fat_g: Mapped[Optional[float]] = mapped_column(Float)
    total_fiber_g: Mapped[Optional[float]] = mapped_column(Float)
    total_sodium_mg: Mapped[Optional[float]] = mapped_column(Float)
    
    # Health scoring
    health_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    glycemic_load: Mapped[Optional[float]] = mapped_column(Float)
    inflammation_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # User feedback
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_corrections: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User", back_populates="meal_photos")
    ingredients = relationship("MealPhotoIngredient", back_populates="meal_photo", cascade="all, delete-orphan")
    nutrition = relationship("MealPhotoNutrition", back_populates="meal_photo", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_meal_photo_user_date', 'user_id', 'eaten_at'),
        Index('idx_meal_photo_status', 'processing_status'),
        CheckConstraint('ai_confidence >= 0 AND ai_confidence <= 1', name='check_confidence'),
    )


class MealPhotoIngredient(Base):
    """Individual ingredients detected in meal photos"""
    __tablename__ = "meal_photo_ingredients"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    meal_photo_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meal_photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Optional[float]] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    
    # Nutritional data for this ingredient
    calories: Mapped[Optional[float]] = mapped_column(Float)
    protein_g: Mapped[Optional[float]] = mapped_column(Float)
    carbs_g: Mapped[Optional[float]] = mapped_column(Float)
    fat_g: Mapped[Optional[float]] = mapped_column(Float)
    
    # User adjustments
    user_adjusted: Mapped[bool] = mapped_column(Boolean, default=False)
    original_quantity: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meal_photo = relationship("MealPhoto", back_populates="ingredients")
    
    __table_args__ = (
        Index('idx_ingredient_meal_photo', 'meal_photo_id'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_ingredient_confidence'),
    )


class MealPhotoNutrition(Base):
    """Detailed nutritional analysis of meal photos"""
    __tablename__ = "meal_photo_nutrition"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    meal_photo_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meal_photos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Complete nutritional breakdown
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    carbohydrates_g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    fiber_g: Mapped[float] = mapped_column(Float, nullable=False)
    sugar_g: Mapped[float] = mapped_column(Float, nullable=False)
    sodium_mg: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Additional nutrients
    saturated_fat_g: Mapped[Optional[float]] = mapped_column(Float)
    cholesterol_mg: Mapped[Optional[float]] = mapped_column(Float)
    potassium_mg: Mapped[Optional[float]] = mapped_column(Float)
    calcium_mg: Mapped[Optional[float]] = mapped_column(Float)
    iron_mg: Mapped[Optional[float]] = mapped_column(Float)
    vitamin_a_iu: Mapped[Optional[float]] = mapped_column(Float)
    vitamin_c_mg: Mapped[Optional[float]] = mapped_column(Float)
    
    # Health metrics
    glycemic_index: Mapped[Optional[float]] = mapped_column(Float)
    glycemic_load: Mapped[Optional[float]] = mapped_column(Float)
    inflammation_score: Mapped[Optional[float]] = mapped_column(Float)
    health_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    meal_photo = relationship("MealPhoto", back_populates="nutrition")


class MealLog(Base):
    """Daily meal logging and tracking"""
    __tablename__ = "meal_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    log_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    meal_type: Mapped[MealType] = mapped_column(SQLEnum(MealType), nullable=False)
    
    # Meal details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Link to recipe if used
    recipe_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="SET NULL")
    )
    
    # Link to meal photo if analyzed
    meal_photo_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meal_photos.id", ondelete="SET NULL")
    )
    
    # Nutritional totals
    total_calories: Mapped[float] = mapped_column(Float, nullable=False)
    total_protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    total_carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    total_fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    
    # User notes
    notes: Mapped[Optional[str]] = mapped_column(Text)
    satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    recipe = relationship("Recipe")
    meal_photo = relationship("MealPhoto")
    items = relationship("MealLogItem", back_populates="meal_log", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_meal_log_user_date', 'user_id', 'log_date'),
        Index('idx_meal_log_type', 'meal_type'),
        CheckConstraint('total_calories >= 0', name='check_meal_log_calories'),
    )


class MealLogItem(Base):
    """Individual items in a meal log entry"""
    __tablename__ = "meal_log_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    meal_log_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("meal_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Nutritional data
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meal_log = relationship("MealLog", back_populates="items")
    
    __table_args__ = (
        Index('idx_meal_item_log', 'meal_log_id'),
        CheckConstraint('quantity > 0', name='check_item_quantity'),
    )
