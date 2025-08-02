import os
from dotenv import load_dotenv
import json
import requests
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
import uvicorn

# Load environment variables
load_dotenv()

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Get free API key from console.groq.com
WIX_BASE_URL = os.getenv("WIX_BASE_URL")  # Your Wix site URL like https://your-site.wixsite.com/your-site

app = FastAPI(title="AI Customer Service Bot", version="1.0.0")

# CORS middleware for web integration
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

# Improved Wix API integration
class WixAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url if base_url else "https://your-wix-site.com"
        print(f"🔗 Wix Base URL: {self.base_url}")
    
    def test_connection(self) -> bool:
        """Test if Wix API is reachable"""
        try:
            # Test the new arrivals endpoint
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
    
    def get_mens_products(self, limit: int = 15) -> List[Dict]:
        """Get men's products from Wix"""
        try:
            url = f"{self.base_url}/_functions/getMensProducts?limit={limit}"
            print(f"👔 Fetching men's products from: {url}")
            
            response = requests.get(url, timeout=15)
            print(f"📡 Men's products response status: {response.status_code}")
            
            if response.status_code == 200:
                products = response.json()
                print(f"✅ Found {len(products)} men's products")
                return products
            else:
                print(f"❌ Error response: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error fetching men's products: {e}")
            return []
    
    def get_womens_products(self, limit: int = 15) -> List[Dict]:
        """Get women's products from Wix"""
        try:
            url = f"{self.base_url}/_functions/getWomensProducts?limit={limit}"
            print(f"👗 Fetching women's products from: {url}")
            
            response = requests.get(url, timeout=15)
            print(f"📡 Women's products response status: {response.status_code}")
            
            if response.status_code == 200:
                products = response.json()
                print(f"✅ Found {len(products)} women's products")
                return products
            else:
                print(f"❌ Error response: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error fetching women's products: {e}")
            return []
    
    def search_products(self, query: str, category: str = None) -> List[Dict]:
        """Search products based on query and optional category"""
        try:
            print(f"🔍 Searching for: '{query}' in category: {category}")
            
            # Get products based on category
            if category == "men":
                products = self.get_mens_products()
            elif category == "women" or category == "womens":
                products = self.get_womens_products()
            else:
                products = self.get_new_arrivals()
            
            if not products:
                print("❌ No products returned from Wix")
                return []
            
            # If no specific query, return all products
            if not query or query.lower() in ["new arrivals", "all", "show me", "latest"]:
                return products[:10]  # Return top 10
            
            # Filter products based on query
            filtered_products = []
            query_lower = query.lower()
            
            for product in products:
                name_lower = product.get('name', '').lower()
                description_lower = product.get('description', '').lower()
                
                if (query_lower in name_lower or 
                    query_lower in description_lower or
                    any(word in name_lower for word in query_lower.split())):
                    filtered_products.append(product)
            
            print(f"✅ Filtered to {len(filtered_products)} products")
            return filtered_products[:10]  # Return top 10 matches
            
        except Exception as e:
            print(f"❌ Error searching products: {e}")
            return []

# Initialize Wix client
wix_client = WixAPIClient(WIX_BASE_URL)

# Define the new arrivals tool
@tool
def get_new_arrivals_tool(query: str = "") -> str:
    """Get the latest new arrivals from the store. Use this when customers ask about new arrivals, latest products, or what's new."""
    try:
        print(f"🛍️ Tool called: get_new_arrivals_tool with query: '{query}'")
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

@tool
def search_products_tool(query: str) -> str:
    """Search for products in the store. Use this when customers ask about finding specific products, colors, or types of items."""
    try:
        print(f"🔍 Tool called: search_products_tool with query: '{query}'")
        
        # Determine category from query
        query_lower = query.lower()
        category = None
        
        if any(word in query_lower for word in ["men", "male", "guys", "mens", "men's"]):
            category = "men"
        elif any(word in query_lower for word in ["women", "female", "ladies", "womens", "women's"]):
            category = "women"
        
        products = wix_client.search_products(query, category)
        
        if not products:
            return f"I couldn't find any products matching '{query}'. Try searching for:\n• New arrivals\n• Men's clothing\n• Women's clothing\n• Or ask me about our latest products!"
        
        result = f"🔍 **Found {len(products)} products for '{query}':**\n\n"
        
        for i, product in enumerate(products, 1):
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
        
        return result
        
    except Exception as e:
        print(f"❌ Error in search_products_tool: {e}")
        return f"I encountered an error while searching for '{query}'. Please try again."

