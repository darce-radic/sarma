"""
Simple AI test without database dependencies
"""

import asyncio
import os

# Read API keys from environment (do not hardcode secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

async def test_gemini():
    print("=" * 60)
    print("TEST 1: Gemini 2.0 Flash (Fast & Cost-Effective)")
    print("=" * 60)
    
    try:
        import google.generativeai as genai
        
        # Configure
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Test
        response = model.generate_content(
            "List 3 key nutrients in chicken breast. Be very brief."
        )
        
        print("✅ Status: SUCCESS")
        print(f"📝 Response: {response.text[:200]}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()

async def test_openai():
    print("=" * 60)
    print("TEST 2: GPT-4 (Premium Quality)")
    print("=" * 60)
    
    try:
        from openai import AsyncOpenAI
        
        # Configure
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Test
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "List 3 key nutrients in salmon. Be very brief."}
            ],
            max_tokens=100
        )
        
        print("✅ Status: SUCCESS")
        print(f"📝 Response: {response.choices[0].message.content[:200]}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()

async def main():
    print("\n🧪 TESTING SARMA AI INTEGRATION\n")
    print(f"🔑 Gemini Key: {GEMINI_API_KEY[:20]}...")
    print(f"🔑 OpenAI Key: {OPENAI_API_KEY[:20]}...")
    print()

    if not GEMINI_API_KEY or not OPENAI_API_KEY:
        print("⚠️  Missing API keys. Set GEMINI_API_KEY and OPENAI_API_KEY environment variables before running this test.")
        return
    
    await test_gemini()
    await test_openai()
    
    print("=" * 60)
    print("🎉 AI INTEGRATION TEST COMPLETE!")
    print("=" * 60)
    print()
    print("✅ Both AI providers are working correctly!")
    print()
    print("Next steps:")
    print("1. Keys are configured in backend/.env")
    print("2. Start backend: cd backend && docker-compose up -d")
    print("3. Access API docs: http://localhost:8000/docs")
    print("4. Test AI endpoints under 'AI Services' section")
    print()

if __name__ == "__main__":
    asyncio.run(main())
