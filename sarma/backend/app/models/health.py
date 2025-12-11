"""
Health Assessment and Tracking Models
"""
from datetime import datetime, date
from typing import Optional, List, Dict
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, Index, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import enum

from app.core.database import Base


class AssessmentStatus(str, enum.Enum):
    INCOMPLETE = "incomplete"
    COMPLETED = "completed"
    EXPIRED = "expired"


class PriorityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealthAssessment(Base):
    """Comprehensive health assessments and risk analysis"""
    __tablename__ = "health_assessments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    assessment_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[AssessmentStatus] = mapped_column(
        SQLEnum(AssessmentStatus),
        default=AssessmentStatus.INCOMPLETE,
        nullable=False
    )
    
    # User-provided health data
    current_conditions: Mapped[Optional[List[str]]] = mapped_column(JSONB)  # ["Type 2 Diabetes", "Hypertension"]
    medications: Mapped[Optional[List[dict]]] = mapped_column(JSONB)
    allergies: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    family_history: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    
    # Current metrics
    weight_lbs: Mapped[Optional[float]] = mapped_column(Float)
    height_inches: Mapped[Optional[float]] = mapped_column(Float)
    bmi: Mapped[Optional[float]] = mapped_column(Float)
    
    # Lab results
    hba1c: Mapped[Optional[float]] = mapped_column(Float)
    fasting_glucose_mg_dl: Mapped[Optional[float]] = mapped_column(Float)
    total_cholesterol_mg_dl: Mapped[Optional[float]] = mapped_column(Float)
    ldl_cholesterol_mg_dl: Mapped[Optional[float]] = mapped_column(Float)
    hdl_cholesterol_mg_dl: Mapped[Optional[float]] = mapped_column(Float)
    triglycerides_mg_dl: Mapped[Optional[float]] = mapped_column(Float)
    blood_pressure_systolic: Mapped[Optional[int]] = mapped_column(Integer)
    blood_pressure_diastolic: Mapped[Optional[int]] = mapped_column(Integer)
    
    # AI-generated insights
    risk_scores: Mapped[Optional[dict]] = mapped_column(JSONB)  # cardiovascular, diabetes, etc.
    personalized_recommendations: Mapped[Optional[List[dict]]] = mapped_column(JSONB)
    dietary_restrictions: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    
    # Goals generated from assessment
    target_calories_daily: Mapped[Optional[int]] = mapped_column(Integer)
    target_protein_g: Mapped[Optional[float]] = mapped_column(Float)
    target_carbs_g: Mapped[Optional[float]] = mapped_column(Float)
    target_fat_g: Mapped[Optional[float]] = mapped_column(Float)
    target_sodium_mg: Mapped[Optional[float]] = mapped_column(Float)
    target_sugar_g: Mapped[Optional[float]] = mapped_column(Float)
    
    # Next assessment due
    next_assessment_due: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User", back_populates="health_assessments")
    
    __table_args__ = (
        Index('idx_assessment_user_date', 'user_id', 'assessment_date'),
        Index('idx_assessment_status', 'status'),
        CheckConstraint('weight_lbs > 0', name='check_weight'),
        CheckConstraint('height_inches > 0', name='check_height'),
        CheckConstraint('bmi > 0', name='check_bmi'),
    )


class HealthMetric(Base):
    """Time-series health metrics tracking"""
    __tablename__ = "health_metrics"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # weight, glucose, blood_pressure
    
    # Generic value storage
    value: Mapped[float] = mapped_column(Float, nullable=False)
    value_secondary: Mapped[Optional[float]] = mapped_column(Float)  # For blood pressure diastolic
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Context
    notes: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="manual")  # manual, device, lab
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_metric_user_type_date', 'user_id', 'metric_type', 'recorded_at'),
    )


class BiometricReading(Base):
    """Biometric data from wearables and devices"""
    __tablename__ = "biometric_readings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Vitals
    heart_rate_bpm: Mapped[Optional[int]] = mapped_column(Integer)
    blood_pressure_systolic: Mapped[Optional[int]] = mapped_column(Integer)
    blood_pressure_diastolic: Mapped[Optional[int]] = mapped_column(Integer)
    blood_oxygen_percent: Mapped[Optional[float]] = mapped_column(Float)
    temperature_f: Mapped[Optional[float]] = mapped_column(Float)
    
    # Activity
    steps: Mapped[Optional[int]] = mapped_column(Integer)
    calories_burned: Mapped[Optional[int]] = mapped_column(Integer)
    active_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Sleep
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float)
    sleep_quality_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Device info
    device_type: Mapped[Optional[str]] = mapped_column(String(100))
    device_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_biometric_user_date', 'user_id', 'recorded_at'),
    )


class LabResult(Base):
    """Laboratory test results"""
    __tablename__ = "lab_results"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    test_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Result data
    result_value: Mapped[float] = mapped_column(Float, nullable=False)
    result_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_range_low: Mapped[Optional[float]] = mapped_column(Float)
    reference_range_high: Mapped[Optional[float]] = mapped_column(Float)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Context
    ordering_provider: Mapped[Optional[str]] = mapped_column(String(255))
    lab_name: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_lab_user_date', 'user_id', 'test_date'),
        Index('idx_lab_test_name', 'test_name'),
    )


class Medication(Base):
    """User medications tracking"""
    __tablename__ = "medications"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)  # daily, twice daily, etc.
    
    # Schedule
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Purpose and notes
    purpose: Mapped[Optional[str]] = mapped_column(String(500))
    prescribing_doctor: Mapped[Optional[str]] = mapped_column(String(255))
    pharmacy: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Reminders
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_times: Mapped[Optional[List[str]]] = mapped_column(JSONB)  # ["08:00", "20:00"]
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_medication_user', 'user_id'),
        Index('idx_medication_active', 'is_active'),
    )


class HealthGoal(Base):
    """User health goals and targets"""
    __tablename__ = "health_goals"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    goal_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # weight_loss, hba1c, exercise
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Target values
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Timeline
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Progress tracking
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    milestones: Mapped[Optional[List[dict]]] = mapped_column(JSONB)
    
    # Priority and status
    priority: Mapped[PriorityLevel] = mapped_column(SQLEnum(PriorityLevel), default=PriorityLevel.MEDIUM)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_goal_user_type', 'user_id', 'goal_type'),
        Index('idx_goal_active', 'is_active'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='check_progress'),
    )


class HealthInsight(Base):
    """AI-generated health insights and recommendations"""
    __tablename__ = "health_insights"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # nutrition, trend, alert
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Priority and actionability
    priority: Mapped[PriorityLevel] = mapped_column(SQLEnum(PriorityLevel), default=PriorityLevel.MEDIUM)
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=False)
    action_items: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    
    # Data supporting the insight
    supporting_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # User interaction
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_insight_user_date', 'user_id', 'generated_at'),
        Index('idx_insight_type', 'insight_type'),
        Index('idx_insight_priority', 'priority'),
    )
