"""
Grocery API Service with Coles/Woolworths MCP Server Integration
Connects to the MCP server for real-time product search and pricing
"""
import httpx
import logging
from typing import List, Dict, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class GroceryMCPService:
    """Service for interacting with Coles/Woolworths MCP Server"""
    
    def __init__(self):
        self.mcp_url = getattr(settings, 'COLES_WOOLWORTHS_MCP_URL', 'http://localhost:3001')
        self.timeout = 30.0
        
    async def search_products(
        self,
        query: str,
        store: str = "both",  # 'coles', 'woolworths', or 'both'
        limit: int = 10,
        coles_store_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Search for products using the MCP server
        
        Args:
            query: Search term (e.g., "milk", "bread")
            store: Which store(s) to search ('coles', 'woolworths', 'both')
            limit: Maximum number of results per store
            coles_store_id: Optional Coles store ID for location-specific results
            
        Returns:
            Dict with product results from both stores
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "query": query,
                    "store": store,
                    "limit": limit
                }
                
                if coles_store_id:
                    params["coles_store_id"] = coles_store_id
                
                response = await client.get(
                    f"{self.mcp_url}/search",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"MCP search for '{query}' returned {len(data.get('results', []))} products")
                    return data
                else:
                    logger.error(f"MCP server error: {response.status_code}")
                    return self._get_fallback_results(query, store, limit)
                    
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return self._get_fallback_results(query, store, limit)
    
    async def search_coles(
        self,
        query: str,
        limit: int = 10,
        store_id: Optional[str] = None
    ) -> List[Dict]:
        """Search Coles products specifically"""
        result = await self.search_products(query, "coles", limit, store_id)
        return result.get("coles", [])
    
    async def search_woolworths(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search Woolworths products specifically"""
        result = await self.search_products(query, "woolworths", limit)
        return result.get("woolworths", [])
    
    async def compare_prices(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, any]:
        """
        Compare prices between Coles and Woolworths
        
        Returns:
            Dict with comparison data including best deals
        """
        results = await self.search_products(query, "both", limit)
        
        coles_products = results.get("coles", [])
        woolworths_products = results.get("woolworths", [])
        
        # Find best deals
        coles_cheapest = min(coles_products, key=lambda x: x.get("price", float('inf'))) if coles_products else None
        woolworths_cheapest = min(woolworths_products, key=lambda x: x.get("price", float('inf'))) if woolworths_products else None
        
        return {
            "query": query,
            "coles": {
                "products": coles_products,
                "cheapest": coles_cheapest,
                "count": len(coles_products)
            },
            "woolworths": {
                "products": woolworths_products,
                "cheapest": woolworths_cheapest,
                "count": len(woolworths_products)
            },
            "best_deal": self._determine_best_deal(coles_cheapest, woolworths_cheapest)
        }
    
    async def generate_shopping_list(
        self,
        items: List[str],
        store_preference: str = "both"
    ) -> Dict[str, any]:
        """
        Generate a shopping list with prices from selected store(s)
        
        Args:
            items: List of item names to search
            store_preference: 'coles', 'woolworths', or 'both'
            
        Returns:
            Shopping list with products and total estimate
        """
        shopping_list = []
        total_coles = 0.0
        total_woolworths = 0.0
        
        for item in items:
            result = await self.search_products(item, store_preference, limit=1)
            
            item_data = {
                "item": item,
                "coles": result.get("coles", [])[0] if result.get("coles") else None,
                "woolworths": result.get("woolworths", [])[0] if result.get("woolworths") else None
            }
            
            if item_data["coles"]:
                total_coles += item_data["coles"].get("price", 0)
            if item_data["woolworths"]:
                total_woolworths += item_data["woolworths"].get("price", 0)
            
            shopping_list.append(item_data)
        
        return {
            "items": shopping_list,
            "totals": {
                "coles": round(total_coles, 2),
                "woolworths": round(total_woolworths, 2),
                "savings": round(abs(total_coles - total_woolworths), 2),
                "cheaper_store": "coles" if total_coles < total_woolworths else "woolworths"
            }
        }
    
    def _determine_best_deal(
        self,
        coles_product: Optional[Dict],
        woolworths_product: Optional[Dict]
    ) -> Optional[Dict]:
        """Determine which product is the best deal"""
        if not coles_product and not woolworths_product:
            return None
        
        if not coles_product:
            return {"store": "woolworths", "product": woolworths_product}
        
        if not woolworths_product:
            return {"store": "coles", "product": coles_product}
        
        coles_price = coles_product.get("price", float('inf'))
        woolworths_price = woolworths_product.get("price", float('inf'))
        
        if coles_price < woolworths_price:
            return {
                "store": "coles",
                "product": coles_product,
                "savings": round(woolworths_price - coles_price, 2)
            }
        else:
            return {
                "store": "woolworths",
                "product": woolworths_product,
                "savings": round(coles_price - woolworths_price, 2)
            }
    
    def _get_fallback_results(
        self,
        query: str,
        store: str,
        limit: int
    ) -> Dict[str, any]:
        """Return mock data when MCP server is unavailable"""
        logger.warning(f"Using fallback mock data for '{query}'")
        
        mock_product = {
            "name": f"{query.title()} (Product)",
            "price": 4.99,
            "unit": "each",
            "brand": "Generic Brand",
            "image_url": "/api/placeholder/200/200",
            "availability": "In Stock",
            "note": "⚠️ Mock data - MCP server unavailable"
        }
        
        result = {}
        if store in ["coles", "both"]:
            result["coles"] = [mock_product] * min(limit, 3)
        if store in ["woolworths", "both"]:
            result["woolworths"] = [mock_product] * min(limit, 3)
        
        return result


# Global instance
grocery_mcp_service = GroceryMCPService()
