"""
Health Assessment Schemas
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime, date


class HealthAssessmentCreate(BaseModel):
    """Create health assessment"""
    current_conditions: Optional[List[str]] = []
    medications: Optional[List[Dict]] = []
    allergies: Optional[List[str]] = []
    family_history: Optional[List[str]] = []
    
    # Metrics
    weight_lbs: Optional[float] = Field(None, gt=0)
    height_inches: Optional[float] = Field(None, gt=0)
    
    # Lab results
    hba1c: Optional[float] = Field(None, ge=0, le=20)
    fasting_glucose_mg_dl: Optional[float] = Field(None, ge=0)
    total_cholesterol_mg_dl: Optional[float] = Field(None, ge=0)
    ldl_cholesterol_mg_dl: Optional[float] = Field(None, ge=0)
    hdl_cholesterol_mg_dl: Optional[float] = Field(None, ge=0)
    triglycerides_mg_dl: Optional[float] = Field(None, ge=0)
    blood_pressure_systolic: Optional[int] = Field(None, ge=60, le=250)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=150)
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_conditions": ["Type 2 Diabetes", "Hypertension"],
                "medications": [
                    {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"}
                ],
                "allergies": ["penicillin"],
                "family_history": ["heart disease", "diabetes"],
                "weight_lbs": 180,
                "height_inches": 70,
                "hba1c": 7.2,
                "fasting_glucose_mg_dl": 140,
                "blood_pressure_systolic": 135,
                "blood_pressure_diastolic": 85
            }
        }


class HealthAssessmentResponse(BaseModel):
    """Health assessment response"""
    id: UUID
    user_id: UUID
    assessment_date: datetime
    status: str
    
    # User data
    current_conditions: Optional[List[str]] = []
    weight_lbs: Optional[float] = None
    height_inches: Optional[float] = None
    bmi: Optional[float] = None
    hba1c: Optional[float] = None
    
    # AI insights
    risk_scores: Optional[Dict] = None
    personalized_recommendations: Optional[List[Dict]] = []
    dietary_restrictions: Optional[List[str]] = []
    
    # Goals
    target_calories_daily: Optional[int] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HealthMetricCreate(BaseModel):
    """Create health metric"""
    metric_type: str = Field(..., pattern="^(weight|glucose|blood_pressure|hba1c)$")
    value: float = Field(..., gt=0)
    value_secondary: Optional[float] = Field(None, gt=0)  # For blood pressure diastolic
    unit: str
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "metric_type": "glucose",
                "value": 120,
                "unit": "mg/dL",
                "notes": "Fasting measurement",
                "recorded_at": "2024-01-15T08:00:00Z"
            }
        }


class HealthMetricResponse(BaseModel):
    """Health metric response"""
    id: UUID
    user_id: UUID
    metric_type: str
    value: float
    value_secondary: Optional[float] = None
    unit: str
    notes: Optional[str] = None
    recorded_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class HealthGoalCreate(BaseModel):
    """Create health goal"""
    goal_type: str
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    target_value: float = Field(..., gt=0)
    current_value: float = Field(..., gt=0)
    unit: str
    target_date: date
    priority: str = Field("medium", pattern="^(low|medium|high|critical)$")


class HealthGoalResponse(BaseModel):
    """Health goal response"""
    id: UUID
    user_id: UUID
    goal_type: str
    title: str
    description: Optional[str] = None
    target_value: float
    current_value: float
    unit: str
    start_date: date
    target_date: date
    progress_percentage: float
    priority: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
