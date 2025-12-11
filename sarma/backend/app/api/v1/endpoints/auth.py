"""
Forecast Health - Authentication Endpoints
User registration, login, token refresh
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, UserHealthProfile, UserPreferences
from app.schemas.user import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    AuthResponse,
    UserResponse,
    TokenResponse,
    SubscriptionResponse,
)

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    - **email**: Valid email address (unique)
    - **password**: Minimum 8 characters with uppercase, lowercase, and digit
    - **first_name**: User's first name
    - **last_name**: User's last name
    
    Returns user profile and JWT tokens
    """
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email.lower()))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email.lower(),
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    
    db.add(user)
    await db.flush()  # Get user.id
    
    # Create empty health profile
    health_profile = UserHealthProfile(user_id=user.id)
    db.add(health_profile)
    
    # Create empty preferences
    preferences = UserPreferences(user_id=user.id)
    db.add(preferences)
    
    await db.commit()
    await db.refresh(user)
    await db.refresh(health_profile)
    await db.refresh(preferences)
    
    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    # Build response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        date_of_birth=user.date_of_birth,
        gender=user.gender.value if user.gender else None,
        phone_number=user.phone_number,
        email_verified=user.email_verified,
        onboarding_completed=user.onboarding_completed,
        created_at=user.created_at,
        subscription=SubscriptionResponse(
            tier=user.subscription_tier.value,
            status=user.subscription_status.value,
            current_period_end=user.subscription_end_date
        ),
        health_profile=health_profile,
        preferences=preferences
    )
    
    return AuthResponse(
        user=user_response,
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns user profile and JWT tokens
    """
    
    # Find user by email
    result = await db.execute(
        select(User)
        .where(User.email == credentials.email.lower())
        .where(User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Load relationships
    await db.refresh(user, ["health_profile", "preferences"])
    
    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    # Build response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        date_of_birth=user.date_of_birth,
        gender=user.gender.value if user.gender else None,
        phone_number=user.phone_number,
        email_verified=user.email_verified,
        onboarding_completed=user.onboarding_completed,
        created_at=user.created_at,
        subscription=SubscriptionResponse(
            tier=user.subscription_tier.value,
            status=user.subscription_status.value,
            current_period_end=user.subscription_end_date
        ),
        health_profile=user.health_profile,
        preferences=user.preferences
    )
    
    return AuthResponse(
        user=user_response,
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token
    """
    
    # Decode refresh token
    try:
        payload = decode_token(token_data.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Refresh token required."
        )
    
    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Verify user exists
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .where(User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Generate new access token
    access_token = create_access_token(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=token_data.refresh_token  # Return same refresh token
    )
