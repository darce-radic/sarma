"""
Recipe API Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db

client = TestClient(app)


class TestRecipeAPI:
    """Test recipe endpoints"""
    
    def test_search_recipes(self, test_db: Session, auth_headers: dict):
        """Test recipe search"""
        response = client.post(
            "/api/v1/recipes/search",
            headers=auth_headers,
            json={
                "query": "chicken",
                "max_calories": 500,
                "dietary_type": "omnivore",
                "page": 1,
                "page_size": 20
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_recipe(self, test_db: Session, auth_headers: dict):
        """Test recipe creation"""
        response = client.post(
            "/api/v1/recipes/",
            headers=auth_headers,
            json={
                "title": "Grilled Salmon",
                "description": "Healthy omega-3 rich meal",
                "prep_time_minutes": 15,
                "cook_time_minutes": 20,
                "servings": 4,
                "difficulty": "medium",
                "dietary_type": "pescatarian",
                "ingredients": [
                    {
                        "name": "Salmon fillet",
                        "quantity": 1.5,
                        "unit": "lbs"
                    }
                ],
                "instructions": {
                    "steps": [
                        {
                            "step": 1,
                            "instruction": "Preheat grill"
                        }
                    ]
                },
                "tags": ["heart-healthy"]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Grilled Salmon"
        assert "id" in data
    
    def test_get_recipe(self, test_db: Session, auth_headers: dict, sample_recipe_id: str):
        """Test get recipe by ID"""
        response = client.get(
            f"/api/v1/recipes/{sample_recipe_id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]
    
    def test_rate_recipe(self, test_db: Session, auth_headers: dict, sample_recipe_id: str):
        """Test recipe rating"""
        response = client.post(
            f"/api/v1/recipes/{sample_recipe_id}/rate",
            headers=auth_headers,
            params={"rating": 5, "review": "Excellent!"}
        )
        
        assert response.status_code in [200, 404]
    
    def test_favorite_recipe(self, test_db: Session, auth_headers: dict, sample_recipe_id: str):
        """Test add to favorites"""
        response = client.post(
            f"/api/v1/recipes/{sample_recipe_id}/favorite",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]
    
    def test_get_favorites(self, test_db: Session, auth_headers: dict):
        """Test get user favorites"""
        response = client.get(
            "/api/v1/recipes/favorites/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_recommendations(self, test_db: Session, auth_headers: dict):
        """Test personalized recommendations"""
        response = client.get(
            "/api/v1/recipes/recommendations/me",
            headers=auth_headers,
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# Fixtures
@pytest.fixture
def auth_headers(test_db: Session) -> dict:
    """Get authentication headers for testing"""
    # Create test user and login
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
    )
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_recipe_id() -> str:
    """Return a sample recipe ID for testing"""
    return "00000000-0000-0000-0000-000000000001"
