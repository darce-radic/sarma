"""
OpenAI API Integration
"""
import os
from typing import List, Dict, Optional
import openai
from openai import AsyncOpenAI

from app.core.config import settings


class OpenAIClient:
    """Wrapper for OpenAI API calls"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = "text-embedding-3-small"
        self.chat_model = "gpt-4-turbo-preview"
        self.vision_model = "gpt-4-vision-preview"
    
    async def generate_embedding(
        self,
        text: str,
        dimensions: int = 1536
    ) -> List[float]:
        """
        Generate text embedding
        
        Used for semantic search
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                dimensions=dimensions
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * dimensions
    
    async def chat_completion(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Generate chat completion
        
        Used for AI assistant
        """
        try:
            # Add system prompt if provided
            if system_prompt:
                messages = [
                    {"role": "system", "content": system_prompt},
                    *messages
                ]
            
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": self.chat_model,
                "finish_reason": response.choices[0].finish_reason
            }
        
        except Exception as e:
            print(f"Error in chat completion: {e}")
            return {
                "content": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "tokens_used": 0,
                "model": self.chat_model,
                "error": str(e)
            }
    
    async def analyze_meal_image(
        self,
        image_url: str,
        prompt: Optional[str] = None
    ) -> Dict:
        """
        Analyze meal photo with GPT-4 Vision
        
        Returns:
        - Description
        - Detected ingredients with quantities
        - Nutritional estimates
        - Confidence scores
        """
        try:
            default_prompt = """Analyze this meal photo and provide:
1. A detailed description of the meal
2. List of ingredients with estimated quantities
3. Approximate nutritional information (calories, protein, carbs, fat)
4. Confidence level for each detection (0-1)

Format your response as JSON with these keys:
- description: string
- confidence: float (0-1)
- ingredients: array of {name, quantity, unit, confidence, calories, protein_g, carbs_g, fat_g}
"""
            
            response = await self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt or default_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            import json
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, return as plain text
                result = {
                    "description": content,
                    "confidence": 0.7,
                    "ingredients": []
                }
            
            result["tokens_used"] = response.usage.total_tokens
            result["model"] = self.vision_model
            
            return result
        
        except Exception as e:
            print(f"Error analyzing meal image: {e}")
            return {
                "description": "Error analyzing image",
                "confidence": 0.0,
                "ingredients": [],
                "error": str(e)
            }
    
    async def generate_health_recommendations(
        self,
        health_data: Dict,
        user_context: Dict
    ) -> List[Dict]:
        """
        Generate personalized health recommendations
        
        Uses GPT-4 with health expertise
        """
        try:
            prompt = f"""As a health and nutrition expert, analyze this health profile and provide personalized recommendations:

Health Data:
{health_data}

User Context:
{user_context}

Provide 3-5 specific, actionable recommendations focusing on:
1. Nutrition improvements
2. Dietary changes
3. Health risk mitigation
4. Lifestyle modifications

Format as JSON array of objects with: category, priority, title, description, action_items
"""
            
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            import json
            try:
                recommendations = json.loads(content)
            except json.JSONDecodeError:
                # Fallback to generic recommendation
                recommendations = [
                    {
                        "category": "nutrition",
                        "priority": "high",
                        "title": "Personalized Recommendations Available",
                        "description": content,
                        "action_items": []
                    }
                ]
            
            return recommendations
        
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []


# Global instance
openai_client = OpenAIClient()


# Convenience functions
async def generate_embedding(text: str) -> List[float]:
    """Generate text embedding"""
    return await openai_client.generate_embedding(text)


async def chat_completion(messages: List[Dict], **kwargs) -> Dict:
    """Generate chat completion"""
    return await openai_client.chat_completion(messages, **kwargs)


async def analyze_meal_image(image_url: str, prompt: Optional[str] = None) -> Dict:
    """Analyze meal photo"""
    return await openai_client.analyze_meal_image(image_url, prompt)
