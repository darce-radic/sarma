"""
Google Gemini 2.0 Flash Integration
Fast, cost-effective vision and text generation
"""

import time
import base64
from typing import List, Dict, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from .base import BaseAIService, AIProvider, AIConfig, AIResponse


class GeminiService(BaseAIService):
    """Google Gemini 2.0 Flash Service"""
    
    # Pricing per 1M tokens (as of Dec 2024)
    INPUT_COST_PER_1M = 0.075  # $0.075 per 1M input tokens
    OUTPUT_COST_PER_1M = 0.30  # $0.30 per 1M output tokens
    IMAGE_COST_PER_1K = 0.0025  # $0.0025 per 1K images
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        config = AIConfig(
            provider=AIProvider.GEMINI_FLASH,
            model=model,
            api_key=api_key,
            temperature=0.7,
            max_tokens=2048
        )
        super().__init__(config)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        
    async def analyze_image(
        self, 
        image_url: str, 
        prompt: str,
        **kwargs
    ) -> AIResponse:
        """
        Analyze image with Gemini Vision
        
        Args:
            image_url: URL or base64 encoded image
            prompt: Analysis instructions
            **kwargs: Additional parameters
            
        Returns:
            AIResponse with analysis results
        """
        start_time = time.time()
        
        try:
            # Prepare image data
            if image_url.startswith('data:image'):
                # Base64 encoded image
                image_data = image_url.split(',')[1]
                image_bytes = base64.b64decode(image_data)
            else:
                # URL - Gemini can handle URLs directly
                import requests
                response = requests.get(image_url, timeout=10)
                image_bytes = response.content
            
            # Create generation config
            generation_config = GenerationConfig(
                temperature=kwargs.get('temperature', self.config.temperature),
                max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            )
            
            # Generate response
            response = self.model.generate_content(
                [prompt, {"mime_type": "image/jpeg", "data": image_bytes}],
                generation_config=generation_config
            )
            
            # Calculate metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract token usage (approximate if not available)
            input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else len(prompt) // 4
            output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else len(response.text) // 4
            
            total_tokens = input_tokens + output_tokens
            cost = self.calculate_cost(input_tokens, output_tokens) + (self.IMAGE_COST_PER_1K / 1000)
            
            # Assess confidence
            confidence = self.assess_confidence(response.text)
            
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content=response.text,
                confidence=confidence,
                tokens_used=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time_ms,
                timestamp=time.time(),
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None
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
        """Generate text response with Gemini"""
        start_time = time.time()
        
        try:
            # Combine context and prompt
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            # Create generation config
            generation_config = GenerationConfig(
                temperature=kwargs.get('temperature', self.config.temperature),
                max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            )
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Calculate metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            
            input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else len(full_prompt) // 4
            output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else len(response.text) // 4
            
            total_tokens = input_tokens + output_tokens
            cost = self.calculate_cost(input_tokens, output_tokens)
            confidence = self.assess_confidence(response.text)
            
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content=response.text,
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
    
    async def chat(
        self, 
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AIResponse:
        """Chat conversation with Gemini"""
        start_time = time.time()
        
        try:
            # Start chat session
            chat = self.model.start_chat(history=[])
            
            # Convert messages to Gemini format and send
            for msg in messages[:-1]:  # Add history
                role = "user" if msg["role"] == "user" else "model"
                chat.history.append({"role": role, "parts": [msg["content"]]})
            
            # Send last message
            last_message = messages[-1]["content"]
            response = chat.send_message(last_message)
            
            # Calculate metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Approximate tokens
            total_prompt_length = sum(len(m["content"]) for m in messages)
            input_tokens = total_prompt_length // 4
            output_tokens = len(response.text) // 4
            
            total_tokens = input_tokens + output_tokens
            cost = self.calculate_cost(input_tokens, output_tokens)
            confidence = self.assess_confidence(response.text)
            
            return AIResponse(
                provider=self.provider,
                model=self.config.model,
                content=response.text,
                confidence=confidence,
                tokens_used=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time_ms,
                timestamp=time.time()
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
        """Calculate Gemini API cost in USD"""
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        return input_cost + output_cost
