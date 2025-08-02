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
            # New order endpoints
            "order_items": f"{self.base_url}/_functions/getOrderItems",
            "order_item_status": f"{self.base_url}/_functions/getOrderItemStatus",
            "order_summary": f"{self.base_url}/_functions/getOrderSummary",
            "user_orders": f"{self.base_url}/_functions/getUserOrders",
            "order_status": f"{self.base_url}/_functions/getOrderStatus"  # Legacy
        }
        
        print(f"🔗 WixAPIClient initialized with base URL: {self.base_url}")
    
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
                        # Handle both list and dict responses
                        products = data if isinstance(data, list) else data.get('products', [])
                        print(f"✅ Retrieved {len(products)} new arrivals")
                        return products
                    else:
                        print(f"❌ API returned status {response.status}")
                        text = await response.text()
                        print(f"Response: {text}")
                        return []
                        
        except asyncio.TimeoutError:
            print("❌ Timeout while fetching new arrivals")
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

    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get single product by ID"""
        try:
            print(f"📦 Fetching product: {product_id}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["get_product"],
                    params={"productId": product_id}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        product = data.get('product')
                        if product:
                            print(f"✅ Retrieved product: {product.get('name', 'Unknown')}")
                        return product
                    else:
                        print(f"❌ Product API returned status {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ Error fetching product: {e}")
            return None

    # ============== NEW ORDER STATUS METHODS ==============

    async def get_order_items(self, order_id: str) -> Dict[str, Any]:
        """Get all items in an order - Bot accessible"""
        try:
            print(f"📋 Fetching order items for order: {order_id}")
            
            headers = {
                'User-Agent': 'ai-customer-service-bot/2.0',
                'X-Bot-Request': 'true'
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_items"],
                    params={"orderId": order_id},
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved order items for order: {order_id}")
                        return {
                            "success": True,
                            "orderId": data.get("orderId"),
                            "items": data.get("items", []),
                            "totalItems": data.get("totalItems", 0)
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

    async def get_order_item_status(self, order_id: str, catalog_item_id: str) -> Dict[str, Any]:
        """Get specific order item status - Bot accessible"""
        try:
            print(f"📦 Fetching order item status for order: {order_id}, item: {catalog_item_id}")
            
            headers = {
                'User-Agent': 'ai-customer-service-bot/2.0',
                'X-Bot-Request': 'true'
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_item_status"],
                    params={"orderId": order_id, "catalogItemId": catalog_item_id},
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved order item status")
                        return {
                            "success": True,
                            "orderId": data.get("orderId"),
                            "item": data.get("item"),
                            "shipmentStatus": data.get("shipmentStatus")
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Order item status API returned status {response.status}")
                        return {
                            "success": False,
                            "error": error_data.get("error", "Failed to retrieve order item status"),
                            "code": error_data.get("code", "API_ERROR")
                        }
                        
        except Exception as e:
            print(f"❌ Error fetching order item status: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": "NETWORK_ERROR"
            }

    async def get_order_summary(self, order_id: str) -> Dict[str, Any]:
        """Get order summary - Bot accessible with limited fields"""
        try:
            print(f"📊 Fetching order summary for order: {order_id}")
            
            headers = {
                'User-Agent': 'ai-customer-service-bot/2.0',
                'X-Bot-Request': 'true'
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_summary"],
                    params={"orderId": order_id},
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved order summary")
                        return {
                            "success": True,
                            "order": data.get("order"),
                            "itemCount": data.get("itemCount"),
                            "orderId": data.get("orderId")
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

    # Legacy method for backward compatibility
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Legacy order status method - For backward compatibility"""
        try:
            print(f"📋 Fetching legacy order status: {order_id}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_status"],
                    params={"orderId": order_id}
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
            
            # Test with a simple request to new arrivals
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
    
    def get_endpoint_url(self, endpoint_name: str) -> Optional[str]:
        """Get URL for specific endpoint"""
        return self.endpoints.get(endpoint_name)
    
    def get_all_endpoints(self) -> Dict[str, str]:
        """Get all available endpoints"""
        return self.endpoints.copy()