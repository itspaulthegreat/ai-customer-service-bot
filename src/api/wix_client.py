# src/api/wix_client.py - SIMPLIFIED VERSION
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import json

class WixAPIClient:
    """Client for interacting with Wix API endpoints"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # Available endpoints
        self.endpoints = {
            "new_arrivals": f"{self.base_url}/_functions/getNewArrivals",
            "mens_products": f"{self.base_url}/_functions/getMensProducts", 
            "womens_products": f"{self.base_url}/_functions/getWomensProducts",
            "search_products": f"{self.base_url}/_functions/searchProducts",
            "get_product": f"{self.base_url}/_functions/getProduct",
            # Order endpoints
            "order_items": f"{self.base_url}/_functions/getOrderItems",
            "order_summary": f"{self.base_url}/_functions/getOrderSummary",
            "user_orders": f"{self.base_url}/_functions/getUserOrders",
            "order_status": f"{self.base_url}/_functions/getOrderStatus"  # Legacy
        }
        
        print(f"🔗 WixAPIClient initialized with base URL: {self.base_url}")
    
    def _get_headers(self, user_id: str = None) -> Dict[str, str]:
        """Get simplified headers for requests"""
        headers = {
            'User-Agent': 'ai-customer-service-bot/3.0',
            'X-Bot-Request': 'true',
            'Content-Type': 'application/json'
        }
        
        # ✅ SIMPLIFIED: Just add user ID to headers when available
        if user_id:
            headers['X-User-Id'] = user_id
            print(f"🔑 Added user ID to headers: {user_id}")
        
        return headers
    
    # ============== PRODUCT METHODS (No changes needed) ==============
    
    async def get_new_arrivals(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Fetch new arrivals from Wix"""
        try:
            print(f"📡 Fetching new arrivals (limit: {limit})")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["new_arrivals"],
                    params={"limit": limit}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        products = data if isinstance(data, list) else data.get('products', [])
                        print(f"✅ Retrieved {len(products)} new arrivals")
                        return products
                    else:
                        print(f"❌ API returned status {response.status}")
                        text = await response.text()
                        print(f"Response: {text}")
                        return []
                        
        except Exception as e:
            print(f"❌ Error fetching new arrivals: {e}")
            return []

    async def get_mens_products(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Fetch men's products from Wix"""
        try:
            print(f"👔 Fetching men's products (limit: {limit})")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["mens_products"],
                    params={"limit": limit}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        products = data if isinstance(data, list) else data.get('products', [])
                        print(f"✅ Retrieved {len(products)} men's products")
                        return products
                    else:
                        print(f"❌ API returned status {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Error fetching men's products: {e}")
            return []

    async def get_womens_products(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Fetch women's products from Wix"""
        try:
            print(f"👗 Fetching women's products (limit: {limit})")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["womens_products"],
                    params={"limit": limit}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        products = data if isinstance(data, list) else data.get('products', [])
                        print(f"✅ Retrieved {len(products)} women's products")
                        return products
                    else:
                        print(f"❌ API returned status {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Error fetching women's products: {e}")
            return []

    async def search_products(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Search products by query"""
        try:
            print(f"🔍 Searching products for: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["search_products"],
                    params={"query": query, "limit": limit}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        products = data if isinstance(data, list) else data.get('products', [])
                        print(f"✅ Found {len(products)} products for query: {query}")
                        return products
                    else:
                        print(f"❌ Search API returned status {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Error searching products: {e}")
            return []

    # ============== SIMPLIFIED ORDER METHODS ==============

    async def get_order_items(self, order_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get all items in an order - SIMPLIFIED"""
        try:
            print(f"📋 Fetching order items for order: {order_id}, user: {user_id}")
            
            # ✅ Build params - let backend handle user validation
            params = {"orderId": order_id}
            if user_id:
                params["userId"] = user_id
            
            # ✅ Simple headers
            headers = self._get_headers(user_id)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_items"],
                    params=params,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved order items for order: {order_id}")
                        return {
                            "success": True,
                            **data  # Include all response data
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Order items API returned status {response.status}")
                        return {
                            "success": False,
                            "error": error_data.get("error", "Failed to retrieve order items"),
                            "code": error_data.get("code", "API_ERROR")
                        }
                        
        except Exception as e:
            print(f"❌ Error fetching order items: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": "NETWORK_ERROR"
            }

    async def get_order_summary(self, order_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get order summary - SIMPLIFIED"""
        try:
            print(f"📊 Fetching order summary for order: {order_id}, user: {user_id}")
            
            # ✅ Build params
            params = {"orderId": order_id}
            if user_id:
                params["userId"] = user_id
            
            headers = self._get_headers(user_id)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_summary"],
                    params=params,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved order summary")
                        return {
                            "success": True,
                            **data
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Order summary API returned status {response.status}")
                        return {
                            "success": False,
                            "error": error_data.get("error", "Failed to retrieve order summary"),
                            "code": error_data.get("code", "API_ERROR")
                        }
                        
        except Exception as e:
            print(f"❌ Error fetching order summary: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": "NETWORK_ERROR"
            }

    async def get_user_orders(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get user's orders - SIMPLIFIED"""
        try:
            print(f"📋 Fetching user orders for user: {user_id}")
            
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID is required",
                    "code": "MISSING_USER_ID"
                }
            
            params = {"userId": user_id, "limit": limit}
            headers = self._get_headers(user_id)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["user_orders"],
                    params=params,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved user orders")
                        return {
                            "success": True,
                            **data
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ User orders API returned status {response.status}")
                        return {
                            "success": False,
                            "error": error_data.get("error", "Failed to retrieve user orders"),
                            "code": error_data.get("code", "API_ERROR")
                        }
                        
        except Exception as e:
            print(f"❌ Error fetching user orders: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": "NETWORK_ERROR"
            }

    # Legacy method for backward compatibility
    async def get_order_status(self, order_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Legacy order status method"""
        try:
            print(f"📋 Fetching legacy order status: {order_id}")
            
            params = {"orderId": order_id}
            if user_id:
                params["userId"] = user_id
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_status"],
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        if 'error' not in data:
                            print(f"✅ Retrieved legacy order status")
                            return data
                        else:
                            print(f"❌ Legacy order status error: {data['error']}")
                            return None
                    else:
                        print(f"❌ Legacy order status API returned status {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ Error fetching legacy order status: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """Test connection to Wix API"""
        try:
            print("🔧 Testing Wix API connection...")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(
                    self.endpoints["new_arrivals"],
                    params={"limit": 1}
                ) as response:
                    
                    success = response.status == 200
                    print(f"{'✅' if success else '❌'} Wix API connection test: {'passed' if success else 'failed'}")
                    return success
                    
        except Exception as e:
            print(f"❌ Wix API connection test failed: {e}")
            return False