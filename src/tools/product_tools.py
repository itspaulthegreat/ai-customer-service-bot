# src/tools/product_tools.py
from typing import Dict, List, Any, Optional
import asyncio

class ProductTools:
    """Specialized tools for product-related operations"""
    
    def __init__(self, wix_client):
        self.wix_client = wix_client
    
    async def get_new_arrivals(self, limit: int = 8, category: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get new arrivals with enhanced formatting"""
        try:
            products = await self.wix_client.get_new_arrivals(limit)
            
            return {
                "success": True,
                "type": "new_arrivals",
                "products": products,
                "count": len(products),
                "category": category,
                "limit_requested": limit,
                "message": f"Found {len(products)} latest arrivals" if products else "No new arrivals found"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch new arrivals: {str(e)}",
                "type": "product_error"
            }
    
    async def get_mens_products(self, limit: int = 8, style: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get men's products"""
        try:
            products = await self.wix_client.get_mens_products(limit)
            
            return {
                "success": True,
                "type": "mens_products",
                "products": products,
                "count": len(products),
                "category": "men's",
                "style_filter": style,
                "message": f"Found {len(products)} men's items"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch men's products: {str(e)}",
                "type": "product_error"
            }
    
    async def get_womens_products(self, limit: int = 8, style: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get women's products"""
        try:
            products = await self.wix_client.get_womens_products(limit)
            
            return {
                "success": True,
                "type": "womens_products", 
                "products": products,
                "count": len(products),
                "category": "women's",
                "style_filter": style,
                "message": f"Found {len(products)} women's items"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch women's products: {str(e)}",
                "type": "product_error"
            }
    
    async def search_products(self, query: str, limit: int = 8, category: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Search for products with query"""
        try:
            if not query:
                return {
                    "success": False,
                    "error": "Search query cannot be empty",
                    "type": "validation_error"
                }
            
            products = await self.wix_client.search_products(query, limit)
            
            return {
                "success": True,
                "type": "search_results",
                "products": products,
                "count": len(products),
                "search_query": query,
                "category_filter": category,
                "message": f"Found {len(products)} items matching '{query}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "type": "search_error",
                "search_query": query
            }
    
    async def get_product_details(self, product_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a specific product"""
        try:
            product = await self.wix_client.get_product(product_id)
            
            if product:
                return {
                    "success": True,
                    "type": "product_details",
                    "product": product,
                    "product_id": product_id,
                    "message": f"Found details for {product.get('name', 'product')}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Product {product_id} not found",
                    "type": "not_found",
                    "product_id": product_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get product details: {str(e)}",
                "type": "product_error",
                "product_id": product_id
            }
    
    async def get_product_recommendations(self, based_on: str = "popular", category: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get product recommendations"""
        try:
            # For now, fallback to new arrivals as recommendations
            # This could be enhanced with actual recommendation logic
            products = await self.wix_client.get_new_arrivals(6)
            
            return {
                "success": True,
                "type": "recommendations",
                "products": products,
                "count": len(products),
                "recommendation_type": based_on,
                "category": category,
                "message": f"Here are {len(products)} recommended items based on {based_on}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get recommendations: {str(e)}",
                "type": "recommendation_error"
            }
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run diagnostics on product tools"""
        try:
            # Test basic product fetching
            test_result = await self.get_new_arrivals(2)
            
            return {
                "healthy": test_result.get("success", False),
                "wix_connection": await self.wix_client.test_connection(),
                "test_result": test_result,
                "available_methods": [
                    "get_new_arrivals",
                    "get_mens_products", 
                    "get_womens_products",
                    "search_products",
                    "get_product_details",
                    "get_product_recommendations"
                ]
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def is_healthy(self) -> bool:
        """Check if product tools are healthy"""
        return hasattr(self, 'wix_client') and self.wix_client is not None

