"""
Tests for API Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_success(self):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == "test@example.com"
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # First registration
        client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "password": "SecurePass123!",
            "full_name": "User One"
        })
        
        # Second registration with same email
        response = client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Different123!",
            "full_name": "User Two"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self):
        """Test successful login"""
        # Register user first
        client.post("/api/v1/auth/register", json={
            "email": "login@example.com",
            "password": "SecurePass123!",
            "full_name": "Login User"
        })
        
        # Login
        response = client.post("/api/v1/auth/login", json={
            "email": "login@example.com",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        response = client.post("/api/v1/auth/login", json={
            "email": "login@example.com",
            "password": "WrongPassword!"
        })
        
        assert response.status_code == 401


class TestAIEndpoints:
    """Test AI service endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        # Register and login
        client.post("/api/v1/auth/register", json={
            "email": "ai_test@example.com",
            "password": "SecurePass123!",
            "full_name": "AI Test User"
        })
        
        login_response = client.post("/api/v1/auth/login", json={
            "email": "ai_test@example.com",
            "password": "SecurePass123!"
        })
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_meal_analysis_unauthorized(self):
        """Test meal analysis without authentication"""
        response = client.post("/api/v1/ai/analyze/meal", json={
            "image_url": "https://example.com/meal.jpg"
        })
        
        assert response.status_code == 401
    
    def test_meal_analysis_success(self, auth_headers):
        """Test successful meal analysis"""
        response = client.post(
            "/api/v1/ai/analyze/meal",
            json={"image_url": "https://example.com/meal.jpg"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "calories" in data
        assert "protein" in data
        assert "ingredients" in data
    
    def test_recipe_generation(self, auth_headers):
        """Test AI recipe generation"""
        response = client.post(
            "/api/v1/ai/generate/recipe",
            json={
                "ingredients": ["chicken", "broccoli", "rice"],
                "dietary_restrictions": ["gluten-free"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "instructions" in data
        assert "nutrition" in data
    
    def test_chat_assistant(self, auth_headers):
        """Test health chat assistant"""
        response = client.post(
            "/api/v1/ai/chat",
            json={"message": "What should I eat for breakfast?"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0


class TestSubscriptionEndpoints:
    """Test subscription and payment endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        client.post("/api/v1/auth/register", json={
            "email": "sub_test@example.com",
            "password": "SecurePass123!",
            "full_name": "Sub Test User"
        })
        
        login_response = client.post("/api/v1/auth/login", json={
            "email": "sub_test@example.com",
            "password": "SecurePass123!"
        })
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_current_subscription(self, auth_headers):
        """Test getting current subscription"""
        response = client.get(
            "/api/v1/subscriptions/current",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tier" in data
        assert data["tier"] in ["free", "premium", "pro"]
    
    def test_get_usage_limits(self, auth_headers):
        """Test getting usage limits"""
        response = client.get(
            "/api/v1/subscriptions/usage",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "requests_this_month" in data
        assert "limit" in data
    
    def test_create_checkout_session(self, auth_headers):
        """Test creating Stripe checkout session"""
        response = client.post(
            "/api/v1/subscriptions/checkout",
            json={
                "price_id": "price_premium_monthly",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        client.post("/api/v1/auth/register", json={
            "email": "analytics_test@example.com",
            "password": "SecurePass123!",
            "full_name": "Analytics Test User"
        })
        
        login_response = client.post("/api/v1/auth/login", json={
            "email": "analytics_test@example.com",
            "password": "SecurePass123!"
        })
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_user_analytics(self, auth_headers):
        """Test getting user analytics"""
        response = client.get(
            "/api/v1/analytics?range=week",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "ai_usage" in data
        assert "nutrition" in data
        assert "goals" in data
        assert "recipes" in data
    
    def test_analytics_time_ranges(self, auth_headers):
        """Test different time ranges"""
        for range_param in ["week", "month", "all"]:
            response = client.get(
                f"/api/v1/analytics?range={range_param}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "ai_usage" in data


class TestSettingsEndpoints:
    """Test user settings endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        client.post("/api/v1/auth/register", json={
            "email": "settings_test@example.com",
            "password": "SecurePass123!",
            "full_name": "Settings Test User"
        })
        
        login_response = client.post("/api/v1/auth/login", json={
            "email": "settings_test@example.com",
            "password": "SecurePass123!"
        })
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_settings(self, auth_headers):
        """Test getting user settings"""
        response = client.get(
            "/api/v1/settings",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "default_ai_provider" in data
        assert "dietary_restrictions" in data
    
    def test_update_settings(self, auth_headers):
        """Test updating user settings"""
        response = client.put(
            "/api/v1/settings",
            json={
                "default_ai_provider": "gemini",
                "dietary_restrictions": ["vegetarian", "gluten-free"],
                "health_goals": {
                    "daily_calories": 2000,
                    "weight_goal": "lose"
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["default_ai_provider"] == "gemini"
        assert "vegetarian" in data["dietary_restrictions"]
    
    def test_api_key_encryption(self, auth_headers):
        """Test API key encryption"""
        response = client.put(
            "/api/v1/settings",
            json={
                "gemini_api_key": "test_api_key_123",
                "openai_api_key": "sk-test_key"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Get settings and verify keys are not exposed
        get_response = client.get(
            "/api/v1/settings",
            headers=auth_headers
        )
        
        data = get_response.json()
        # Keys should be masked or not returned
        if "gemini_api_key" in data:
            assert data["gemini_api_key"] != "test_api_key_123"


class TestRateLimiting:
    """Test API rate limiting"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        client.post("/api/v1/auth/register", json={
            "email": "rate_test@example.com",
            "password": "SecurePass123!",
            "full_name": "Rate Test User"
        })
        
        login_response = client.post("/api/v1/auth/login", json={
            "email": "rate_test@example.com",
            "password": "SecurePass123!"
        })
        
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_rate_limit_exceeded(self, auth_headers):
        """Test rate limiting on free tier"""
        # Make 51 requests (free tier limit is 50/month)
        for i in range(51):
            response = client.post(
                "/api/v1/ai/chat",
                json={"message": f"Test message {i}"},
                headers=auth_headers
            )
            
            if i < 50:
                assert response.status_code == 200
            else:
                # 51st request should be rate limited
                assert response.status_code == 429
                assert "limit exceeded" in response.json()["detail"].lower()
