"""
AI Endpoints
Meal analysis, recipe generation, and chat assistant
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.security import get_current_user
from ....core.ai_config import (
    get_meal_analyzer,
    get_recipe_generator,
    get_chat_assistant
)
from ....models.user import User
from ....services.ai.meal_analyzer import MealAnalyzer
from ....services.ai.recipe_generator import RecipeGenerator
from ....services.ai.chat_assistant import ChatAssistant
from ....services.ai.base import AIProvider

router = APIRouter()


# =====================
# Request/Response Models
# =====================

class AnalyzeMealRequest(BaseModel):
    image_url: str
    user_tier: str = "free"  # free or premium
    force_provider: Optional[str] = None


class AnalyzeMealResponse(BaseModel):
    nutrition: dict
    ai_metadata: dict
    analyzed_at: str


class GenerateRecipeRequest(BaseModel):
    ingredients: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    health_goals: Optional[List[str]] = None
    cuisine: Optional[str] = None
    max_calories: Optional[int] = None
    meal_type: Optional[str] = None
    use_gpt4: bool = False


class GenerateRecipeResponse(BaseModel):
    recipe: dict
    ai_metadata: dict
    generated_at: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = None
    use_gpt4: bool = False


class ChatResponse(BaseModel):
    response: str
    ai_metadata: dict
    timestamp: str


class MealSuggestionRequest(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    use_gpt4: bool = False


# =====================
# Meal Analysis Endpoints
# =====================

@router.post("/analyze-meal", response_model=AnalyzeMealResponse)
async def analyze_meal(
    request: AnalyzeMealRequest,
    current_user: User = Depends(get_current_user),
    meal_analyzer: MealAnalyzer = Depends(get_meal_analyzer),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a meal photo and extract nutrition data
    
    - **image_url**: URL or base64 encoded image
    - **user_tier**: "free" (Gemini) or "premium" (GPT-4)
    - **force_provider**: Force specific AI provider
    
    Returns detailed nutrition analysis
    """
    if not meal_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI services not configured. Please set GEMINI_API_KEY and OPENAI_API_KEY"
        )
    
    try:
        # Determine user tier (you can check subscription in database)
        # For now, use the provided tier
        force_provider_enum = None
        if request.force_provider:
            force_provider_enum = AIProvider(request.force_provider)
        
        result = await meal_analyzer.analyze_meal(
            image_url=request.image_url,
            user_tier=request.user_tier,
            force_provider=force_provider_enum
        )
        
        return AnalyzeMealResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Meal analysis failed: {str(e)}"
        )


@router.post("/quick-calorie-estimate")
async def quick_calorie_estimate(
    image_url: str,
    current_user: User = Depends(get_current_user),
    meal_analyzer: MealAnalyzer = Depends(get_meal_analyzer)
):
    """
    Quick calorie estimate (fast, free tier)
    Uses Gemini Flash for instant estimates
    """
    if not meal_analyzer:
        raise HTTPException(
            status_code=503,
            detail="AI services not configured"
        )
    
    try:
        result = await meal_analyzer.quick_calorie_estimate(image_url)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Calorie estimation failed: {str(e)}"
        )


# =====================
# Recipe Generation Endpoints
# =====================

@router.post("/generate-recipe", response_model=GenerateRecipeResponse)
async def generate_recipe(
    request: GenerateRecipeRequest,
    current_user: User = Depends(get_current_user),
    recipe_generator: RecipeGenerator = Depends(get_recipe_generator)
):
    """
    Generate personalized recipe based on preferences
    
    - **ingredients**: Available ingredients
    - **dietary_restrictions**: e.g., ["vegetarian", "gluten-free"]
    - **health_goals**: e.g., ["high-protein", "low-carb"]
    - **cuisine**: e.g., "Italian", "Mexican"
    - **max_calories**: Maximum calories per serving
    - **meal_type**: "breakfast", "lunch", "dinner", "snack"
    - **use_gpt4**: Use GPT-4 for more creative recipes
    """
    if not recipe_generator:
        raise HTTPException(
            status_code=503,
            detail="AI services not configured"
        )
    
    try:
        result = await recipe_generator.generate_recipe(
            ingredients=request.ingredients,
            dietary_restrictions=request.dietary_restrictions,
            health_goals=request.health_goals,
            cuisine=request.cuisine,
            max_calories=request.max_calories,
            meal_type=request.meal_type,
            use_gpt4=request.use_gpt4
        )
        
        return GenerateRecipeResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recipe generation failed: {str(e)}"
        )


