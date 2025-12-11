"""
Forecast Health - Authentication Tests
Test user registration and login
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_register_user():
    """Test user registration"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPass123!",
                "first_name": "Test",
                "last_name": "User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Check user data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["first_name"] == "Test"
        assert data["user"]["last_name"] == "User"
        
        # Check tokens
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_register_duplicate_email():
    """Test registration with existing email fails"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First registration
        await client.post(
            "/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "TestPass123!",
                "first_name": "First",
                "last_name": "User"
            }
        )
        
        # Second registration with same email
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "TestPass123!",
                "first_name": "Second",
                "last_name": "User"
            }
        )
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login():
    """Test user login"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        await client.post(
            "/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "TestPass123!",
                "first_name": "Login",
                "last_name": "Test"
            }
        )
        
        # Login
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "TestPass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user"]["email"] == "login@example.com"
        assert "tokens" in data


@pytest.mark.asyncio
async def test_login_wrong_password():
    """Test login with wrong password fails"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        await client.post(
            "/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "TestPass123!",
                "first_name": "Wrong",
                "last_name": "Pass"
            }
        )
        
        # Login with wrong password
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
