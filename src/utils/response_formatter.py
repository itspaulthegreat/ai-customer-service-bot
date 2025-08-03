# src/utils/response_formatter.py
from typing import Dict, List, Any, Optional
import json

class ResponseFormatter:
    """Formats responses for better presentation"""
    
    def __init__(self):
        self.max_products_display = 8
        self.price_currency = "$"
    
    def format_product_list(self, products: List[Dict], title: str = "Products") -> str:
        """Format a list of products for display"""
        if not products:
            return "No products found."
        
        formatted = f"🛍️ **{title}**\n\n"
        
        for i, product in enumerate(products[:self.max_products_display], 1):
            formatted += self._format_single_product(product, i)
            formatted += "\n"
        
        if len(products) > self.max_products_display:
            remaining = len(products) - self.max_products_display
            formatted += f"\n💡 *Showing {self.max_products_display} of {len(products)} items. {remaining} more available!*"
        
        return formatted
    
    def _format_single_product(self, product: Dict, index: int) -> str:
        """Format a single product"""
        name = product.get('name', 'Product')
        
        # Price formatting
        price_info = self._format_price(product)
        
        # Stock status
        stock_status = "✅ In Stock" if product.get('inStock', False) else "❌ Out of Stock"
        
        # Product link
        link = self._create_product_link(product)
        
        formatted = f"{index}. **{name}**\n"
        formatted += f"   {price_info}\n"
        formatted += f"   📦 {stock_status}\n"
        
        if link:
            formatted += f"   🔗 {link}\n"
        
        return formatted
    
    def _format_price(self, product: Dict) -> str:
        """Format product price with discounts"""
        regular_price = product.get('formattedPrice', '')
        discounted_price = product.get('formattedDiscountedPrice', '')
        
        if discounted_price and discounted_price != regular_price:
            return f"💰 **{discounted_price}** ~~{regular_price}~~ (On Sale!)"
        elif regular_price:
            return f"💰 {regular_price}"
        else:
            return "💰 Price available on request"
    
    def _create_product_link(self, product: Dict) -> Optional[str]:
        """Create product link if available"""
        slug = product.get('slug3') or product.get('slug')
        if slug:
            return f"[View Product](https://your-store.com/product/{slug})"
        return None
    
    def format_order_status(self, order_data: Dict) -> str:
        """Format order status information"""
        order_id = order_data.get('orderId', 'Unknown')
        total_items = order_data.get('totalItems', 0)
        
        formatted = f"📦 **Order {order_id}**\n\n"
        formatted += f"📊 **Total Items:** {total_items}\n\n"
        
        # Status groups
        status_groups = order_data.get('statusGroups', {})
        if status_groups:
            formatted += "**Item Status Breakdown:**\n"
            for status, items in status_groups.items():
                status_emoji = self._get_status_emoji(status)
                formatted += f"{status_emoji} {status.title()}: {len(items)} items\n"
            formatted += "\n"
        
        # Items summary
        items_summary = order_data.get('itemsSummary', [])
        if items_summary:
            formatted += "**Items in this order:**\n"
            for item in items_summary[:5]:  # Show first 5 items
                name = item.get('name', 'Item')
                status = item.get('shipmentStatus', 'Processing')
                quantity = item.get('quantity', 1)
                
                status_emoji = self._get_status_emoji(status)
                formatted += f"{status_emoji} {name} (Qty: {quantity}) - {status}\n"
            
            if len(items_summary) > 5:
                remaining = len(items_summary) - 5
                formatted += f"... and {remaining} more items\n"
        
        return formatted
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for order status"""
        status_emojis = {
            'PROCESSING': '⏳',
            'SHIPPED': '🚚',
            'DELIVERED': '📦',
            'CANCELLED': '❌',
            'RETURNED': '🔄',
            'PENDING': '⏸️'
        }
        return status_emojis.get(status.upper(), '📋')
    
    def format_error_message(self, error: str, error_type: str = "general") -> str:
        """Format error messages with helpful context"""
        error_emojis = {
            "order_error": "📦",
            "product_error": "🛍️", 
            "search_error": "🔍",
            "auth_error": "🔐",
            "network_error": "📡",
            "validation_error": "⚠️",
            "general": "😔"
        }
        
        emoji = error_emojis.get(error_type, error_emojis["general"])
        
        formatted = f"{emoji} **Oops!** {error}\n\n"
        
        # Add helpful suggestions based on error type
        suggestions = self._get_error_suggestions(error_type)
        if suggestions:
            formatted += "**Here's what you can try:**\n"
            for suggestion in suggestions:
                formatted += f"• {suggestion}\n"
        
        return formatted
    
    def _get_error_suggestions(self, error_type: str) -> List[str]:
        """Get helpful suggestions for different error types"""
        suggestions = {
            "order_error": [
                "Double-check your order ID format",
                "Make sure you're logged in with the correct account",
                "Try again in a few moments"
            ],
            "product_error": [
                "Try browsing our categories instead",
                "Check our new arrivals",
                "Contact us if the issue persists"
            ],
            "search_error": [
                "Try different keywords",
                "Browse our categories",
                "Check spelling of search terms"
            ],
            "auth_error": [
                "Make sure you're logged in",
                "Check your account credentials", 
                "Contact customer support if needed"
            ]
        }
        
        return suggestions.get(error_type, [
            "Try refreshing and trying again",
            "Contact our customer support team",
            "Let me help you with something else"
        ])
    
    def format_help_response(self, help_data: Dict) -> str:
        """Format help responses with clear structure"""
        response = help_data.get('response', '')
        help_topic = help_data.get('help_topic', 'general')
        
        formatted = f"💡 **Help - {help_topic.title()}**\n\n"
        formatted += f"{response}\n\n"
        
        # Add additional resources if available
        resources = help_data.get('additional_resources', [])
        if resources:
            formatted += "**Additional Resources:**\n"
            for resource in resources:
                formatted += f"• {resource}\n"
        
        return formatted
    
    def format_store_info(self, info_data: Dict) -> str:
        """Format store information"""
        info_type = info_data.get('type', 'general_info')
        info = info_data.get('info', {})
        
        if info_type == "contact_info":
            formatted = "📞 **Contact Information**\n\n"
            formatted += f"📧 Email: {info.get('email', 'N/A')}\n"
            formatted += f"☎️ Phone: {info.get('phone', 'N/A')}\n"
        
        elif info_type == "store_hours":
            formatted = "🕒 **Store Hours**\n\n"
            formatted += f"{info}\n"
        
        elif info_type == "shipping_policy":
            formatted = "📦 **Shipping Information**\n\n"
            formatted += f"{info}\n"
        
        elif info_type == "return_policy":
            formatted = "🔄 **Return Policy**\n\n"
            formatted += f"{info}\n"
        
        else:
            formatted = "🏪 **Store Information**\n\n"
            if isinstance(info, dict):
                for key, value in info.items():
                    formatted += f"**{key.replace('_', ' ').title()}:** {value}\n"
            else:
                formatted += str(info)
        
        return formatted
    
    def create_summary(self, conversation_data: Dict) -> str:
        """Create a conversation summary"""
        tools_used = conversation_data.get('tools_used', [])
        confidence = conversation_data.get('confidence', 0.0)
        
        summary = "📋 **Conversation Summary**\n\n"
        summary += f"🔧 **Tools Used:** {', '.join(tools_used)}\n"
        summary += f"📊 **Confidence:** {confidence:.1%}\n"
        
        context = conversation_data.get('conversation_context', {})
        if context:
            summary += f"💭 **Context:** {len(context)} items tracked\n"
        
        return summary
    
    def is_healthy(self) -> bool:
        """Check if response formatter is working"""
        return True  # Simple formatter, always healthy