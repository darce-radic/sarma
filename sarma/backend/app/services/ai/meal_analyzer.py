"""
Meal Analyzer with Multi-Model AI
Smart routing between Gemini Flash and GPT-4 Vision
"""

import json
import re
from typing import Optional, Dict
from datetime import datetime

from .base import NutritionData, AIResponse, AIProvider
from .gemini_service import GeminiService
from .openai_service import OpenAIVisionService


class MealAnalyzer:
    """
    Smart meal analysis with multi-model routing
    - Primary: Gemini Flash (fast, cheap)
    - Fallback: GPT-4 Vision (high quality)
    """
    
    CONFIDENCE_THRESHOLD = 0.7  # Upgrade to GPT-4 if below this
    
    def __init__(
        self, 
        gemini_api_key: str, 
        openai_api_key: str,
        default_provider: AIProvider = AIProvider.GEMINI_FLASH
    ):
        self.gemini = GeminiService(gemini_api_key)
        self.gpt4 = OpenAIVisionService(openai_api_key)
        self.default_provider = default_provider
        
    async def analyze_meal(
        self, 
        image_url: str,
        user_tier: str = "free",
        force_provider: Optional[AIProvider] = None
    ) -> Dict:
        """
        Analyze meal photo and extract nutrition data
        
        Args:
            image_url: URL or base64 image
            user_tier: "free" or "premium"
            force_provider: Override auto-selection
            
        Returns:
            Dict with nutrition data and metadata
        """
        # Determine which AI model to use
        provider = self._select_provider(user_tier, force_provider)
        
        # Analyze with selected provider
        if provider == AIProvider.GEMINI_FLASH:
            result = await self._analyze_with_gemini(image_url)
            
            # If confidence is low, upgrade to GPT-4
            if result.confidence < self.CONFIDENCE_THRESHOLD and user_tier == "premium":
                result = await self._analyze_with_gpt4(image_url)
                
        else:  # GPT-4
            result = await self._analyze_with_gpt4(image_url)
        
        # Parse nutrition data from AI response
        nutrition = self._parse_nutrition(result.content)
        
        return {
            "nutrition": nutrition.model_dump(),
            "ai_metadata": {
                "provider": result.provider,
                "model": result.model,
                "confidence": result.confidence,
                "cost_usd": result.cost_usd,
                "response_time_ms": result.response_time_ms,
                "tokens_used": result.tokens_used,
                "error": result.error
            },
            "analyzed_at": datetime.now().isoformat()
        }
    
    async def _analyze_with_gemini(self, image_url: str) -> AIResponse:
        """Analyze meal with Gemini Flash"""
        prompt = self._get_analysis_prompt()
        return await self.gemini.analyze_image(image_url, prompt)
    
    async def _analyze_with_gpt4(self, image_url: str) -> AIResponse:
        """Analyze meal with GPT-4 Vision"""
        prompt = self._get_analysis_prompt()
        return await self.gpt4.analyze_image(image_url, prompt, detail="high")
    
    def _select_provider(
        self, 
        user_tier: str, 
        force_provider: Optional[AIProvider]
    ) -> AIProvider:
        """
        Smart provider selection logic
        
        Logic:
        - If forced, use that
        - Premium users get GPT-4
        - Free users get Gemini
        """
        if force_provider:
            return force_provider
        
        if user_tier == "premium":
            return AIProvider.GPT4_VISION
        
        return AIProvider.GEMINI_FLASH
    
    def _get_analysis_prompt(self) -> str:
        """Generate comprehensive meal analysis prompt"""
        return """Analyze this meal photo and provide detailed nutrition information.

Your response MUST be in valid JSON format following this structure:

{
  "meal_name": "Brief description of the meal",
  "ingredients": ["ingredient1", "ingredient2", ...],
  "portions": {
    "ingredient1": "estimated amount (e.g., 150g, 1 cup)",
    "ingredient2": "estimated amount"
  },
  "nutrition": {
    "calories": 450,
    "protein_g": 25.5,
    "carbs_g": 45.0,
    "fat_g": 15.0,
    "fiber_g": 5.0,
    "sugar_g": 8.0,
    "sodium_mg": 650
  },
  "meal_type": "breakfast|lunch|dinner|snack",
  "confidence_notes": "Any uncertainties or assumptions made"
}

Instructions:
1. Identify ALL visible food items
2. Estimate portion sizes based on typical serving sizes
3. Calculate total nutrition for the ENTIRE meal
4. Be as accurate as possible with nutritional values
5. Include notes about any uncertainties
6. If you cannot clearly identify something, mention it in confidence_notes

Return ONLY valid JSON, no additional text before or after."""
    
    def _parse_nutrition(self, ai_response: str) -> NutritionData:
        """
        Parse AI response into structured NutritionData
        
        Handles both JSON and natural language responses
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Fallback: try parsing entire response
                data = json.loads(ai_response)
            
            # Extract nutrition data
            nutrition_raw = data.get("nutrition", {})
            
            return NutritionData(
                calories=float(nutrition_raw.get("calories", 0)),
                protein_g=float(nutrition_raw.get("protein_g", 0)),
                carbs_g=float(nutrition_raw.get("carbs_g", 0)),
                fat_g=float(nutrition_raw.get("fat_g", 0)),
                fiber_g=float(nutrition_raw.get("fiber_g", 0)) if nutrition_raw.get("fiber_g") else None,
                sugar_g=float(nutrition_raw.get("sugar_g", 0)) if nutrition_raw.get("sugar_g") else None,
                sodium_mg=float(nutrition_raw.get("sodium_mg", 0)) if nutrition_raw.get("sodium_mg") else None,
                
                ingredients=data.get("ingredients", []),
                portions=data.get("portions", {}),
                meal_type=data.get("meal_type"),
                confidence=0.8,  # Base confidence
                notes=data.get("confidence_notes", "")
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback: parse natural language response
            return self._parse_natural_language(ai_response)
    
    def _parse_natural_language(self, text: str) -> NutritionData:
        """
        Fallback parser for natural language responses
        Uses regex to extract nutrition values
        """
        def extract_number(pattern: str, default: float = 0.0) -> float:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
            return default
        
        calories = extract_number(r'calories?:?\s*(\d+\.?\d*)')
        protein = extract_number(r'protein:?\s*(\d+\.?\d*)g?')
        carbs = extract_number(r'carb(?:ohydrate)?s?:?\s*(\d+\.?\d*)g?')
        fat = extract_number(r'fat:?\s*(\d+\.?\d*)g?')
        fiber = extract_number(r'fiber:?\s*(\d+\.?\d*)g?')
        
        # Extract ingredients (look for lists)
        ingredients = []
        ingredients_match = re.search(r'ingredients?:?\s*([^\n]+)', text, re.IGNORECASE)
        if ingredients_match:
            ingredients_text = ingredients_match.group(1)
            ingredients = [i.strip() for i in re.split(r'[,;]', ingredients_text) if i.strip()]
        
        return NutritionData(
            calories=calories,
            protein_g=protein,
            carbs_g=carbs,
            fat_g=fat,
            fiber_g=fiber if fiber > 0 else None,
            ingredients=ingredients,
            confidence=0.6,  # Lower confidence for parsed responses
            notes="Parsed from natural language response (fallback mode)"
        )
    
    async def quick_calorie_estimate(self, image_url: str) -> Dict:
        """
        Fast calorie estimate (Gemini only, simplified prompt)
        For quick previews and free tier
        """
        prompt = """Analyze this meal and provide a quick estimate:

Return JSON format:
{
  "calories": <estimated calories>,
  "description": "brief meal description"
}"""
        
        result = await self.gemini.analyze_image(image_url, prompt)
        
        try:
            data = json.loads(result.content)
            return {
                "calories": data.get("calories", 0),
                "description": data.get("description", "Unknown meal"),
                "cost_usd": result.cost_usd,
                "response_time_ms": result.response_time_ms
            }
        except:
            return {
                "calories": 0,
                "description": "Could not analyze",
                "error": result.error
            }
