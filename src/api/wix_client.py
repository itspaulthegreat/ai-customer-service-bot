// src/api/wix_client.py - SIMPLIFIED & UNIFIED
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional

class WixAPIClient:
    """Simplified Wix API client with unified response format"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # 🎯 SIMPLE: All endpoints in one place
        self.endpoints = {
            # Product endpoints
            "new_arrivals": f"{self.base_url}/_functions/getNewArrivals",
            "mens_products": f"{self.base_url}/_functions/getMensProducts", 
            "womens_products": f"{self.base_url}/_functions/getWomensProducts",
            "search_products": f"{self.base_url}/_functions/searchProducts",
            "get_product": f"{self.base_url}/_functions/getProduct",
            
            # Order endpoints - simplified
            "order_items": f"{self.base_url}/_functions/getOrderItems",
            "order_summary": f"{self.base_url}/_functions/getOrderSummary",
            "order_item_status": f"{self.base_url}/_functions/getOrderItemStatus",
            "user_orders": f"{self.base_url}/_functions/getUserOrders",
            "full_order_details": f"{self.base_url}/_functions/getFullOrderDetails",
            
            # Legacy
            "order_status": f"{self.base_url}/_functions/getOrderStatus"
        }
        
        print(f"🔗 WixAPIClient initialized: {self.base_url}")
    
    def _get_headers(self, user_id: str = None) -> Dict[str, str]:
        """Get standard headers for requests"""
        headers = {
            'User-Agent': 'ai-customer-service-bot/3.0',
            'X-Bot-Request': 'true',
            'Content-Type': 'application/json'
        }
        
        if user_id:
            headers['X-User-Id'] = user_id
        
        return headers
    
    async def _make_request(self, endpoint: str, params: Dict = None, user_id: str = None) -> Dict[str, Any]:
        """Unified request method with consistent response format"""
        try:
            headers = self._get_headers(user_id)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(endpoint, params=params, headers=headers) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Handle unified response format
                        if isinstance(data, dict) and 'success' in data:
                            return data  # Already in our format
                        
                        # Handle legacy product array responses
                        if isinstance(data, list):
                            return {
                                "success": True,
                                "code": "SUCCESS",
                                "message": "Data retrieved successfully",
                                "data": {"items": data, "count": len(data)}
                            }
                        
                        # Handle other object responses
                        return {
                            "success": True,
                            "code": "SUCCESS", 
                            "message": "Data retrieved successfully",
                            "data": data
                        }
                    
                    else:
                        # Handle error responses
                        try:
                            error_data = await response.json()
                        except:
                            error_data = {"error": f"HTTP {response.status}"}
                        
                        return {
                            "success": False,
                            "code": error_data.get("code", "API_ERROR"),
                            "message": error_data.get("error", error_data.get("message", f"Request failed with status {response.status}")),
                            "status": response.status
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "code": "NETWORK_ERROR",
                "message": str(e)
            }
    
    # 🚀 PRODUCT METHODS - Super simple now!
    
    async def get_new_arrivals(self, limit: int = 8) -> Dict[str, Any]:
        """Get new arrivals"""
        return await self._make_request(
            self.endpoints["new_arrivals"], 
            {"limit": limit}
        )
    
    async def get_mens_products(self, limit: int = 8) -> Dict[str, Any]:
        """Get men's products"""
        return await self._make_request(
            self.endpoints["mens_products"], 
            {"limit": limit}
        )
    
    async def get_womens_products(self, limit: int = 8) -> Dict[str, Any]:
        """Get women's products"""
        return await self._make_request(
            self.endpoints["womens_products"], 
            {"limit": limit}
        )
    
    async def search_products(self, query: str, limit: int = 8) -> Dict[str, Any]:
        """Search products"""
        return await self._make_request(
            self.endpoints["search_products"], 
            {"query": query, "limit": limit}
        )
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get single product"""
        return await self._make_request(
            self.endpoints["get_product"], 
            {"id": product_id}
        )
    
    # 🚀 ORDER METHODS - Unified and simple!
    
    async def get_order_items(self, order_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get all items in an order"""
        if not user_id:
            return {
                "success": False,
                "code": "MISSING_USER_ID",
                "message": "User ID is required for order access"
            }
        
        return await self._make_request(
            self.endpoints["order_items"],
            {"orderId": order_id},
            user_id
        )
    
    async def get_order_summary(self, order_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get order summary"""
        if not user_id:
            return {
                "success": False,
                "code": "MISSING_USER_ID", 
                "message": "User ID is required for order access"
            }
        
        return await self._make_request(
            self.endpoints["order_summary"],
            {"orderId": order_id},
            user_id
        )
    
    async def get_order_item_status(self, order_id: str, catalog_item_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get specific order item status"""
        if not user_id:
            return {
                "success": False,
                "code": "MISSING_USER_ID",
                "message": "User ID is required for order access"
            }
        
        return await self._make_request(
            self.endpoints["order_item_status"],
            {"orderId": order_id, "catalogItemId": catalog_item_id},
            user_id
        )
    
    async def get_user_orders(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get user's orders"""
        if not user_id:
            return {
                "success": False,
                "code": "MISSING_USER_ID",
                "message": "User ID is required"
            }
        
        return await self._make_request(
            self.endpoints["user_orders"],
            {"limit": limit},
            user_id
        )
    
    async def get_full_order_details(self, order_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get complete order details"""
        if not user_id:
            return {
                "success": False,
                "code": "MISSING_USER_ID",
                "message": "User ID is required for order access"
            }
        
        return await self._make_request(
            self.endpoints["full_order_details"],
            {"orderId": order_id},
            user_id
        )
    
    # 🛠️ UTILITY METHODS
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            result = await self.get_new_arrivals(1)
            return result.get("success", False)
        except:
            return False
    
    def get_endpoint_url(self, endpoint_name: str) -> Optional[str]:
        """Get specific endpoint URL"""
        return self.endpoints.get(endpoint_name)
    
    def get_all_endpoints(self) -> Dict[str, str]:
        """Get all endpoints"""
        return self.endpoints.copy()
    
    # 🆕 EASY TO EXTEND: Add new methods here!
    
    async def get_orders_by_status(self, status: str, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get orders by status - example of easy extension"""
        # This would need the corresponding backend endpoint
        endpoint = f"{self.base_url}/_functions/getOrdersByStatus"
        return await self._make_request(
            endpoint,
            {"status": status, "limit": limit},
            user_id
        )
    
    async def get_recent_orders(self, user_id: str, days: int = 30, limit: int = 10) -> Dict[str, Any]:
        """Get recent orders - another easy extension"""
        endpoint = f"{self.base_url}/_functions/getRecentOrders"
        return await self._make_request(
            endpoint,
            {"days": days, "limit": limit},
            user_id
        )