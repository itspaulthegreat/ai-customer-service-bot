import os
from dotenv import load_dotenv
import requests
from typing import List, Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import uvicorn
import asyncio

# Load environment variables
load_dotenv()

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WIX_BASE_URL = os.getenv("WIX_BASE_URL")
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(title="Enhanced AI Customer Service Bot", version="4.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    confidence: float = 0.8

# Initialize Groq LLM
try:
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=1200,
        groq_api_key=GROQ_API_KEY
    )
    print("✅ Groq LLM initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Groq: {e}")
    raise

# Try to import the enhanced AI system
try:
    from src.api.wix_client import WixAPIClient
    from src.bot.pure_ai_agent import PureAIAgent
    
    # Initialize Wix client
    wix_client = WixAPIClient(WIX_BASE_URL)
    
    # Initialize the Enhanced Pure AI agent
    agent = PureAIAgent(GROQ_API_KEY, wix_client)
    print("✅ Enhanced Pure AI agent system initialized successfully!")
    print("🚀 NEW FEATURES: Multiple orders, order history, statistics, contextual queries")
    use_ai_system = True
    
except Exception as e:
    print(f"⚠️  Error loading Enhanced AI system: {e}")
    print("📦 Falling back to legacy system...")
    use_ai_system = False

# Legacy Wix API client for fallback
class LegacyWixAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url if base_url else "https://your-wix-site.com"
        print(f"🔗 Legacy Wix Base URL: {self.base_url}")
    
    def test_connection(self) -> bool:
        """Test if Wix API is reachable"""
        try:
            url = f"{self.base_url}/_functions/getNewArrivals"
            print(f"🔍 Testing connection to: {url}")
            response = requests.get(url, timeout=10)
            print(f"📡 Response status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def get_new_arrivals(self, limit: int = 15) -> List[Dict]:
        """Get new arrivals from Wix"""
        try:
            url = f"{self.base_url}/_functions/getNewArrivals?limit={limit}"
            print(f"🛍️ Fetching new arrivals from: {url}")
            
            response = requests.get(url, timeout=15)
            print(f"📡 New arrivals response status: {response.status_code}")
            
            if response.status_code == 200:
                products = response.json()
                print(f"✅ Found {len(products)} new arrivals")
                return products
            else:
                print(f"❌ Error response: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error fetching new arrivals: {e}")
            return []

# Initialize legacy client as fallback
if not use_ai_system:
    legacy_wix_client = LegacyWixAPIClient(WIX_BASE_URL)

# Legacy fallback function
def legacy_process_message(message: str) -> str:
    """Legacy message processing with basic pattern matching"""
    message_lower = message.lower()
    print(f"🤔 Legacy processing message: '{message}'")
    
    # Very basic new arrivals detection
    if any(phrase in message_lower for phrase in [
        "new arrivals", "new arrival", "what's new", "whats new", 
        "latest", "recent", "newest", "show me new", "new items",
        "new products", "fresh", "just added", "arrivals"
    ]):
        print("🆕 Detected new arrivals request")
        try:
            products = legacy_wix_client.get_new_arrivals(8)
            if not products:
                return "I'm sorry, I couldn't retrieve the new arrivals right now. Please try again later or check our website directly."
            
            result = "🆕 **Here are our latest new arrivals:**\n\n"
            
            for i, product in enumerate(products[:6], 1):
                result += f"{i}. **{product.get('name', 'Product')}**\n"
                
                if product.get('formattedDiscountedPrice') and product.get('formattedDiscountedPrice') != product.get('formattedPrice'):
                    result += f"   💰 **{product['formattedDiscountedPrice']}** ~~{product.get('formattedPrice', 'N/A')}~~\n"
                else:
                    result += f"   💰 {product.get('formattedPrice', 'Price not available')}\n"
                
                result += f"   📦 {'✅ In Stock' if product.get('inStock', False) else '❌ Out of Stock'}\n"
                
                if product.get('slug'):
                    result += f"   🔗 [View Product]({legacy_wix_client.base_url}/product/{product['slug']})\n\n"
                else:
                    result += "\n"
            
            result += f"\n💡 *Showing {len(products[:6])} of {len(products)} new arrivals. Visit our website to see more!*"
            return result
            
        except Exception as e:
            print(f"❌ Error in legacy new arrivals: {e}")
            return "I encountered an error while fetching new arrivals. Please try again or contact support."
    
    else:
        return "👋 Hello! I'm here to help you discover our latest new arrivals and assist with order management. Just ask me 'show me new arrivals' or 'check my orders' to get started!"

# ============================================================================
# API ENDPOINTS - ENHANCED FOR ADVANCED ORDER MANAGEMENT
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        print(f"\n💬 Received message: {message.message}")
        print(f"👤 User ID: {message.user_id}")
        
        if use_ai_system:
            # 🆕 ENHANCED: Pass user_id to the agent for all order-related queries
            result = await agent.process_message(
                message.message, 
                user_id=message.user_id
            )
            
            return ChatResponse(
                response=result["response"],
                confidence=result["confidence"]
            )
        else:
            # Fallback to legacy system
            response_text = legacy_process_message(message.message)
            return ChatResponse(response=response_text, confidence=0.9)
    
    except Exception as e:
        print(f"❌ Error in chat: {e}")
        import traceback
        traceback.print_exc()
        
        return ChatResponse(
            response="I apologize for the technical difficulty. Please try again or contact our customer service team.",
            confidence=0.1
        )

@app.get("/")
async def root():
    system_status = "enhanced_ai" if use_ai_system else "legacy_fallback"
    features = []
    
    if use_ai_system:
        features = [
            "🧠 Advanced AI Intent Recognition",
            "📋 Single & Multiple Order Status",
            "🕒 Order History (Last N Orders)",
            "📅 Recent Orders (Time-based)",
            "🔍 Orders by Status Filter",
            "📊 Order Statistics & Analytics",
            "💭 Conversation Memory",
            "🛍️ Product Search & Discovery",
            "🚫 Zero Pattern Matching"
        ]
    else:
        features = ["Basic Pattern Matching", "Legacy Fallback"]
    
    return {
        "message": "Enhanced AI Customer Service Bot is running! Ask me about orders, products, or get personalized shopping assistance!", 
        "status": "healthy",
        "system": system_status,
        "version": "4.0.0",
        "new_capabilities": [
            "Multiple order status checking",
            "Order history queries (last N orders)",
            "Time-based order filtering (recent orders)",
            "Status-based order filtering", 
            "Order statistics and analytics",
            "Enhanced conversation memory",
            "Contextual order assistance"
        ],
        "features": features
    }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    if use_ai_system:
        try:
            wix_connected = await wix_client.test_connection()
            agent_healthy = agent.is_healthy()
            
            return {
                "status": "healthy", 
                "system": "enhanced_ai",
                "model": "llama-3.3-70b-versatile",
                "wix_api": "connected" if wix_connected else "disconnected",
                "wix_url": wix_client.base_url,
                "groq_api": "connected" if GROQ_API_KEY else "missing",
                "agent_healthy": agent_healthy,
                "available_endpoints": len(wix_client.endpoints),
                "enhanced_features": {
                    "multiple_order_check": True,
                    "order_history": True,
                    "order_statistics": True,
                    "conversation_memory": True,
                    "contextual_queries": True,
                    "time_based_filtering": True,
                    "status_filtering": True
                },
                "order_capabilities": [
                    "Single order status",
                    "Multiple order status",
                    "Last N orders",
                    "Recent orders (time-based)",
                    "Orders by status",
                    "Order statistics",
                    "Order history analysis"
                ],
                "no_regex": True,
                "no_patterns": True
            }
        except Exception as e:
            return {
                "status": "degraded",
                "system": "enhanced_ai",
                "error": str(e),
                "fallback_available": True
            }
    else:
        try:
            wix_connected = legacy_wix_client.test_connection()
            
            return {
                "status": "healthy", 
                "system": "legacy_fallback",
                "model": "llama-3.3-70b-versatile",
                "wix_api": "connected" if wix_connected else "disconnected",
                "wix_url": legacy_wix_client.base_url,
                "groq_api": "connected" if GROQ_API_KEY else "missing",
                "note": "Using basic pattern matching as fallback"
            }
        except Exception as e:
            return {
                "status": "error",
                "system": "legacy_fallback", 
                "error": str(e)
            }

@app.get("/test-ai")
async def test_ai():
    """Test the enhanced AI agent capabilities"""
    if not use_ai_system:
        return {
            "error": "Enhanced AI system not available",
            "system": "legacy_fallback",
            "message": "Enhanced AI agent failed to load"
        }
    
    try:
        print("🧪 Testing enhanced AI agent capabilities...")
        
        # Test with different types of messages including new order features
        test_messages = [
            "Show me new arrivals",
            "Check my order ABC123", 
            "Check orders ABC123, XYZ789, DEF456",
            "Show my last 3 orders",
            "Orders from last week",
            "My pending orders",
            "How much have I spent?",
            "What's new in men's clothing?",
            "I need help with returns"
        ]
        
        test_results = []
        for msg in test_messages:
            try:
                result = await agent.process_message(msg, "test_user_enhanced")
                test_results.append({
                    "message": msg,
                    "action": result.get("action", "unknown"),
                    "confidence": result.get("confidence", 0),
                    "success": result.get("success", False),
                    "response_preview": result.get("response", "")[:100] + "..." if len(result.get("response", "")) > 100 else result.get("response", "")
                })
            except Exception as e:
                test_results.append({
                    "message": msg,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "system": "enhanced_ai",
            "agent_healthy": agent.is_healthy(),
            "test_results": test_results,
            "enhanced_capabilities": {
                "multiple_order_queries": True,
                "order_history_analysis": True,
                "time_based_filtering": True,
                "status_based_filtering": True,
                "order_statistics": True,
                "conversation_memory": True,
                "natural_language_processing": True,
                "no_regex": True,
                "no_patterns": True
            },
            "test_status": "completed"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "system": "enhanced_ai",
            "test_status": "failed"
        }

@app.get("/test-wix")
async def test_wix():
    """Test enhanced Wix integration"""
    try:
        print("🧪 Testing enhanced Wix integration...")
        
        if use_ai_system:
            # Test enhanced system with new endpoints
            connection_ok = await wix_client.test_connection()
            new_arrivals = await wix_client.get_new_arrivals(3)
            
            # Test new order endpoints (these would require a real user ID)
            test_results = {
                "new_arrivals": len(new_arrivals) > 0,
                "connection": connection_ok
            }
            
            return {
                "system": "enhanced_ai",
                "wix_connection": connection_ok,
                "wix_url": wix_client.base_url,
                "new_arrivals_count": len(new_arrivals),
                "sample_product": new_arrivals[0] if new_arrivals else "No products found",
                "available_endpoints": list(wix_client.endpoints.keys()),
                "enhanced_endpoints": [
                    "multiple_order_status",
                    "last_orders", 
                    "recent_orders",
                    "orders_by_status",
                    "user_order_stats"
                ],
                "test_results": test_results,
                "test_status": "success" if connection_ok and new_arrivals else "partial"
            }
        else:
            # Test legacy system
            connection_ok = legacy_wix_client.test_connection()
            new_arrivals = legacy_wix_client.get_new_arrivals(3)
            
            return {
                "system": "legacy_fallback",
                "wix_connection": connection_ok,
                "wix_url": legacy_wix_client.base_url,
                "new_arrivals_count": len(new_arrivals),
                "sample_product": new_arrivals[0] if new_arrivals else "No products found",
                "test_status": "success" if connection_ok and new_arrivals else "failed"
            }
    except Exception as e:
        return {
            "error": str(e), 
            "system": "enhanced_ai" if use_ai_system else "legacy_fallback",
            "test_status": "failed"
        }

@app.get("/agent-info")
async def agent_info():
    """Get information about the enhanced agent system"""
    if use_ai_system:
        return {
            "system": "enhanced_ai",
            "version": "4.0.0",
            "description": "Enhanced Pure AI-driven customer service agent with advanced order management",
            "features": {
                "intent_recognition": "LLM-based natural language understanding",
                "parameter_extraction": "AI extracts order IDs, search terms, quantities, time periods",
                "response_generation": "Contextual AI-generated responses",
                "conversation_memory": "Session-based conversation tracking",
                "no_regex": "Zero regular expressions or pattern matching",
                "no_hardcoded_rules": "Fully adaptive AI decision making"
            },
            "order_capabilities": {
                "single_order_check": "Check status of individual orders",
                "multiple_order_check": "Check status of multiple orders simultaneously",
                "order_history": "Get last N orders (1-20)",
                "recent_orders": "Get orders from specific time periods",
                "orders_by_status": "Filter orders by status (pending, shipped, etc.)",
                "order_statistics": "Get comprehensive order analytics",
                "contextual_queries": "Handle 'my last order', 'recent purchases', etc."
            },
            "product_capabilities": [
                "New arrivals display",
                "Men's/Women's product filtering",
                "Product search with natural language",
                "Category-based browsing"
            ],
            "general_capabilities": [
                "Natural conversation flow",
                "Contextual help and support",
                "Memory of conversation history",
                "Error handling and recovery"
            ],
            "ai_model": "llama-3.3-70b-versatile",
            "agent_healthy": agent.is_healthy() if 'agent' in globals() else False,
            "supported_queries": [
                "Check my order ABC123",
                "Status of orders ABC123, XYZ789",
                "Show my last 5 orders", 
                "Orders from last week",
                "My pending orders",
                "How much have I spent?",
                "Show new arrivals",
                "Search for red dresses"
            ]
        }
    else:
        return {
            "system": "legacy_fallback",
            "version": "2.0.0",
            "description": "Basic pattern matching fallback system",
            "features": {
                "pattern_matching": "Basic regex-based intent detection",
                "limited_responses": "Template-based responses",
                "fallback_only": "Used when AI system fails to load"
            },
            "capabilities": [
                "Basic new arrivals display",
                "Simple greetings"
            ],
            "note": "This is a fallback system. The Enhanced AI system is preferred."
        }

@app.get("/memory-test")
async def memory_test():
    """Test the conversation memory system"""
    if not use_ai_system:
        return {"error": "Enhanced AI system not available"}
    
    try:
        from src.bot.session_memory import session_memory
        
        # Get memory statistics
        stats = session_memory.get_session_stats()
        
        return {
            "system": "enhanced_ai",
            "memory_system": "active",
            "session_stats": stats,
            "memory_features": [
                "User message tracking",
                "Bot response tracking", 
                "Conversation context",
                "Order ID history extraction",
                "Order ID history extraction",
                "Session timeout management"
            ],
            "test_status": "healthy"
        }
    except Exception as e:
        return {
            "error": str(e),
            "system": "enhanced_ai",
            "test_status": "failed"
        }

if __name__ == "__main__":
    print(f"\n🚀 Starting Enhanced AI Customer Service Bot v4.0...")
    print(f"📡 Wix URL: {WIX_BASE_URL}")
    print(f"🔑 Groq API Key: {'✅ Set' if GROQ_API_KEY else '❌ Missing'}")
    print(f"🤖 System: {'Enhanced AI (Advanced Order Management!)' if use_ai_system else 'Legacy Fallback'}")
    
    if use_ai_system:
        print("✨ NEW ENHANCED FEATURES:")
        print("   🔍 Multiple Order Status Checking")
        print("   📋 Order History Queries (Last N Orders)")
        print("   📅 Time-based Order Filtering (Recent Orders)")
        print("   🏷️  Status-based Order Filtering")
        print("   📊 Order Statistics & Analytics")
        print("   💭 Enhanced Conversation Memory")
        print("   🧠 Natural Language Understanding")
        print("   🚫 Zero Pattern Matching")
        print("\n📝 Example Queries:")
        print("   • 'Check my order ABC123'")
        print("   • 'Status of orders ABC123, XYZ789, DEF456'")
        print("   • 'Show my last 3 orders'")
        print("   • 'Orders from last week'")
        print("   • 'My pending orders'")
        print("   • 'How much have I spent?'")
        print("   • 'What order IDs did I mention?'")
    else:
        print("⚠️  Running in fallback mode with basic pattern matching")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)