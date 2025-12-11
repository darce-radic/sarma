"""
Stripe Payment Service
Handle subscriptions, checkouts, and webhooks
"""

import os
import stripe
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.user import User
from ..models.subscription import Subscription, SubscriptionTier, SubscriptionStatus, Payment


# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class StripeService:
    """Stripe payment service"""
    
    # Pricing (configure these in Stripe Dashboard and update here)
    PRICE_IDS = {
        SubscriptionTier.PREMIUM: os.getenv("STRIPE_PREMIUM_PRICE_ID", "price_premium"),
        SubscriptionTier.PRO: os.getenv("STRIPE_PRO_PRICE_ID", "price_pro"),
    }
    
    PRICES = {
        SubscriptionTier.FREE: 0.00,
        SubscriptionTier.PREMIUM: 9.99,
        SubscriptionTier.PRO: 19.99,
    }
    
    @staticmethod
    async def get_or_create_customer(user: User, db: AsyncSession) -> str:
        """
        Get or create Stripe customer for user
        
        Args:
            user: User model
            db: Database session
            
        Returns:
            Stripe customer ID
        """
        # Check if user has subscription with customer ID
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription and subscription.stripe_customer_id:
            return subscription.stripe_customer_id
        
        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}" if hasattr(user, 'first_name') else user.email,
            metadata={
                "user_id": str(user.id)
            }
        )
        
        # Save customer ID
        if not subscription:
            subscription = Subscription(
                user_id=user.id,
                stripe_customer_id=customer.id
            )
            db.add(subscription)
        else:
            subscription.stripe_customer_id = customer.id
        
        await db.commit()
        
        return customer.id
    
    @staticmethod
    async def create_checkout_session(
        user: User,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
        db: AsyncSession
    ) -> Dict:
        """
        Create Stripe checkout session for subscription
        
        Args:
            user: User purchasing subscription
            tier: Subscription tier to purchase
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            db: Database session
            
        Returns:
            Dict with session_id and url
        """
        if tier == SubscriptionTier.FREE:
            raise ValueError("Cannot create checkout for free tier")
        
        # Get or create customer
        customer_id = await StripeService.get_or_create_customer(user, db)
        
        # Get price ID
        price_id = StripeService.PRICE_IDS.get(tier)
        if not price_id:
            raise ValueError(f"No price ID configured for tier: {tier}")
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user.id),
                "tier": tier.value
            },
            subscription_data={
                "metadata": {
                    "user_id": str(user.id),
                    "tier": tier.value
                }
            }
        )
        
        return {
            "session_id": session.id,
            "url": session.url
        }
    
    @staticmethod
    async def create_portal_session(
        user: User,
        return_url: str,
        db: AsyncSession
    ) -> Dict:
        """
        Create Stripe customer portal session
        
        Args:
            user: Current user
            return_url: URL to return to after portal
            db: Database session
            
        Returns:
            Dict with portal url
        """
        # Get customer ID
        customer_id = await StripeService.get_or_create_customer(user, db)
        
        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        
        return {"url": session.url}
    
    @staticmethod
    async def handle_checkout_completed(
        session: Dict,
        db: AsyncSession
    ):
        """
        Handle successful checkout
        
        Args:
            session: Stripe checkout session
            db: Database session
        """
        user_id = int(session["metadata"]["user_id"])
        tier = SubscriptionTier(session["metadata"]["tier"])
        
        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            subscription = Subscription(user_id=user_id)
            db.add(subscription)
        
        # Update subscription
        subscription.tier = tier
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.stripe_subscription_id = session["subscription"]
        subscription.amount = StripeService.PRICES[tier]
        
        # Get subscription details from Stripe
        stripe_subscription = stripe.Subscription.retrieve(session["subscription"])
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_subscription.current_period_start
        )
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription.current_period_end
        )
        
        # Set limits
        if tier == SubscriptionTier.PREMIUM:
            subscription.ai_requests_limit = 999999  # Unlimited
        elif tier == SubscriptionTier.PRO:
            subscription.ai_requests_limit = 999999  # Unlimited
        
        await db.commit()
    
    @staticmethod
    async def handle_subscription_updated(
        subscription_data: Dict,
        db: AsyncSession
    ):
        """
        Handle subscription update webhook
        
        Args:
            subscription_data: Stripe subscription object
            db: Database session
        """
        stripe_subscription_id = subscription_data["id"]
        
        # Find subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return
        
        # Update status
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "canceled": SubscriptionStatus.CANCELED,
            "past_due": SubscriptionStatus.PAST_DUE,
            "trialing": SubscriptionStatus.TRIALING,
            "incomplete": SubscriptionStatus.INCOMPLETE,
        }
        subscription.status = status_map.get(
            subscription_data["status"],
            SubscriptionStatus.ACTIVE
        )
        
        # Update billing period
        subscription.current_period_start = datetime.fromtimestamp(
            subscription_data["current_period_start"]
        )
        subscription.current_period_end = datetime.fromtimestamp(
            subscription_data["current_period_end"]
        )
        
        await db.commit()
    
    @staticmethod
    async def handle_subscription_deleted(
        subscription_data: Dict,
        db: AsyncSession
    ):
        """
        Handle subscription cancellation
        
        Args:
            subscription_data: Stripe subscription object
            db: Database session
        """
        stripe_subscription_id = subscription_data["id"]
        
        # Find subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return
        
        # Downgrade to free
        subscription.tier = SubscriptionTier.FREE
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.utcnow()
        subscription.ai_requests_limit = 50
        
        await db.commit()
    
    @staticmethod
    async def handle_payment_succeeded(
        payment_intent: Dict,
        db: AsyncSession
    ):
        """
        Handle successful payment
        
        Args:
            payment_intent: Stripe payment intent
            db: Database session
        """
        # Get invoice ID
        invoice_id = payment_intent.get("invoice")
        if not invoice_id:
            return
        
        # Get invoice
        invoice = stripe.Invoice.retrieve(invoice_id)
        
        # Find subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == invoice.subscription
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return
        
        # Record payment
        payment = Payment(
            subscription_id=subscription.id,
            stripe_payment_intent_id=payment_intent["id"],
            stripe_invoice_id=invoice_id,
            amount=payment_intent["amount"] / 100,  # Convert cents to dollars
            currency=payment_intent["currency"],
            status="succeeded",
            paid_at=datetime.fromtimestamp(payment_intent["created"])
        )
        
        db.add(payment)
        await db.commit()
    
    @staticmethod
    async def cancel_subscription(
        user: User,
        immediate: bool,
        db: AsyncSession
    ) -> Dict:
        """
        Cancel user's subscription
        
        Args:
            user: User canceling subscription
            immediate: Cancel immediately or at period end
            db: Database session
            
        Returns:
            Dict with cancellation details
        """
        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription or not subscription.stripe_subscription_id:
            raise ValueError("No active subscription found")
        
        # Cancel in Stripe
        if immediate:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            
            # Update local subscription
            subscription.tier = SubscriptionTier.FREE
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.utcnow()
            subscription.ai_requests_limit = 50
        else:
            # Cancel at period end
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "canceled": True,
            "immediate": immediate,
            "access_until": subscription.current_period_end if not immediate else None
        }
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Dict:
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Request body
            sig_header: Stripe signature header
            
        Returns:
            Verified event data
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")
