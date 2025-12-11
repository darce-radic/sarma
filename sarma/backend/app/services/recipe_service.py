"""
Recipe Search and Management Business Logic Service
"""
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.models.recipe import (
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeStep,
    RecipeTag,
    RecipeRating,
    RecipeFavorite
)
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeSearchRequest
)


class RecipeService:
    """Service for recipe search and management"""
    
    @staticmethod
    async def search_recipes(
        db: Session,
        user_id: UUID,
        search_request: RecipeSearchRequest
    ) -> List[Recipe]:
        """
        AI-powered recipe search with health filtering
        
        Uses vector similarity search for semantic matching
        Filters by dietary requirements and health conditions
        """
        query = db.query(Recipe).filter(Recipe.is_active == True)
        
        # Text search on title and description
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    Recipe.title.ilike(search_term),
                    Recipe.description.ilike(search_term)
                )
            )
        
        # Dietary type filter
        if search_request.dietary_type:
            query = query.filter(Recipe.dietary_type == search_request.dietary_type)
        
        # Nutritional filters
        if search_request.max_calories:
            query = query.filter(Recipe.calories <= search_request.max_calories)
        
        if search_request.max_prep_time:
            total_time = search_request.max_prep_time
            query = query.filter(Recipe.total_time_minutes <= total_time)
        
        # Difficulty filter
        if search_request.difficulty:
            query = query.filter(Recipe.difficulty == search_request.difficulty)
        
        # Health score filter
        if search_request.min_health_score:
            query = query.filter(Recipe.health_score >= search_request.min_health_score)
        
        # Filter by allergens
        if search_request.exclude_allergens:
            for allergen in search_request.exclude_allergens:
                if allergen.lower() == "gluten":
                    query = query.filter(Recipe.is_gluten_free == True)
                elif allergen.lower() == "dairy":
                    query = query.filter(Recipe.is_dairy_free == True)
                elif allergen.lower() == "nuts":
                    query = query.filter(Recipe.is_nut_free == True)
        
        # Health condition filters
        if search_request.health_conditions:
            conditions_lower = [c.lower() for c in search_request.health_conditions]
            
            if any("diabetes" in c for c in conditions_lower):
                query = query.filter(Recipe.is_diabetic_friendly == True)
            
            if any("heart" in c or "cardiovascular" in c for c in conditions_lower):
                query = query.filter(Recipe.is_heart_healthy == True)
            
            if any("hypertension" in c or "blood pressure" in c for c in conditions_lower):
                query = query.filter(Recipe.is_low_sodium == True)
        
        # Sort by relevance (default: rating)
        query = query.order_by(desc(Recipe.rating_avg))
        
        # Pagination
        offset = (search_request.page - 1) * search_request.page_size
        query = query.offset(offset).limit(search_request.page_size)
        
        return query.all()
    
    @staticmethod
    async def search_recipes_semantic(
        db: Session,
        user_id: UUID,
        query_text: str,
        query_embedding: List[float],
        limit: int = 20
    ) -> List[Recipe]:
        """
        Semantic search using vector embeddings
        
        TODO: Implement vector similarity search with pgvector
        Uses cosine similarity on recipe embeddings
        """
        # Vector search using pgvector
        # recipes = db.query(Recipe).order_by(
        #     Recipe.embedding.cosine_distance(query_embedding)
        # ).limit(limit).all()
        
        # Fallback to text search for now
        search_term = f"%{query_text}%"
        recipes = db.query(Recipe).filter(
            and_(
                Recipe.is_active == True,
                or_(
                    Recipe.title.ilike(search_term),
                    Recipe.description.ilike(search_term)
                )
            )
        ).limit(limit).all()
        
        return recipes
    
    @staticmethod
    async def create_recipe(
        db: Session,
        user_id: UUID,
        recipe_data: RecipeCreate
    ) -> Recipe:
        """Create a new recipe with ingredients and steps"""
        
        # Calculate total time
        total_time = recipe_data.prep_time_minutes + recipe_data.cook_time_minutes
        
        # Create recipe
        recipe = Recipe(
            title=recipe_data.title,
            description=recipe_data.description,
            prep_time_minutes=recipe_data.prep_time_minutes,
            cook_time_minutes=recipe_data.cook_time_minutes,
            total_time_minutes=total_time,
            servings=recipe_data.servings,
            difficulty=recipe_data.difficulty,
            dietary_type=recipe_data.dietary_type,
            created_by_user_id=user_id,
            # Nutritional data will be calculated from ingredients
            calories=0,
            protein_g=0,
            carbs_g=0,
            fat_g=0
        )
        
        db.add(recipe)
        db.flush()  # Get recipe ID
        
        # Add ingredients
        for idx, ingredient_data in enumerate(recipe_data.ingredients):
            ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                name=ingredient_data["name"],
                quantity=ingredient_data["quantity"],
                unit=ingredient_data["unit"],
                notes=ingredient_data.get("notes"),
                order_index=idx,
                is_optional=ingredient_data.get("is_optional", False),
                ingredient_group=ingredient_data.get("group")
            )
            db.add(ingredient)
        
        # Add cooking steps
        if recipe_data.instructions and "steps" in recipe_data.instructions:
            for step_data in recipe_data.instructions["steps"]:
                step = RecipeStep(
                    recipe_id=recipe.id,
                    step_number=step_data["step"],
                    instruction=step_data["instruction"],
                    duration_minutes=step_data.get("duration_minutes")
                )
                db.add(step)
        
        # Add tags
        if recipe_data.tags:
            for tag_name in recipe_data.tags:
                tag = RecipeTag(
                    recipe_id=recipe.id,
                    tag=tag_name.lower()
                )
                db.add(tag)
        
        db.commit()
        db.refresh(recipe)
        
        # TODO: Calculate nutrition and generate embedding
        # await RecipeService._calculate_nutrition(db, recipe.id)
        # await RecipeService._generate_embedding(db, recipe.id)
        
        return recipe
    
    @staticmethod
    async def get_recipe(
        db: Session,
        recipe_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[Recipe]:
        """Get recipe by ID and increment view count"""
        recipe = db.query(Recipe).filter(
            Recipe.id == recipe_id,
            Recipe.is_active == True
        ).first()
        
        if recipe:
            # Increment view count
            recipe.view_count += 1
            db.commit()
        
        return recipe
    
    @staticmethod
    async def update_recipe(
        db: Session,
        recipe_id: UUID,
        user_id: UUID,
        update_data: RecipeUpdate
    ) -> Optional[Recipe]:
        """Update recipe (only by creator)"""
        recipe = db.query(Recipe).filter(
            Recipe.id == recipe_id,
            Recipe.created_by_user_id == user_id
        ).first()
        
        if not recipe:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(recipe, field, value)
        
        recipe.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(recipe)
        
        return recipe
    
    @staticmethod
    async def rate_recipe(
        db: Session,
        recipe_id: UUID,
        user_id: UUID,
        rating: int,
        review: Optional[str] = None
    ) -> RecipeRating:
        """Add or update recipe rating"""
        
        # Check if user already rated
        existing_rating = db.query(RecipeRating).filter(
            RecipeRating.recipe_id == recipe_id,
            RecipeRating.user_id == user_id
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.review = review
            existing_rating.updated_at = datetime.utcnow()
            db.commit()
            rating_obj = existing_rating
        else:
            # Create new rating
            rating_obj = RecipeRating(
                recipe_id=recipe_id,
                user_id=user_id,
                rating=rating,
                review=review
            )
            db.add(rating_obj)
            db.commit()
        
        # Update recipe average rating
        await RecipeService._update_recipe_rating(db, recipe_id)
        
        return rating_obj
    
    @staticmethod
    async def favorite_recipe(
        db: Session,
        recipe_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None
    ) -> RecipeFavorite:
        """Add recipe to favorites"""
        
        # Check if already favorited
        existing = db.query(RecipeFavorite).filter(
            RecipeFavorite.recipe_id == recipe_id,
            RecipeFavorite.user_id == user_id
        ).first()
        
        if existing:
            return existing
        
        favorite = RecipeFavorite(
            recipe_id=recipe_id,
            user_id=user_id,
            notes=notes
        )
        db.add(favorite)
        
        # Update favorite count
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if recipe:
            recipe.favorite_count += 1
        
        db.commit()
        db.refresh(favorite)
        
        return favorite
    
    @staticmethod
    async def unfavorite_recipe(
        db: Session,
        recipe_id: UUID,
        user_id: UUID
    ) -> bool:
        """Remove recipe from favorites"""
        favorite = db.query(RecipeFavorite).filter(
            RecipeFavorite.recipe_id == recipe_id,
            RecipeFavorite.user_id == user_id
        ).first()
        
        if not favorite:
            return False
        
        db.delete(favorite)
        
        # Update favorite count
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if recipe and recipe.favorite_count > 0:
            recipe.favorite_count -= 1
        
        db.commit()
        return True
    
    @staticmethod
    async def get_user_favorites(
        db: Session,
        user_id: UUID,
        limit: int = 50
    ) -> List[Recipe]:
        """Get user's favorite recipes"""
        favorites = db.query(Recipe).join(
            RecipeFavorite,
            Recipe.id == RecipeFavorite.recipe_id
        ).filter(
            RecipeFavorite.user_id == user_id,
            Recipe.is_active == True
        ).order_by(desc(RecipeFavorite.created_at)).limit(limit).all()
        
        return favorites
    
    @staticmethod
    async def get_recommended_recipes(
        db: Session,
        user_id: UUID,
        limit: int = 20
    ) -> List[Recipe]:
        """
        Get personalized recipe recommendations
        
        Based on:
        - User's health conditions
        - Dietary preferences
        - Past favorites and ratings
        - Nutritional goals
        """
        # TODO: Implement personalized recommendations
        # For now, return highly rated recipes
        recipes = db.query(Recipe).filter(
            Recipe.is_active == True,
            Recipe.rating_avg >= 4.0
        ).order_by(desc(Recipe.rating_avg)).limit(limit).all()
        
        return recipes
    
    @staticmethod
    async def _update_recipe_rating(db: Session, recipe_id: UUID):
        """Recalculate recipe average rating"""
        from sqlalchemy import func
        
        result = db.query(
            func.avg(RecipeRating.rating).label('avg_rating'),
            func.count(RecipeRating.id).label('count')
        ).filter(RecipeRating.recipe_id == recipe_id).first()
        
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if recipe:
            recipe.rating_avg = float(result.avg_rating) if result.avg_rating else 0.0
            recipe.rating_count = result.count
            db.commit()
    
    @staticmethod
    async def _calculate_nutrition(db: Session, recipe_id: UUID):
        """
        Calculate nutritional information from ingredients
        
        TODO: Integrate with nutrition API or database
        """
        pass
    
    @staticmethod
    async def _generate_embedding(db: Session, recipe_id: UUID):
        """
        Generate vector embedding for semantic search
        
        TODO: Use OpenAI embeddings API
        """
        pass
