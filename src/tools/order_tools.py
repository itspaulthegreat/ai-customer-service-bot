# src/tools/order_tools.py
from typing import Dict, List, Any, Optional
import asyncio

class OrderTools:
    """Specialized tools for order-related operations"""
    
    def __init__(self, wix_client):
        self.wix_client = wix_client
    
    async def get_order_status(self, order_id: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get comprehensive order status"""
        try:
            if not order_id:
                return {
                    "success": False,
                    "error": "Order ID is required",
                    "type": "validation_error",
                    "help_message": "Please provide your order ID (e.g., order_ABC123)"
                }
            
            if not user_id:
                return {
                    "success": False,
                    "error": "User authentication required",
                    "type": "auth_error", 
                    "help_message": "Please make sure you're logged in to check your order"
                }
            
            # Get order items (most comprehensive info)
            order_result = await self.wix_client.get_order_items(order_id, user_id)
            
            if order_result.get("success"):
                return {
                    "success": True,
                    "type": "order_status",
                    "order_id": order_id,
                    "order_data": order_result,
                    "items_count": order_result.get("totalItems", 0),
                    "status_summary": self._create_status_summary(order_result),
                    "message": f"Order {order_id} found with {order_result.get('totalItems', 0)} items"
                }
            else:
                error_code = order_result.get("code", "UNKNOWN_ERROR")
                
                if error_code == "UNAUTHORIZED":
                    return {
                        "success": False,
                        "error": "Order not found or access denied",
                        "type": "access_denied",
                        "order_id": order_id,
                        "help_message": "Please check your order ID and make sure you're logged in with the correct account"
                    }
                else:
                    return {
                        "success": False,
                        "error": order_result.get("error", "Order not found"),
                        "type": "order_error",
                        "order_id": order_id,
                        "code": error_code
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to check order status: {str(e)}",
                "type": "system_error",
                "order_id": order_id
            }
    
    async def get_order_items(self, order_id: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get detailed list of items in an order"""
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "User authentication required",
                    "type": "auth_error"
                }
            
            result = await self.wix_client.get_order_items(order_id, user_id)
            
            if result.get("success"):
                return {
                    "success": True,
                    "type": "order_items",
                    "order_id": order_id,
                    "items": result.get("items", []),
                    "items_summary": result.get("itemsSummary", []),
                    "status_groups": result.get("statusGroups", {}),
                    "total_items": result.get("totalItems", 0),
                    "message": f"Found {result.get('totalItems', 0)} items in order {order_id}"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Could not retrieve order items"),
                    "type": "order_error",
                    "order_id": order_id,
                    "code": result.get("code")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get order items: {str(e)}",
                "type": "system_error"
            }
    
    async def get_user_orders(self, user_id: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Get user's order history"""
        try:
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID required",
                    "type": "auth_error"
                }
            
            # This would use the user orders endpoint
            # For now, return a placeholder response
            return {
                "success": False,
                "error": "Order history feature coming soon",
                "type": "feature_unavailable",
                "message": "We're working on making order history available. For now, please check specific orders by ID."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get order history: {str(e)}",
                "type": "system_error"
            }
    
    async def track_shipment(self, order_id: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get shipment tracking information"""
        try:
            # Get order status first
            order_result = await self.get_order_status(order_id, user_id)
            
            if order_result.get("success"):
                order_data = order_result.get("order_data", {})
                status_groups = order_data.get("statusGroups", {})
                
                # Extract tracking information
                tracking_info = {
                    "order_id": order_id,
                    "shipment_statuses": status_groups,
                    "tracking_available": bool(status_groups.get("SHIPPED") or status_groups.get("DELIVERED"))
                }
                
                return {
                    "success": True,
                    "type": "tracking_info",
                    "tracking_data": tracking_info,
                    "message": "Here's your shipment tracking information"
                }
            else:
                return order_result  # Return the error from order status
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get tracking information: {str(e)}",
                "type": "tracking_error"
            }
    
    async def handle_return_request(self, order_id: str, reason: str = "", user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Handle return/exchange requests"""
        try:
            # For now, provide return policy information and guidance
            return {
                "success": True,
                "type": "return_request",
                "order_id": order_id,
                "return_policy": {
                    "return_window": "30 days",
                    "condition": "Items must be unworn with tags",
                    "process": "Contact customer service to initiate return"
                },
                "next_steps": [
                    "Keep your order confirmation and items with tags",
                    "Contact our customer service team",
                    "We'll provide a return shipping label"
                ],
                "message": "I can help you with your return request. Here's what you need to know about our return policy."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process return request: {str(e)}",
                "type": "return_error"
            }
    
    def _create_status_summary(self, order_data: Dict) -> Dict[str, Any]:
        """Create a human-readable status summary"""
        try:
            status_groups = order_data.get("statusGroups", {})
            total_items = order_data.get("totalItems", 0)
            
            summary = {
                "total_items": total_items,
                "status_breakdown": {},
                "overall_status": "Processing",
                "estimated_delivery": "5-7 business days"
            }
            
            # Analyze status groups
            for status, items in status_groups.items():
                summary["status_breakdown"][status] = len(items)
            
            # Determine overall status
            if status_groups.get("DELIVERED"):
                summary["overall_status"] = "Delivered"
            elif status_groups.get("SHIPPED"):
                summary["overall_status"] = "Shipped"
            elif status_groups.get("PROCESSING"):
                summary["overall_status"] = "Processing"
            
            return summary
            
        except Exception:
            return {"total_items": 0, "overall_status": "Unknown"}
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run diagnostics on order tools"""
        try:
            # Test with a dummy order (this will fail gracefully)
            test_result = await self.get_order_status("test_order_123", "test_user")
            
            return {
                "healthy": True,  # Tool is healthy even if test order fails
                "wix_connection": await self.wix_client.test_connection(),
                "test_result": test_result,
                "available_methods": [
                    "get_order_status",
                    "get_order_items",
                    "get_user_orders", 
                    "track_shipment",
                    "handle_return_request"
                ]
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def is_healthy(self) -> bool:
        """Check if order tools are healthy"""
        return hasattr(self, 'wix_client') and self.wix_client is not None