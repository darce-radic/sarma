"""
Meal Tracking and Photo Analysis Schemas
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID
from datetime import datetime


class MealPhotoCreate(BaseModel):
    """Create meal photo for AI analysis"""
    photo_url: HttpUrl
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack|beverage|other)$")
    eaten_at: datetime
    location: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "photo_url": "https://storage.example.com/meals/abc123.jpg",
                "meal_type": "lunch",
                "eaten_at": "2024-01-15T12:30:00Z",
                "location": "Home",
                "notes": "Homemade salad"
            }
        }


class MealPhotoIngredientResponse(BaseModel):
    """Detected ingredient in meal photo"""
    id: UUID
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    confidence: float
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    
    class Config:
        from_attributes = True


class MealPhotoResponse(BaseModel):
    """Meal photo response with AI analysis"""
    id: UUID
    user_id: UUID
    photo_url: str
    meal_type: str
    eaten_at: datetime
    processing_status: str
    
    # AI Analysis
    ai_description: Optional[str] = None
    ai_confidence: Optional[float] = None
    detected_foods: Optional[List[str]] = []
    
    # Nutrition
    total_calories: Optional[float] = None
    total_protein_g: Optional[float] = None
    total_carbs_g: Optional[float] = None
    total_fat_g: Optional[float] = None
    health_score: Optional[float] = None
    
    # User feedback
    user_confirmed: bool = False
    
    ingredients: List[MealPhotoIngredientResponse] = []
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MealLogItemCreate(BaseModel):
    """Meal log item"""
    food_name: str
    quantity: float = Field(..., gt=0)
    unit: str
    calories: float = Field(..., ge=0)
    protein_g: float = Field(..., ge=0)
    carbs_g: float = Field(..., ge=0)
    fat_g: float = Field(..., ge=0)


class MealLogCreate(BaseModel):
    """Create meal log"""
    log_date: datetime
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack|beverage|other)$")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    recipe_id: Optional[UUID] = None
    meal_photo_id: Optional[UUID] = None
    items: List[MealLogItemCreate] = []
    notes: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('At least one meal item is required')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "log_date": "2024-01-15T18:30:00Z",
                "meal_type": "dinner",
                "title": "Grilled Chicken Salad",
                "description": "Healthy dinner with lean protein",
                "items": [
                    {
                        "food_name": "Grilled Chicken Breast",
                        "quantity": 6,
                        "unit": "oz",
                        "calories": 280,
                        "protein_g": 53,
                        "carbs_g": 0,
                        "fat_g": 6
                    }
                ],
                "satisfaction_rating": 5
            }
        }


class MealLogItemResponse(BaseModel):
    """Meal log item response"""
    id: UUID
    food_name: str
    quantity: float
    unit: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    
    class Config:
        from_attributes = True


class MealLogResponse(BaseModel):
    """Meal log response"""
    id: UUID
    user_id: UUID
    log_date: datetime
    meal_type: str
    title: str
    description: Optional[str] = None
    recipe_id: Optional[UUID] = None
    meal_photo_id: Optional[UUID] = None
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    notes: Optional[str] = None
    satisfaction_rating: Optional[int] = None
    items: List[MealLogItemResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
