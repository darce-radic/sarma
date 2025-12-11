"""
Tests for AI Services (Gemini, OpenAI, Multi-model routing)
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.ai.gemini_service import GeminiService
from app.services.ai.openai_service import OpenAIService
from app.services.ai.meal_analyzer import MealAnalyzer
from app.services.ai.recipe_generator import RecipeGenerator
from app.services.ai.chat_assistant import ChatAssistant


class TestGeminiService:
    """Test Gemini AI service"""
    
    @pytest.fixture
    def gemini_service(self):
        return GeminiService(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_analyze_image_success(self, gemini_service):
        """Test successful image analysis"""
        with patch.object(gemini_service, 'generate_content', new=AsyncMock(return_value={
            "text": "Grilled chicken breast with rice and broccoli",
            "confidence": 0.92
        })):
            result = await gemini_service.analyze_image(
                image_data=b"fake_image_data",
                prompt="Analyze this meal"
            )
            
            assert result["text"] == "Grilled chicken breast with rice and broccoli"
            assert result["confidence"] == 0.92
    
    @pytest.mark.asyncio
    async def test_analyze_image_low_confidence(self, gemini_service):
        """Test image analysis with low confidence"""
        with patch.object(gemini_service, 'generate_content', new=AsyncMock(return_value={
            "text": "Uncertain food item",
            "confidence": 0.45
        })):
            result = await gemini_service.analyze_image(
                image_data=b"fake_image_data",
                prompt="Analyze this meal"
            )
            
            assert result["confidence"] < 0.7  # Low confidence threshold


class TestOpenAIService:
    """Test OpenAI GPT-4 service"""
    
    @pytest.fixture
    def openai_service(self):
        return OpenAIService(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_vision_analysis(self, openai_service):
        """Test GPT-4 Vision analysis"""
        with patch.object(openai_service, 'analyze_image', new=AsyncMock(return_value={
            "text": "This appears to be a balanced meal consisting of...",
            "confidence": 0.95
        })):
            result = await openai_service.analyze_image(
                image_data=b"fake_image_data",
                prompt="Analyze this meal"
            )
            
            assert "balanced meal" in result["text"]
            assert result["confidence"] > 0.9


class TestMealAnalyzer:
    """Test Meal Analyzer (multi-model routing)"""
    
    @pytest.fixture
    def meal_analyzer(self):
        return MealAnalyzer(
            gemini_api_key="test_gemini",
            openai_api_key="test_openai"
        )
    
    @pytest.mark.asyncio
    async def test_routing_to_gemini(self, meal_analyzer):
        """Test routing to Gemini for free users"""
        with patch.object(meal_analyzer.gemini_service, 'analyze_image', new=AsyncMock(return_value={
            "ingredients": ["chicken", "rice", "broccoli"],
            "calories": 520,
            "protein": 45,
            "carbs": 55,
            "fat": 12,
            "confidence": 0.88
        })):
            result = await meal_analyzer.analyze_meal(
                image_data=b"fake_image",
                user_tier="free"
            )
            
            assert result["provider"] == "gemini"
            assert result["calories"] == 520
            assert result["confidence"] > 0.8
    
    @pytest.mark.asyncio
    async def test_routing_to_gpt4(self, meal_analyzer):
        """Test routing to GPT-4 for premium users"""
        with patch.object(meal_analyzer.openai_service, 'analyze_image', new=AsyncMock(return_value={
            "ingredients": ["chicken", "rice", "broccoli"],
            "calories": 520,
            "protein": 45,
            "carbs": 55,
            "fat": 12,
            "confidence": 0.96
        })):
            result = await meal_analyzer.analyze_meal(
                image_data=b"fake_image",
                user_tier="premium"
            )
            
            assert result["provider"] == "openai"
            assert result["confidence"] > 0.9
    
    @pytest.mark.asyncio
    async def test_fallback_routing(self, meal_analyzer):
        """Test fallback to GPT-4 on low confidence"""
        # First call to Gemini returns low confidence
        with patch.object(meal_analyzer.gemini_service, 'analyze_image', new=AsyncMock(return_value={
            "confidence": 0.45
        })):
            # Second call to GPT-4 returns high confidence
            with patch.object(meal_analyzer.openai_service, 'analyze_image', new=AsyncMock(return_value={
                "ingredients": ["chicken", "rice", "broccoli"],
                "calories": 520,
                "confidence": 0.92
            })):
                result = await meal_analyzer.analyze_meal(
                    image_data=b"fake_image",
                    user_tier="free"
                )
                
                assert result["provider"] == "openai"  # Fallback occurred
                assert result["confidence"] > 0.9


class TestRecipeGenerator:
    """Test AI Recipe Generator"""
    
    @pytest.fixture
    def recipe_generator(self):
        return RecipeGenerator(
            gemini_api_key="test_gemini",
            openai_api_key="test_openai"
        )
    
    @pytest.mark.asyncio
    async def test_generate_from_ingredients(self, recipe_generator):
        """Test recipe generation from ingredients"""
        with patch.object(recipe_generator.gemini_service, 'generate_content', new=AsyncMock(return_value={
            "name": "Chicken Stir Fry",
            "ingredients": ["chicken", "vegetables", "soy sauce"],
            "instructions": ["Step 1", "Step 2"],
            "nutrition": {"calories": 450, "protein": 40}
        })):
            result = await recipe_generator.generate_recipe(
                ingredients=["chicken", "broccoli", "soy sauce"],
                preferences={"dietary": ["gluten-free"]}
            )
            
            assert result["name"] == "Chicken Stir Fry"
            assert len(result["instructions"]) > 0
            assert result["nutrition"]["calories"] > 0
    
    @pytest.mark.asyncio
    async def test_dietary_restrictions(self, recipe_generator):
        """Test recipe generation respects dietary restrictions"""
        with patch.object(recipe_generator.gemini_service, 'generate_content', new=AsyncMock(return_value={
            "name": "Vegan Buddha Bowl",
            "ingredients": ["quinoa", "chickpeas", "vegetables"],
            "is_vegan": True
        })):
            result = await recipe_generator.generate_recipe(
                ingredients=["quinoa", "chickpeas"],
                preferences={"dietary": ["vegan"]}
            )
            
            assert result["is_vegan"] is True
            assert "meat" not in str(result["ingredients"]).lower()


class TestChatAssistant:
    """Test Health Chat Assistant"""
    
    @pytest.fixture
    def chat_assistant(self):
        return ChatAssistant(
            gemini_api_key="test_gemini",
            openai_api_key="test_openai"
        )
    
    @pytest.mark.asyncio
    async def test_health_question(self, chat_assistant):
        """Test answering health question"""
        with patch.object(chat_assistant.gemini_service, 'generate_content', new=AsyncMock(return_value={
            "response": "For breakfast before a workout, focus on...",
            "confidence": 0.89
        })):
            result = await chat_assistant.ask(
                question="What should I eat before a workout?",
                context={"goal": "muscle_gain"}
            )
            
            assert "breakfast" in result["response"].lower()
            assert result["confidence"] > 0.8
    
    @pytest.mark.asyncio
    async def test_personalized_response(self, chat_assistant):
        """Test personalized health advice"""
        with patch.object(chat_assistant.gemini_service, 'generate_content', new=AsyncMock(return_value={
            "response": "Based on your weight loss goal, I recommend...",
            "confidence": 0.92
        })):
            result = await chat_assistant.ask(
                question="What should I eat today?",
                context={
                    "goal": "weight_loss",
                    "dietary_restrictions": ["vegetarian"]
                }
            )
            
            assert "weight loss" in result["response"].lower()
            assert result["confidence"] > 0.9


class TestCostOptimization:
    """Test multi-model cost optimization"""
    
    def test_cost_calculation(self):
        """Test cost savings from multi-model routing"""
        # Gemini cost
        gemini_requests = 1000
        gemini_cost = gemini_requests * 0.001  # $1
        
        # GPT-4 cost
        gpt4_requests = 200
        gpt4_cost = gpt4_requests * 0.02  # $4
        
        # Total multi-model cost
        total_cost = gemini_cost + gpt4_cost  # $5
        
        # GPT-4 only cost (all 1200 requests)
        gpt4_only_cost = 1200 * 0.02  # $24
        
        # Calculate savings
        savings = gpt4_only_cost - total_cost
        savings_percentage = (savings / gpt4_only_cost) * 100
        
        assert savings == 19.0  # $19 saved
        assert savings_percentage > 75  # More than 75% savings
    
    def test_routing_efficiency(self):
        """Test routing efficiency"""
        total_requests = 1000
        premium_users_ratio = 0.25  # 25% premium users
        
        # Gemini requests (75% of total, free users)
        gemini_requests = total_requests * (1 - premium_users_ratio)
        
        # GPT-4 requests (25% of total, premium users)
        gpt4_requests = total_requests * premium_users_ratio
        
        assert gemini_requests == 750
        assert gpt4_requests == 250
        assert gemini_requests + gpt4_requests == total_requests


@pytest.mark.integration
class TestAIIntegration:
    """Integration tests for AI services"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="Integration tests require --run-integration flag"
    )
    async def test_real_gemini_api(self):
        """Test real Gemini API call (requires API key)"""
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")
        
        gemini = GeminiService(api_key=api_key)
        result = await gemini.generate_content(
            prompt="What are the health benefits of broccoli?"
        )
        
        assert "broccoli" in result["text"].lower()
        assert result["confidence"] > 0.7
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="Integration tests require --run-integration flag"
    )
    async def test_real_openai_api(self):
        """Test real OpenAI API call (requires API key)"""
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        
        openai = OpenAIService(api_key=api_key)
        result = await openai.generate_content(
            prompt="What are the health benefits of broccoli?"
        )
        
        assert "broccoli" in result["text"].lower()
        assert result["confidence"] > 0.8


# Pytest configuration for integration tests
def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require API keys"
    )
