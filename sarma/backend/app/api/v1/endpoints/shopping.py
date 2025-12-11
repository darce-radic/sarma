"""
Shopping API Endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.shopping_service import ShoppingService

router = APIRouter()


@router.post("/lists/from-recipes")
async def generate_shopping_list(
    recipe_ids: List[UUID],
    servings_multiplier: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate shopping list from recipes
    
    Automatically:
    - Consolidates ingredients
    - Adjusts quantities for servings
    - Categorizes items
    - Matches to store products
    - Estimates costs
    """
    shopping_list = await ShoppingService.generate_shopping_list_from_recipes(
        db,
        current_user.id,
        recipe_ids,
        servings_multiplier
    )
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate shopping list"
        )
    
    return shopping_list


@router.get("/lists")
async def get_shopping_lists(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's shopping lists"""
    lists = await ShoppingService.get_user_shopping_lists(
        db,
        current_user.id,
        active_only
    )
    return lists


@router.get("/lists/{list_id}")
async def get_shopping_list(
    list_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get shopping list by ID"""
    from app.models.shopping import ShoppingList
    
    shopping_list = db.query(ShoppingList).filter(
        ShoppingList.id == list_id,
        ShoppingList.user_id == current_user.id
    ).first()
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found"
        )
    
    return shopping_list


@router.post("/orders")
async def create_order(
    shopping_list_id: UUID,
    store_id: UUID,
    delivery_address: dict,
    delivery_instructions: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create shopping order from list
    
    Integrates with:
    - Instacart
    - Amazon Fresh
    - Walmart
    - Kroger
    
    Order requires human review before confirmation
    """
    order = await ShoppingService.create_order_from_list(
        db,
        current_user.id,
        shopping_list_id,
        store_id,
        delivery_address,
        delivery_instructions
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create order"
        )
    
    return order


@router.post("/orders/{order_id}/review")
async def review_order(
    order_id: UUID,
    modifications: dict = None,
    confirm: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Human-in-the-loop order review
    
    Review and confirm or cancel order
    """
    order = await ShoppingService.review_and_confirm_order(
        db,
        current_user.id,
        order_id,
        modifications,
        confirm
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return {
        "message": "Order confirmed" if confirm else "Order cancelled",
        "order": order
    }


@router.get("/orders")
async def get_orders(
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's shopping orders"""
    orders = await ShoppingService.get_user_orders(
        db,
        current_user.id,
        status
    )
    return orders


@router.get("/orders/{order_id}")
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order by ID"""
    from app.models.shopping import ShoppingOrder
    
    order = db.query(ShoppingOrder).filter(
        ShoppingOrder.id == order_id,
        ShoppingOrder.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.get("/stores")
async def get_stores(
    zip_code: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available stores
    
    Optionally filter by ZIP code
    """
    stores = await ShoppingService.get_available_stores(db, zip_code)
    return stores
