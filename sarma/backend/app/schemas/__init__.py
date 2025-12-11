"""
Forecast Platform - Pydantic Schemas Package
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfileResponse,
    UserHealthProfileResponse
)
from app.schemas.auth import (
    Token,
    TokenPayload,
    LoginRequest,
    SignupRequest
)
from app.schemas.recipe import (
    RecipeBase,
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeSearchRequest,
    RecipeIngredientResponse
)
from app.schemas.health import (
    HealthAssessmentCreate,
    HealthAssessmentResponse,
    HealthMetricCreate,
    HealthMetricResponse
)
from app.schemas.meal import (
    MealPhotoCreate,
    MealPhotoResponse,
    MealLogCreate,
    MealLogResponse
)

__all__ = [
    # Auth
    "Token",
    "TokenPayload",
    "LoginRequest",
    "SignupRequest",
    
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfileResponse",
    "UserHealthProfileResponse",
    
    # Recipe
    "RecipeBase",
    "RecipeCreate",
    "RecipeUpdate",
    "RecipeResponse",
    "RecipeSearchRequest",
    "RecipeIngredientResponse",
    
    # Health
    "HealthAssessmentCreate",
    "HealthAssessmentResponse",
    "HealthMetricCreate",
    "HealthMetricResponse",
    
    # Meal
    "MealPhotoCreate",
    "MealPhotoResponse",
    "MealLogCreate",
    "MealLogResponse",
]
