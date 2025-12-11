"""
Meal Tracking and Photo Analysis API Endpoints
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.meal import (
    MealPhotoCreate,
    MealPhotoResponse,
    MealLogCreate,
    MealLogResponse
)
from app.services.meal_service import MealAnalysisService

router = APIRouter()


@router.post("/photos", response_model=MealPhotoResponse, status_code=status.HTTP_201_CREATED)
async def analyze_meal_photo(
    photo_data: MealPhotoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze meal photo with GPT-4 Vision
    
    Process:
    1. Upload photo to storage
    2. Analyze with GPT-4 Vision
    3. Detect ingredients and quantities
    4. Calculate nutrition
    5. Generate health score
    
    Returns immediately with processing_status='pending'
    Check back for completed analysis
    """
    meal_photo = await MealAnalysisService.analyze_meal_photo(
        db,
        current_user.id,
        photo_data
    )
    
    # Trigger async processing
    # In production: use Celery task
    # For now, process synchronously for demo
    try:
        meal_photo = await MealAnalysisService.process_meal_photo_with_gpt4_vision(
            db,
            meal_photo.id
        )
    except Exception as e:
        # Processing failed, but photo is saved
        pass
    
    return meal_photo


@router.get("/photos/{photo_id}", response_model=MealPhotoResponse)
async def get_meal_photo(
    photo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get meal photo analysis by ID"""
    from app.models.meal import MealPhoto
    
    photo = db.query(MealPhoto).filter(
        MealPhoto.id == photo_id,
        MealPhoto.user_id == current_user.id
    ).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal photo not found"
        )
    
    return photo


@router.get("/photos", response_model=List[MealPhotoResponse])
async def get_meal_photos(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's meal photos with optional date range"""
    photos = await MealAnalysisService.get_user_meal_photos(
        db,
        current_user.id,
        start_date,
        end_date,
        limit
    )
    return photos


@router.post("/photos/{photo_id}/confirm")
async def confirm_meal_photo(
    photo_id: UUID,
    corrections: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm or correct meal photo analysis
    
    Helps improve AI accuracy through user feedback
    """
    photo = await MealAnalysisService.confirm_meal_photo(
        db,
        photo_id,
        current_user.id,
        corrections
    )
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal photo not found"
        )
    
    return {
        "message": "Meal photo confirmed",
        "photo_id": photo.id
    }


@router.post("/logs", response_model=MealLogResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_log(
    log_data: MealLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create manual meal log entry
    
    Use this for:
    - Tracking meals without photos
    - Logging restaurant meals
    - Recording recipes you cooked
    """
    meal_log = await MealAnalysisService.create_meal_log(
        db,
        current_user.id,
        log_data
    )
    return meal_log


@router.get("/logs", response_model=List[MealLogResponse])
async def get_meal_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    meal_type: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get meal logs with optional filtering"""
    from app.models.meal import MealLog
    from sqlalchemy import desc
    
    query = db.query(MealLog).filter(
        MealLog.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(MealLog.log_date >= start_date)
    
    if end_date:
        query = query.filter(MealLog.log_date <= end_date)
    
    if meal_type:
        query = query.filter(MealLog.meal_type == meal_type)
    
    logs = query.order_by(desc(MealLog.log_date)).limit(limit).all()
    
    return logs


@router.get("/nutrition/daily")
async def get_daily_nutrition(
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete nutritional summary for a day
    
    Includes:
    - All meal logs
    - All analyzed photos
    - Total macros
    - Meal count
    """
    summary = await MealAnalysisService.get_daily_nutrition_summary(
        db,
        current_user.id,
        target_date
    )
    return summary


@router.get("/nutrition/trends")
async def get_nutrition_trends(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get nutrition trends over time
    
    Shows:
    - Daily summaries
    - Average intake
    - Trends and patterns
    """
    trends = await MealAnalysisService.get_nutrition_trends(
        db,
        current_user.id,
        days
    )
    return trends
