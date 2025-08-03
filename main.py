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

app = FastAPI(title="AI Customer Service Bot", version="3.0.0")

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

# Try to import the new Pure AI system
try:
    from src.api.wix_client import WixAPIClient
    from src.bot.pure_ai_agent import PureAIAgent
    
    # Initialize Wix client
    wix_client = WixAPIClient(WIX_BASE_URL)
    
    # Initialize the Pure AI agent (no pattern matching!)
    agent = PureAIAgent(GROQ_API_KEY, wix_client)
    print("✅ Pure AI agent system initialized successfully - NO REGEX!")
    use_ai_system = True
    
except Exception as e:
    print(f"⚠️  Error loading Pure AI system: {e}")
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

# Legacy fallback function (only used if AI system fails to load)
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
            
            for i, product in enumerate(products[:6], 1):  # Show top 6 products
                result += f"{i}. **{product.get('name', 'Product')}**\n"
                
                # Price information
                if product.get('formattedDiscountedPrice') and product.get('formattedDiscountedPrice') != product.get('formattedPrice'):
                    result += f"   💰 **{product['formattedDiscountedPrice']}** ~~{product.get('formattedPrice', 'N/A')}~~\n"
                else:
                    result += f"   💰 {product.get('formattedPrice', 'Price not available')}\n"
                
                # Stock status
                result += f"   📦 {'✅ In Stock' if product.get('inStock', False) else '❌ Out of Stock'}\n"
                
                # Link to product
                if product.get('slug'):
                    result += f"   🔗 [View Product]({legacy_wix_client.base_url}/product/{product['slug']})\n\n"
                else:
                    result += "\n"
            
            result += f"\n💡 *Showing {len(products[:6])} of {len(products)} new arrivals. Visit our website to see more!*"
            return result
            
        except Exception as e:
            print(f"❌ Error in legacy new arrivals: {e}")
            return "I encountered an error while fetching new arrivals. Please try again or contact support."
    
    # For all other messages, provide general help
    else:
        return "👋 Hello! I'm here to help you discover our latest new arrivals. Just ask me 'show me new arrivals' to see what's fresh in our store! I can also help with general store questions."

# ============================================================================
# API ENDPOINTS - SIMPLIFIED FOR PURE AI
# ============================================================================

# Update your chat endpoint in main.py

# Fix your chat endpoint in main.py - remove the userEmail reference

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        print(f"\n💬 Received message: {message.message}")
        print(f"👤 User ID: {message.user_id}")
        # ❌ REMOVED: print(f"📧 User Email: {message.userEmail}")  # This attribute doesn't exist
        
        if use_ai_system:
            # 🆕 CRITICAL: Pass user_id to the agent for order-related queries
            # The agent will use this to authenticate with Wix backend
            result = await agent.process_message(
                message.message, 
                user_id=message.user_id  # This gets passed to order functions
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
    system_status = "pure_ai" if use_ai_system else "legacy_fallback"
    return {
        "message": "AI Customer Service Bot is running! Ask me about new arrivals, order status, or anything else!", 
        "status": "healthy",
        "system": system_status,
        "version": "3.0.0",
        "features": ["Pure AI Intent Recognition", "Natural Language Processing", "No Pattern Matching"] if use_ai_system else ["Basic Pattern Matching", "Legacy Fallback"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if use_ai_system:
        try:
            wix_connected = await wix_client.test_connection()
            agent_healthy = agent.is_healthy()
            
            return {
                "status": "healthy", 
                "system": "pure_ai",
                "model": "llama-3.3-70b-versatile",
                "wix_api": "connected" if wix_connected else "disconnected",
                "wix_url": wix_client.base_url,
                "groq_api": "connected" if GROQ_API_KEY else "missing",
                "agent_healthy": agent_healthy,
                "ai_features": ["Intent Analysis", "Parameter Extraction", "Response Generation"],
                "no_regex": True,
                "no_patterns": True
            }
        except Exception as e:
            return {
                "status": "degraded",
                "system": "pure_ai",
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
    """Test the AI agent capabilities"""
    if not use_ai_system:
        return {
            "error": "AI system not available",
            "system": "legacy_fallback",
            "message": "Pure AI agent failed to load"
        }
    
    try:
        print("🧪 Testing AI agent capabilities...")
        
        # Test with different types of messages
        test_messages = [
            "Show me new arrivals",
            "Check my order ABC123", 
            "What's new in men's clothing?",
            "I need help with returns"
        ]
        
        test_results = []
        for msg in test_messages:
            try:
                result = await agent.process_message(msg, "test_user")
                test_results.append({
                    "message": msg,
                    "action": result.get("action", "unknown"),
                    "confidence": result.get("confidence", 0),
                    "success": result.get("success", False)
                })
            except Exception as e:
                test_results.append({
                    "message": msg,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "system": "pure_ai",
            "agent_healthy": agent.is_healthy(),
            "test_results": test_results,
            "ai_features": {
                "intent_analysis": True,
                "parameter_extraction": True,
                "natural_language": True,
                "no_regex": True,
                "no_patterns": True
            },
            "test_status": "completed"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "system": "pure_ai",
            "test_status": "failed"
        }

@app.get("/test-wix")
async def test_wix():
    """Test Wix integration"""
    try:
        print("🧪 Testing Wix integration...")
        
        if use_ai_system:
            # Test AI system with Wix
            connection_ok = await wix_client.test_connection()
            new_arrivals = await wix_client.get_new_arrivals(3)
            
            return {
                "system": "pure_ai",
                "wix_connection": connection_ok,
                "wix_url": wix_client.base_url,
                "new_arrivals_count": len(new_arrivals),
                "sample_product": new_arrivals[0] if new_arrivals else "No products found",
                "test_status": "success" if connection_ok and new_arrivals else "failed",
                "available_endpoints": list(wix_client.endpoints.keys())
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
            "system": "pure_ai" if use_ai_system else "legacy_fallback",
            "test_status": "failed"
        }

@app.get("/agent-info")
async def agent_info():
    """Get information about the current agent system"""
    if use_ai_system:
        return {
            "system": "pure_ai",
            "version": "3.0.0",
            "description": "Pure AI-driven customer service agent",
            "features": {
                "intent_recognition": "LLM-based natural language understanding",
                "parameter_extraction": "AI extracts order IDs, search terms, etc.",
                "response_generation": "Contextual AI-generated responses",
                "no_regex": "Zero regular expressions or pattern matching",
                "no_hardcoded_rules": "Fully adaptive AI decision making"
            },
            "capabilities": [
                "New arrivals display",
                "Product search",
                "Order status checking", 
                "General customer support",
                "Natural conversation"
            ],
            "ai_model": "llama-3.3-70b-versatile",
            "agent_healthy": agent.is_healthy() if 'agent' in globals() else False
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
            "note": "This is a fallback system. The Pure AI system is preferred."
        }

if __name__ == "__main__":
    print(f"\n🚀 Starting AI Customer Service Bot v3.0...")
    print(f"📡 Wix URL: {WIX_BASE_URL}")
    print(f"🔑 Groq API Key: {'✅ Set' if GROQ_API_KEY else '❌ Missing'}")
    print(f"🤖 System: {'Pure AI (No Regex!)' if use_ai_system else 'Legacy Fallback'}")
    
    if use_ai_system:
        print("✨ Features: Natural Language Understanding, AI Intent Recognition, Zero Pattern Matching")
    else:
        print("⚠️  Running in fallback mode with basic pattern matching")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)