from typing import Dict, List, Any
from .base_tool import BaseTool

class OrderStatusTool(BaseTool):
    """Tool for checking order status and tracking information"""
    
    def __init__(self, wix_client):
        super().__init__(
            wix_client=wix_client,
            name="order_status",
            description="Check order status, track shipments, and get order item details"
        )
    
    def get_intent_patterns(self) -> List[str]:
        """Return patterns that trigger order status queries"""
        return [
            "order status", "order tracking", "track order", "my order",
            "shipment status", "shipping status", "delivery status",
            "where is my order", "order update", "track shipment",
            "check order", "order progress", "shipping tracking",
            "delivery tracking", "order id", "tracking number"
        ]
    
    def get_fallback_response(self) -> str:
        """Fallback response when tool fails"""
        return "I'm sorry, I couldn't retrieve your order information right now. Please try again with your order ID or contact customer service for assistance."
    
    async def execute(self, query: str, order_id: str = None, **kwargs) -> Dict[str, Any]:
        """Execute order status check"""
        try:
            print(f"🚚 Checking order status for query: '{query}'")
            
            # Extract order ID from query if not provided
            if not order_id:
                order_id = self._extract_order_id(query)
                print(f"🔍 Extracted order ID: '{order_id}'")
            
            if not order_id:
                return self.format_response(
                    data="To check your order status, please provide your order ID. For example: 'Check order status for order 12345' or 'Check status of #order_QsItdDdq8jJJMT'",
                    success=False
                )
            
            print(f"📋 Attempting to fetch order items for order ID: '{order_id}'")
            
            # Get order items first to see what's in the order
            order_items_result = await self.wix_client.get_order_items(order_id)
            
            print(f"📡 Order items API response: {order_items_result}")
            
            if not order_items_result.get('success', True):
                error_msg = order_items_result.get('error', 'Order not found')
                print(f"❌ Order items API error: {error_msg}")
                
                if 'access denied' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                    return self.format_response(
                        data="I can only check order status for the customer service team. For order tracking, please log into your account on our website or contact customer service with your order ID.",
                        success=False
                    )
                else:
                    return self.format_response(
                        data=f"Order {order_id} was not found. Please check your order ID and try again. Make sure to include the complete order ID (e.g., 'order_QsItdDdq8jJJMT').",
                        success=False
                    )
            
            # Format the response with order items
            response_text = self._format_order_status_response(order_id, order_items_result)
            
            return self.format_response(
                data=response_text,
                success=True
            )
            
        except Exception as e:
            print(f"❌ Error in OrderStatusTool: {e}")
            import traceback
            traceback.print_exc()
            return self.format_response(
                data=self.get_fallback_response(),
                success=False
            )
    
    def _extract_order_id(self, query: str) -> str:
        """Extract order ID from query string"""
        import re
        
        # Look for patterns like "order 12345", "#order_QsItdDdq8jJJMT", "order ID 12345"
        patterns = [
            r'#(order_[a-zA-Z0-9]+)',  # #order_QsItdDdq8jJJMT
            r'order[_\s]+([a-zA-Z0-9_]+)',  # order_QsItdDdq8jJJMT or order QsItdDdq8jJJMT
            r'#([a-zA-Z0-9_]{10,})',  # Any long alphanumeric string with underscores after #
            r'id[_\s]+([a-zA-Z0-9_]+)',  # id_QsItdDdq8jJJMT or id QsItdDdq8jJJMT
            r'\b([a-zA-Z0-9_]{10,})\b'  # Any alphanumeric string with underscores, 10+ chars
        ]
        
        # Process the query to handle the specific format
        query_processed = query.replace('#order_', 'order_').replace(' ', '_')
        
        for pattern in patterns:
            match = re.search(pattern, query_processed, re.IGNORECASE)
            if match:
                extracted_id = match.group(1)
                print(f"🔍 Extracted order ID: '{extracted_id}' from query: '{query}'")
                return extracted_id
        
        # Fallback: look for any string that looks like an order ID
        fallback_match = re.search(r'([a-zA-Z0-9_]{8,})', query)
        if fallback_match:
            extracted_id = fallback_match.group(1)
            print(f"🔍 Fallback extracted order ID: '{extracted_id}' from query: '{query}'")
            return extracted_id
        
        print(f"❌ Could not extract order ID from query: '{query}'")
        return None
    
    def _format_order_status_response(self, order_id: str, order_data: dict) -> str:
        """Format order status information into readable response"""
        
        if not order_data or 'items' not in order_data:
            return f"📦 **Order {order_id}**\n\nI found your order but couldn't retrieve the item details. Please contact customer service for more information."
        
        items = order_data.get('items', [])
        total_items = order_data.get('totalItems', len(items))
        
        response = f"📦 **Order Status for #{order_id}**\n\n"
        
        if total_items == 0:
            response += "No items found in this order. Please contact customer service if this seems incorrect.\n"
            return response
        
        response += f"**Order Summary:**\n"
        response += f"• Total Items: {total_items}\n\n"
        
        # Group items by shipment status
        status_groups = {}
        for item in items:
            status = item.get('shipmentStatus', 'Unknown')
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(item)
        
        # Display items grouped by status
        for status, status_items in status_groups.items():
            response += f"**{self._format_status_display(status)}** ({len(status_items)} item{'s' if len(status_items) != 1 else ''})\n"
            
            for item in status_items[:5]:  # Show max 5 items per status
                name = item.get('name', 'Unknown Item')
                options = item.get('options', {})
                
                response += f"• {name}"
                
                # Add options like size, color, etc.
                if options and isinstance(options, dict):
                    option_str = ', '.join([f"{k}: {v}" for k, v in options.items() if v])
                    if option_str:
                        response += f" ({option_str})"
                
                response += "\n"
            
            if len(status_items) > 5:
                response += f"  ... and {len(status_items) - 5} more items\n"
            
            response += "\n"
        
        # Add helpful information
        response += "**Next Steps:**\n"
        if any('shipped' in status.lower() or 'transit' in status.lower() for status in status_groups.keys()):
            response += "• Your items are on their way! You should receive tracking information via email.\n"
        elif any('processing' in status.lower() or 'preparing' in status.lower() for status in status_groups.keys()):
            response += "• Your order is being prepared for shipment.\n"
        elif any('delivered' in status.lower() for status in status_groups.keys()):
            response += "• Some or all items have been delivered!\n"
        
        response += "• For detailed tracking info, check your email or log into your account\n"
        response += "• Need help? Contact our customer service team\n"
        
        return response
    
    def _format_status_display(self, status: str) -> str:
        """Format shipment status for display"""
        if not status or status.lower() == 'unknown':
            return "📋 Processing"
        
        status_lower = status.lower()
        
        if 'delivered' in status_lower:
            return "✅ Delivered"
        elif 'shipped' in status_lower or 'transit' in status_lower:
            return "🚚 In Transit"
        elif 'processing' in status_lower or 'preparing' in status_lower:
            return "📋 Processing"
        elif 'cancelled' in status_lower:
            return "❌ Cancelled"
        elif 'returned' in status_lower:
            return "↩️ Returned"
        else:
            return f"📦 {status.title()}"