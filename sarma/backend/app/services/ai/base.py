"""
Base AI Service Classes
Abstract interfaces for multi-model AI integration
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel
from datetime import datetime


class AIProvider(str, Enum):
    """AI Model Providers"""
    GEMINI_FLASH = "gemini-flash"
    GPT4_VISION = "gpt4-vision"
    CLAUDE_VISION = "claude-vision"


class AIConfig(BaseModel):
    """AI Configuration"""
    provider: AIProvider
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30


class AIResponse(BaseModel):
    """Standardized AI Response"""
    provider: AIProvider
    model: str
    content: str
    confidence: float  # 0.0 to 1.0
    tokens_used: int
    cost_usd: float
    response_time_ms: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "gemini-flash",
                "model": "gemini-2.0-flash",
                "content": "Chicken breast with rice and vegetables",
                "confidence": 0.92,
                "tokens_used": 256,
                "cost_usd": 0.0012,
                "response_time_ms": 1234,
                "timestamp": "2024-12-11T14:00:00Z"
            }
        }


class BaseAIService(ABC):
    """Abstract base class for AI services"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.provider = config.provider
        
    @abstractmethod
    async def analyze_image(
        self, 
        image_url: str, 
        prompt: str,
        **kwargs
    ) -> AIResponse:
        """Analyze an image with AI vision model"""
        pass
    
    @abstractmethod
    async def generate_text(
        self, 
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """Generate text response"""
        pass
    
    @abstractmethod
    async def chat(
        self, 
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AIResponse:
        """Chat conversation"""
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost in USD"""
        # Override in subclasses with actual pricing
        return 0.0
    
    def assess_confidence(self, response: str) -> float:
        """
        Assess confidence score based on response characteristics
        Returns 0.0 to 1.0
        """
        # Basic heuristics - can be improved with ML
        confidence = 0.8  # Default
        
        # Lower confidence if response contains uncertainty phrases
        uncertainty_phrases = [
            "might be", "could be", "possibly", "probably",
            "not sure", "unclear", "difficult to tell"
        ]
        
        lower_response = response.lower()
        for phrase in uncertainty_phrases:
            if phrase in lower_response:
                confidence -= 0.1
        
        # Higher confidence if response is detailed and specific
        if len(response) > 200:
            confidence += 0.05
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, confidence))


class NutritionData(BaseModel):
    """Standardized nutrition data structure"""
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    
    # Meal components
    ingredients: List[str] = []
    portions: Optional[Dict[str, str]] = None
    meal_type: Optional[str] = None  # breakfast, lunch, dinner, snack
    
    # Confidence and metadata
    confidence: float = 0.8
    notes: Optional[str] = None


class RecipeData(BaseModel):
    """Recipe structure"""
    name: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    prep_time_min: int
    cook_time_min: int
    servings: int
    difficulty: str  # easy, medium, hard
    
    # Nutrition per serving
    nutrition: NutritionData
    
    # Tags and categories
    tags: List[str] = []
    cuisine: Optional[str] = None
    dietary_info: List[str] = []  # vegetarian, vegan, gluten-free, etc.
