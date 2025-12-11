from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.meal import Meal
from app.models.ai_request import AIRequest

router = APIRouter()


@router.get("/")
async def get_analytics(
    range: str = Query("month", regex="^(week|month|year)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user analytics including AI usage, meals, goals, and cost analysis.
    """
    # Calculate date range
    now = datetime.utcnow()
    if range == "week":
        start_date = now - timedelta(days=7)
    elif range == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)

    # AI Usage Statistics
    ai_requests_query = select(AIRequest).where(
        AIRequest.user_id == current_user.id,
        AIRequest.created_at >= start_date
    )
    ai_requests = (await db.execute(ai_requests_query)).scalars().all()

    total_ai_requests = len(ai_requests)
    requests_by_provider = {
        "gemini": sum(1 for req in ai_requests if req.provider == "gemini"),
        "openai": sum(1 for req in ai_requests if req.provider == "openai"),
    }
    
    avg_response_time = (
        sum(req.response_time for req in ai_requests if req.response_time)
        / len(ai_requests)
        if ai_requests
        else 0
    )

    # Meal Statistics
    meals_query = select(Meal).where(
        Meal.user_id == current_user.id,
        Meal.created_at >= start_date
    )
    meals = (await db.execute(meals_query)).scalars().all()

    total_meals = len(meals)
    meals_this_week = sum(
        1 for meal in meals if meal.created_at >= (now - timedelta(days=7))
    )
    
    avg_calories = (
        sum(meal.calories for meal in meals if meal.calories) / len(meals)
        if meals
        else 0
    )
    avg_protein = (
        sum(meal.protein for meal in meals if meal.protein) / len(meals)
        if meals
        else 0
    )

    # Favorite meals (top 5)
    favorite_meals = []
    if meals:
        meal_counts = {}
        for meal in meals:
            meal_counts[meal.name] = meal_counts.get(meal.name, 0) + 1
        favorite_meals = [
            {"name": name, "count": count}
            for name, count in sorted(
                meal_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

    # Health Goals Progress
    user_settings = current_user.settings
    daily_calorie_goal = (
        user_settings.health_goals.get("daily_calories", 2000)
        if user_settings and user_settings.health_goals
        else 2000
    )
    
    goal_adherence = 0
    if meals and daily_calorie_goal:
        days_tracked = len(set(meal.created_at.date() for meal in meals))
        days_met_goal = sum(
            1
            for date in set(meal.created_at.date() for meal in meals)
            if sum(
                meal.calories for meal in meals
                if meal.created_at.date() == date and meal.calories
            ) <= daily_calorie_goal * 1.1  # 10% tolerance
        )
        goal_adherence = (days_met_goal / days_tracked * 100) if days_tracked > 0 else 0

    # Streak calculation (consecutive days with meals logged)
    streak_days = 0
    if meals:
        dates = sorted(set(meal.created_at.date() for meal in meals), reverse=True)
        current_date = now.date()
        for date in dates:
            if date == current_date or date == current_date - timedelta(days=streak_days):
                streak_days += 1
                current_date = date
            else:
                break

    # Cost Analysis
    gemini_cost = requests_by_provider["gemini"] * 0.001
    openai_cost = requests_by_provider["openai"] * 0.02
    total_spent = gemini_cost + openai_cost
    savings = (total_ai_requests * 0.02) - total_spent  # vs GPT-4 only

    # Estimate next month based on current usage
    days_in_range = (now - start_date).days
    daily_avg_requests = total_ai_requests / days_in_range if days_in_range > 0 else 0
    estimated_next_month = daily_avg_requests * 30 * (
        requests_by_provider["gemini"] / total_ai_requests * 0.001
        + requests_by_provider["openai"] / total_ai_requests * 0.02
        if total_ai_requests > 0
        else 0
    )

    return {
        "ai_usage": {
            "total_requests": total_ai_requests,
            "requests_this_month": sum(
                1 for req in ai_requests
                if req.created_at >= (now - timedelta(days=30))
            ),
            "requests_by_provider": requests_by_provider,
            "average_response_time": round(avg_response_time, 2),
        },
        "meals": {
            "total_logged": total_meals,
            "logged_this_week": meals_this_week,
            "average_calories": round(avg_calories, 1),
            "average_protein": round(avg_protein, 1),
            "favorite_meals": favorite_meals,
        },
        "goals": {
            "daily_calorie_goal": daily_calorie_goal,
            "daily_calorie_avg": round(avg_calories, 1),
            "goal_adherence_percentage": round(goal_adherence, 1),
            "streak_days": streak_days,
        },
        "costs": {
            "total_spent_this_month": round(total_spent, 2),
            "savings_vs_standard": round(savings, 2),
            "estimated_next_month": round(estimated_next_month, 2),
        },
    }


@router.get("/export")
async def export_analytics(
    format: str = Query("csv", regex="^(csv|json)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export user data in CSV or JSON format.
    """
    # Fetch all user data
    meals_query = select(Meal).where(Meal.user_id == current_user.id)
    meals = (await db.execute(meals_query)).scalars().all()

    ai_requests_query = select(AIRequest).where(AIRequest.user_id == current_user.id)
    ai_requests = (await db.execute(ai_requests_query)).scalars().all()

    if format == "json":
        return {
            "user": {
                "id": str(current_user.id),
                "email": current_user.email,
                "created_at": current_user.created_at.isoformat(),
            },
            "meals": [
                {
                    "name": meal.name,
                    "calories": meal.calories,
                    "protein": meal.protein,
                    "carbs": meal.carbs,
                    "fat": meal.fat,
                    "created_at": meal.created_at.isoformat(),
                }
                for meal in meals
            ],
            "ai_requests": [
                {
                    "provider": req.provider,
                    "feature": req.feature,
                    "cost": req.cost,
                    "response_time": req.response_time,
                    "created_at": req.created_at.isoformat(),
                }
                for req in ai_requests
            ],
        }
    else:  # CSV
        # Return CSV format (simplified)
        csv_data = "Type,Date,Name,Value\n"
        for meal in meals:
            csv_data += f"meal,{meal.created_at.date()},{meal.name},{meal.calories}\n"
        for req in ai_requests:
            csv_data += f"ai_request,{req.created_at.date()},{req.feature},{req.cost}\n"
        
        return {"data": csv_data, "filename": f"sarma_data_{datetime.now().strftime('%Y%m%d')}.csv"}
