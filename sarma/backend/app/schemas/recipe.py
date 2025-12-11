"""
Recipe Schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime


class RecipeIngredientResponse(BaseModel):
    """Recipe ingredient response"""
    id: UUID
    name: str
    quantity: float
    unit: str
    notes: Optional[str] = None
    is_optional: bool = False
    
    class Config:
        from_attributes = True


class RecipeBase(BaseModel):
    """Base recipe schema"""
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    prep_time_minutes: int = Field(..., gt=0)
    cook_time_minutes: int = Field(..., gt=0)
    servings: int = Field(..., gt=0)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    dietary_type: str


class RecipeCreate(RecipeBase):
    """Create recipe schema"""
    ingredients: List[dict]
    instructions: dict
    tags: Optional[List[str]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Grilled Salmon with Quinoa",
                "description": "Heart-healthy omega-3 rich meal",
                "prep_time_minutes": 15,
                "cook_time_minutes": 20,
                "servings": 4,
                "difficulty": "medium",
                "dietary_type": "pescatarian",
                "ingredients": [
                    {"name": "Salmon fillet", "quantity": 1.5, "unit": "lbs"},
                    {"name": "Quinoa", "quantity": 2, "unit": "cups"}
                ],
                "instructions": {
                    "steps": [
                        {"step": 1, "instruction": "Preheat grill to medium-high"},
                        {"step": 2, "instruction": "Season salmon with olive oil and herbs"}
                    ]
                },
                "tags": ["heart-healthy", "high-protein"]
            }
        }


class RecipeUpdate(BaseModel):
    """Update recipe schema"""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    prep_time_minutes: Optional[int] = Field(None, gt=0)
    cook_time_minutes: Optional[int] = Field(None, gt=0)
    servings: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class RecipeResponse(RecipeBase):
    """Recipe response schema"""
    id: UUID
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    health_score: Optional[float] = None
    rating_avg: float
    rating_count: int
    view_count: int
    favorite_count: int
    ingredients: List[RecipeIngredientResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RecipeSearchRequest(BaseModel):
    """Recipe search request"""
    query: Optional[str] = None
    dietary_type: Optional[str] = None
    max_calories: Optional[int] = None
    max_prep_time: Optional[int] = None
    difficulty: Optional[str] = None
    health_conditions: Optional[List[str]] = []
    exclude_allergens: Optional[List[str]] = []
    min_health_score: Optional[float] = Field(None, ge=0, le=100)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "low carb dinner",
                "dietary_type": "keto",
                "max_calories": 500,
                "max_prep_time": 30,
                "difficulty": "easy",
                "health_conditions": ["diabetes", "hypertension"],
                "exclude_allergens": ["nuts", "dairy"],
                "min_health_score": 70,
                "page": 1,
                "page_size": 20
            }
        }
