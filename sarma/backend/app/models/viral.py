"""
Viral Growth and Gamification Models
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, Index, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import enum

from app.core.database import Base


class AchievementType(str, enum.Enum):
    STREAK = "streak"
    RECIPE = "recipe"
    HEALTH = "health"
    SOCIAL = "social"
    MILESTONE = "milestone"


class SharePlatform(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    PINTEREST = "pinterest"
    EMAIL = "email"
    OTHER = "other"


class ReferralStatus(str, enum.Enum):
    PENDING = "pending"
    SIGNED_UP = "signed_up"
    CONVERTED = "converted"


class UserStreak(Base):
    """User streak tracking for daily engagement"""
    __tablename__ = "user_streaks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Current streak
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak_days: Mapped[int] = mapped_column(Integer, default=0)
    
    # Tracking
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date)
    streak_start_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Streak freeze (allowing missed days)
    freeze_count_remaining: Mapped[int] = mapped_column(Integer, default=2)  # Free streak saves
    
    # Milestones
    total_active_days: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User", back_populates="streak")
    
    __table_args__ = (
        Index('idx_streak_user', 'user_id'),
        CheckConstraint('current_streak_days >= 0', name='check_current_streak'),
        CheckConstraint('longest_streak_days >= 0', name='check_longest_streak'),
    )


class UserAchievement(Base):
    """User achievements and badges"""
    __tablename__ = "user_achievements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Achievement details
    achievement_type: Mapped[AchievementType] = mapped_column(SQLEnum(AchievementType), nullable=False)
    achievement_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., "streak_7_days"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Visual
    badge_icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    badge_color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color
    
    # Points and rewards
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)
    
    # Progress
    is_completed: Mapped[bool] = mapped_column(Boolean, default=True)
    progress_current: Mapped[Optional[int]] = mapped_column(Integer)
    progress_target: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_achievement_user', 'user_id'),
        Index('idx_achievement_type', 'achievement_type'),
        Index('idx_achievement_id_user', 'achievement_id', 'user_id', unique=True),
    )


class UserReferral(Base):
    """User referral tracking"""
    __tablename__ = "user_referrals"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    referrer_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    referred_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True
    )
    
    # Referral details
    referral_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    referred_email: Mapped[Optional[str]] = mapped_column(String(255))
    referred_phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Status tracking
    status: Mapped[ReferralStatus] = mapped_column(
        SQLEnum(ReferralStatus),
        default=ReferralStatus.PENDING,
        nullable=False
    )
    
    # Dates
    referred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    signed_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    converted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Rewards
    reward_granted_to_referrer: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_granted_to_referred: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_type: Mapped[Optional[str]] = mapped_column(String(50))  # premium_month, credits, etc.
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_user_id])
    referred = relationship("User", foreign_keys=[referred_user_id])
    
    __table_args__ = (
        Index('idx_referral_referrer', 'referrer_user_id'),
        Index('idx_referral_referred', 'referred_user_id'),
        Index('idx_referral_code', 'referral_code'),
        Index('idx_referral_status', 'status'),
    )


class SocialShare(Base):
    """Track social shares for viral growth"""
    __tablename__ = "social_shares"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Share details
    platform: Mapped[SharePlatform] = mapped_column(SQLEnum(SharePlatform), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # recipe, achievement, meal_photo
    content_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    # Tracking
    share_url: Mapped[Optional[str]] = mapped_column(String(500))
    share_text: Mapped[Optional[str]] = mapped_column(Text)
    
    # Engagement
    views: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)  # Users who signed up
    
    shared_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_share_user', 'user_id'),
        Index('idx_share_platform', 'platform'),
        Index('idx_share_content', 'content_type', 'content_id'),
    )


class Leaderboard(Base):
    """Global and friend leaderboards"""
    __tablename__ = "leaderboards"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Scoring period
    period_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # weekly, monthly, all_time
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Scores
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    recipes_tried: Mapped[int] = mapped_column(Integer, default=0)
    meals_logged: Mapped[int] = mapped_column(Integer, default=0)
    health_score_avg: Mapped[Optional[float]] = mapped_column(Float)
    
    # Ranking
    global_rank: Mapped[Optional[int]] = mapped_column(Integer)
    percentile: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    
    # Metadata
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_leaderboard_user_period', 'user_id', 'period_type', 'period_start', unique=True),
        Index('idx_leaderboard_period_rank', 'period_type', 'period_start', 'global_rank'),
        Index('idx_leaderboard_points', 'total_points'),
    )
