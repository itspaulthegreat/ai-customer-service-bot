from typing import Dict, List, Any
from .base_tool import BaseTool

class NewArrivalsTool(BaseTool):
    """Tool for fetching and displaying new arrivals"""
    
    def __init__(self, wix_client):
        super().__init__(
            wix_client=wix_client,
            name="new_arrivals",
            description="Get the latest new arrivals from the store"
        )
    
    def get_intent_patterns(self) -> List[str]:
        """Return patterns that trigger new arrivals"""
        return [
            "new arrivals", "new arrival", "what's new", "whats new",
            "latest", "recent", "newest", "show me new", "new items",
            "new products", "fresh", "just added", "arrivals", "just in"
        ]
    
    def get_fallback_response(self) -> str:
        """Fallback response when tool fails"""
        return "I'm sorry, I couldn't retrieve the new arrivals right now. Please try again later or visit our website to browse our latest collection."
    
    async def execute(self, query: str, limit: int = 8, **kwargs) -> Dict[str, Any]:
        """Execute new arrivals fetch"""
        try:
            print(f"🛍️ Fetching new arrivals (limit: {limit})")
            
            # Get products from Wix
            products = await self.wix_client.get_new_arrivals(limit * 2)  # Fetch more for filtering
            
            if not products:
                return self.format_response(
                    data=self.get_fallback_response(),
                    success=False
                )
            
            # Format the response
            response_text = self._format_products_response(products[:limit])
            
            return self.format_response(
                data={
                    "response": response_text,
                    "product_count": len(products[:limit]),
                    "total_available": len(products)
                }
            )
            
        except Exception as e:
            print(f"❌ Error in NewArrivalsTool: {e}")
            return self.format_response(
                data=self.get_fallback_response(),
                success=False
            )
    
    def _format_products_response(self, products: List[Dict]) -> str:
        """Format products into a readable response"""
        if not products:
            return self.get_fallback_response()
        
        response = "🆕 **Here are our latest new arrivals:**\n\n"
        
        for i, product in enumerate(products, 1):
            response += f"{i}. **{product.get('name', 'Product')}**\n"
            
            # Price information with better formatting
            discounted_price = product.get('formattedDiscountedPrice')
            regular_price = product.get('formattedPrice', 'Price not available')
            
            if discounted_price and discounted_price != regular_price:
                response += f"   💰 **{discounted_price}** ~~{regular_price}~~ 🏷️ *Sale!*\n"
            else:
                response += f"   💰 {regular_price}\n"
            
            # Stock status with emojis
            in_stock = product.get('inStock', False)
            response += f"   📦 {'✅ In Stock' if in_stock else '❌ Out of Stock'}\n"
            
            # Product link if available
            slug = product.get('slug')
            if slug:
                product_url = f"{self.wix_client.base_url}/product/{slug}"
                response += f"   🔗 [View Product]({product_url})\n\n"
            else:
                response += "\n"
        
        # Add footer with additional info
        total_shown = len(products)
        response += f"\n💡 *Showing {total_shown} latest arrivals. "
        response += "Ask me about 'men's new arrivals' or 'women's new arrivals' for category-specific items!*\n\n"
        response += "🛒 **Ready to shop?** Click any product link above or visit our website to explore more!"
        
        return response