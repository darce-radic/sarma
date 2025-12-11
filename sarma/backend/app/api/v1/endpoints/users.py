"""
Forecast Health - User Endpoints
User profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    HealthProfileUpdate,
    PreferencesUpdate,
    SubscriptionResponse,
)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get authenticated user's complete profile
    
    Returns:
    - User account details
    - Health profile
    - Preferences
    - Subscription info
    """
    
    # Load relationships
    await db.refresh(current_user, ["health_profile", "preferences"])
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        date_of_birth=current_user.date_of_birth,
        gender=current_user.gender.value if current_user.gender else None,
        phone_number=current_user.phone_number,
        email_verified=current_user.email_verified,
        onboarding_completed=current_user.onboarding_completed,
        created_at=current_user.created_at,
        subscription=SubscriptionResponse(
            tier=current_user.subscription_tier.value,
            status=current_user.subscription_status.value,
            current_period_end=current_user.subscription_end_date
        ),
        health_profile=current_user.health_profile,
        preferences=current_user.preferences
    )


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update authenticated user's profile
    
    Only provided fields will be updated (partial update)
    """
    
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user, ["health_profile", "preferences"])
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        date_of_birth=current_user.date_of_birth,
        gender=current_user.gender.value if current_user.gender else None,
        phone_number=current_user.phone_number,
        email_verified=current_user.email_verified,
        onboarding_completed=current_user.onboarding_completed,
        created_at=current_user.created_at,
        subscription=SubscriptionResponse(
            tier=current_user.subscription_tier.value,
            status=current_user.subscription_status.value,
            current_period_end=current_user.subscription_end_date
        ),
        health_profile=current_user.health_profile,
        preferences=current_user.preferences
    )


@router.patch("/me/health-profile", response_model=UserResponse)
async def update_health_profile(
    profile_update: HealthProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's health profile
    
    Includes: physical measurements, medical history, lab values, lifestyle
    """
    
    # Load health profile
    await db.refresh(current_user, ["health_profile", "preferences"])
    
    if not current_user.health_profile:
        from app.models.user import UserHealthProfile
        current_user.health_profile = UserHealthProfile(user_id=current_user.id)
        db.add(current_user.health_profile)
    
    # Update health profile fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user.health_profile, field, value)
    
    await db.commit()
    await db.refresh(current_user, ["health_profile", "preferences"])
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        date_of_birth=current_user.date_of_birth,
        gender=current_user.gender.value if current_user.gender else None,
        phone_number=current_user.phone_number,
        email_verified=current_user.email_verified,
        onboarding_completed=current_user.onboarding_completed,
        created_at=current_user.created_at,
        subscription=SubscriptionResponse(
            tier=current_user.subscription_tier.value,
            status=current_user.subscription_status.value,
            current_period_end=current_user.subscription_end_date
        ),
        health_profile=current_user.health_profile,
        preferences=current_user.preferences
    )


@router.patch("/me/preferences", response_model=UserResponse)
async def update_preferences(
    preferences_update: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's dietary and lifestyle preferences
    
    Includes: dietary restrictions, cuisine preferences, cooking skill, goals
    """
    
    # Load preferences
    await db.refresh(current_user, ["health_profile", "preferences"])
    
    if not current_user.preferences:
        from app.models.user import UserPreferences
        current_user.preferences = UserPreferences(user_id=current_user.id)
        db.add(current_user.preferences)
    
    # Update preferences fields
    update_data = preferences_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user.preferences, field, value)
    
    await db.commit()
    await db.refresh(current_user, ["health_profile", "preferences"])
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        date_of_birth=current_user.date_of_birth,
        gender=current_user.gender.value if current_user.gender else None,
        phone_number=current_user.phone_number,
        email_verified=current_user.email_verified,
        onboarding_completed=current_user.onboarding_completed,
        created_at=current_user.created_at,
        subscription=SubscriptionResponse(
            tier=current_user.subscription_tier.value,
            status=current_user.subscription_status.value,
            current_period_end=current_user.subscription_end_date
        ),
        health_profile=current_user.health_profile,
        preferences=current_user.preferences
    )
