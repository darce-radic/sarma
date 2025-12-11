"""
External Recipe API Integration Endpoints
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.core.security import get_current_user
from app.models.user import User
from app.services.recipe_api_service import RecipeAPIService, EdamamRecipeService

router = APIRouter()


@router.get("/search")
async def search_external_recipes(
    query: str = Query(..., description="Recipe search query"),
    cuisine: Optional[str] = Query(None, description="Cuisine type"),
    diet: Optional[str] = Query(None, description="Diet type (vegetarian, vegan, keto, etc.)"),
    intolerances: Optional[List[str]] = Query(None, description="Food intolerances"),
    max_results: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """
    Search for recipes using external API (Spoonacular)
    
    - **query**: Recipe name or keywords
    - **cuisine**: Filter by cuisine (italian, mexican, asian, etc.)
    - **diet**: Filter by diet (vegetarian, vegan, keto, paleo, etc.)
    - **intolerances**: Food intolerances (gluten, dairy, egg, etc.)
    - **max_results**: Number of results to return
    """
    recipe_service = RecipeAPIService()
    
    recipes = await recipe_service.search_recipes(
        query=query,
        cuisine=cuisine,
        diet=diet,
        intolerances=intolerances,
        max_results=max_results,
    )
    
    return {
        "query": query,
        "count": len(recipes),
        "recipes": recipes,
    }


@router.get("/details/{recipe_id}")
async def get_recipe_details(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific recipe
    
    - **recipe_id**: Spoonacular recipe ID
    """
    recipe_service = RecipeAPIService()
    recipe = await recipe_service.get_recipe_details(recipe_id)
    
    if not recipe:
        return {"error": "Recipe not found"}
    
    return recipe


@router.get("/by-ingredients")
async def find_recipes_by_ingredients(
    ingredients: List[str] = Query(..., description="List of available ingredients"),
    max_results: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """
    Find recipes that can be made with given ingredients
    
    - **ingredients**: List of ingredient names
    - **max_results**: Number of results to return
    """
    recipe_service = RecipeAPIService()
    
    recipes = await recipe_service.get_recipes_by_ingredients(
        ingredients=ingredients,
        max_results=max_results,
    )
    
    return {
        "ingredients": ingredients,
        "count": len(recipes),
        "recipes": recipes,
    }


@router.get("/similar/{recipe_id}")
async def get_similar_recipes(
    recipe_id: int,
    max_results: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    """
    Get recipes similar to a given recipe
    
    - **recipe_id**: Spoonacular recipe ID
    - **max_results**: Number of similar recipes to return
    """
    recipe_service = RecipeAPIService()
    
    similar = await recipe_service.get_similar_recipes(
        recipe_id=recipe_id,
        max_results=max_results,
    )
    
    return {
        "recipe_id": recipe_id,
        "count": len(similar),
        "similar_recipes": similar,
    }


@router.get("/meal-plan")
async def generate_meal_plan(
    timeframe: str = Query("day", description="Time frame (day/week)"),
    target_calories: Optional[int] = Query(None, description="Target daily calories"),
    diet: Optional[str] = Query(None, description="Diet type"),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a meal plan using external API
    
    - **timeframe**: 'day' or 'week'
    - **target_calories**: Target daily calorie intake
    - **diet**: Diet type (vegetarian, vegan, keto, etc.)
    """
    # This would integrate with Spoonacular's meal planning API
    # For now, return a placeholder
    
    return {
        "message": "Meal plan generation - coming soon!",
        "timeframe": timeframe,
        "target_calories": target_calories,
        "diet": diet,
    }
