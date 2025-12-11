"""
AI Recipe Generator
Creates personalized recipes based on ingredients, preferences, and health goals
"""

import json
import re
from typing import List, Optional, Dict
from datetime import datetime

from .base import RecipeData, NutritionData, AIProvider
from .gemini_service import GeminiService
from .openai_service import OpenAIVisionService


class RecipeGenerator:
    """
    AI-powered recipe generation
    Uses GPT-4 for creative recipes, Gemini for speed
    """
    
    def __init__(self, gemini_api_key: str, openai_api_key: str):
        self.gemini = GeminiService(gemini_api_key)
        self.gpt4 = OpenAIVisionService(openai_api_key)
    
    async def generate_recipe(
        self,
        ingredients: Optional[List[str]] = None,
        dietary_restrictions: Optional[List[str]] = None,
        health_goals: Optional[List[str]] = None,
        cuisine: Optional[str] = None,
        max_calories: Optional[int] = None,
        meal_type: Optional[str] = None,
        use_gpt4: bool = False
    ) -> Dict:
        """
        Generate personalized recipe
        
        Args:
            ingredients: Available ingredients
            dietary_restrictions: e.g., ["vegetarian", "gluten-free"]
            health_goals: e.g., ["high-protein", "low-carb"]
            cuisine: e.g., "Italian", "Mexican"
            max_calories: Maximum calories per serving
            meal_type: "breakfast", "lunch", "dinner", "snack"
            use_gpt4: Use GPT-4 for more creative recipes
            
        Returns:
            Dict with recipe data and metadata
        """
        prompt = self._build_recipe_prompt(
            ingredients=ingredients,
            dietary_restrictions=dietary_restrictions,
            health_goals=health_goals,
            cuisine=cuisine,
            max_calories=max_calories,
            meal_type=meal_type
        )
        
        # Select AI provider
        if use_gpt4:
            result = await self.gpt4.generate_text(prompt)
        else:
            result = await self.gemini.generate_text(prompt)
        
        # Parse recipe from response
        recipe = self._parse_recipe(result.content)
        
        return {
            "recipe": recipe.model_dump(),
            "ai_metadata": {
                "provider": result.provider,
                "model": result.model,
                "confidence": result.confidence,
                "cost_usd": result.cost_usd,
                "response_time_ms": result.response_time_ms
            },
            "generated_at": datetime.now().isoformat()
        }
    
    async def generate_from_photo(
        self,
        image_url: str,
        preference: str = "similar"
    ) -> Dict:
        """
        Generate recipe based on a meal photo
        
        Args:
            image_url: Photo of a meal
            preference: "similar" (recreate), "healthier" (healthier version), "different" (inspired by)
            
        Returns:
            Recipe inspired by the photo
        """
        if preference == "healthier":
            extra_instruction = "Create a healthier version with fewer calories, less fat, and more vegetables."
        elif preference == "different":
            extra_instruction = "Create a different recipe inspired by the flavors and ingredients in this dish."
        else:  # similar
            extra_instruction = "Create a recipe that recreates this dish as accurately as possible."
        
        prompt = f"""Analyze this meal photo and create a detailed recipe.

{extra_instruction}

Return JSON format:
{{
  "name": "Recipe name",
  "description": "Brief description",
  "ingredients": ["ingredient 1 with amount", "ingredient 2 with amount", ...],
  "instructions": ["Step 1", "Step 2", ...],
  "prep_time_min": 15,
  "cook_time_min": 30,
  "servings": 4,
  "difficulty": "easy|medium|hard",
  "nutrition_per_serving": {{
    "calories": 350,
    "protein_g": 25,
    "carbs_g": 40,
    "fat_g": 10,
    "fiber_g": 5
  }},
  "tags": ["quick", "healthy", ...],
  "cuisine": "Italian",
  "dietary_info": ["vegetarian", ...]
}}"""
        
        # Use GPT-4 for photo-based recipes (better vision understanding)
        result = await self.gpt4.analyze_image(image_url, prompt, detail="high")
        
        recipe = self._parse_recipe(result.content)
        
        return {
            "recipe": recipe.model_dump(),
            "ai_metadata": {
                "provider": result.provider,
                "cost_usd": result.cost_usd,
                "response_time_ms": result.response_time_ms
            }
        }
    
    async def suggest_recipes(
        self,
        user_preferences: Dict,
        count: int = 5,
        use_gpt4: bool = False
    ) -> List[Dict]:
        """
        Suggest multiple recipes based on user preferences
        
        Args:
            user_preferences: User dietary preferences, health goals, etc.
            count: Number of recipes to suggest
            use_gpt4: Use GPT-4 for suggestions
            
        Returns:
            List of recipe suggestions
        """
        prompt = f"""Suggest {count} recipe ideas for a user with these preferences:

{json.dumps(user_preferences, indent=2)}

Return JSON array:
[
  {{
    "name": "Recipe name",
    "description": "Why this recipe fits the user",
    "key_benefits": ["benefit1", "benefit2"],
    "estimated_calories": 400,
    "prep_time_min": 20,
    "difficulty": "easy"
  }},
  ...
]

Focus on variety - different meal types, cuisines, and cooking methods."""
        
        if use_gpt4:
            result = await self.gpt4.generate_text(prompt)
        else:
            result = await self.gemini.generate_text(prompt)
        
        try:
            # Extract JSON array
            json_match = re.search(r'\[.*\]', result.content, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions[:count]
        except:
            pass
        
        return []
    
    def _build_recipe_prompt(
        self,
        ingredients: Optional[List[str]],
        dietary_restrictions: Optional[List[str]],
        health_goals: Optional[List[str]],
        cuisine: Optional[str],
        max_calories: Optional[int],
        meal_type: Optional[str]
    ) -> str:
        """Build comprehensive recipe generation prompt"""
        
        prompt = "Create a detailed, delicious recipe with the following requirements:\n\n"
        
        if ingredients:
            prompt += f"**Must include these ingredients:** {', '.join(ingredients)}\n\n"
        
        if dietary_restrictions:
            prompt += f"**Dietary restrictions:** {', '.join(dietary_restrictions)}\n\n"
        
        if health_goals:
            prompt += f"**Health goals:** {', '.join(health_goals)}\n\n"
        
        if cuisine:
            prompt += f"**Cuisine type:** {cuisine}\n\n"
        
        if max_calories:
            prompt += f"**Max calories per serving:** {max_calories}\n\n"
        
        if meal_type:
            prompt += f"**Meal type:** {meal_type}\n\n"
        
        prompt += """
Return a complete recipe in JSON format:

{
  "name": "Recipe name",
  "description": "Appetizing description (2-3 sentences)",
  "ingredients": [
    "1 cup ingredient 1",
    "2 tablespoons ingredient 2",
    ...
  ],
  "instructions": [
    "Step 1: Detailed instruction",
    "Step 2: Detailed instruction",
    ...
  ],
  "prep_time_min": 15,
  "cook_time_min": 30,
  "servings": 4,
  "difficulty": "easy|medium|hard",
  "nutrition_per_serving": {
    "calories": 350,
    "protein_g": 25,
    "carbs_g": 40,
    "fat_g": 10,
    "fiber_g": 5,
    "sugar_g": 8,
    "sodium_mg": 500
  },
  "tags": ["quick", "healthy", "family-friendly"],
  "cuisine": "Italian",
  "dietary_info": ["vegetarian", "gluten-free"]
}

Make it delicious, practical, and aligned with the requirements!"""
        
        return prompt
    
    def _parse_recipe(self, ai_response: str) -> RecipeData:
        """Parse AI response into RecipeData"""
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(ai_response)
            
            # Extract nutrition
            nutrition_raw = data.get("nutrition_per_serving", {})
            nutrition = NutritionData(
                calories=float(nutrition_raw.get("calories", 0)),
                protein_g=float(nutrition_raw.get("protein_g", 0)),
                carbs_g=float(nutrition_raw.get("carbs_g", 0)),
                fat_g=float(nutrition_raw.get("fat_g", 0)),
                fiber_g=float(nutrition_raw.get("fiber_g", 0)) if nutrition_raw.get("fiber_g") else None,
                sugar_g=float(nutrition_raw.get("sugar_g", 0)) if nutrition_raw.get("sugar_g") else None,
                sodium_mg=float(nutrition_raw.get("sodium_mg", 0)) if nutrition_raw.get("sodium_mg") else None
            )
            
            return RecipeData(
                name=data.get("name", "Untitled Recipe"),
                description=data.get("description", ""),
                ingredients=data.get("ingredients", []),
                instructions=data.get("instructions", []),
                prep_time_min=int(data.get("prep_time_min", 0)),
                cook_time_min=int(data.get("cook_time_min", 0)),
                servings=int(data.get("servings", 1)),
                difficulty=data.get("difficulty", "medium"),
                nutrition=nutrition,
                tags=data.get("tags", []),
                cuisine=data.get("cuisine"),
                dietary_info=data.get("dietary_info", [])
            )
            
        except Exception as e:
            # Return minimal recipe on error
            return RecipeData(
                name="Recipe Generation Error",
                description=f"Could not parse recipe: {str(e)}",
                ingredients=[],
                instructions=[],
                prep_time_min=0,
                cook_time_min=0,
                servings=1,
                difficulty="medium",
                nutrition=NutritionData(
                    calories=0, protein_g=0, carbs_g=0, fat_g=0
                )
            )
