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

# Load environment variables
load_dotenv()

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WIX_BASE_URL = os.getenv("WIX_BASE_URL")

app = FastAPI(title="AI Customer Service Bot", version="1.0.0")

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
        max_tokens=1000,
        groq_api_key=GROQ_API_KEY
    )
    print("✅ Groq LLM initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Groq: {e}")
    raise

# Simplified Wix API client - New Arrivals Only
class WixAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url if base_url else "https://your-wix-site.com"
        print(f"🔗 Wix Base URL: {self.base_url}")
    
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

# Initialize Wix client
wix_client = WixAPIClient(WIX_BASE_URL)

# New arrivals tool
@tool
def get_new_arrivals_tool(query: str = "") -> str:
    """Get the latest new arrivals from the store. Use this when customers ask about new arrivals, latest products, or what's new."""
    try:
        print(f"🛍️ Tool called: get_new_arrivals_tool")
        products = wix_client.get_new_arrivals(15)
        
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
                result += f"   🔗 [View Product]({wix_client.base_url}/product/{product['slug']})\n\n"
            else:
                result += "\n"
        
        result += f"\n💡 *Showing {len(products[:8])} of {len(products)} new arrivals. Visit our website to see more!*"
        
        return result
        
    except Exception as e:
        print(f"❌ Error in get_new_arrivals_tool: {e}")
        return "I encountered an error while fetching new arrivals. Please try again or contact support."

# Create the customer service agent
def create_customer_service_agent():
    """Create a customer service agent focused on new arrivals"""
    
    system_prompt = """You are a helpful customer service assistant for an online clothing store.

Your main function is to show customers our latest new arrivals when they ask.

You have access to this tool:
- get_new_arrivals_tool: Get the latest new arrivals from the store

Guidelines:
- Be friendly, helpful, and professional
- Use get_new_arrivals_tool when customers ask about "new arrivals", "latest products", "what's new", or similar
- For general greetings, be welcoming and mention you can show them new arrivals
- If customers ask about other things you can't help with, politely let them know your specialty is showing new arrivals
- Keep responses concise but informative

Common phrases that should trigger new arrivals:
- "new arrivals"
- "what's new"
- "latest products" 
- "show me new items"
- "recent additions"
- "newest items"

When customers greet you, welcome them and offer to show new arrivals."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    return prompt | llm

# Create the agent
try:
    agent_chain = create_customer_service_agent()
    print("✅ Customer service agent created successfully")
except Exception as e:
    print(f"❌ Error creating agent: {e}")
    raise

def process_message(message: str) -> str:
    """Process message and decide whether to show new arrivals or use general AI"""
    message_lower = message.lower()
    print(f"🤔 Processing message: '{message}'")
    
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
            print("🤖 Using AI agent for general response")
            response = agent_chain.invoke({"input": message})
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"❌ Error with agent: {e}")
            return "Hello! I'm here to help you discover our latest new arrivals. Just ask me 'show me new arrivals' to see what's fresh in our store!"

# API Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint"""
    try:
        print(f"\n💬 Received message: {message.message}")
        
        # Process the message
        response_text = process_message(message.message)
        
        print(f"🤖 Bot response: {response_text[:100]}...")
        
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
    return {"message": "AI Customer Service Bot is running! Ask me about new arrivals!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    wix_connected = wix_client.test_connection()
    return {
        "status": "healthy", 
        "model": "llama-3.3-70b-versatile",
        "wix_api": "connected" if wix_connected else "disconnected",
        "wix_url": wix_client.base_url,
        "groq_api": "connected" if GROQ_API_KEY else "missing"
    }

@app.get("/test-wix")
async def test_wix():
    """Test Wix integration"""
    try:
        print("🧪 Testing Wix integration...")
        
        # Test connection
        connection_ok = wix_client.test_connection()
        
        # Test new arrivals
        new_arrivals = wix_client.get_new_arrivals(5)
        
        return {
            "wix_connection": connection_ok,
            "wix_url": wix_client.base_url,
            "new_arrivals_count": len(new_arrivals),
            "sample_product": new_arrivals[0] if new_arrivals else "No products found",
            "test_status": "success" if connection_ok and new_arrivals else "failed"
        }
    except Exception as e:
        return {
            "error": str(e), 
            "wix_url": wix_client.base_url,
            "test_status": "failed"
        }

if __name__ == "__main__":
    print(f"\n🚀 Starting AI Customer Service Bot (New Arrivals Only)...")
    print(f"📡 Wix URL: {WIX_BASE_URL}")
    print(f"🔑 Groq API Key: {'✅ Set' if GROQ_API_KEY else '❌ Missing'}")
    print(f"🌐 Chat interface: Open chat.html in your browser")
    print(f"🔧 Health check: http://localhost:8000/health")
    print(f"🧪 Test Wix: http://localhost:8000/test-wix")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)