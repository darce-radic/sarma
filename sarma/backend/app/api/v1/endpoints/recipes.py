"""
Recipe API Endpoints
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeSearchRequest,
    RecipeIngredientResponse
)
from app.services.recipe_service import RecipeService

router = APIRouter()


@router.post("/search", response_model=List[RecipeResponse])
async def search_recipes(
    search_request: RecipeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search recipes with AI-powered filtering
    
    Supports:
    - Text search on title and description
    - Dietary type filtering
    - Nutritional constraints (calories, prep time)
    - Health condition filtering
    - Allergen exclusion
    """
    recipes = await RecipeService.search_recipes(
        db,
        current_user.id,
        search_request
    )
    return recipes


@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new recipe
    
    Automatically calculates:
    - Total cooking time
    - Nutritional information (from ingredients)
    - Health score
    - Vector embeddings for semantic search
    """
    recipe = await RecipeService.create_recipe(
        db,
        current_user.id,
        recipe_data
    )
    return recipe


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recipe by ID (increments view count)"""
    recipe = await RecipeService.get_recipe(db, recipe_id, current_user.id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: UUID,
    update_data: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update recipe (only by creator)"""
    recipe = await RecipeService.update_recipe(
        db,
        recipe_id,
        current_user.id,
        update_data
    )
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found or you don't have permission to edit"
        )
    
    return recipe


@router.post("/{recipe_id}/rate")
async def rate_recipe(
    recipe_id: UUID,
    rating: int,
    review: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add or update recipe rating (1-5 stars)"""
    if not 1 <= rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    rating_obj = await RecipeService.rate_recipe(
        db,
        recipe_id,
        current_user.id,
        rating,
        review
    )
    
    return {
        "message": "Rating submitted successfully",
        "rating": rating_obj.rating
    }


@router.post("/{recipe_id}/favorite")
async def favorite_recipe(
    recipe_id: UUID,
    notes: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add recipe to favorites"""
    favorite = await RecipeService.favorite_recipe(
        db,
        recipe_id,
        current_user.id,
        notes
    )
    
    return {
        "message": "Recipe added to favorites",
        "favorite_id": favorite.id
    }


@router.delete("/{recipe_id}/favorite")
async def unfavorite_recipe(
    recipe_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove recipe from favorites"""
    success = await RecipeService.unfavorite_recipe(
        db,
        recipe_id,
        current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    return {"message": "Recipe removed from favorites"}


@router.get("/favorites/me", response_model=List[RecipeResponse])
async def get_my_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's favorite recipes"""
    favorites = await RecipeService.get_user_favorites(
        db,
        current_user.id
    )
    return favorites


@router.get("/recommendations/me", response_model=List[RecipeResponse])
async def get_recommendations(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recipe recommendations
    
    Based on:
    - User's health conditions
    - Dietary preferences
    - Past favorites and ratings
    - Nutritional goals
    """
    recommendations = await RecipeService.get_recommended_recipes(
        db,
        current_user.id,
        limit
    )
    return recommendations


@router.get("/{recipe_id}/similar", response_model=List[RecipeResponse])
async def get_similar_recipes(
    recipe_id: UUID,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recipes similar to the given recipe"""
    from app.services.vector_service import VectorSearchService
    
    similar = await VectorSearchService.find_similar_recipes(
        recipe_id,
        db,
        limit
    )
    return similar
