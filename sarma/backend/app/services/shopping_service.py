"""
Shopping List and Multi-Store Integration Service
"""
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.shopping import (
    ShoppingList,
    ShoppingListItem,
    ShoppingOrder,
    ShoppingOrderItem,
    Store,
    StoreProduct,
    OrderStatus
)
from app.models.recipe import Recipe, RecipeIngredient


class ShoppingService:
    """Service for shopping list generation and multi-store ordering"""
    
    @staticmethod
    async def generate_shopping_list_from_recipes(
        db: Session,
        user_id: UUID,
        recipe_ids: List[UUID],
        servings_multiplier: Dict[UUID, float] = None
    ) -> ShoppingList:
        """
        Generate shopping list from selected recipes
        
        Process:
        1. Collect all ingredients from recipes
        2. Consolidate duplicate ingredients
        3. Adjust quantities for servings
        4. Categorize items
        5. Match to store products
        """
        
        # Get recipes
        recipes = db.query(Recipe).filter(
            Recipe.id.in_(recipe_ids),
            Recipe.is_active == True
        ).all()
        
        if not recipes:
            return None
        
        # Create shopping list
        shopping_list = ShoppingList(
            user_id=user_id,
            title=f"Shopping List - {datetime.utcnow().strftime('%Y-%m-%d')}",
            recipe_ids=recipe_ids,
            week_start_date=datetime.utcnow(),
            is_active=True
        )
        
        db.add(shopping_list)
        db.flush()
        
        # Collect and consolidate ingredients
        ingredient_map = {}  # {ingredient_name: {quantity, unit, recipe_ids}}
        
        for recipe in recipes:
            multiplier = servings_multiplier.get(recipe.id, 1.0) if servings_multiplier else 1.0
            
            for ingredient in recipe.ingredients:
                key = ingredient.name.lower()
                
                if key in ingredient_map:
                    # Consolidate quantities (if same unit)
                    if ingredient_map[key]["unit"] == ingredient.unit:
                        ingredient_map[key]["quantity"] += ingredient.quantity * multiplier
                    else:
                        # Different unit - create separate item
                        key = f"{ingredient.name.lower()}_{ingredient.unit}"
                        ingredient_map[key] = {
                            "name": ingredient.name,
                            "quantity": ingredient.quantity * multiplier,
                            "unit": ingredient.unit,
                            "recipe_ids": [recipe.id]
                        }
                else:
                    ingredient_map[key] = {
                        "name": ingredient.name,
                        "quantity": ingredient.quantity * multiplier,
                        "unit": ingredient.unit,
                        "recipe_ids": [recipe.id]
                    }
        
        # Create shopping list items
        total_estimated_cost = Decimal(0)
        
        for ing_data in ingredient_map.values():
            # Categorize ingredient
            category = ShoppingService._categorize_ingredient(ing_data["name"])
            
            # Match to store product
            matched_product = await ShoppingService._match_to_store_product(
                db, ing_data["name"]
            )
            
            item = ShoppingListItem(
                shopping_list_id=shopping_list.id,
                item_name=ing_data["name"],
                quantity=ing_data["quantity"],
                unit=ing_data["unit"],
                category=category,
                matched_product_id=matched_product["id"] if matched_product else None,
                product_name=matched_product["name"] if matched_product else None,
                estimated_price=matched_product["price"] if matched_product else None
            )
            
            db.add(item)
            
            if matched_product and matched_product["price"]:
                total_estimated_cost += Decimal(str(matched_product["price"]))
        
        shopping_list.estimated_total = total_estimated_cost
        
        db.commit()
        db.refresh(shopping_list)
        
        return shopping_list
    
    @staticmethod
    async def create_order_from_list(
        db: Session,
        user_id: UUID,
        shopping_list_id: UUID,
        store_id: UUID,
        delivery_address: Dict,
        delivery_instructions: Optional[str] = None
    ) -> ShoppingOrder:
        """
        Create shopping order from list
        
        Integrates with:
        - Instacart
        - Amazon Fresh
        - Walmart
        - Kroger
        """
        
        shopping_list = db.query(ShoppingList).filter(
            ShoppingList.id == shopping_list_id,
            ShoppingList.user_id == user_id
        ).first()
        
        if not shopping_list:
            return None
        
        store = db.query(Store).filter(Store.id == store_id).first()
        
        if not store:
            return None
        
        # Generate order number
        order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create order
        order = ShoppingOrder(
            user_id=user_id,
            shopping_list_id=shopping_list_id,
            store_id=store_id,
            order_number=order_number,
            status=OrderStatus.DRAFT,
            delivery_address=delivery_address,
            delivery_instructions=delivery_instructions,
            subtotal=Decimal(0),
            tax=Decimal(0),
            delivery_fee=store.delivery_fee or Decimal(0),
            tip=Decimal(0),
            total=Decimal(0),
            requires_review=True  # Human-in-the-loop
        )
        
        db.add(order)
        db.flush()
        
        # Add order items from shopping list
        subtotal = Decimal(0)
        
        for list_item in shopping_list.items:
            if not list_item.is_checked:
                # Find best matching product at this store
                product = await ShoppingService._find_store_product(
                    db, store_id, list_item.item_name
                )
                
                if product:
                    order_item = ShoppingOrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.product_name,
                        product_brand=product.brand,
                        quantity=int(list_item.quantity) or 1,
                        unit_price=product.price,
                        total_price=product.price * (int(list_item.quantity) or 1)
                    )
                    
                    db.add(order_item)
                    subtotal += order_item.total_price
        
        # Calculate totals
        order.subtotal = subtotal
        order.tax = subtotal * Decimal("0.08")  # 8% tax
        order.total = order.subtotal + order.tax + order.delivery_fee
        
        db.commit()
        db.refresh(order)
        
        # TODO: Send to external API (Instacart, etc.)
        # await ShoppingService._submit_to_instacart(order)
        
        return order
    
    @staticmethod
    async def review_and_confirm_order(
        db: Session,
        user_id: UUID,
        order_id: UUID,
        modifications: Optional[Dict] = None,
        confirm: bool = True
    ) -> ShoppingOrder:
        """
        Human-in-the-loop order review
        
        User can:
        - Review items and prices
        - Make modifications
        - Confirm or cancel
        """
        
        order = db.query(ShoppingOrder).filter(
            ShoppingOrder.id == order_id,
            ShoppingOrder.user_id == user_id
        ).first()
        
        if not order:
            return None
        
        if modifications:
            order.user_modifications = modifications
            # Apply modifications to order items
            # TODO: Update items based on modifications
        
        order.reviewed_by_user = True
        order.reviewed_at = datetime.utcnow()
        
        if confirm:
            order.status = OrderStatus.CONFIRMED
            # TODO: Submit to external service
            # await ShoppingService._confirm_with_store(order)
        else:
            order.status = OrderStatus.CANCELLED
        
        db.commit()
        db.refresh(order)
        
        return order
    
    @staticmethod
    async def get_user_shopping_lists(
        db: Session,
        user_id: UUID,
        active_only: bool = True
    ) -> List[ShoppingList]:
        """Get user's shopping lists"""
        query = db.query(ShoppingList).filter(
            ShoppingList.user_id == user_id
        )
        
        if active_only:
            query = query.filter(ShoppingList.is_active == True)
        
        return query.order_by(desc(ShoppingList.created_at)).all()
    
    @staticmethod
    async def get_user_orders(
        db: Session,
        user_id: UUID,
        status: Optional[str] = None
    ) -> List[ShoppingOrder]:
        """Get user's shopping orders"""
        query = db.query(ShoppingOrder).filter(
            ShoppingOrder.user_id == user_id
        )
        
        if status:
            query = query.filter(ShoppingOrder.status == status)
        
        return query.order_by(desc(ShoppingOrder.created_at)).all()
    
    @staticmethod
    async def get_available_stores(
        db: Session,
        zip_code: Optional[str] = None
    ) -> List[Store]:
        """Get available stores (optionally filtered by location)"""
        query = db.query(Store).filter(Store.is_active == True)
        
        if zip_code:
            query = query.filter(Store.zip_code == zip_code)
        
        return query.all()
    
    @staticmethod
    def _categorize_ingredient(ingredient_name: str) -> str:
        """Categorize ingredient for organization"""
        name_lower = ingredient_name.lower()
        
        # Produce
        produce_keywords = ["lettuce", "tomato", "onion", "carrot", "pepper", "spinach", 
                           "kale", "broccoli", "cauliflower", "cucumber", "apple", "banana",
                           "orange", "berry", "avocado", "zucchini", "squash"]
        if any(kw in name_lower for kw in produce_keywords):
            return "produce"
        
        # Meat
        meat_keywords = ["chicken", "beef", "pork", "turkey", "fish", "salmon", 
                        "tuna", "shrimp", "lamb", "steak"]
        if any(kw in name_lower for kw in meat_keywords):
            return "meat"
        
        # Dairy
        dairy_keywords = ["milk", "cheese", "yogurt", "butter", "cream", "egg"]
        if any(kw in name_lower for kw in dairy_keywords):
            return "dairy"
        
        # Pantry
        pantry_keywords = ["rice", "pasta", "flour", "sugar", "salt", "pepper", 
                          "oil", "vinegar", "sauce", "spice"]
        if any(kw in name_lower for kw in pantry_keywords):
            return "pantry"
        
        # Bakery
        bakery_keywords = ["bread", "bagel", "tortilla", "bun", "roll"]
        if any(kw in name_lower for kw in bakery_keywords):
            return "bakery"
        
        return "other"
    
    @staticmethod
    async def _match_to_store_product(
        db: Session,
        ingredient_name: str
    ) -> Optional[Dict]:
        """Match ingredient to store product"""
        # Simple text matching for now
        # TODO: Implement smart matching with ML
        
        product = db.query(StoreProduct).filter(
            StoreProduct.product_name.ilike(f"%{ingredient_name}%"),
            StoreProduct.in_stock == True
        ).first()
        
        if product:
            return {
                "id": product.id,
                "name": product.product_name,
                "price": product.price,
                "brand": product.brand
            }
        
        return None
    
    @staticmethod
    async def _find_store_product(
        db: Session,
        store_id: UUID,
        product_name: str
    ) -> Optional[StoreProduct]:
        """Find product at specific store"""
        return db.query(StoreProduct).filter(
            StoreProduct.store_id == store_id,
            StoreProduct.product_name.ilike(f"%{product_name}%"),
            StoreProduct.in_stock == True
        ).first()
