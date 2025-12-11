"""
Grocery API endpoints for Coles/Woolworths product search
Integrates with MCP server for real-time data
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.services.grocery_mcp_service import grocery_mcp_service

router = APIRouter()


class ShoppingListRequest(BaseModel):
    items: List[str]
    store_preference: str = "both"


@router.get("/search")
async def search_products(
    query: str = Query(..., description="Search term (e.g., 'milk', 'bread')"),
    store: str = Query("both", description="Store to search: 'coles', 'woolworths', or 'both'"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results per store"),
    coles_store_id: Optional[str] = Query(None, description="Optional Coles store ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Search for products at Coles and/or Woolworths
    
    - **query**: Product name to search for
    - **store**: Which store(s) to search ('coles', 'woolworths', 'both')
    - **limit**: Maximum number of results (1-50)
    - **coles_store_id**: Optional store ID for Coles location-specific results
    """
    try:
        results = await grocery_mcp_service.search_products(
            query=query,
            store=store,
            limit=limit,
            coles_store_id=coles_store_id
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/coles")
async def search_coles(
    query: str = Query(..., description="Search term"),
    limit: int = Query(10, ge=1, le=50),
    store_id: Optional[str] = Query(None, description="Coles store ID"),
    current_user: User = Depends(get_current_user)
):
    """Search Coles products specifically"""
    try:
        results = await grocery_mcp_service.search_coles(
            query=query,
            limit=limit,
            store_id=store_id
        )
        return {"store": "coles", "products": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coles search failed: {str(e)}")


@router.get("/search/woolworths")
async def search_woolworths(
    query: str = Query(..., description="Search term"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Search Woolworths products specifically"""
    try:
        results = await grocery_mcp_service.search_woolworths(
            query=query,
            limit=limit
        )
        return {"store": "woolworths", "products": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Woolworths search failed: {str(e)}")


@router.get("/compare")
async def compare_prices(
    query: str = Query(..., description="Product to compare"),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    """
    Compare prices between Coles and Woolworths
    
    Returns the best deals and price differences
    """
    try:
        comparison = await grocery_mcp_service.compare_prices(
            query=query,
            limit=limit
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price comparison failed: {str(e)}")


@router.post("/shopping-list")
async def generate_shopping_list(
    request: ShoppingListRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a shopping list with price estimates
    
    - **items**: List of product names
    - **store_preference**: 'coles', 'woolworths', or 'both'
    
    Returns products with prices and total estimates from each store
    """
    try:
        shopping_list = await grocery_mcp_service.generate_shopping_list(
            items=request.items,
            store_preference=request.store_preference
        )
        return shopping_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shopping list generation failed: {str(e)}")


@router.get("/health")
async def check_mcp_health(
    current_user: User = Depends(get_current_user)
):
    """Check if MCP server is available"""
    try:
        # Try a simple search to test connectivity
        result = await grocery_mcp_service.search_products("test", "coles", 1)
        
        is_mock = any(
            product.get("note", "").startswith("⚠️")
            for products in result.values()
            for product in products
        )
        
        return {
            "status": "degraded" if is_mock else "healthy",
            "mcp_server": grocery_mcp_service.mcp_url,
            "using_mock_data": is_mock,
            "message": "MCP server unavailable - using mock data" if is_mock else "Connected to MCP server"
        }
    except Exception as e:
        return {
            "status": "error",
            "mcp_server": grocery_mcp_service.mcp_url,
            "using_mock_data": True,
            "error": str(e)
        }
