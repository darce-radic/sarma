"""
Subscription & Payment Models
Stripe integration for premium features
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class SubscriptionTier(str, enum.Enum):
    """Subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class Subscription(Base):
    """User subscription model"""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Subscription Details
    tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    
    # Stripe Integration
    stripe_customer_id = Column(String(255), unique=True, nullable=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    stripe_price_id = Column(String(255), nullable=True)
    
    # Billing
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    
    # Usage Tracking
    ai_requests_this_month = Column(Integer, default=0)
    ai_requests_limit = Column(Integer, default=50)  # 50 for free, unlimited for premium
    
    # Pricing
    amount = Column(Float, default=0.0)  # Monthly amount in USD
    currency = Column(String(3), default="usd")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    canceled_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, tier={self.tier}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium access"""
        return self.tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO] and self.is_active
    
    @property
    def has_ai_quota(self) -> bool:
        """Check if user has remaining AI quota"""
        if self.is_premium:
            return True  # Unlimited for premium
        return self.ai_requests_this_month < self.ai_requests_limit
    
    def increment_ai_usage(self):
        """Increment AI request counter"""
        self.ai_requests_this_month += 1


class Payment(Base):
    """Payment history"""
    
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    
    # Stripe Details
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False)
    stripe_invoice_id = Column(String(255), nullable=True)
    
    # Payment Info
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(50), nullable=False)  # succeeded, failed, pending
    
    # Description
    description = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status})>"
