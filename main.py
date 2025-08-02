import os
from dotenv import load_dotenv
import requests
from typing import List, Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_groq import ChatGroq
import uvicorn
import asyncio

# Load environment variables
load_dotenv()

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WIX_BASE_URL = os.getenv("WIX_BASE_URL")
PORT = int(os.getenv("PORT", 8000))  # For Render

app = FastAPI(title="AI Customer Service Bot", version="2.0.0")

# CORS middleware - Allow all origins for now
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
        max_tokens=1000,
        groq_api_key=GROQ_API_KEY
    )
    print("✅ Groq LLM initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Groq: {e}")
    raise

# Import the modular components
try:
    from src.api.wix_client import WixAPIClient
    from src.bot.agent import CustomerServiceAgent
    
    # Initialize Wix client
    wix_client = WixAPIClient(WIX_BASE_URL)
    
    # Initialize the main agent
    agent = CustomerServiceAgent(GROQ_API_KEY, wix_client)
    print("✅ Modular agent system initialized successfully")
    use_modular_system = True
    
except Exception as e:
    print(f"⚠️  Error loading modular system: {e}")
    print("📦 Falling back to legacy system...")
    use_modular_system = False

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
legacy_wix_client = LegacyWixAPIClient(WIX_BASE_URL)

# Legacy new arrivals tool
@tool
def get_new_arrivals_tool(query: str = "") -> str:
    """Get the latest new arrivals from the store. Use this when customers ask about new arrivals, latest products, or what's new."""
    try:
        print(f"🛍️ Legacy tool called: get_new_arrivals_tool")
        products = legacy_wix_client.get_new_arrivals(15)
        
        if not products:
            return "I'm sorry, I couldn't retrieve the new arrivals right now. Please try again later or check our website directly."
        
        result = "🆕 **Here are our latest new arrivals:**\n\n"
        
        for i, product in enumerate(products[:8], 1):  # Show top 8 products
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
        
        result += f"\n💡 *Showing {len(products[:8])} of {len(products)} new arrivals. Visit our website to see more!*"
        
        return result
        
    except Exception as e:
        print(f"❌ Error in get_new_arrivals_tool: {e}")
        return "I encountered an error while fetching new arrivals. Please try again or contact support."

# Legacy agent for fallback
def create_legacy_agent():
    """Create a legacy customer service agent"""
    
    system_prompt = """You are a helpful customer service assistant for an online clothing store.

Your main function is to show customers our latest new arrivals when they ask.

You have access to this tool:
- get_new_arrivals_tool: Get the latest new arrivals from the store

Guidelines:
- Be friendly, helpful, and professional
- Use get_new_arrivals_tool when customers ask about "new arrivals", "latest products", "what's new", or similar
- For general greetings, be welcoming and mention you can show them new arrivals
- If customers ask about other things you can't help with, politely let them know your specialty is showing new arrivals
- Keep responses concise but informative"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    return prompt | llm

# Create the legacy agent
try:
    legacy_agent_chain = create_legacy_agent()
    print("✅ Legacy customer service agent created successfully")
except Exception as e:
    print(f"❌ Error creating legacy agent: {e}")
    raise

def legacy_process_message(message: str) -> str:
    """Legacy message processing"""
    message_lower = message.lower()
    print(f"🤔 Legacy processing message: '{message}'")
    
    # Check for new arrivals requests
    if any(phrase in message_lower for phrase in [
        "new arrivals", "new arrival", "what's new", "whats new", 
        "latest", "recent", "newest", "show me new", "new items",
        "new products", "fresh", "just added", "arrivals"
    ]):
        print("🆕 Detected new arrivals request")
        return get_new_arrivals_tool.invoke({"query": message})
    
    # For all other messages, use the AI agent
    else:
        try:
            print("🤖 Using legacy AI agent for general response")
            response = legacy_agent_chain.invoke({"input": message})
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"❌ Error with legacy agent: {e}")
            return "Hello! I'm here to help you discover our latest new arrivals. Just ask me 'show me new arrivals' to see what's fresh in our store!"

# API Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint"""
    try:
        print(f"\n💬 Received message: {message.message}")
        
        if use_modular_system:
            # Use the new modular agent system
            print("🚀 Using modular agent system")
            result = await agent.process_message(message.message, message.user_id)
            
            response_text = result.get("response", "I'm sorry, I couldn't process your request.")
            confidence = result.get("confidence", 0.8)
            
            print(f"🤖 Modular bot response: {response_text[:100]}...")
            
            return ChatResponse(
                response=response_text,
                confidence=confidence
            )
        else:
            # Use legacy system
            print("📦 Using legacy system")
            response_text = legacy_process_message(message.message)
            
            print(f"🤖 Legacy bot response: {response_text[:100]}...")
            
            return ChatResponse(
                response=response_text,
                confidence=0.9
            )
    
    except Exception as e:
        print(f"❌ Error in chat: {e}")
        return ChatResponse(
            response="I'm sorry, I encountered an error. Please try again or contact support.",
            confidence=0.1
        )

