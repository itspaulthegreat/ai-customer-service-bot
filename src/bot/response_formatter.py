from typing import Dict, Any, Optional

class ResponseFormatter:
    """Formats responses for different result types in a consistent and scalable way"""

    @staticmethod
    def format_new_arrivals(result: Dict[str, Any]) -> str:
        """Format response for new arrivals"""
        products = result.get("data", {}).get("products", [])
        if not products:
            return "No new arrivals right now. Want to see men's or women's products?"
        products_text = "\n".join([f"• {p.get('name', 'Unknown')} - ${p.get('price', 'N/A')}" for p in products[:5]])
        more_text = "There are more new arrivals! Want to see the full list?" if len(products) > 5 else ""
        return f"Check out our latest arrivals! 🛍️\nHere are our newest arrivals:\n{products_text}\n{more_text}"

    @staticmethod
    def format_mens_products(result: Dict[str, Any]) -> str:
        """Format response for men's products"""
        products = result.get("data", {}).get("products", [])
        if not products:
            return "No men's products found. Try searching for something specific or check out new arrivals!"
        products_text = "\n".join([f"• {p.get('name', 'Unknown')} - ${p.get('price', 'N/A')}" for p in products[:5]])
        more_text = "There are more men's products! Want to see the full list?" if len(products) > 5 else ""
        return f"Here are some men's products:\n{products_text}\n{more_text}"

    @staticmethod
    def format_womens_products(result: Dict[str, Any]) -> str:
        """Format response for women's products"""
        products = result.get("data", {}).get("products", [])
        if not products:
            return "No women's products found. Try searching for something specific or check out new arrivals!"
        products_text = "\n".join([f"• {p.get('name', 'Unknown')} - ${p.get('price', 'N/A')}" for p in products[:5]])
        more_text = "There are more women's products! Want to see the full list?" if len(products) > 5 else ""
        return f"Here are some women's products:\n{products_text}\n{more_text}"

    @staticmethod
    def format_search_results(result: Dict[str, Any]) -> str:
        """Format response for search results"""
        products = result.get("data", {}).get("products", [])
        query = result.get("data", {}).get("search_query", "your search")
        if not products:
            return f"No products found for '{query}'. Try a different search or check out our new arrivals!"
        products_text = "\n".join([f"• {p.get('name', 'Unknown')} - ${p.get('price', 'N/A')}" for p in products[:5]])
        more_text = "There are more results! Want to see the full list?" if len(products) > 5 else ""
        return f"Here are the results for '{query}':\n{products_text}\n{more_text}"

    @staticmethod
    def format_order_status(result: Dict[str, Any]) -> str:
        """Format response for order status"""
        if not result.get("success", False):
            error_code = result.get("code", "")
            order_id = result.get("order_id", "unknown")
            if error_code == "MISSING_USER_ID":
                return "🔐 Please make sure you're logged in to check your order status. Once logged in, I'll be happy to help you track your orders!"
            elif error_code == "UNAUTHORIZED":
                return f"🔐 I'm sorry, but I couldn't find order {order_id} for your account. This could mean:\n• The order ID might be incorrect\n• The order belongs to a different account\n• You might need to log in first\nPlease double-check your order ID and make sure you're logged into the correct account."
            elif error_code == "NOT_FOUND":
                return f"🤔 I couldn't find order {order_id}. Please double-check the order ID and try again. If you need help, let me know!"
            else:
                return f"😔 Sorry, I ran into an issue checking your order: {result.get('error', 'Unknown error')}. Please try again or contact support for assistance."

        order_id = result.get("data", {}).get("orderId", "")
        total_items = result.get("data", {}).get("totalItems", 0)
        items_summary = result.get("data", {}).get("itemsSummary", [])
        items_text = []
        for item in items_summary:
            options = item.get("options", {})
            size = options.get("Size", "N/A")
            items_text.append(f"• {item.get('name', 'Unknown')} (Size {size}) - {item.get('shipmentStatus', 'Unknown')}")
        items_str = "\n".join(items_text) if items_text else "No items found."
        if total_items > 1:
            return f"Great news! I found your order {order_id} with {total_items} items! 🛍️\n\nYour order includes:\n{items_str}\n\nAll items are currently being prepared. You'll receive tracking information once they ship. Anything else I can help with?"
        else:
            return f"🎉 I found your order {order_id} with 1 item! Your {items_text[0]}. You'll receive tracking information once it's shipped. Anything else I can help with?"

    @staticmethod
    def format_user_orders(result: Dict[str, Any]) -> str:
        """Format response for user orders"""
        if not result.get("success", False):
            error_code = result.get("code", "")
            if error_code == "UNAUTHORIZED":
                return "🔐 Please log in to view your orders. Once logged in, I can show you all your recent orders!"
            else:
                return f"😔 Sorry, I ran into an issue fetching your orders: {result.get('error', 'Unknown error')}. Please try again or contact support."
        orders = result.get("data", {}).get("orders", [])
        if not orders:
            return "You haven't placed any orders yet. Want to check out our new arrivals?"
        orders_text = "\n".join([f"• Order {o.get('orderId', 'Unknown')} - {o.get('orderStatus', 'Unknown')} ({o.get('itemCount', 0)} items)" for o in orders[:5]])
        more_text = "There are more orders! Want to see the full list?" if len(orders) > 5 else ""
        return f"Here are your recent orders:\n{orders_text}\n{more_text}"

    @staticmethod
    def format_memory_response(result: Dict[str, Any]) -> str:
        """Format response for memory requests"""
        request_type = result.get("request_type", "general")
        memory_content = result.get("memory_content", "")

        if request_type == "order_id_history":
            if isinstance(memory_content, list):
                if memory_content:
                    return f"💭 You asked for the order IDs you've mentioned. Here they are:\n" + "\n".join([f"• {oid}" for oid in memory_content]) + "\nWould you like me to check the status of any of these orders?"
                else:
                    return "💭 You haven't mentioned any order IDs in our conversation yet. If you share one, I can check its status for you!"
            else:
                return memory_content
        elif request_type == "previous_user_message":
            return f"💭 Your last message was: {memory_content}" if result.get("found", False) else memory_content
        elif request_type == "previous_bot_message":
            return f"💭 I last said: {memory_content}" if result.get("found", False) else memory_content
        elif request_type == "conversation_summary":
            return memory_content
        else:
            return "💭 I remember our conversation and I'm here to help! What would you like to know?"

    @staticmethod
    def format_help_response(result: Dict[str, Any]) -> str:
        """Format response for help requests"""
        return result.get("data", {}).get("content", "I'm here to help! Could you clarify what you're looking for, or would you like to see our latest products?")

    @staticmethod
    def format_error(result: Dict[str, Any], original_message: str) -> str:
        """Format response for general errors"""
        return f"😔 Sorry, I ran into an issue: {result.get('error', 'Unknown error')}. Please try again or ask for something else!"