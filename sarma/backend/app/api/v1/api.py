"""
API v1 Router - Central API Configuration
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, recipes, health, meals, shopping, chat, ai, settings, subscriptions, analytics, admin, referrals, grocery, recipes_external

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# User management endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# Recipe endpoints
api_router.include_router(
    recipes.router,
    prefix="/recipes",
    tags=["Recipes"]
)

# Health assessment endpoints
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

# Meal tracking endpoints
api_router.include_router(
    meals.router,
    prefix="/meals",
    tags=["Meals"]
)

# Shopping endpoints
api_router.include_router(
    shopping.router,
    prefix="/shopping",
    tags=["Shopping"]
)

# Chat assistant endpoints
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat Assistant"]
)

# AI services endpoints (meal analysis, recipe generation, AI chat)
api_router.include_router(
    ai.router,
    prefix="/ai",
    tags=["AI Services"]
)

# User settings endpoints
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["Settings"]
)

# Subscription & payment endpoints
api_router.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["Subscriptions"]
)

# Analytics endpoints
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

# Admin panel endpoints
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

# Referral & viral loop endpoints
api_router.include_router(
    referrals.router,
    prefix="/referrals",
    tags=["Referrals & Viral"]
)

# Grocery store integration endpoints
api_router.include_router(
    grocery.router,
    prefix="/grocery",
    tags=["Grocery Stores"]
)

# External recipe API endpoints
api_router.include_router(
    recipes_external.router,
    prefix="/recipes/external",
    tags=["External Recipes"]
)

# TODO: Add remaining endpoint groups
# - Brand Partnerships (/partnerships)
