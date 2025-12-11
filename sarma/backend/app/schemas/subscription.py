"""
Subscription Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SubscriptionTierEnum(str, Enum):
    """Subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"


class SubscriptionStatusEnum(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class SubscriptionBase(BaseModel):
    """Base subscription schema"""
    tier: SubscriptionTierEnum = SubscriptionTierEnum.FREE
    status: SubscriptionStatusEnum = SubscriptionStatusEnum.ACTIVE


class SubscriptionResponse(SubscriptionBase):
    """Subscription response"""
    
    id: int
    user_id: int
    
    # Stripe (masked)
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Billing
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    
    # Usage
    ai_requests_this_month: int
    ai_requests_limit: int
    
    # Pricing
    amount: float
    currency: str
    
    # Computed
    is_active: bool
    is_premium: bool
    has_ai_quota: bool
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    canceled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreateCheckoutSessionRequest(BaseModel):
    """Create Stripe checkout session"""
    tier: SubscriptionTierEnum = Field(..., description="Subscription tier to purchase")
    success_url: str = Field(..., description="URL to redirect on success")
    cancel_url: str = Field(..., description="URL to redirect on cancel")


class CreateCheckoutSessionResponse(BaseModel):
    """Checkout session response"""
    session_id: str
    url: str


class CreatePortalSessionRequest(BaseModel):
    """Create Stripe customer portal session"""
    return_url: str = Field(..., description="URL to return to after portal")


class CreatePortalSessionResponse(BaseModel):
    """Portal session response"""
    url: str


class CancelSubscriptionRequest(BaseModel):
    """Cancel subscription request"""
    immediate: bool = Field(False, description="Cancel immediately or at period end")