@router.post("/generate-recipe-from-photo")
async def generate_recipe_from_photo(
    image_url: str,
    preference: str = "similar",  # similar, healthier, different
    current_user: User = Depends(get_current_user),
    recipe_generator: RecipeGenerator = Depends(get_recipe_generator)
):
    """
    Generate recipe inspired by a meal photo
    
    - **image_url**: Photo of a meal
    - **preference**: "similar" (recreate), "healthier", or "different" (inspired by)
    """
    if not recipe_generator:
        raise HTTPException(
            status_code=503,
            detail="AI services not configured"
        )
    
    try:
        result = await recipe_generator.generate_from_photo(
            image_url=image_url,
            preference=preference
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recipe generation failed: {str(e)}"
        )


@router.get("/suggest-recipes")
async def suggest_recipes(
    count: int = 5,
    use_gpt4: bool = False,
    current_user: User = Depends(get_current_user),
    recipe_generator: RecipeGenerator = Depends(get_recipe_generator),
    db: AsyncSession = Depends(get_db)
):
    """
    Suggest recipes based on user preferences
    
    - **count**: Number of recipes to suggest
    - **use_gpt4**: Use GPT-4 for suggestions
    """
    if not recipe_generator:
        raise HTTPException(
            status_code=503,
            detail="AI services not configured"
        )
    
    try:
        # Get user preferences from database
        # For now, use default preferences
        user_preferences = {
            "dietary_restrictions": [],
            "health_goals": ["balanced"],
            "favorite_cuisines": [],
            "cooking_skill": "intermediate"
        }
        
        result = await recipe_generator.suggest_recipes(
            user_preferences=user_preferences,
            count=count,
            use_gpt4=use_gpt4
        )
        
        return {"suggestions": result, "count": len(result)}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recipe suggestions failed: {str(e)}"
        )


# =====================
# Chat Assistant Endpoints
# =====================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    chat_assistant: ChatAssistant = Depends(get_chat_assistant),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with AI nutrition assistant
    
    - **message**: User's message
    - **conversation_history**: Previous messages
    - **use_gpt4**: Use GPT-4 for complex questions
    """
    if not chat_assistant:
        raise HTTPException(
            status_code=503,
            detail="AI services not configured"
        )
    
    try:
        # Get user context from database
        # For now, use minimal context
        user_context = {
            "health_goals": ["balanced nutrition"],
            "dietary_restrictions": [],
            "recent_meals": 0
        }
        
        result = await chat_assistant.chat(
            message=request.message,
            conversation_history=request.conversation_history,
            user_context=user_context,
            use_gpt4=request.use_gpt4
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/suggest-meal")
async def suggest_meal(
    request: MealSuggestionRequest,
    current_user: User = Depends(get_current_user),
    chat_assistant: ChatAssistant = Depends(get_chat_assistant)
):
    """
    Get meal suggestion for specific meal type
    
    - **meal_type**: breakfast, lunch, dinner, or snack
    - **use_gpt4**: Use GPT-4 for suggestions
    """
    if not chat_assistant:
        raise HTTPException(
            status_code=503,
            detail="AI services not configured"
        )
    
    try:
        # Get user context
        user_context = {
            "health_goals": ["balanced nutrition"],
            "dietary_restrictions": []
        }
        
        result = await chat_assistant.suggest_meal(
            meal_type=request.meal_type,
            user_context=user_context,
            use_gpt4=request.use_gpt4
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Meal suggestion failed: {str(e)}"
        )


@router.get("/analyze-diet")
async def analyze_diet(
    days: int = 7,
    use_gpt4: bool = False,
    current_user: User = Depends(get_current_user),
    chat_assistant: ChatAssistant = Depends(get_chat_assistant),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze user's diet trends and provide insights
    
    - **days**: Number of days to analyze (default: 7)
    - **use_gpt4**: Use GPT-4 for analysis
    """
    if not chat_assistant:
        raise HTTPException(
            status_code=503,
            detail="AI services not configured"
        )
    
    try:
        # Fetch user's recent meals from database
        # For now, return empty analysis
        recent_meals = []  # TODO: Fetch from database
        
        if not recent_meals:
            return {
                "analysis": "No meals logged yet. Start logging meals to get personalized insights!",
                "meals_analyzed": 0
            }
        
        result = await chat_assistant.analyze_diet_trends(
            recent_meals=recent_meals,
            time_period_days=days,
            use_gpt4=use_gpt4
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Diet analysis failed: {str(e)}"
        )


# =====================
# Health Check
# =====================

@router.get("/health")
async def ai_health_check(
    meal_analyzer: MealAnalyzer = Depends(get_meal_analyzer),
    recipe_generator: RecipeGenerator = Depends(get_recipe_generator),
    chat_assistant: ChatAssistant = Depends(get_chat_assistant)
):
    """Check AI services availability"""
    return {
        "meal_analyzer": meal_analyzer is not None,
        "recipe_generator": recipe_generator is not None,
        "chat_assistant": chat_assistant is not None,
        "status": "healthy" if all([meal_analyzer, recipe_generator, chat_assistant]) else "degraded"
    }
