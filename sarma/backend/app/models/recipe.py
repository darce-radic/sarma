"""
Recipe and Recipe-Related Models
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Index, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY, JSONB
from pgvector.sqlalchemy import Vector
import enum

from app.core.database import Base


class DietaryType(str, enum.Enum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    PALEO = "paleo"
    LOW_CARB = "low_carb"
    MEDITERRANEAN = "mediterranean"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Recipe(Base):
    """Recipe model with AI-powered nutritional data"""
    __tablename__ = "recipes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Cooking details
    prep_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    cook_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    servings: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(SQLEnum(DifficultyLevel), nullable=False)
    
    # Dietary information
    dietary_type: Mapped[DietaryType] = mapped_column(SQLEnum(DietaryType), nullable=False)
    is_gluten_free: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dairy_free: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nut_free: Mapped[bool] = mapped_column(Boolean, default=False)
    is_low_sodium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_diabetic_friendly: Mapped[bool] = mapped_column(Boolean, default=False)
    is_heart_healthy: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Nutritional summary (calories per serving)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    fiber_g: Mapped[Optional[float]] = mapped_column(Float)
    sugar_g: Mapped[Optional[float]] = mapped_column(Float)
    sodium_mg: Mapped[Optional[float]] = mapped_column(Float)
    
    # Health scoring
    health_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    glycemic_load: Mapped[Optional[float]] = mapped_column(Float)
    inflammation_score: Mapped[Optional[float]] = mapped_column(Float)  # lower is better
    
    # Vector embedding for semantic search
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    
    # Creator and source
    created_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True
    )
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Engagement metrics
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Content
    instructions: Mapped[Optional[dict]] = mapped_column(JSONB)  # Structured step data
    cooking_tips: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    nutrition_details = relationship("RecipeNutrition", back_populates="recipe", uselist=False, cascade="all, delete-orphan")
    steps = relationship("RecipeStep", back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeStep.step_number")
    tags = relationship("RecipeTag", back_populates="recipe", cascade="all, delete-orphan")
    ratings = relationship("RecipeRating", back_populates="recipe", cascade="all, delete-orphan")
    favorites = relationship("RecipeFavorite", back_populates="recipe", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by_user_id])
    
    __table_args__ = (
        Index('idx_recipe_dietary', 'dietary_type'),
        Index('idx_recipe_health_score', 'health_score'),
        Index('idx_recipe_calories', 'calories'),
        Index('idx_recipe_created_at', 'created_at'),
        CheckConstraint('servings > 0', name='check_recipe_servings'),
        CheckConstraint('calories >= 0', name='check_recipe_calories'),
        CheckConstraint('health_score >= 0 AND health_score <= 100', name='check_health_score'),
    )


class RecipeIngredient(Base):
    """Individual ingredients for recipes"""
    __tablename__ = "recipe_ingredients"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recipe_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)  # cup, tbsp, oz, g, etc.
    notes: Mapped[Optional[str]] = mapped_column(String(500))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Ingredient metadata
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    ingredient_group: Mapped[Optional[str]] = mapped_column(String(100))  # "sauce", "marinade", etc.
    
    # Product linking
    suggested_product_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    
    __table_args__ = (
        Index('idx_ingredient_recipe', 'recipe_id'),
        CheckConstraint('quantity > 0', name='check_ingredient_quantity'),
    )


class RecipeNutrition(Base):
    """Detailed nutritional information for recipes"""
    __tablename__ = "recipe_nutrition"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recipe_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Macronutrients (per serving)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    carbohydrates_g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    fiber_g: Mapped[float] = mapped_column(Float, nullable=False)
    sugar_g: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Fat breakdown
    saturated_fat_g: Mapped[Optional[float]] = mapped_column(Float)
    trans_fat_g: Mapped[Optional[float]] = mapped_column(Float)
    polyunsaturated_fat_g: Mapped[Optional[float]] = mapped_column(Float)
    monounsaturated_fat_g: Mapped[Optional[float]] = mapped_column(Float)
    
    # Other nutrients
    cholesterol_mg: Mapped[Optional[float]] = mapped_column(Float)
    sodium_mg: Mapped[float] = mapped_column(Float, nullable=False)
    potassium_mg: Mapped[Optional[float]] = mapped_column(Float)
    calcium_mg: Mapped[Optional[float]] = mapped_column(Float)
    iron_mg: Mapped[Optional[float]] = mapped_column(Float)
    vitamin_a_iu: Mapped[Optional[float]] = mapped_column(Float)
    vitamin_c_mg: Mapped[Optional[float]] = mapped_column(Float)
    vitamin_d_iu: Mapped[Optional[float]] = mapped_column(Float)
    
    # Health metrics
    glycemic_index: Mapped[Optional[float]] = mapped_column(Float)
    glycemic_load: Mapped[Optional[float]] = mapped_column(Float)
    inflammation_score: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    recipe = relationship("Recipe", back_populates="nutrition_details")
    
    __table_args__ = (
        CheckConstraint('calories >= 0', name='check_nutrition_calories'),
        CheckConstraint('protein_g >= 0', name='check_nutrition_protein'),
        CheckConstraint('carbohydrates_g >= 0', name='check_nutrition_carbs'),
        CheckConstraint('fat_g >= 0', name='check_nutrition_fat'),
    )


class RecipeStep(Base):
    """Cooking instructions broken into steps"""
    __tablename__ = "recipe_steps"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recipe_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="steps")
    
    __table_args__ = (
        Index('idx_recipe_step', 'recipe_id', 'step_number'),
        CheckConstraint('step_number > 0', name='check_step_number'),
    )


class RecipeTag(Base):
    """Tags for recipe categorization and search"""
    __tablename__ = "recipe_tags"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recipe_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tag: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="tags")
    
    __table_args__ = (
        Index('idx_recipe_tag_lookup', 'recipe_id', 'tag'),
    )


class RecipeRating(Base):
    """User ratings and reviews for recipes"""
    __tablename__ = "recipe_ratings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recipe_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    review: Mapped[Optional[str]] = mapped_column(Text)
    would_make_again: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    # Photo of user's result
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ratings")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_rating_user_recipe', 'user_id', 'recipe_id', unique=True),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_value'),
    )


class RecipeFavorite(Base):
    """User favorites/bookmarks"""
    __tablename__ = "recipe_favorites"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recipe_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="favorites")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_favorite_user_recipe', 'user_id', 'recipe_id', unique=True),
    )


class RecipeCollection(Base):
    """User-created recipe collections/meal plans"""
    __tablename__ = "recipe_collections"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Recipe IDs in this collection
    recipe_ids: Mapped[List[UUID]] = mapped_column(ARRAY(PG_UUID(as_uuid=True)), default=list)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_collection_user', 'user_id'),
    )
