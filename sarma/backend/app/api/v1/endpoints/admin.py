from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.ai_request import AIRequest
from app.models.system_setting import SystemSetting
from app.schemas.system_setting import SystemSettingsPayload, SystemSettingsResponse

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require admin role.
    """
    # TODO: Add is_admin field to User model
    # For now, check if email is admin email
    if current_user.email != "admin@sarma.app":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


KEY_MAP = {
    "openai_api_key": "OPENAI_API_KEY",
    "gemini_api_key": "GEMINI_API_KEY",
    "spoonacular_api_key": "SPOONACULAR_API_KEY",
    "stripe_secret_key": "STRIPE_SECRET_KEY",
    "coles_woolworths_mcp_url": "COLES_WOOLWORTHS_MCP_URL",
}


async def _load_settings(db: AsyncSession) -> dict:
    rows = (await db.execute(select(SystemSetting))).scalars().all()
    return {row.key: row.value for row in rows}


async def _save_settings(db: AsyncSession, settings: dict) -> None:
    existing = await db.execute(select(SystemSetting).where(SystemSetting.key.in_(list(settings.keys()))))
    existing_map = {row.key: row for row in existing.scalars().all()}
    for key, value in settings.items():
        if key in existing_map:
            existing_map[key].value = value
        else:
            db.add(SystemSetting(key=key, value=value))
    await db.commit()


@router.get("/system-settings", response_model=SystemSettingsResponse)
async def get_system_settings(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stored = await _load_settings(db)
    # Only return known keys to avoid leaking unrelated settings
    response = {}
    for field, db_key in KEY_MAP.items():
        response[field] = stored.get(db_key)
    return response


@router.put("/system-settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    payload: SystemSettingsPayload,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    updates = {}
    for field, db_key in KEY_MAP.items():
        value = getattr(payload, field)
        if value is not None:
            updates[db_key] = value
    if not updates:
        return await get_system_settings(admin, db)  # type: ignore

    await _save_settings(db, updates)
    return await get_system_settings(admin, db)  # type: ignore


@router.get("/stats")
async def get_admin_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive admin statistics.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # User statistics
    total_users_query = select(func.count(User.id))
    total_users = (await db.execute(total_users_query)).scalar()

    active_today_query = select(func.count(User.id)).where(
        User.last_login >= today_start
    )
    active_today = (await db.execute(active_today_query)).scalar() or 0

    # Subscription breakdown
    free_query = select(func.count(User.id)).where(User.subscription_tier == "free")
    free_count = (await db.execute(free_query)).scalar() or 0

    premium_query = select(func.count(User.id)).where(User.subscription_tier == "premium")
    premium_count = (await db.execute(premium_query)).scalar() or 0

    pro_query = select(func.count(User.id)).where(User.subscription_tier == "pro")
    pro_count = (await db.execute(pro_query)).scalar() or 0

    # Revenue statistics
    revenue_today_query = select(func.sum(Payment.amount)).where(
        Payment.created_at >= today_start,
        Payment.status == "succeeded"
    )
    revenue_today = (await db.execute(revenue_today_query)).scalar() or 0

    revenue_month_query = select(func.sum(Payment.amount)).where(
        Payment.created_at >= month_start,
        Payment.status == "succeeded"
    )
    revenue_month = (await db.execute(revenue_month_query)).scalar() or 0

    revenue_total_query = select(func.sum(Payment.amount)).where(
        Payment.status == "succeeded"
    )
    revenue_total = (await db.execute(revenue_total_query)).scalar() or 0

    # AI Usage statistics
    ai_today_query = select(func.count(AIRequest.id)).where(
        AIRequest.created_at >= today_start
    )
    ai_today = (await db.execute(ai_today_query)).scalar() or 0

    ai_month_query = select(func.count(AIRequest.id)).where(
        AIRequest.created_at >= month_start
    )
    ai_month = (await db.execute(ai_month_query)).scalar() or 0

    ai_cost_query = select(func.sum(AIRequest.cost)).where(
        AIRequest.created_at >= month_start
    )
    ai_cost = (await db.execute(ai_cost_query)).scalar() or 0

    # System health (placeholder - would come from monitoring service)
    uptime = "99.9%"  # TODO: Get from monitoring
    db_size = "2.4 GB"  # TODO: Get actual DB size
    api_response_time = 145  # milliseconds - TODO: Get from monitoring

    return {
        "total_users": total_users,
        "active_users_today": active_today,
        "total_subscriptions": {
            "free": free_count,
            "premium": premium_count,
            "pro": pro_count,
        },
        "revenue": {
            "today": float(revenue_today),
            "this_month": float(revenue_month),
            "total": float(revenue_total),
        },
        "ai_usage": {
            "requests_today": ai_today,
            "requests_this_month": ai_month,
            "total_cost": float(ai_cost),
        },
        "system": {
            "uptime": uptime,
            "database_size": db_size,
            "api_response_time": api_response_time,
        },
    }


@router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of all users with their subscription info.
    """
    query = select(User).offset(skip).limit(limit)
    users = (await db.execute(query)).scalars().all()

    result = []
    for user in users:
        # Get AI request count
        ai_count_query = select(func.count(AIRequest.id)).where(
            AIRequest.user_id == user.id
        )
        ai_count = (await db.execute(ai_count_query)).scalar() or 0

        result.append({
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "subscription_tier": user.subscription_tier,
            "subscription_status": user.subscription_status,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "ai_requests_count": ai_count,
        })

    return result


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific user.
    """
    query = select(User).where(User.id == user_id)
    user = (await db.execute(query)).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get subscription info
    sub_query = select(Subscription).where(Subscription.user_id == user.id)
    subscription = (await db.execute(sub_query)).scalar_one_or_none()

    # Get AI usage
    ai_query = select(AIRequest).where(AIRequest.user_id == user.id)
    ai_requests = (await db.execute(ai_query)).scalars().all()

    # Get payments
    payment_query = select(Payment).where(Payment.user_id == user.id)
    payments = (await db.execute(payment_query)).scalars().all()

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "subscription_tier": user.subscription_tier,
            "subscription_status": user.subscription_status,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
        "subscription": {
            "id": str(subscription.id),
            "tier": subscription.tier,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end.isoformat()
            if subscription.current_period_end
            else None,
        } if subscription else None,
        "ai_usage": {
            "total_requests": len(ai_requests),
            "total_cost": sum(req.cost for req in ai_requests if req.cost),
            "by_provider": {
                "gemini": sum(1 for req in ai_requests if req.provider == "gemini"),
                "openai": sum(1 for req in ai_requests if req.provider == "openai"),
            },
        },
        "payments": [
            {
                "id": str(payment.id),
                "amount": float(payment.amount),
                "status": payment.status,
                "created_at": payment.created_at.isoformat(),
            }
            for payment in payments
        ],
    }


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Suspend a user account.
    """
    query = select(User).where(User.id == user_id)
    user = (await db.execute(query)).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await db.commit()

    return {"message": "User suspended successfully"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a suspended user account.
    """
    query = select(User).where(User.id == user_id)
    user = (await db.execute(query)).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    await db.commit()

    return {"message": "User activated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user account (soft delete).
    """
    query = select(User).where(User.id == user_id)
    user = (await db.execute(query)).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Soft delete
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    await db.commit()

    return {"message": "User deleted successfully"}


@router.get("/metrics")
async def get_system_metrics(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed system metrics for monitoring.
    """
    # TODO: Integrate with monitoring service (Sentry, Datadog, etc.)
    return {
        "cpu_usage": "45%",
        "memory_usage": "67%",
        "disk_usage": "32%",
        "api_requests_per_minute": 150,
        "error_rate": "0.02%",
        "average_response_time": 145,
    }
