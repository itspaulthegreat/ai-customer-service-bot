# Remove all the old tool files and create a simple function-based approach

# src/tools/ai_functions.py
"""
AI-driven functions for the customer service agent
No pattern matching, no regex, just clean functions that the LLM calls
"""
from typing import Dict, List, Any, Optional
import json

class AIFunctions:
    """Collection of functions that the AI agent can call"""
    
    def __init__(self, wix_client, llm):
        self.wix_client = wix_client
        self.llm = llm
    
    async def get_new_arrivals(self, limit: int = 8) -> Dict[str, Any]:
        """Fetch new arrivals from the store"""
        try:
            print(f"🆕 Fetching {limit} new arrivals")
            products = await self.wix_client.get_new_arrivals(limit)
            
            return {
                "success": True,
                "products": products,
                "count": len(products),
                "message": f"Found {len(products)} new arrivals"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Could not fetch new arrivals"
            }
    
    async def get_mens_products(self, limit: int = 8) -> Dict[str, Any]:
        """Fetch men's products from the store"""
        try:
            print(f"👔 Fetching {limit} men's products")
            products = await self.wix_client.get_mens_products(limit)
            
            return {
                "success": True,
                "products": products,
                "count": len(products),
                "category": "men's",
                "message": f"Found {len(products)} men's products"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Could not fetch men's products"
            }
    
    async def get_womens_products(self, limit: int = 8) -> Dict[str, Any]:
        """Fetch women's products from the store"""
        try:
            print(f"👗 Fetching {limit} women's products")
            products = await self.wix_client.get_womens_products(limit)
            
            return {
                "success": True,
                "products": products,
                "count": len(products),
                "category": "women's",
                "message": f"Found {len(products)} women's products"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Could not fetch women's products"
            }
    
    async def search_products(self, query: str, limit: int = 8) -> Dict[str, Any]:
        """Search for products using a query"""
        try:
            print(f"🔍 Searching products: '{query}'")
            products = await self.wix_client.search_products(query, limit)
            
            return {
                "success": True,
                "products": products,
                "count": len(products),
                "search_query": query,
                "message": f"Found {len(products)} products matching '{query}'"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "search_query": query,
                "message": f"Could not search for '{query}'"
            }
    
    async def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check the status of an order using AI-extracted order ID"""
        try:
            print(f"📦 Checking order status: {order_id}")
            
            # Get order items/details
            order_result = await self.wix_client.get_order_items(order_id)
            
            if order_result.get("success"):
                return {
                    "success": True,
                    "order_id": order_id,
                    "order_data": order_result,
                    "items": order_result.get("items", []),
                    "total_items": order_result.get("totalItems", 0),
                    "message": f"Retrieved status for order {order_id}"
                }
            else:
                return {
                    "success": False,
                    "order_id": order_id,
                    "error": order_result.get("error", "Order not found"),
                    "message": f"Could not find order {order_id}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "order_id": order_id,
                "error": str(e),
                "message": f"Error checking order {order_id}"
            }
    
    async def get_general_info(self, topic: str = "") -> Dict[str, Any]:
        """Get general store information using AI"""
        try:
            # Use LLM to generate contextual help
            from langchain_core.prompts import ChatPromptTemplate
            
            info_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a knowledgeable customer service representative. 
                Provide helpful, accurate information about:
                - Store policies (shipping, returns, exchanges)
                - How to shop and find products
                - New arrivals and product categories
                - Contact information and support
                - General shopping guidance
                
                Be friendly and informative. Use appropriate emojis."""),
                ("human", "Customer is asking about: {topic}")
            ])
            
            chain = info_prompt | self.llm
            result = chain.invoke({"topic": topic or "general help"})
            
            return {
                "success": True,
                "topic": topic,
                "response": result.content if hasattr(result, 'content') else str(result),
                "message": "Generated helpful information"
            }
            
        except Exception as e:
            return {
                "success": False,
                "topic": topic,
                "error": str(e),
                "response": "I'm here to help! I can show you our new arrivals, assist with orders, and answer questions about our store. What would you like to know?",
                "message": "Used fallback response"
            }


# Simplified agent with AI function calling
# src/bot/simple_agent.py
"""
Simplified AI agent that uses LLM for everything
"""
import asyncio
import json
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.tools.ai_functions import AIFunctions

