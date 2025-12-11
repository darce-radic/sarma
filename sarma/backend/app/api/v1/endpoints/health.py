"""
Health Assessment API Endpoints
"""
from typing import List
from uuid import UUID
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.health import (
    HealthAssessmentCreate,
    HealthAssessmentResponse,
    HealthMetricCreate,
    HealthMetricResponse,
    HealthGoalCreate,
    HealthGoalResponse
)
from app.services.health_service import HealthAssessmentService

router = APIRouter()


@router.post("/assessments", response_model=HealthAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_health_assessment(
    assessment_data: HealthAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create comprehensive health assessment
    
    Analyzes:
    - Current health conditions
    - Lab results (HbA1c, cholesterol, blood pressure)
    - Medications and allergies
    - Family history
    
    Generates:
    - Disease risk scores
    - Personalized recommendations
    - Dietary restrictions
    - Nutritional targets
    """
    assessment = await HealthAssessmentService.create_assessment(
        db,
        current_user.id,
        assessment_data
    )
    return assessment


@router.get("/assessments/latest", response_model=HealthAssessmentResponse)
async def get_latest_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's most recent health assessment"""
    assessment = await HealthAssessmentService.get_latest_assessment(
        db,
        current_user.id
    )
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No health assessment found. Please create one first."
        )
    
    return assessment


@router.post("/metrics", response_model=HealthMetricResponse, status_code=status.HTTP_201_CREATED)
async def add_health_metric(
    metric_data: HealthMetricCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add health metric reading
    
    Supports:
    - Weight
    - Blood glucose
    - Blood pressure
    - HbA1c
    """
    metric = await HealthAssessmentService.add_health_metric(
        db,
        current_user.id,
        metric_data
    )
    return metric


@router.get("/metrics", response_model=List[HealthMetricResponse])
async def get_health_metrics(
    metric_type: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health metrics with optional filtering"""
    from app.models.health import HealthMetric
    from sqlalchemy import desc
    
    query = db.query(HealthMetric).filter(
        HealthMetric.user_id == current_user.id
    )
    
    if metric_type:
        query = query.filter(HealthMetric.metric_type == metric_type)
    
    if start_date:
        query = query.filter(HealthMetric.recorded_at >= start_date)
    
    if end_date:
        query = query.filter(HealthMetric.recorded_at <= end_date)
    
    metrics = query.order_by(desc(HealthMetric.recorded_at)).limit(limit).all()
    
    return metrics


@router.post("/goals", response_model=HealthGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_health_goal(
    goal_data: HealthGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create health goal
    
    Examples:
    - Weight loss: Target 165 lbs by 2024-06-01
    - HbA1c reduction: Target 6.5% by 2024-12-31
    - Exercise: Target 150 minutes/week
    """
    from app.models.health import HealthGoal
    from datetime import date
    
    goal = HealthGoal(
        user_id=current_user.id,
        goal_type=goal_data.goal_type,
        title=goal_data.title,
        description=goal_data.description,
        target_value=goal_data.target_value,
        current_value=goal_data.current_value,
        unit=goal_data.unit,
        start_date=date.today(),
        target_date=goal_data.target_date,
        priority=goal_data.priority,
        is_active=True
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return goal


@router.get("/goals", response_model=List[HealthGoalResponse])
async def get_health_goals(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's health goals"""
    from app.models.health import HealthGoal
    
    query = db.query(HealthGoal).filter(
        HealthGoal.user_id == current_user.id
    )
    
    if active_only:
        query = query.filter(HealthGoal.is_active == True)
    
    goals = query.all()
    
    return goals


@router.get("/insights", response_model=List[dict])
async def get_health_insights(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-generated health insights
    
    Provides:
    - Trend analysis
    - Health alerts
    - Nutritional recommendations
    - Progress updates
    """
    from app.models.health import HealthInsight
    from sqlalchemy import desc
    
    insights = db.query(HealthInsight).filter(
        HealthInsight.user_id == current_user.id,
        HealthInsight.is_dismissed == False
    ).order_by(desc(HealthInsight.generated_at)).limit(limit).all()
    
    return [
        {
            "id": insight.id,
            "type": insight.insight_type,
            "title": insight.title,
            "description": insight.description,
            "priority": insight.priority,
            "is_actionable": insight.is_actionable,
            "action_items": insight.action_items,
            "generated_at": insight.generated_at
        }
        for insight in insights
    ]
