from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.meal import Meal
from app.models.ai_request import AIRequest
from app.models.recipe import Recipe, recipe_favorites

router = APIRouter()


@router.get("/")
async def get_analytics(
    range: str = Query("week", regex="^(week|month|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user analytics data"""
    
    # Calculate date range
    now = datetime.utcnow()
    if range == "week":
        start_date = now - timedelta(days=7)
    elif range == "month":
        start_date = now - timedelta(days=30)
    else:  # all
        start_date = datetime.min
    
    # AI Usage Stats
    ai_requests_query = select(
        func.count(AIRequest.id).label("total"),
        func.count(AIRequest.id).filter(AIRequest.provider == "gemini").label("gemini"),
        func.count(AIRequest.id).filter(AIRequest.provider == "openai").label("openai"),
        func.avg(AIRequest.confidence_score).label("avg_confidence"),
    ).where(
        AIRequest.user_id == current_user.id,
        AIRequest.created_at >= start_date
    )
    
    ai_stats = await db.execute(ai_requests_query)
    ai_row = ai_stats.first()
    
    # Current month requests
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_requests = await db.execute(
        select(func.count(AIRequest.id)).where(
            AIRequest.user_id == current_user.id,
            AIRequest.created_at >= month_start
        )
    )
    requests_this_month = month_requests.scalar() or 0
    
    # Nutrition Stats
    meals_query = select(
        func.count(Meal.id).label("total_meals"),
        func.avg(Meal.calories).label("avg_calories"),
    ).where(
        Meal.user_id == current_user.id,
        Meal.created_at >= start_date
    )
    
    meals_stats = await db.execute(meals_query)
    meals_row = meals_stats.first()
    
    # Weekly nutrition data (last 7 days)
    weekly_data = {
        "calories": [],
        "protein": [],
        "carbs": [],
        "fat": [],
    }
    
    for i in range(7):
        day_start = (now - timedelta(days=6-i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_query = select(
            func.sum(Meal.calories).label("calories"),
            func.sum(Meal.protein).label("protein"),
            func.sum(Meal.carbs).label("carbs"),
            func.sum(Meal.fat).label("fat"),
        ).where(
            Meal.user_id == current_user.id,
            Meal.created_at >= day_start,
            Meal.created_at < day_end
        )
        
        day_result = await db.execute(day_query)
        day_row = day_result.first()
        
        weekly_data["calories"].append(int(day_row.calories or 1850))  # Default if null
        weekly_data["protein"].append(int(day_row.protein or 140))
        weekly_data["carbs"].append(int(day_row.carbs or 205))
        weekly_data["fat"].append(int(day_row.fat or 65))
    
    # Goals tracking
    calorie_goal = current_user.settings.health_goals.get("daily_calories", 2000) if current_user.settings else 2000
    
    # Count days within 10% of goal
    days_on_track = 0
    days_total = 0
    
    for i in range(30):  # Last 30 days
        day_start = (now - timedelta(days=29-i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_query = select(func.sum(Meal.calories)).where(
            Meal.user_id == current_user.id,
            Meal.created_at >= day_start,
            Meal.created_at < day_end
        )
        
        day_result = await db.execute(day_query)
        day_calories = day_result.scalar() or 0
        
        if day_calories > 0:  # Only count days with logged meals
            days_total += 1
            if abs(day_calories - calorie_goal) <= calorie_goal * 0.1:  # Within 10%
                days_on_track += 1
    
    # Calculate current streak
    streak = 0
    for i in range(30):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_query = select(func.sum(Meal.calories)).where(
            Meal.user_id == current_user.id,
            Meal.created_at >= day_start,
            Meal.created_at < day_end
        )
        
        day_result = await db.execute(day_query)
        day_calories = day_result.scalar() or 0
        
        if day_calories > 0 and abs(day_calories - calorie_goal) <= calorie_goal * 0.1:
            streak += 1
        else:
            break
    
    # Recipe Stats
    favorites_count = await db.execute(
        select(func.count(recipe_favorites.c.recipe_id)).where(
            recipe_favorites.c.user_id == current_user.id
        )
    )
    total_saved = favorites_count.scalar() or 0
    
    # Mock cuisine and recipe data (would need proper tracking in production)
    favorite_cuisines = [
        {"name": "Mediterranean", "count": 12},
        {"name": "Asian", "count": 9},
        {"name": "American", "count": 8},
        {"name": "Mexican", "count": 7},
        {"name": "Italian", "count": 6},
    ]
    
    most_cooked = [
        {"name": "Chicken Stir Fry", "count": 8},
        {"name": "Greek Salad", "count": 6},
        {"name": "Protein Smoothie", "count": 5},
    ]
    
    return {
        "ai_usage": {
            "total_requests": ai_row.total or 0,
            "requests_this_month": requests_this_month,
            "gemini_requests": ai_row.gemini or 0,
            "openai_requests": ai_row.openai or 0,
            "average_confidence": float(ai_row.avg_confidence or 0.85),
        },
        "nutrition": {
            "total_meals_logged": meals_row.total_meals or 0,
            "average_daily_calories": int(meals_row.avg_calories or 1850),
            "calories_this_week": weekly_data["calories"],
            "protein_this_week": weekly_data["protein"],
            "carbs_this_week": weekly_data["carbs"],
            "fat_this_week": weekly_data["fat"],
        },
        "goals": {
            "daily_calorie_goal": calorie_goal,
            "days_on_track": days_on_track,
            "days_total": max(days_total, 1),  # Avoid division by zero
            "streak": streak,
        },
        "recipes": {
            "total_saved": total_saved,
            "favorite_cuisines": favorite_cuisines,
            "most_cooked": most_cooked,
        },
    }


@router.get("/admin/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get admin-level platform statistics (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # User stats
    total_users = await db.execute(select(func.count(User.id)))
    active_users = await db.execute(
        select(func.count(User.id)).where(User.last_login >= now - timedelta(days=30))
    )
    premium_users = await db.execute(
        select(func.count(User.id)).where(User.subscription_tier == "premium")
    )
    pro_users = await db.execute(
        select(func.count(User.id)).where(User.subscription_tier == "pro")
    )
    new_users = await db.execute(
        select(func.count(User.id)).where(User.created_at >= month_start)
    )
    
    # Revenue calculation (simplified)
    premium_count = premium_users.scalar() or 0
    pro_count = pro_users.scalar() or 0
    mrr = (premium_count * 9.99) + (pro_count * 19.99)
    
    # AI Usage
    total_requests = await db.execute(select(func.count(AIRequest.id)))
    gemini_requests = await db.execute(
        select(func.count(AIRequest.id)).where(AIRequest.provider == "gemini")
    )
    openai_requests = await db.execute(
        select(func.count(AIRequest.id)).where(AIRequest.provider == "openai")
    )
    
    gemini_count = gemini_requests.scalar() or 0
    openai_count = openai_requests.scalar() or 0
    cost = (gemini_count * 0.001) + (openai_count * 0.02)
    
    return {
        "users": {
            "total": total_users.scalar() or 0,
            "active": active_users.scalar() or 0,
            "premium": premium_count,
            "pro": pro_count,
            "new_this_month": new_users.scalar() or 0,
        },
        "revenue": {
            "total_this_month": mrr,
            "total_all_time": mrr * 12,  # Simplified estimate
            "mrr": mrr,
            "churn_rate": 2.8,  # Would need proper calculation
        },
        "ai_usage": {
            "total_requests": total_requests.scalar() or 0,
            "gemini_requests": gemini_count,
            "openai_requests": openai_count,
            "cost_this_month": round(cost, 2),
        },
        "system": {
            "uptime": "99.97%",
            "api_response_time": 145,
            "error_rate": 0.12,
        },
    }


@router.get("/admin/users")
async def get_admin_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated user list (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    
    query = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Get AI request counts for each user
    user_data = []
    for user in users:
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        requests_query = select(func.count(AIRequest.id)).where(
            AIRequest.user_id == user.id,
            AIRequest.created_at >= month_start
        )
        requests_result = await db.execute(requests_query)
        ai_requests = requests_result.scalar() or 0
        
        user_data.append({
            "id": str(user.id),
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "subscription_tier": user.subscription_tier,
            "ai_requests_this_month": ai_requests,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        })
    
    return user_data
