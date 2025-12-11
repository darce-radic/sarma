"""
Forecast Platform - Database Models Package
"""
from app.models.user import (
    User,
    UserProfile,
    UserPreferences,
    UserHealthProfile,
    UserAllergy,
    UserMedication,
    UserNutritionGoal
)
from app.models.recipe import (
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeStep,
    RecipeTag,
    RecipeRating,
    RecipeFavorite,
    RecipeCollection
)
from app.models.meal import (
    MealPhoto,
    MealPhotoIngredient,
    MealPhotoNutrition,
    MealLog,
    MealLogItem
)
from app.models.shopping import (
    ShoppingList,
    ShoppingListItem,
    ShoppingOrder,
    ShoppingOrderItem,
    Store,
    StoreProduct
)
from app.models.health import (
    HealthAssessment,
    HealthMetric,
    BiometricReading,
    LabResult,
    Medication,
    HealthGoal,
    HealthInsight
)
from app.models.chat import (
    ChatSession,
    ChatMessage,
    ChatFeedback
)
from app.models.partnership import (
    Brand,
    BrandPartnership,
    BrandProduct,
    BrandCampaign,
    BrandAnalytics
)
from app.models.viral import (
    UserStreak,
    UserAchievement,
    UserReferral,
    SocialShare,
    Leaderboard
)
from app.models.system_setting import SystemSetting

__all__ = [
    # User models
    "User",
    "UserProfile",
    "UserPreferences",
    "UserHealthProfile",
    "UserAllergy",
    "UserMedication",
    "UserNutritionGoal",
    
    # Recipe models
    "Recipe",
    "RecipeIngredient",
    "RecipeNutrition",
    "RecipeStep",
    "RecipeTag",
    "RecipeRating",
    "RecipeFavorite",
    "RecipeCollection",
    
    # Meal models
    "MealPhoto",
    "MealPhotoIngredient",
    "MealPhotoNutrition",
    "MealLog",
    "MealLogItem",
    
    # Shopping models
    "ShoppingList",
    "ShoppingListItem",
    "ShoppingOrder",
    "ShoppingOrderItem",
    "Store",
    "StoreProduct",
    
    # Health models
    "HealthAssessment",
    "HealthMetric",
    "BiometricReading",
    "LabResult",
    "Medication",
    "HealthGoal",
    "HealthInsight",
    
    # Chat models
    "ChatSession",
    "ChatMessage",
    "ChatFeedback",
    
    # Partnership models
    "Brand",
    "BrandPartnership",
    "BrandProduct",
    "BrandCampaign",
    "BrandAnalytics",
    
    # Viral models
    "UserStreak",
    "UserAchievement",
    "UserReferral",
    "SocialShare",
    "Leaderboard",
    "SystemSetting",
]
