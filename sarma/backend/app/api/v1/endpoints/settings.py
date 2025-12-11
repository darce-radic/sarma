"""
User Settings Endpoints
Manage user preferences, API keys, and configurations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
import os
import time

from ....core.database import get_db
from ....core.security import get_current_user
from ....models.user import User
from ....models.user_settings import UserSettings
from ....schemas.settings import (
    UserSettingsResponse,
    UserSettingsUpdate,
    TestAPIKeyRequest,
    TestAPIKeyResponse
)

router = APIRouter()

# Encryption key for API keys (in production, use proper key management)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher = Fernet(ENCRYPTION_KEY)


def mask_api_key(key: str) -> str:
    """Mask API key for display"""
    if not key or len(key) < 10:
        return "****"
    return f"{key[:10]}...{key[-4:]}"


def encrypt_api_key(key: str) -> str:
    """Encrypt API key"""
    if not key:
        return None
    return cipher.encrypt(key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key"""
    if not encrypted_key:
        return None
    return cipher.decrypt(encrypted_key.encode()).decode()


@router.get("/", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's settings
    """
    from sqlalchemy import select
    
    # Get or create settings
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    # Mask API keys
    response_data = UserSettingsResponse.model_validate(settings)
    if settings.openai_api_key:
        response_data.openai_api_key = mask_api_key(decrypt_api_key(settings.openai_api_key))
    if settings.gemini_api_key:
        response_data.gemini_api_key = mask_api_key(decrypt_api_key(settings.gemini_api_key))
    
    return response_data


@router.patch("/", response_model=UserSettingsResponse)
async def update_user_settings(
    update_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user settings
    """
    from sqlalchemy import select
    
    # Get settings
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Encrypt API keys before saving
    if "openai_api_key" in update_dict and update_dict["openai_api_key"]:
        update_dict["openai_api_key"] = encrypt_api_key(update_dict["openai_api_key"])
    
    if "gemini_api_key" in update_dict and update_dict["gemini_api_key"]:
        update_dict["gemini_api_key"] = encrypt_api_key(update_dict["gemini_api_key"])
    
    for key, value in update_dict.items():
        setattr(settings, key, value)
    
    await db.commit()
    await db.refresh(settings)
    
    # Mask API keys in response
    response_data = UserSettingsResponse.model_validate(settings)
    if settings.openai_api_key:
        response_data.openai_api_key = mask_api_key(decrypt_api_key(settings.openai_api_key))
    if settings.gemini_api_key:
        response_data.gemini_api_key = mask_api_key(decrypt_api_key(settings.gemini_api_key))
    
    return response_data


@router.post("/test-api-key", response_model=TestAPIKeyResponse)
async def test_api_key(
    request: TestAPIKeyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Test an API key to verify it works
    """
    start_time = time.time()
    
    try:
        if request.provider == "gemini":
            # Test Gemini key
            import google.generativeai as genai
            genai.configure(api_key=request.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            response = model.generate_content("Say 'API key working' in 3 words")
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return TestAPIKeyResponse(
                success=True,
                provider="gemini",
                message="Gemini API key is valid and working!",
                response_time_ms=response_time_ms
            )
            
        elif request.provider == "openai":
            # Test OpenAI key
            from openai import OpenAI
            client = OpenAI(api_key=request.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Say 'API key working' in 3 words"}],
                max_tokens=10
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return TestAPIKeyResponse(
                success=True,
                provider="openai",
                message="OpenAI API key is valid and working!",
                response_time_ms=response_time_ms
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown provider: {request.provider}. Use 'gemini' or 'openai'"
            )
    
    except Exception as e:
        return TestAPIKeyResponse(
            success=False,
            provider=request.provider,
            message=f"API key test failed: {str(e)}"
        )


@router.delete("/api-keys")
async def delete_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove user's stored API keys
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if settings:
        settings.openai_api_key = None
        settings.gemini_api_key = None
        await db.commit()
    
    return {"message": "API keys removed successfully"}
