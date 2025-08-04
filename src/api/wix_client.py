# src/api/wix_client.py - ENHANCED VERSION WITH NEW ORDER ENDPOINTS
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import json

class WixAPIClient:
    """Enhanced client for interacting with Wix API endpoints with advanced order management"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # Available endpoints - ENHANCED with new order capabilities
        self.endpoints = {
            # Product endpoints (unchanged)
            "new_arrivals": f"{self.base_url}/_functions/getNewArrivals",
            "mens_products": f"{self.base_url}/_functions/getMensProducts", 
            "womens_products": f"{self.base_url}/_functions/getWomensProducts",
            "search_products": f"{self.base_url}/_functions/searchProducts",
            "get_product": f"{self.base_url}/_functions/getProduct",
            
            # Existing order endpoints
            "order_items": f"{self.base_url}/_functions/getOrderItems",
            "order_summary": f"{self.base_url}/_functions/getOrderSummary",
            "user_orders": f"{self.base_url}/_functions/getUserOrders",
            "order_status": f"{self.base_url}/_functions/getOrderStatus",  # Legacy
            
            # NEW: Enhanced order endpoints
            "multiple_order_status": f"{self.base_url}/_functions/getMultipleOrderStatus",
            "last_orders": f"{self.base_url}/_functions/getLastOrders",
            "recent_orders": f"{self.base_url}/_functions/getRecentOrders",
            "orders_by_status": f"{self.base_url}/_functions/getOrdersByStatus",
            "user_order_stats": f"{self.base_url}/_functions/getUserOrderStats"
        }
        
        print(f"🔗 Enhanced WixAPIClient initialized with base URL: {self.base_url}")
        print(f"📋 Available endpoints: {len(self.endpoints)} total")
        print(f"🆕 New order endpoints: multiple_order_status, last_orders, recent_orders, orders_by_status, user_order_stats")
    
    def _get_headers(self, user_id: str = None) -> Dict[str, str]:
        """Get headers for requests with enhanced bot identification"""
        headers = {
            'User-Agent': 'ai-customer-service-bot/4.0-enhanced',
            'X-Bot-Request': 'true',
            'Content-Type': 'application/json',
            'X-Bot-Version': '4.0',
            'X-Feature-Set': 'enhanced-order-management'
        }
        
        # Add user ID to headers when available
        if user_id:
            headers['X-User-Id'] = user_id
            print(f"🔑 Added user ID to headers: {user_id}")
        
        return headers
    
    # ============== PRODUCT METHODS (Unchanged) ==============
    
    async def get_new_arrivals(self, limit: int = 8) -> Dict[str, Any]:
        """Fetch new arrivals from Wix"""
        try:
            print(f"📡 Fetching new arrivals (limit: {limit})")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["new_arrivals"],
                    params={"limit": limit},
                    headers=self._get_headers()
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved {len(data.get('metric_value', []))} new arrivals")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        print(f"❌ API returned status {response.status}")
                        text = await response.text()
                        print(f"Response: {text}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": "Failed to retrieve new arrivals",
                            "code": "API_ERROR",
                            "context": {"type": "new_arrivals"}
                        }

        except Exception as e:
            print(f"❌ Error fetching new arrivals: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "new_arrivals"}
            }
    async def get_mens_products(self, limit: int = 8) -> Dict[str, Any]:
        """Fetch men's products from Wix"""
        try:
            print(f"👔 Fetching men's products (limit: {limit})")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["mens_products"],
                    params={"limit": limit},
                    headers=self._get_headers()
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved {len(data.get('metric_value', []))} men's products")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        print(f"❌ API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": "Failed to retrieve men's products",
                            "code": "API_ERROR",
                            "context": {"type": "mens_products"}
                        }

        except Exception as e:
            print(f"❌ Error fetching men's products: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "mens_products"}
            }

    async def get_womens_products(self, limit: int = 8) -> Dict[str, Any]:
        """Fetch women's products from Wix"""
        try:
            print(f"👗 Fetching women's products (limit: {limit})")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["womens_products"],
                    params={"limit": limit},
                    headers=self._get_headers()
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved {len(data.get('metric_value', []))} women's products")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        print(f"❌ API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": "Failed to retrieve women's products",
                            "code": "API_ERROR",
                            "context": {"type": "womens_products"}
                        }

        except Exception as e:
            print(f"❌ Error fetching women's products: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "womens_products"}
            }

    async def search_products(self, query: str, limit: int = 8) -> Dict[str, Any]:
        """Search products by query"""
        try:
            print(f"🔍 Searching products for: {query}")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["search_products"],
                    params={"query": query, "limit": limit},
                    headers=self._get_headers()
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Found {len(data.get('metric_value', []))} products for query: {query}")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        print(f"❌ Search API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": "Failed to search products",
                            "code": "API_ERROR",
                            "context": {"type": "search_products"}
                        }

        except Exception as e:
            print(f"❌ Error searching products: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "search_products"}
            }

    # ============== EXISTING ORDER METHODS (Enhanced) ==============

    async def get_order_items(self, order_id: str, user_id: str = None) -> Dict[str, Any]:
        try:
            print(f"📋 Fetching order items for order: {order_id}, user: {user_id}")
            
            params = {"orderId": order_id}
            if user_id:
                params["userId"] = user_id
            
            headers = self._get_headers(user_id)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_items"],
                    params=params,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Raw response: {data}") # Add this log to inspect the response
                        print(f"✅ Retrieved order items for order: {order_id}")
                        return {
                            "success": True,
                            **data
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
        """Get order summary - Enhanced"""
        try:
            print(f"📊 Fetching order summary for order: {order_id}, user: {user_id}")

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
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Order summary API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": error_data.get("error", "Failed to retrieve order summary"),
                            "code": error_data.get("code", "API_ERROR"),
                            "context": {"type": "order_summary", "orderId": order_id}
                        }

        except Exception as e:
            print(f"❌ Error fetching order summary: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "order_summary", "orderId": order_id}
            }

    async def get_user_orders(self, user_id: str, limit: int = 20, include_items: bool = False) -> Dict[str, Any]:
        """Get user's orders - Enhanced with more options"""
        try:
            print(f"📋 Fetching user orders for user: {user_id}, limit: {limit}, include_items: {include_items}")

            if not user_id:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "User ID is required",
                    "code": "MISSING_USER_ID",
                    "context": {"type": "user_orders"}
                }

            params = {
                "userId": user_id,
                "limit": limit,
                "includeItems": str(include_items).lower()
            }
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
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ User orders API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": error_data.get("error", "Failed to retrieve user orders"),
                            "code": error_data.get("code", "API_ERROR"),
                            "context": {"type": "user_orders", "userId": user_id}
                        }

        except Exception as e:
            print(f"❌ Error fetching user orders: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "user_orders", "userId": user_id}
            }

    # ============== NEW: ENHANCED ORDER MANAGEMENT METHODS ==============

    async def get_multiple_order_status(self, order_ids: List[str], user_id: str = None) -> Dict[str, Any]:
        """Check status of multiple orders at once - NEW"""
        try:
            print(f"🔍 Checking multiple order status: {order_ids}, user: {user_id}")

            if not order_ids or len(order_ids) == 0:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "Order IDs list is required",
                    "code": "MISSING_PARAMETER",
                    "context": {"type": "multiple_order_status"}
                }

            if len(order_ids) > 10:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "Maximum 10 orders can be checked at once",
                    "code": "TOO_MANY_ORDERS",
                    "context": {"type": "multiple_order_status"}
                }

            order_ids_str = ",".join(order_ids)

            params = {"orderIds": order_ids_str}
            if user_id:
                params["userId"] = user_id

            headers = self._get_headers(user_id)

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["multiple_order_status"],
                    params=params,
                    headers=headers
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved multiple order status for {len(order_ids)} orders")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Multiple order status API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": error_data.get("error", "Failed to retrieve multiple order status"),
                            "code": error_data.get("code", "API_ERROR"),
                            "context": {"type": "multiple_order_status", "orderIds": order_ids}
                        }

        except Exception as e:
            print(f"❌ Error checking multiple order status: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "multiple_order_status", "orderIds": order_ids}
            }

    async def get_last_orders(self, user_id: str, count: int = 1) -> Dict[str, Any]:
        """Get user's last N orders - NEW"""
        try:
            print(f"📋 Fetching last {count} orders for user: {user_id}")

            if not user_id:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "User ID is required",
                    "code": "MISSING_USER_ID",
                    "context": {"type": "last_orders"}
                }

            if count < 1 or count > 20:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "Count must be between 1 and 20",
                    "code": "INVALID_PARAMETER",
                    "context": {"type": "last_orders"}
                }

            params = {
                "userId": user_id,
                "count": count
            }
            headers = self._get_headers(user_id)

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["last_orders"],
                    params=params,
                    headers=headers
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved last {count} orders")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Last orders API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": error_data.get("error", "Failed to retrieve last orders"),
                            "code": error_data.get("code", "API_ERROR"),
                            "context": {"type": "last_orders", "userId": user_id}
                        }

        except Exception as e:
            print(f"❌ Error fetching last orders: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "last_orders", "userId": user_id}
            }
    async def get_recent_orders(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's orders from last N days - NEW"""
        try:
            print(f"📅 Fetching orders from last {days} days for user: {user_id}")

            if not user_id:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "User ID is required",
                    "code": "MISSING_USER_ID",
                    "context": {"type": "recent_orders"}
                }

            if days < 1 or days > 365:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "Days must be between 1 and 365",
                    "code": "INVALID_PARAMETER",
                    "context": {"type": "recent_orders"}
                }

            params = {
                "userId": user_id,
                "days": days
            }
            headers = self._get_headers(user_id)

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["recent_orders"],
                    params=params,
                    headers=headers
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved orders from last {days} days")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Recent orders API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": error_data.get("error", "Failed to retrieve recent orders"),
                            "code": error_data.get("code", "API_ERROR"),
                            "context": {"type": "recent_orders", "userId": user_id}
                        }

        except Exception as e:
            print(f"❌ Error fetching recent orders: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "recent_orders", "userId": user_id}
            }
    async def get_orders_by_status(self, user_id: str, status: str, limit: int = 10) -> Dict[str, Any]:
        """Get user's orders filtered by status - NEW"""
        try:
            print(f"🏷️ Fetching orders with status '{status}' for user: {user_id}")

            if not user_id:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "User ID is required",
                    "code": "MISSING_USER_ID",
                    "context": {"type": "orders_by_status"}
                }

            if not status:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "Status parameter is required",
                    "code": "MISSING_PARAMETER",
                    "context": {"type": "orders_by_status"}
                }

            params = {
                "userId": user_id,
                "status": status,
                "limit": limit
            }
            headers = self._get_headers(user_id)

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["orders_by_status"],
                    params=params,
                    headers=headers
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved orders with status '{status}'")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Orders by status API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": error_data.get("error", "Failed to retrieve orders by status"),
                            "code": error_data.get("code", "API_ERROR"),
                            "context": {"type": "orders_by_status", "status": status}
                        }

        except Exception as e:
            print(f"❌ Error fetching orders by status: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "orders_by_status", "status": status}
            }

    async def get_user_order_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive order statistics for user - NEW"""
        try:
            print(f"📊 Fetching order statistics for user: {user_id}")

            if not user_id:
                return {
                    "success": False,
                    "metric_value": [],
                    "error": "User ID is required",
                    "code": "MISSING_USER_ID",
                    "context": {"type": "user_order_stats"}
                }

            params = {"userId": user_id}
            headers = self._get_headers(user_id)

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["user_order_stats"],
                    params=params,
                    headers=headers
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Retrieved order statistics")
                        return {
                            "success": data.get("success", False),
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        print(f"❌ Order statistics API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": error_data.get("error", "Failed to retrieve order statistics"),
                            "code": error_data.get("code", "API_ERROR"),
                            "context": {"type": "user_order_stats", "userId": user_id}
                        }

        except Exception as e:
            print(f"❌ Error fetching order statistics: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "user_order_stats", "userId": user_id}
            }

    # ============== HELPER AND UTILITY METHODS ==============

    # Legacy method for backward compatibility
    async def get_order_status(self, order_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Legacy order status method - maintained for backward compatibility"""
        try:
            print(f"📋 Fetching legacy order status: {order_id}")

            params = {"orderId": order_id}
            if user_id:
                params["userId"] = user_id

            headers = self._get_headers(user_id)

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.endpoints["order_status"],
                    params=params,
                    headers=headers
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        if 'error' in data:
                            print(f"❌ Legacy order status error: {data['error']}")
                            return {
                                "success": False,
                                "metric_value": [],
                                "error": data.get("error", "Unknown error"),
                                "code": data.get("code", "API_ERROR"),
                                "context": {"type": "order_status", "orderId": order_id}
                            }
                        print(f"✅ Retrieved legacy order status")
                        return {
                            "success": True,
                            "metric_value": data.get("metric_value", []),
                            "context": data.get("context", {})
                        }
                    else:
                        print(f"❌ Legacy order status API returned status {response.status}")
                        return {
                            "success": False,
                            "metric_value": [],
                            "error": "Failed to retrieve order status",
                            "code": "API_ERROR",
                            "context": {"type": "order_status", "orderId": order_id}
                        }

        except Exception as e:
            print(f"❌ Error fetching legacy order status: {e}")
            return {
                "success": False,
                "metric_value": [],
                "error": str(e),
                "code": "NETWORK_ERROR",
                "context": {"type": "order_status", "orderId": order_id}
            }
    
    async def test_connection(self) -> bool:
        """Test connection to Wix API - Enhanced with more comprehensive testing"""
        try:
            print("🔧 Testing enhanced Wix API connection...")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Test basic product endpoint
                async with session.get(
                    self.endpoints["new_arrivals"],
                    params={"limit": 1},
                    headers=self._get_headers()
                ) as response:
                    
                    success = response.status == 200
                    print(f"{'✅' if success else '❌'} Basic API connection test: {'passed' if success else 'failed'}")
                    
                    if success:
                        print(f"🆕 Enhanced order endpoints available: {len([k for k in self.endpoints.keys() if 'order' in k])}")
                        print(f"🎯 Total API endpoints: {len(self.endpoints)}")
                    
                    return success
                    
        except Exception as e:
            print(f"❌ Enhanced Wix API connection test failed: {e}")
            return False

    def get_available_endpoints(self) -> Dict[str, str]:
        """Get list of all available API endpoints"""
        return self.endpoints.copy()

    def get_order_endpoints(self) -> Dict[str, str]:
        """Get list of order-related endpoints only"""
        return {k: v for k, v in self.endpoints.items() if 'order' in k.lower()}

    def get_enhanced_capabilities(self) -> List[str]:
        """Get list of enhanced capabilities provided by this client"""
        return [
            "Multiple order status checking",
            "Last N orders retrieval", 
            "Time-based order filtering (recent orders)",
            "Status-based order filtering",
            "Comprehensive order statistics",
            "Enhanced error handling",
            "User context preservation",
            "Bot request identification"
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all systems"""
        try:
            print("🏥 Running comprehensive health check...")
            
            # Test basic connection
            connection_ok = await self.test_connection()
            
            # Test a few key endpoints
            endpoint_tests = {}
            test_endpoints = ["new_arrivals", "search_products"]
            
            for endpoint_name in test_endpoints:
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.get(
                            self.endpoints[endpoint_name],
                            params={"limit": 1} if "arrivals" in endpoint_name else {"query": "test", "limit": 1},
                            headers=self._get_headers()
                        ) as response:
                            endpoint_tests[endpoint_name] = response.status == 200
                except Exception:
                    endpoint_tests[endpoint_name] = False
            
            return {
                "overall_health": connection_ok,
                "base_url": self.base_url,
                "total_endpoints": len(self.endpoints),
                "order_endpoints": len(self.get_order_endpoints()),
                "enhanced_features": len(self.get_enhanced_capabilities()),
                "endpoint_tests": endpoint_tests,
                "enhanced_version": "4.0",
                "capabilities": self.get_enhanced_capabilities()
            }
            
        except Exception as e:
            return {
                "overall_health": False,
                "error": str(e),
                "base_url": self.base_url
            }