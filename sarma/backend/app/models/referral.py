"""
Referral and Viral Loop Models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Referral(Base):
    """Referral tracking model"""
    __tablename__ = "referrals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Referrer (user who shares)
    referrer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referrer = relationship("User", foreign_keys=[referrer_id], backref="referrals_made")
    
    # Referee (user who signs up via referral)
    referee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    referee = relationship("User", foreign_keys=[referee_id], backref="referred_by_relation")
    
    # Referral code
    code = Column(String(20), unique=True, nullable=False, index=True)
    
    # Referee email (before signup)
    referee_email = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, completed, rewarded
    
    # Rewards
    referrer_reward = Column(Float, default=0.0)  # Credits or discount
    referee_reward = Column(Float, default=0.0)
    
    # Tracking
    clicked_at = Column(DateTime, nullable=True)
    signed_up_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)  # When referee subscribes
    
    # Metadata
    source = Column(String(50), nullable=True)  # email, social, link, etc.
    campaign = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReferralReward(Base):
    """Track rewards given to users"""
    __tablename__ = "referral_rewards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="referral_rewards")
    
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id"), nullable=False)
    referral = relationship("Referral", backref="rewards")
    
    # Reward details
    reward_type = Column(String(50), nullable=False)  # credits, discount, premium_days, etc.
    reward_value = Column(Float, nullable=False)  # Amount of reward
    
    # Status
    is_claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime, nullable=True)
    
    # Expiry
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SocialShare(Base):
    """Track social media shares"""
    __tablename__ = "social_shares"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="social_shares")
    
    # Share details
    platform = Column(String(50), nullable=False)  # facebook, twitter, instagram, etc.
    share_type = Column(String(50), nullable=False)  # recipe, meal, achievement, etc.
    content_id = Column(UUID(as_uuid=True), nullable=True)  # ID of shared content
    
    # Tracking
    share_url = Column(String(500), nullable=True)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)  # How many signups from this share
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ViralMilestone(Base):
    """Track user achievements that can be shared"""
    __tablename__ = "viral_milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="viral_milestones")
    
    # Milestone details
    milestone_type = Column(String(50), nullable=False)  # weight_lost, meals_logged, streak, etc.
    milestone_value = Column(Float, nullable=False)  # 5kg, 100 meals, 30 days, etc.
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Sharing
    is_shared = Column(Boolean, default=False)
    shared_at = Column(DateTime, nullable=True)
    share_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
