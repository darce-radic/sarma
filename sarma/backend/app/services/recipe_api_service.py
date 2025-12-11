"""
Recipe API Integration Service
Integrates with Spoonacular API for recipe data
"""
import httpx
from typing import List, Dict, Optional
from app.core.config import settings


class RecipeAPIService:
    """Service for interacting with external recipe APIs"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SPOONACULAR_API_KEY
        self.base_url = "https://api.spoonacular.com"
        self.timeout = 30.0
        
    async def search_recipes(
        self,
        query: str,
        cuisine: Optional[str] = None,
        diet: Optional[str] = None,
        intolerances: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[Dict]:
        """
        Search for recipes using Spoonacular API
        
        Args:
            query: Search query (ingredients or recipe name)
            cuisine: Cuisine type (italian, mexican, etc.)
            diet: Diet type (vegetarian, vegan, keto, etc.)
            intolerances: List of intolerances (gluten, dairy, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            List of recipe dictionaries
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {
                "apiKey": self.api_key,
                "query": query,
                "number": max_results,
                "addRecipeInformation": True,
                "fillIngredients": True,
            }
            
            if cuisine:
                params["cuisine"] = cuisine
            if diet:
                params["diet"] = diet
            if intolerances:
                params["intolerances"] = ",".join(intolerances)
            
            try:
                response = await client.get(
                    f"{self.base_url}/recipes/complexSearch",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Transform to our format
                recipes = []
                for recipe in data.get("results", []):
                    recipes.append({
                        "id": recipe["id"],
                        "name": recipe["title"],
                        "image_url": recipe.get("image"),
                        "ready_in_minutes": recipe.get("readyInMinutes"),
                        "servings": recipe.get("servings"),
                        "source_url": recipe.get("sourceUrl"),
                        "summary": recipe.get("summary", ""),
                        "nutrition": {
                            "calories": self._extract_nutrient(recipe, "Calories"),
                            "protein": self._extract_nutrient(recipe, "Protein"),
                            "carbs": self._extract_nutrient(recipe, "Carbohydrates"),
                            "fat": self._extract_nutrient(recipe, "Fat"),
                        },
                        "source": "spoonacular",
                    })
                
                return recipes
                
            except httpx.HTTPError as e:
                print(f"Error fetching recipes from Spoonacular: {e}")
                return []
    
    async def get_recipe_details(self, recipe_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific recipe
        
        Args:
            recipe_id: Spoonacular recipe ID
            
        Returns:
            Detailed recipe dictionary or None if not found
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/recipes/{recipe_id}/information",
                    params={
                        "apiKey": self.api_key,
                        "includeNutrition": True,
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract ingredients
                ingredients = []
                for ing in data.get("extendedIngredients", []):
                    ingredients.append({
                        "name": ing["name"],
                        "amount": ing.get("amount"),
                        "unit": ing.get("unit"),
                        "original": ing.get("original"),
                    })
                
                # Extract instructions
                instructions = []
                for step in data.get("analyzedInstructions", [{}])[0].get("steps", []):
                    instructions.append({
                        "number": step["number"],
                        "step": step["step"],
                    })
                
                return {
                    "id": data["id"],
                    "name": data["title"],
                    "description": data.get("summary", ""),
                    "image_url": data.get("image"),
                    "ready_in_minutes": data.get("readyInMinutes"),
                    "servings": data.get("servings"),
                    "ingredients": ingredients,
                    "instructions": instructions,
                    "nutrition": {
                        "calories": self._extract_nutrient(data, "Calories"),
                        "protein": self._extract_nutrient(data, "Protein"),
                        "carbs": self._extract_nutrient(data, "Carbohydrates"),
                        "fat": self._extract_nutrient(data, "Fat"),
                    },
                    "diet_labels": data.get("diets", []),
                    "source_url": data.get("sourceUrl"),
                    "source": "spoonacular",
                }
                
            except httpx.HTTPError as e:
                print(f"Error fetching recipe details: {e}")
                return None
    
    async def get_recipes_by_ingredients(
        self,
        ingredients: List[str],
        max_results: int = 10,
    ) -> List[Dict]:
        """
        Find recipes that can be made with given ingredients
        
        Args:
            ingredients: List of ingredient names
            max_results: Maximum number of results
            
        Returns:
            List of recipe dictionaries
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/recipes/findByIngredients",
                    params={
                        "apiKey": self.api_key,
                        "ingredients": ",".join(ingredients),
                        "number": max_results,
                        "ranking": 2,  # Maximize used ingredients
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                recipes = []
                for recipe in data:
                    recipes.append({
                        "id": recipe["id"],
                        "name": recipe["title"],
                        "image_url": recipe.get("image"),
                        "used_ingredients": len(recipe.get("usedIngredients", [])),
                        "missed_ingredients": len(recipe.get("missedIngredients", [])),
                        "source": "spoonacular",
                    })
                
                return recipes
                
            except httpx.HTTPError as e:
                print(f"Error finding recipes by ingredients: {e}")
                return []
    
    async def get_similar_recipes(
        self,
        recipe_id: int,
        max_results: int = 5,
    ) -> List[Dict]:
        """
        Get recipes similar to a given recipe
        
        Args:
            recipe_id: Spoonacular recipe ID
            max_results: Maximum number of results
            
        Returns:
            List of similar recipe dictionaries
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/recipes/{recipe_id}/similar",
                    params={
                        "apiKey": self.api_key,
                        "number": max_results,
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return [
                    {
                        "id": recipe["id"],
                        "name": recipe["title"],
                        "ready_in_minutes": recipe.get("readyInMinutes"),
                        "servings": recipe.get("servings"),
                        "source": "spoonacular",
                    }
                    for recipe in data
                ]
                
            except httpx.HTTPError as e:
                print(f"Error fetching similar recipes: {e}")
                return []
    
    def _extract_nutrient(self, recipe_data: Dict, nutrient_name: str) -> Optional[float]:
        """Extract nutrient value from recipe data"""
        nutrition = recipe_data.get("nutrition", {})
        nutrients = nutrition.get("nutrients", [])
        
        for nutrient in nutrients:
            if nutrient.get("name") == nutrient_name:
                return nutrient.get("amount")
        
        return None


# Alternative: Edamam Recipe API
class EdamamRecipeService:
    """Alternative recipe API service using Edamam"""
    
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
    ):
        self.app_id = app_id or settings.EDAMAM_APP_ID
        self.app_key = app_key or settings.EDAMAM_APP_KEY
        self.base_url = "https://api.edamam.com/api/recipes/v2"
        self.timeout = 30.0
    
    async def search_recipes(
        self,
        query: str,
        diet: Optional[str] = None,
        health: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[Dict]:
        """Search recipes using Edamam API"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {
                "type": "public",
                "app_id": self.app_id,
                "app_key": self.app_key,
                "q": query,
                "to": max_results,
            }
            
            if diet:
                params["diet"] = diet
            if health:
                params["health"] = health
            
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                recipes = []
                for hit in data.get("hits", []):
                    recipe = hit["recipe"]
                    recipes.append({
                        "id": recipe["uri"].split("#")[-1],
                        "name": recipe["label"],
                        "image_url": recipe.get("image"),
                        "source_url": recipe.get("url"),
                        "calories": recipe.get("calories"),
                        "servings": recipe.get("yield"),
                        "ingredients": [ing["text"] for ing in recipe.get("ingredients", [])],
                        "diet_labels": recipe.get("dietLabels", []),
                        "health_labels": recipe.get("healthLabels", []),
                        "source": "edamam",
                    })
                
                return recipes
                
            except httpx.HTTPError as e:
                print(f"Error fetching recipes from Edamam: {e}")
                return []
