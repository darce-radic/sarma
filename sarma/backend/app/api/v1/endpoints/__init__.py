"""
API v1 Endpoints Package
"""
from app.api.v1.endpoints import (
    auth,
    users,
    recipes,
    health,
    meals,
    shopping,
    chat
)

__all__ = [
    "auth",
    "users",
    "recipes",
    "health",
    "meals",
    "shopping",
    "chat"
]
