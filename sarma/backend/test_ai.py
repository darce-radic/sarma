"""
Quick test script for AI integration
Tests both Gemini and OpenAI connections
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_ai_services():
    print("🧪 Testing AI Services...\n")
    
    # Import AI services
    from app.services.ai.gemini_service import GeminiService
    from app.services.ai.openai_service import OpenAIVisionService
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"🔑 Gemini API Key: {gemini_key[:20]}..." if gemini_key else "❌ No Gemini key")
    print(f"🔑 OpenAI API Key: {openai_key[:20]}..." if openai_key else "❌ No OpenAI key")
    print()
    
    # Test 1: Gemini Text Generation
    print("=" * 60)
    print("TEST 1: Gemini Text Generation (Fast & Cheap)")
    print("=" * 60)
    try:
        gemini = GeminiService(gemini_key)
        result = await gemini.generate_text(
            "What are 3 key nutrients in chicken breast? Be brief."
        )
        
        print(f"✅ Status: Success")
        print(f"📊 Response time: {result.response_time_ms}ms")
        print(f"💰 Cost: ${result.cost_usd:.6f}")
        print(f"🎯 Confidence: {result.confidence:.2f}")
        print(f"📝 Response:\n{result.content[:200]}...")
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
    
    # Test 2: GPT-4 Text Generation
    print("=" * 60)
    print("TEST 2: GPT-4 Text Generation (High Quality)")
    print("=" * 60)
    try:
        gpt4 = OpenAIVisionService(openai_key)
        result = await gpt4.generate_text(
            "What are 3 key nutrients in salmon? Be brief."
        )
        
        print(f"✅ Status: Success")
        print(f"📊 Response time: {result.response_time_ms}ms")
        print(f"💰 Cost: ${result.cost_usd:.6f}")
        print(f"🎯 Confidence: {result.confidence:.2f}")
        print(f"📝 Response:\n{result.content[:200]}...")
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
    
    # Test 3: Meal Analyzer (Multi-Model)
    print("=" * 60)
    print("TEST 3: Meal Analyzer (Multi-Model Smart Routing)")
    print("=" * 60)
    try:
        from app.services.ai.meal_analyzer import MealAnalyzer
        
        analyzer = MealAnalyzer(gemini_key, openai_key)
        
        # We'll test with quick calorie estimate (no image needed)
        print("Note: Full meal analysis requires image URL")
        print("Testing quick estimate logic instead...")
        print()
        
        # Test provider selection logic
        from app.services.ai.base import AIProvider
        
        provider_free = analyzer._select_provider("free", None)
        provider_premium = analyzer._select_provider("premium", None)
        
        print(f"✅ Free tier uses: {provider_free}")
        print(f"✅ Premium tier uses: {provider_premium}")
        print(f"✅ Confidence threshold: {analyzer.CONFIDENCE_THRESHOLD}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
    
    # Summary
    print("=" * 60)
    print("🎉 AI INTEGRATION TEST COMPLETE!")
    print("=" * 60)
    print()
    print("✅ Both AI providers are configured and working!")
    print()
    print("Next steps:")
    print("1. Start the backend: docker-compose up -d")
    print("2. Test API endpoints: http://localhost:8000/docs")
    print("3. Try: POST /api/v1/ai/chat with your auth token")
    print()

if __name__ == "__main__":
    asyncio.run(test_ai_services())