@app.get("/")
async def root():
    system_status = "modular" if use_modular_system else "legacy"
    return {
        "message": "AI Customer Service Bot is running! Ask me about new arrivals and order status!", 
        "status": "healthy",
        "system": system_status,
        "version": "2.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if use_modular_system:
        wix_connected = await wix_client.test_connection()
        agent_healthy = agent.is_healthy()
        
        return {
            "status": "healthy", 
            "system": "modular",
            "model": "llama-3.3-70b-versatile",
            "wix_api": "connected" if wix_connected else "disconnected",
            "wix_url": wix_client.base_url,
            "groq_api": "connected" if GROQ_API_KEY else "missing",
            "agent_healthy": agent_healthy,
            "tools": list(agent.tools.keys()) if agent_healthy else []
        }
    else:
        wix_connected = legacy_wix_client.test_connection()
        
        return {
            "status": "healthy", 
            "system": "legacy",
            "model": "llama-3.3-70b-versatile",
            "wix_api": "connected" if wix_connected else "disconnected",
            "wix_url": legacy_wix_client.base_url,
            "groq_api": "connected" if GROQ_API_KEY else "missing"
        }

@app.get("/test-wix")
async def test_wix():
    """Test Wix integration"""
    try:
        print("🧪 Testing Wix integration...")
        
        if use_modular_system:
            # Test modular system
            connection_ok = await wix_client.test_connection()
            new_arrivals = await wix_client.get_new_arrivals(5)
            
            return {
                "system": "modular",
                "wix_connection": connection_ok,
                "wix_url": wix_client.base_url,
                "new_arrivals_count": len(new_arrivals),
                "sample_product": new_arrivals[0] if new_arrivals else "No products found",
                "test_status": "success" if connection_ok and new_arrivals else "failed",
                "endpoints": list(wix_client.endpoints.keys())
            }
        else:
            # Test legacy system
            connection_ok = legacy_wix_client.test_connection()
            new_arrivals = legacy_wix_client.get_new_arrivals(5)
            
            return {
                "system": "legacy",
                "wix_connection": connection_ok,
                "wix_url": legacy_wix_client.base_url,
                "new_arrivals_count": len(new_arrivals),
                "sample_product": new_arrivals[0] if new_arrivals else "No products found",
                "test_status": "success" if connection_ok and new_arrivals else "failed"
            }
    except Exception as e:
        return {
            "error": str(e), 
            "system": "modular" if use_modular_system else "legacy",
            "test_status": "failed"
        }

@app.get("/test-order-status")
async def test_order_status():
    """Test order status functionality (modular system only)"""
    if not use_modular_system:
        return {
            "error": "Order status testing only available in modular system",
            "system": "legacy"
        }
    
    try:
        print("🧪 Testing order status functionality...")
        
        # Test order status tool
        order_tool = agent.tools.get("order_status")
        if not order_tool:
            return {
                "error": "Order status tool not found",
                "available_tools": list(agent.tools.keys())
            }
        
        # Test with a sample order ID
        test_result = await order_tool.execute("Check order status for order TEST123")
        
        return {
            "system": "modular",
            "order_tool_available": True,
            "test_query": "Check order status for order TEST123",
            "test_result": test_result,
            "test_status": "success" if test_result.get("success", False) else "expected_failure"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "system": "modular",
            "test_status": "failed"
        }

if __name__ == "__main__":
    print(f"\n🚀 Starting AI Customer Service Bot v2.0...")
    print(f"📡 Wix URL: {WIX_BASE_URL}")
    print(f"🔑 Groq API Key: {'✅ Set' if GROQ_API_KEY else '❌ Missing'}")
    print(f"🤖 System: {'Modular' if use_modular_system else 'Legacy'}")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)