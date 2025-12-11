"""
AI Chat Assistant
Health Q&A, meal suggestions, nutrition advice
"""

from typing import List, Dict, Optional
from datetime import datetime

from .base import AIProvider
from .gemini_service import GeminiService
from .openai_service import OpenAIVisionService


class ChatAssistant:
    """
    AI-powered nutrition and health chat assistant
    Context-aware conversations about food, health, and wellness
    """
    
    SYSTEM_PROMPT = """You are Sarma, an expert nutrition and health assistant. Your role is to:

1. **Provide accurate nutrition advice** based on current scientific evidence
2. **Suggest healthy meals** tailored to user preferences and goals
3. **Answer health questions** about diet, weight management, and wellness
4. **Motivate and encourage** users on their health journey
5. **Be conversational and friendly** while maintaining professionalism

Guidelines:
- Always prioritize user safety - recommend consulting doctors for medical issues
- Provide practical, actionable advice
- Consider dietary restrictions and allergies
- Be positive and encouraging
- Use simple language, avoid excessive jargon
- When unsure, acknowledge limitations

You have access to the user's meal history, health goals, and dietary preferences through context."""
    
    def __init__(
        self, 
        gemini_api_key: str, 
        openai_api_key: str,
        default_provider: AIProvider = AIProvider.GEMINI_FLASH
    ):
        self.gemini = GeminiService(gemini_api_key)
        self.gpt4 = OpenAIVisionService(openai_api_key)
        self.default_provider = default_provider
    
    async def chat(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        user_context: Optional[Dict] = None,
        use_gpt4: bool = False
    ) -> Dict:
        """
        Send a message to the chat assistant
        
        Args:
            message: User's message
            conversation_history: Previous messages [{"role": "user|assistant", "content": "..."}]
            user_context: User's health data, preferences, recent meals
            use_gpt4: Use GPT-4 for complex questions
            
        Returns:
            Dict with assistant response and metadata
        """
        # Build conversation with context
        messages = self._build_conversation(
            message, 
            conversation_history, 
            user_context
        )
        
        # Select provider
        provider = self.gpt4 if use_gpt4 else self.gemini
        
        # Get response
        result = await provider.chat(messages)
        
        return {
            "response": result.content,
            "ai_metadata": {
                "provider": result.provider,
                "model": result.model,
                "confidence": result.confidence,
                "cost_usd": result.cost_usd,
                "response_time_ms": result.response_time_ms,
                "tokens_used": result.tokens_used
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def suggest_meal(
        self,
        meal_type: str,  # breakfast, lunch, dinner, snack
        user_context: Optional[Dict] = None,
        use_gpt4: bool = False
    ) -> Dict:
        """
        Suggest a meal based on user context
        
        Args:
            meal_type: Type of meal
            user_context: User's preferences, goals, recent meals
            use_gpt4: Use GPT-4 for suggestions
            
        Returns:
            Meal suggestion with reasoning
        """
        prompt = f"""The user is asking for a {meal_type} suggestion.

Based on their context:
{self._format_user_context(user_context)}

Suggest a specific {meal_type} that:
1. Fits their dietary preferences and restrictions
2. Helps them reach their health goals
3. Provides good nutrition balance
4. Is practical and enjoyable

Provide:
- Meal name and description
- Why this meal is a good choice for them
- Key nutrition highlights
- Quick preparation tips (if relevant)

Be specific, enthusiastic, and helpful!"""
        
        provider = self.gpt4 if use_gpt4 else self.gemini
        result = await provider.generate_text(prompt)
        
        return {
            "suggestion": result.content,
            "meal_type": meal_type,
            "ai_metadata": {
                "provider": result.provider,
                "cost_usd": result.cost_usd,
                "response_time_ms": result.response_time_ms
            }
        }
    
    async def get_nutrition_advice(
        self,
        question: str,
        user_context: Optional[Dict] = None,
        use_gpt4: bool = True  # Default to GPT-4 for medical/health questions
    ) -> Dict:
        """
        Get specific nutrition or health advice
        
        Args:
            question: User's health/nutrition question
            user_context: User's health data and goals
            use_gpt4: Use GPT-4 (recommended for health questions)
            
        Returns:
            Personalized advice
        """
        context_str = self._format_user_context(user_context)
        
        prompt = f"""The user has a nutrition/health question:

"{question}"

User context:
{context_str}

Provide a helpful, accurate response that:
1. Addresses their specific question
2. Considers their personal context (goals, restrictions, history)
3. Provides actionable advice
4. Includes relevant scientific basis when appropriate
5. Reminds them to consult healthcare providers for medical concerns

Be thorough but concise. Focus on practical guidance."""
        
        provider = self.gpt4 if use_gpt4 else self.gemini
        result = await provider.generate_text(prompt, context=self.SYSTEM_PROMPT)
        
        return {
            "advice": result.content,
            "ai_metadata": {
                "provider": result.provider,
                "cost_usd": result.cost_usd,
                "response_time_ms": result.response_time_ms
            }
        }
    
    async def analyze_diet_trends(
        self,
        recent_meals: List[Dict],
        time_period_days: int = 7,
        use_gpt4: bool = False
    ) -> Dict:
        """
        Analyze user's recent eating patterns and provide insights
        
        Args:
            recent_meals: List of recent meals with nutrition data
            time_period_days: Number of days to analyze
            use_gpt4: Use GPT-4 for analysis
            
        Returns:
            Diet analysis and recommendations
        """
        meals_summary = self._summarize_meals(recent_meals)
        
        prompt = f"""Analyze this user's eating patterns over the last {time_period_days} days:

{meals_summary}

Provide:
1. **Nutrition Trends**: What patterns do you see? (e.g., consistent protein, low vegetables, high sodium)
2. **Strengths**: What are they doing well?
3. **Areas for Improvement**: What could be better?
4. **Specific Recommendations**: 3-5 actionable suggestions to improve their diet
5. **Encouragement**: Positive, motivating message

Be specific, constructive, and encouraging!"""
        
        provider = self.gpt4 if use_gpt4 else self.gemini
        result = await provider.generate_text(prompt, context=self.SYSTEM_PROMPT)
        
        return {
            "analysis": result.content,
            "time_period_days": time_period_days,
            "meals_analyzed": len(recent_meals),
            "ai_metadata": {
                "provider": result.provider,
                "cost_usd": result.cost_usd,
                "response_time_ms": result.response_time_ms
            }
        }
    
    def _build_conversation(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        user_context: Optional[Dict]
    ) -> List[Dict[str, str]]:
        """Build conversation array with system prompt and context"""
        messages = []
        
        # Add system prompt with user context
        system_content = self.SYSTEM_PROMPT
        if user_context:
            system_content += f"\n\nUser Context:\n{self._format_user_context(user_context)}"
        
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history
        if history:
            messages.extend(history)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return messages
    
    def _format_user_context(self, context: Optional[Dict]) -> str:
        """Format user context for AI prompt"""
        if not context:
            return "No user context available"
        
        parts = []
        
        if context.get("health_goals"):
            parts.append(f"**Health Goals:** {', '.join(context['health_goals'])}")
        
        if context.get("dietary_restrictions"):
            parts.append(f"**Dietary Restrictions:** {', '.join(context['dietary_restrictions'])}")
        
        if context.get("daily_calorie_goal"):
            parts.append(f"**Daily Calorie Goal:** {context['daily_calorie_goal']} kcal")
        
        if context.get("recent_meals"):
            parts.append(f"**Recent Meals:** {context['recent_meals']} meals logged")
        
        if context.get("average_daily_calories"):
            parts.append(f"**Avg Daily Calories:** {context['average_daily_calories']} kcal")
        
        if context.get("preferences"):
            parts.append(f"**Preferences:** {context['preferences']}")
        
        return "\n".join(parts) if parts else "No detailed context available"
    
    def _summarize_meals(self, meals: List[Dict]) -> str:
        """Summarize meals for analysis"""
        if not meals:
            return "No meals logged"
        
        summary = []
        for i, meal in enumerate(meals, 1):
            meal_info = f"{i}. {meal.get('name', 'Unnamed meal')}"
            
            if meal.get('nutrition'):
                n = meal['nutrition']
                meal_info += f" - {n.get('calories', 0)} cal, {n.get('protein_g', 0)}g protein, {n.get('carbs_g', 0)}g carbs, {n.get('fat_g', 0)}g fat"
            
            if meal.get('logged_at'):
                meal_info += f" ({meal['logged_at']})"
            
            summary.append(meal_info)
        
        return "\n".join(summary)