class SimpleAIAgent:
    """AI-first customer service agent"""
    
    def __init__(self, groq_api_key: str, wix_client):
        # Initialize LLM
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1000,
            groq_api_key=groq_api_key
        )
        
        # Initialize AI functions
        self.functions = AIFunctions(wix_client, self.llm)
        
        # Create the decision chain
        self.decision_chain = self._create_decision_chain()
        self.response_chain = self._create_response_chain()
        
        print("✅ Simple AI Agent initialized")
    
    def _create_decision_chain(self):
        """Create LLM chain to decide what to do"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI that analyzes customer messages and decides what action to take.

Available actions:
- get_new_arrivals: Show latest/new products (limit: number)
- get_mens_products: Show men's products (limit: number)  
- get_womens_products: Show women's products (limit: number)
- search_products: Search for specific items (query: string, limit: number)
- check_order_status: Check order status (order_id: string)
- get_general_info: Provide general help/info (topic: string)

Analyze the message and respond with JSON:
{
    "action": "function_name",
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    },
    "confidence": 0.95,
    "reasoning": "Why this action was chosen"
}

For order status, extract order IDs intelligently:
- "Check order 12345" -> order_id: "12345"
- "Status of #ABC123" -> order_id: "ABC123"  
- "Where is my order_XYZ789" -> order_id: "order_XYZ789"

For product searches, extract relevant terms:
- "Blue shirts" -> query: "blue shirts"
- "Nike sneakers" -> query: "Nike sneakers"
- "Red dress under $100" -> query: "red dress"

Always set reasonable limits (default 8 for products)."""),
            ("human", "Customer message: {message}")
        ])
        
        return prompt | self.llm | JsonOutputParser()
    
    def _create_response_chain(self):
        """Create LLM chain to generate customer responses"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly customer service representative.
            
Create natural, helpful responses based on the function results.
- Use appropriate emojis
- Format product data nicely (name, price, availability, links)
- Explain order status clearly with next steps
- Be conversational and engaging
- Always offer to help further

For products: Show them in an attractive list with details
For orders: Explain status and what it means
For errors: Be apologetic and suggest alternatives"""),
            ("human", """Customer asked: {original_message}

Action taken: {action}
Function result: {result}

Generate a helpful response.""")
        ])
        
        return prompt | self.llm
    
    async def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process customer message with AI"""
        try:
            print(f"🤖 Processing: {message}")
            
            # Step 1: AI decides what to do
            decision = await asyncio.to_thread(
                self.decision_chain.invoke,
                {"message": message}
            )
            
            print(f"🧠 Decision: {decision}")
            
            action = decision.get("action", "get_general_info")
            parameters = decision.get("parameters", {})
            confidence = decision.get("confidence", 0.8)
            
            # Step 2: Execute the function
            function_result = await self._execute_function(action, parameters)
            
            # Step 3: Generate natural response
            response_text = await self._generate_response(message, action, function_result)
            
            return {
                "response": response_text,
                "confidence": confidence,
                "action_taken": action,
                "success": function_result.get("success", True)
            }
            
        except Exception as e:
            print(f"❌ Error in AI agent: {e}")
            return {
                "response": "I apologize, but I'm having some technical difficulties. Please try again or contact our customer service team for immediate assistance.",
                "confidence": 0.3,
                "action_taken": "error",
                "success": False
            }
    
    async def _execute_function(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate function"""
        try:
            if action == "get_new_arrivals":
                return await self.functions.get_new_arrivals(
                    limit=parameters.get("limit", 8)
                )
            elif action == "get_mens_products":
                return await self.functions.get_mens_products(
                    limit=parameters.get("limit", 8)
                )
            elif action == "get_womens_products":
                return await self.functions.get_womens_products(
                    limit=parameters.get("limit", 8)
                )
            elif action == "search_products":
                return await self.functions.search_products(
                    query=parameters.get("query", ""),
                    limit=parameters.get("limit", 8)
                )
            elif action == "check_order_status":
                return await self.functions.check_order_status(
                    order_id=parameters.get("order_id", "")
                )
            elif action == "get_general_info":
                return await self.functions.get_general_info(
                    topic=parameters.get("topic", "")
                )
            else:
                return await self.functions.get_general_info(topic="help")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": action,
                "parameters": parameters
            }
    
    async def _generate_response(self, original_message: str, action: str, result: Dict) -> str:
        """Generate natural response using LLM"""
        try:
            response = await asyncio.to_thread(
                self.response_chain.invoke,
                {
                    "original_message": original_message,
                    "action": action,
                    "result": json.dumps(result, indent=2)
                }
            )
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            
            # Fallback response generation
            if result.get("success"):
                if "products" in result:
                    products = result.get("products", [])
                    if products:
                        response = f"🛍️ I found {len(products)} products for you:\n\n"
                        for i, product in enumerate(products[:5], 1):
                            name = product.get("name", "Product")
                            price = product.get("formattedPrice", "Price not available")
                            response += f"{i}. **{name}** - {price}\n"
                        response += "\nWould you like to see more details or have other questions?"
                        return response
                    else:
                        return "I couldn't find any products matching your request. Would you like to try a different search or see our new arrivals?"
                
                elif "order_data" in result:
                    order_id = result.get("order_id", "")
                    items_count = result.get("total_items", 0)
                    return f"📦 I found your order {order_id} with {items_count} items. The order details are available. Would you like me to explain the status of specific items?"
                
                else:
                    return result.get("response", "I'm here to help! What would you like to know about our store or products?")
            else:
                error_msg = result.get("error", "")
                if "order" in action.lower() and "not found" in error_msg.lower():
                    return "I couldn't find that order. Please double-check your order ID and try again, or contact customer service for assistance."
                else:
                    return "I encountered an issue processing your request. Please try again or let me know how else I can help!"
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return hasattr(self, 'llm') and hasattr(self, 'functions')


# Updated main.py integration
"""
Replace the agent initialization in main.py with:

from src.bot.simple_agent import SimpleAIAgent

# Initialize the simple AI agent
try:
    agent = SimpleAIAgent(GROQ_API_KEY, wix_client)
    print("✅ Simple AI agent system initialized successfully")
    use_ai_system = True
    
except Exception as e:
    print(f"⚠️  Error loading AI system: {e}")
    print("📦 Falling back to legacy system...")
    use_ai_system = False

# Then in the chat endpoint:
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        print(f"\n💬 Received message: {message.message}")
        
        if use_ai_system:
            # Use the AI agent - no pattern matching, pure AI
            result = await agent.process_message(message.message, message.user_id)
            
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
        return ChatResponse(
            response="I apologize for the technical difficulty. Please try again or contact our customer service team.",
            confidence=0.1
        )
"""