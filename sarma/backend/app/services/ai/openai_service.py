"""
OpenAI GPT-4 Vision Integration
High-quality vision and text generation
"""

import time
from typing import List, Dict, Optional
from openai import AsyncOpenAI

from .base import BaseAIService, AIProvider, AIConfig, AIResponse


class OpenAIVisionService(BaseAIService):
    """OpenAI GPT-4 Vision Service"""
    
    # Pricing (as of Dec 2024)
    INPUT_COST_PER_1M = 5.00  # $5.00 per 1M input tokens
    OUTPUT_COST_PER_1M = 15.00  # $15.00 per 1M output tokens
    IMAGE_COST_BASE = 0.01275  # $0.01275 per image (1024x1024)
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        config = AIConfig(
            provider=AIProvider.GPT4_VISION,
            model=model,
            api_key=api_key,
            temperature=0.7,
            max_tokens=2048
        )
        super().__init__(config)
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=api_key)
        
    async def analyze_image(
        self, 
        image_url: str, 
        prompt: str,
        **kwargs
    ) -> AIResponse:
        """
        Analyze image with GPT-4 Vision
        
        Args:
            image_url: URL or base64 encoded image
            prompt: Analysis instructions
            **kwargs: Additional parameters (detail level, etc.)
            
        Returns:
            AIResponse with analysis results
        """
        start_time = time.time()
        
        try:
            # Prepare message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": kwargs.get("detail", "high")  # low, high, auto
                            }
                        }
                    ]
                }
            ]
            
            # Call GPT-4 Vision
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            )
            
            # Calculate metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract token usage
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate cost (including image cost)
            cost = self.calculate_cost(input_tokens, output_tokens)
            cost += self.IMAGE_COST_BASE  # Add image processing cost
            
            # Extract content
            content = response.choices[0].message.content
            
            # Assess confidence
            confidence = self.assess_confidence(content)
            
            # Higher confidence for GPT-4 by default
            confidence = min(1.0, confidence + 0.05)
            
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content=content,
                confidence=confidence,
                tokens_used=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time_ms,
                timestamp=time.time(),
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": response.choices[0].finish_reason,
                    "model": response.model
                }
            )
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content="",
                confidence=0.0,
                tokens_used=0,
                cost_usd=0.0,
                response_time_ms=response_time_ms,
                timestamp=time.time(),
                error=str(e)
            )
    
    async def generate_text(
        self, 
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """Generate text response with GPT-4"""
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})
            
            # Call GPT-4
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            )
            
            # Calculate metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            cost = self.calculate_cost(input_tokens, output_tokens)
            content = response.choices[0].message.content
            confidence = self.assess_confidence(content) + 0.05
            
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content=content,
                confidence=confidence,
                tokens_used=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time_ms,
                timestamp=time.time(),
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": response.choices[0].finish_reason
                }
            )
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content="",
                confidence=0.0,
                tokens_used=0,
                cost_usd=0.0,
                response_time_ms=response_time_ms,
                timestamp=time.time(),
                error=str(e)
            )
    
    async def chat(
        self, 
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AIResponse:
        """Chat conversation with GPT-4"""
        start_time = time.time()
        
        try:
            # Call GPT-4 with conversation history
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            )
            
            # Calculate metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            cost = self.calculate_cost(input_tokens, output_tokens)
            content = response.choices[0].message.content
            confidence = self.assess_confidence(content) + 0.05
            
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content=content,
                confidence=confidence,
                tokens_used=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time_ms,
                timestamp=time.time(),
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            )
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content="",
                confidence=0.0,
                tokens_used=0,
                cost_usd=0.0,
                response_time_ms=response_time_ms,
                timestamp=time.time(),
                error=str(e)
            )
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate OpenAI API cost in USD"""
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        return input_cost + output_cost
