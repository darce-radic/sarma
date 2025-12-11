"""
AI Configuration and Service Factory
Centralized AI service initialization
"""

import os
from typing import Optional
from functools import lru_cache

from ..services.ai.meal_analyzer import MealAnalyzer
from ..services.ai.recipe_generator import RecipeGenerator
from ..services.ai.chat_assistant import ChatAssistant
from ..services.ai.gemini_service import GeminiService
from ..services.ai.openai_service import OpenAIVisionService
from ..services.ai.base import AIProvider


class AIServiceFactory:
    """Factory for creating AI service instances"""
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Validate API keys
        if not self.gemini_api_key:
            print("Warning: GEMINI_API_KEY not set. Gemini services will not be available.")
        
        if not self.openai_api_key:
            print("Warning: OPENAI_API_KEY not set. GPT-4 services will not be available.")
    
    @lru_cache()
    def get_gemini_service(self) -> Optional[GeminiService]:
        """Get Gemini service instance (cached)"""
        if not self.gemini_api_key:
            return None
        return GeminiService(self.gemini_api_key)
    
    @lru_cache()
    def get_openai_service(self) -> Optional[OpenAIVisionService]:
        """Get OpenAI service instance (cached)"""
        if not self.openai_api_key:
            return None
        return OpenAIVisionService(self.openai_api_key)
    
    @lru_cache()
    def get_meal_analyzer(self) -> Optional[MealAnalyzer]:
        """Get Meal Analyzer instance (cached)"""
        if not self.gemini_api_key or not self.openai_api_key:
            print("Warning: Both API keys required for MealAnalyzer")
            return None
        
        return MealAnalyzer(
            gemini_api_key=self.gemini_api_key,
            openai_api_key=self.openai_api_key
        )
    
    @lru_cache()
    def get_recipe_generator(self) -> Optional[RecipeGenerator]:
        """Get Recipe Generator instance (cached)"""
        if not self.gemini_api_key or not self.openai_api_key:
            print("Warning: Both API keys required for RecipeGenerator")
            return None
        
        return RecipeGenerator(
            gemini_api_key=self.gemini_api_key,
            openai_api_key=self.openai_api_key
        )
    
    @lru_cache()
    def get_chat_assistant(self) -> Optional[ChatAssistant]:
        """Get Chat Assistant instance (cached)"""
        if not self.gemini_api_key or not self.openai_api_key:
            print("Warning: Both API keys required for ChatAssistant")
            return None
        
        return ChatAssistant(
            gemini_api_key=self.gemini_api_key,
            openai_api_key=self.openai_api_key
        )
    
    def is_available(self, provider: AIProvider) -> bool:
        """Check if a specific AI provider is available"""
        if provider == AIProvider.GEMINI_FLASH:
            return bool(self.gemini_api_key)
        elif provider == AIProvider.GPT4_VISION:
            return bool(self.openai_api_key)
        return False


# Global factory instance
_ai_factory: Optional[AIServiceFactory] = None


def get_ai_factory() -> AIServiceFactory:
    """Get or create global AI factory instance"""
    global _ai_factory
    if _ai_factory is None:
        _ai_factory = AIServiceFactory()
    return _ai_factory


# Convenience functions for dependency injection
def get_meal_analyzer() -> Optional[MealAnalyzer]:
    """FastAPI dependency for meal analyzer"""
    return get_ai_factory().get_meal_analyzer()


def get_recipe_generator() -> Optional[RecipeGenerator]:
    """FastAPI dependency for recipe generator"""
    return get_ai_factory().get_recipe_generator()


def get_chat_assistant() -> Optional[ChatAssistant]:
    """FastAPI dependency for chat assistant"""
    return get_ai_factory().get_chat_assistant()