# List of available tools
tools = [get_new_arrivals_tool, search_products_tool]

# Create the customer service agent
def create_customer_service_agent():
    """Create a customer service agent using LangChain components"""
    
    system_prompt = """You are a helpful customer service assistant for an online clothing store.

Your role is to:
1. Help customers find products they're looking for
2. Show new arrivals and featured products
3. Search for specific items customers want
4. Provide friendly and helpful customer service

You have access to these tools:
- get_new_arrivals_tool: Get the latest new arrivals from the store
- search_products_tool: Search for specific products by name, type, or keywords

Guidelines:
- Be friendly, helpful, and professional
- Use get_new_arrivals_tool when customers ask about "new arrivals", "latest products", "what's new", or similar
- Use search_products_tool when customers ask about specific products, colors, or types
- If you can't find specific information, apologize and suggest alternatives
- Keep responses concise but informative
- Always encourage customers to visit the website for more details

Common phrases that should trigger new arrivals:
- "new arrivals"
- "what's new"
- "latest products"
- "show me new items"
- "recent additions"

When customers greet you, be friendly and offer to help them find products or see new arrivals."""

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

def process_message_with_tools(message: str) -> str:
    """Process message and decide which tools to use"""
    message_lower = message.lower()
    print(f"🤔 Processing message: '{message}'")
    
    # Check for new arrivals requests
    if any(phrase in message_lower for phrase in [
        "new arrivals", "new arrival", "what's new", "whats new", 
        "latest", "recent", "newest", "show me new", "new items",
        "new products", "fresh", "just added"
    ]):
        print("🆕 Detected new arrivals request")
        return get_new_arrivals_tool.invoke({"query": message})
    
    # Check for product search requests
    elif any(word in message_lower for word in [
        "find", "search", "have", "show", "looking for", "want", 
        "shirt", "dress", "jeans", "shoes", "blue", "red", "black", 
        "white", "men", "women", "clothing", "product"
    ]):
        print("🔍 Detected product search request")
        return search_products_tool.invoke({"query": message})
    
    # For general messages, use the AI agent
    else:
        try:
            print("🤖 Using AI agent for general response")
            response = agent_chain.invoke({"input": message})
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"❌ Error with agent: {e}")
            return "I'm here to help! You can ask me about new arrivals, search for specific products, or browse our categories."

# API Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint"""
    try:
        print(f"\n💬 Received message: {message.message}")
        
        # Process the message with tools and AI
        response_text = process_message_with_tools(message.message)
        
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
    return {"message": "AI Customer Service Bot is running!", "status": "healthy"}

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

@app.post("/test-chat")
async def test_chat_endpoint():
    """Test chat functionality"""
    test_messages = [
        "Hello!",
        "Show me new arrivals",
        "Do you have any blue shirts?",
        "What's new in the store?"
    ]
    
    results = []
    for msg in test_messages:
        try:
            response = process_message_with_tools(msg)
            results.append({
                "message": msg,
                "response": response[:200] + "..." if len(response) > 200 else response,
                "success": True
            })
        except Exception as e:
            results.append({
                "message": msg,
                "response": str(e),
                "success": False
            })
    
    return {"test_results": results}

if __name__ == "__main__":
    print(f"\n🚀 Starting AI Customer Service Bot...")
    print(f"📡 Wix URL: {WIX_BASE_URL}")
    print(f"🔑 Groq API Key: {'✅ Set' if GROQ_API_KEY else '❌ Missing'}")
    print(f"🌐 Chat interface will be available at: http://localhost:8000")
    print(f"🔧 Health check at: http://localhost:8000/health")
    print(f"🧪 Test endpoints at: http://localhost:8000/test-wix")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)