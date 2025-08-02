from typing import Dict, List, Any
from .base_tool import BaseTool

class GeneralSupportTool(BaseTool):
    """Tool for handling general customer support inquiries"""
    
    def __init__(self, wix_client):
        super().__init__(
            wix_client=wix_client,
            name="general_support",
            description="Handle general customer support questions and provide helpful responses"
        )
    
    def get_intent_patterns(self) -> List[str]:
        """Return patterns that trigger general support"""
        return [
            "help", "support", "question", "issue", "problem", 
            "contact", "assistance", "information", "about",
            "how", "what", "when", "where", "why", "can you",
            "store hours", "shipping", "return", "exchange",
            "size", "payment", "order"
        ]
    
    def get_fallback_response(self) -> str:
        """Fallback response when tool fails"""
        return "I'm here to help! I can assist you with information about our new arrivals and general questions about our store. What would you like to know?"
    
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute general support response"""
        try:
            print(f"🤝 Processing general support query: {query}")
            
            # Analyze the query and provide appropriate response
            response = self._generate_support_response(query.lower().strip())
            
            return self.format_response(
                data=response,
                success=True
            )
            
        except Exception as e:
            print(f"❌ Error in GeneralSupportTool: {e}")
            return self.format_response(
                data=self.get_fallback_response(),
                success=False
            )
    
    def _generate_support_response(self, query: str) -> str:
        """Generate appropriate support response based on query"""
        
        # Greeting responses
        if any(word in query for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            return "👋 Hello! Welcome to our store! I'm here to help you discover our latest new arrivals and answer any questions you might have. What can I assist you with today?"
        
        # Shipping inquiries
        if any(word in query for word in ["shipping", "delivery", "ship", "deliver"]):
            return "📦 **Shipping Information:**\n\n• We offer various shipping options to meet your needs\n• Standard shipping typically takes 3-7 business days\n• Express shipping available for faster delivery\n• Free shipping may be available on orders over a certain amount\n\nFor specific shipping rates and timeframes to your location, please check our shipping policy on our website or contact our customer service team."
        
        # Return/Exchange inquiries
        if any(word in query for word in ["return", "exchange", "refund"]):
            return "↩️ **Returns & Exchanges:**\n\n• We want you to love your purchase!\n• Returns are typically accepted within 30 days of purchase\n• Items should be in original condition with tags attached\n• Exchange options available for different sizes or colors\n\nFor detailed return instructions and to start a return, please visit our returns page or contact our customer service team."
        
        # Size inquiries
        if any(word in query for word in ["size", "sizing", "fit", "measurement"]):
            return "📏 **Size Guide:**\n\n• Each product page includes detailed size charts\n• We recommend checking measurements against our size guide\n• Size guides vary by brand and product type\n• When in doubt, contact us for personalized sizing advice\n\nYou can find size charts on individual product pages or in our general size guide section."
        
        # Payment inquiries
        if any(word in query for word in ["payment", "pay", "card", "checkout"]):
            return "💳 **Payment Options:**\n\n• We accept major credit cards (Visa, MasterCard, American Express)\n• Secure checkout process protects your information\n• Multiple payment methods may be available\n\nAll transactions are processed securely. For specific payment questions, please contact our customer service team."
        
        # Store hours
        if any(word in query for word in ["hours", "open", "close", "time"]):
            return "🕒 **Store Information:**\n\nOur online store is available 24/7 for your shopping convenience!\n\nFor customer service hours and contact information, please check our contact page. Our team is ready to help you with any questions about our products or services."
        
        # Contact information
        if any(word in query for word in ["contact", "phone", "email", "support"]):
            return "📞 **Contact Us:**\n\n• Visit our Contact page for detailed contact information\n• Customer service team available during business hours\n• Email support for non-urgent inquiries\n• Live chat available on our website\n\nI'm also here to help with questions about our new arrivals and general product information!"
        
        # Product inquiries
        if any(word in query for word in ["product", "item", "clothing", "clothes"]):
            return "👕 **Product Information:**\n\nI'd love to help you find what you're looking for! Here's what I can assist you with:\n\n• **New Arrivals** - Just ask about our latest products!\n• Product details and descriptions\n• Size and fit information\n• Availability and stock status\n\nWhat specific products are you interested in? Try asking about our 'new arrivals' to see our latest items!"
        
        # Order inquiries - Future feature
        if any(word in query for word in ["order", "track", "tracking", "status"]):
            return "📋 **Order Support:**\n\nFor order-related inquiries including:\n• Order status and tracking\n• Order modifications\n• Delivery updates\n\nPlease contact our customer service team directly, as they have access to your specific order information and can provide real-time updates.\n\nYou can also check your account on our website for order history and tracking information."
        
        # General help
        if any(word in query for word in ["help", "assist", "support"]):
            return "🤗 **How I Can Help:**\n\nI'm your friendly shopping assistant! Here's what I can do for you:\n\n✨ **Show you our latest new arrivals**\n📦 Provide general store information\n❓ Answer common questions about shipping, returns, and sizing\n🛍️ Help you discover new products\n\nWhat would you like to explore? Try asking about our 'new arrivals' or 'what's new' to see our latest collection!"
        
        # Default friendly response
        return "😊 Thanks for reaching out! I'm here to help you with information about our store and products.\n\n🆕 **Want to see what's new?** Ask me about our 'new arrivals'!\n🛍️ **Need general help?** I can assist with shipping, returns, sizing, and more.\n💬 **Have a specific question?** Feel free to ask!\n\nWhat can I help you discover today?"