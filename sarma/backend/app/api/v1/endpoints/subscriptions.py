"""
Subscription & Payment Endpoints
Stripe integration for premium features
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ....core.database import get_db
from ....core.security import get_current_user
from ....models.user import User
from ....models.subscription import Subscription, SubscriptionTier
from ....schemas.subscription import (
    SubscriptionResponse,
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    CreatePortalSessionRequest,
    CreatePortalSessionResponse,
    CancelSubscriptionRequest
)
from ....services.stripe_service import StripeService

router = APIRouter()


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's subscription details
    """
    # Get or create subscription
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        # Create free tier subscription
        subscription = Subscription(
            user_id=current_user.id,
            tier=SubscriptionTier.FREE
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
    
    # Convert to response model
    response = SubscriptionResponse.model_validate(subscription)
    
    # Add computed properties
    response.is_active = subscription.is_active
    response.is_premium = subscription.is_premium
    response.has_ai_quota = subscription.has_ai_quota
    
    return response


@router.post("/checkout", response_model=CreateCheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create Stripe checkout session for subscription upgrade
    
    - **tier**: Subscription tier to purchase (premium or pro)
    - **success_url**: URL to redirect on successful payment
    - **cancel_url**: URL to redirect if user cancels
    
    Returns checkout session URL for redirect
    """
    try:
        result = await StripeService.create_checkout_session(
            user=current_user,
            tier=request.tier,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            db=db
        )
        
        return CreateCheckoutSessionResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/portal", response_model=CreatePortalSessionResponse)
async def create_portal_session(
    request: CreatePortalSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create Stripe customer portal session
    
    Users can manage their subscription, update payment methods, view invoices
    
    - **return_url**: URL to return to after portal
    
    Returns portal URL for redirect
    """
    try:
        result = await StripeService.create_portal_session(
            user=current_user,
            return_url=request.return_url,
            db=db
        )
        
        return CreatePortalSessionResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create portal session: {str(e)}"
        )


@router.post("/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel current subscription
    
    - **immediate**: If true, cancel immediately. If false, cancel at period end.
    
    Returns cancellation confirmation
    """
    try:
        result = await StripeService.cancel_subscription(
            user=current_user,
            immediate=request.immediate,
            db=db
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.get("/usage")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current usage statistics
    
    Returns AI request usage for current billing period
    """
    # Get subscription
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        return {
            "ai_requests_used": 0,
            "ai_requests_limit": 50,
            "ai_requests_remaining": 50,
            "percentage_used": 0,
            "tier": "free"
        }
    
    remaining = max(0, subscription.ai_requests_limit - subscription.ai_requests_this_month)
    percentage = (subscription.ai_requests_this_month / subscription.ai_requests_limit * 100) if subscription.ai_requests_limit > 0 else 0
    
    return {
        "ai_requests_used": subscription.ai_requests_this_month,
        "ai_requests_limit": subscription.ai_requests_limit,
        "ai_requests_remaining": remaining,
        "percentage_used": round(percentage, 1),
        "tier": subscription.tier.value,
        "is_premium": subscription.is_premium,
        "has_quota": subscription.has_ai_quota
    }


@router.post("/webhooks")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Stripe webhook handler
    
    Handles events:
    - checkout.session.completed
    - customer.subscription.updated
    - customer.subscription.deleted
    - payment_intent.succeeded
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    # Get raw body
    payload = await request.body()
    
    try:
        # Verify webhook signature
        event = StripeService.verify_webhook_signature(payload, stripe_signature)
        
        # Handle different event types
        event_type = event["type"]
        
        if event_type == "checkout.session.completed":
            await StripeService.handle_checkout_completed(event["data"]["object"], db)
        
        elif event_type == "customer.subscription.updated":
            await StripeService.handle_subscription_updated(event["data"]["object"], db)
        
        elif event_type == "customer.subscription.deleted":
            await StripeService.handle_subscription_deleted(event["data"]["object"], db)
        
        elif event_type == "payment_intent.succeeded":
            await StripeService.handle_payment_succeeded(event["data"]["object"], db)
        
        return {"status": "success", "event_type": event_type}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/tiers")
async def get_subscription_tiers():
    """
    Get available subscription tiers with pricing
    """
    return {
        "tiers": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "50 AI meal analyses per month",
                    "Gemini AI (fast & accurate)",
                    "Basic meal tracking",
                    "Recipe browsing",
                    "Health dashboard",
                    "Mobile app access"
                ],
                "ai_limit": 50,
                "ai_provider": "gemini-flash"
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 9.99,
                "currency": "usd",
                "interval": "month",
                "popular": True,
                "features": [
                    "Unlimited AI meal analyses",
                    "GPT-4 Vision (premium quality)",
                    "AI recipe generation",
                    "Health chat assistant",
                    "Diet trend analysis",
                    "Advanced analytics",
                    "Priority support",
                    "Ad-free experience"
                ],
                "ai_limit": 999999,
                "ai_provider": "gpt4-vision"
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 19.99,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Everything in Premium",
                    "API access for integrations",
                    "Custom AI model training",
                    "White-label options",
                    "Dedicated support",
                    "Early access to features",
                    "Data export (CSV, JSON)",
                    "Team collaboration (coming soon)"
                ],
                "ai_limit": 999999,
                "ai_provider": "gpt4-vision"
            }
        ]
    }
