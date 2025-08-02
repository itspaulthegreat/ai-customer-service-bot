"""
AI-Driven Customer Service Agent - Complete Refactor
This removes all regex/pattern matching and uses LLM for everything
"""

# src/bot/agent.py
import asyncio
import json
from typing import Dict, List, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config.settings import Settings

class CustomerServiceAgent:
    """AI-driven customer service agent that uses LLM for all decision making"""
    
    def __init__(self, groq_api_key: str, wix_client):
        self.settings = Settings()
        self.wix_client = wix_client
        
        # Initialize LLM
        try:
            self.llm = ChatGroq(
                model_name=self.settings.LLM_MODEL,
                temperature=self.settings.LLM_TEMPERATURE,
                max_tokens=self.settings.LLM_MAX_TOKENS,
                groq_api_key=groq_api_key
            )
            print("✅ Groq LLM initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Groq: {e}")
            raise
        
        # Available tools/functions
        self.available_functions = {
            "get_new_arrivals": self._get_new_arrivals,
            "get_mens_products": self._get_mens_products,
            "get_womens_products": self._get_womens_products,
            "search_products": self._search_products,
            "get_order_status": self._get_order_status,
            "get_order_items": self._get_order_items,
            "provide_general_support": self._provide_general_support
        }
        
        # Create the main agent
        self.intent_classifier = self._create_intent_classifier()
        self.response_generator = self._create_response_generator()
        
        print("✅ AI-driven customer service agent initialized")
    
    def _create_intent_classifier(self):
        """Create LLM chain for intent classification and parameter extraction"""
        
        system_prompt = """You are an AI assistant that analyzes customer messages to determine intent and extract relevant parameters.

Available functions and when to use them:
- get_new_arrivals: When customers ask about new arrivals, latest products, what's new, fresh items, just added items
- get_mens_products: When specifically asking for men's/male products, men's clothing, men's new arrivals
- get_womens_products: When specifically asking for women's/female products, women's clothing, women's new arrivals  
- search_products: When looking for specific products, brands, categories, or searching with keywords
- get_order_status: When asking about order status, tracking, shipment status, delivery updates, "where is my order"
- get_order_items: When asking about what items are in an order, order contents, order details
- provide_general_support: For greetings, general questions, store info, policies, shipping info, returns, contact info

Analyze the user message and respond with JSON containing:
{
    "intent": "function_name",
    "confidence": 0.0-1.0,
    "parameters": {
        "key": "value"
    },
    "reasoning": "Brief explanation of why this intent was chosen"
}

For order-related queries, extract order IDs from natural language:
- "Check my order #12345" -> order_id: "12345"  
- "Status of order ABC123" -> order_id: "ABC123"
- "Where is order_QsItdDdq8jJJMT" -> order_id: "order_QsItdDdq8jJJMT"
- "Track order #order_ABC123XYZ" -> order_id: "order_ABC123XYZ"

For product searches, extract search terms:
- "Show me blue shirts" -> query: "blue shirts"
- "Do you have Nike shoes?" -> query: "Nike shoes"
- "Red dresses under $50" -> query: "red dresses", price_filter: "under 50"

Always extract the most relevant parameters from the natural language."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Analyze this customer message: {message}")
        ])
        
        parser = JsonOutputParser()
        return prompt | self.llm | parser
    
    def _create_response_generator(self):
        """Create LLM chain for generating customer responses"""
        
        system_prompt = """You are a friendly, helpful customer service representative for an online clothing store.

Guidelines:
- Be warm, professional, and conversational
- Use appropriate emojis to make responses engaging
- Keep responses concise but informative
- If you have product data, format it nicely with prices, availability, and links
- For order status, explain clearly what the status means and next steps
- For errors, be apologetic and offer alternatives
- Always end with an offer to help further

When formatting product lists:
- Use bullet points or numbered lists
- Include product name, price, and availability
- Add direct links when available
- Highlight any sales or special offers

When handling order status:
- Clearly explain what each status means
- Provide expected timeframes when possible
- Offer next steps or contact info if needed

Response format should be natural conversation, not JSON."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """Generate a customer service response based on:

Customer message: {original_message}
Function used: {function_name}
Function result: {function_result}
Success: {success}

Create a natural, helpful response.""")
        ])
        
        return prompt | self.llm
    
    async def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process customer message using AI for everything"""
        try:
            print(f"🤖 AI Agent processing: {message}")
            
            # Step 1: Use LLM to classify intent and extract parameters
            intent_analysis = await self._analyze_intent(message)
            print(f"🧠 Intent Analysis: {intent_analysis}")
            
            function_name = intent_analysis.get("intent")
            parameters = intent_analysis.get("parameters", {})
            confidence = intent_analysis.get("confidence", 0.8)
            
            # Step 2: Execute the appropriate function
            if function_name in self.available_functions:
                function_result = await self.available_functions[function_name](**parameters)
                success = function_result.get("success", True)
            else:
                # Fallback to general support
                function_result = await self._provide_general_support(query=message)
                function_name = "provide_general_support"
                success = True
            
            print(f"🔧 Function {function_name} result: {success}")
            
            # Step 3: Use LLM to generate natural response
            response_text = await self._generate_response(
                original_message=message,
                function_name=function_name,
                function_result=function_result,
                success=success
            )
            
            return {
                "response": response_text,
                "confidence": confidence,
                "intent": function_name,
                "success": success
            }
            
        except Exception as e:
            print(f"❌ Error in AI agent: {e}")
            import traceback
            traceback.print_exc()
            
            # Use LLM for error response too
            error_response = await self._generate_error_response(message, str(e))
            return {
                "response": error_response,
                "confidence": 0.3,
                "intent": "error",
                "success": False
            }
    
    async def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Use LLM to analyze customer intent"""
        try:
            result = await asyncio.to_thread(
                self.intent_classifier.invoke,
                {"message": message}
            )
            return result
        except Exception as e:
            print(f"❌ Error in intent analysis: {e}")
            # Fallback
            return {
                "intent": "provide_general_support",
                "confidence": 0.5,
                "parameters": {"query": message},
                "reasoning": "Fallback due to analysis error"
            }
    
    async def _generate_response(self, original_message: str, function_name: str, function_result: Dict, success: bool) -> str:
        """Use LLM to generate natural customer response"""
        try:
            result = await asyncio.to_thread(
                self.response_generator.invoke,
                {
                    "original_message": original_message,
                    "function_name": function_name,
                    "function_result": json.dumps(function_result, indent=2),
                    "success": success
                }
            )
            return result.content if hasattr(result, 'content') else str(result)
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return "I'm here to help! Could you please try rephrasing your question?"
    
    async def _generate_error_response(self, original_message: str, error: str) -> str:
        """Generate error response using LLM"""
        error_prompt = ChatPromptTemplate.from_messages([
            ("system", "Generate a friendly, apologetic customer service response for when there's a technical error. Be helpful and suggest alternatives."),
            ("human", "Customer asked: {message}\nError occurred: {error}\nGenerate a helpful response.")
        ])
        
        try:
            chain = error_prompt | self.llm
            result = await asyncio.to_thread(
                chain.invoke,
                {"message": original_message, "error": error}
            )
            return result.content if hasattr(result, 'content') else str(result)
        except:
            return "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment or contact our customer service team for immediate assistance."
    
    # ============== FUNCTION IMPLEMENTATIONS ==============
    
    async def _get_new_arrivals(self, limit: int = 8, **kwargs) -> Dict[str, Any]:
        """Get new arrivals from Wix"""
        try:
            products = await self.wix_client.get_new_arrivals(limit)
            return {
                "success": True,
                "function": "get_new_arrivals",
                "data": {
                    "products": products,
                    "count": len(products),
                    "store_url": self.wix_client.base_url
                }
            }
        except Exception as e:
            return {
                "success": False,
                "function": "get_new_arrivals", 
                "error": str(e)
            }
    
    async def _get_mens_products(self, limit: int = 8, **kwargs) -> Dict[str, Any]:
        """Get men's products from Wix"""
        try:
            products = await self.wix_client.get_mens_products(limit)
            return {
                "success": True,
                "function": "get_mens_products",
                "data": {
                    "products": products,
                    "count": len(products),
                    "category": "men",
                    "store_url": self.wix_client.base_url
                }
            }
        except Exception as e:
            return {
                "success": False,
                "function": "get_mens_products",
                "error": str(e)
            }
    
    async def _get_womens_products(self, limit: int = 8, **kwargs) -> Dict[str, Any]:
        """Get women's products from Wix"""
        try:
            products = await self.wix_client.get_womens_products(limit)
            return {
                "success": True,
                "function": "get_womens_products",
                "data": {
                    "products": products,
                    "count": len(products),
                    "category": "women",
                    "store_url": self.wix_client.base_url
                }
            }
        except Exception as e:
            return {
                "success": False,
                "function": "get_womens_products",
                "error": str(e)
            }
    
    async def _search_products(self, query: str, limit: int = 8, **kwargs) -> Dict[str, Any]:
        """Search products in Wix"""
        try:
            products = await self.wix_client.search_products(query, limit)
            return {
                "success": True,
                "function": "search_products",
                "data": {
                    "products": products,
                    "count": len(products),
                    "search_query": query,
                    "store_url": self.wix_client.base_url
                }
            }
        except Exception as e:
            return {
                "success": False,
                "function": "search_products",
                "error": str(e),
                "search_query": query
            }
    
    async def _get_order_status(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Get order status - AI extracted order ID"""
        try:
            print(f"🔍 AI extracted order ID: {order_id}")
            
            # Try to get order items (main order data)
            order_result = await self.wix_client.get_order_items(order_id)
            
            if order_result.get("success"):
                return {
                    "success": True,
                    "function": "get_order_status",
                    "data": {
                        "order_id": order_id,
                        "order_info": order_result,
                        "items_count": order_result.get("totalItems", 0)
                    }
                }
            else:
                return {
                    "success": False,
                    "function": "get_order_status",
                    "error": order_result.get("error", "Order not found"),
                    "order_id": order_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "function": "get_order_status",
                "error": str(e),
                "order_id": order_id
            }
    
    async def _get_order_items(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed order items"""
        return await self._get_order_status(order_id, **kwargs)
    
    async def _provide_general_support(self, query: str = "", **kwargs) -> Dict[str, Any]:
        """Provide general customer support"""
        try:
            # Use LLM to generate contextual support response
            support_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful customer service representative. Provide helpful information about:
                - Store policies (shipping, returns, exchanges)
                - How to find products and new arrivals
                - General shopping guidance
                - Contact information and store hours
                - Size guides and product information
                
                Be concise but helpful. Include relevant emojis."""),
                ("human", "Customer query: {query}")
            ])
            
            support_chain = support_prompt | self.llm
            result = await asyncio.to_thread(
                support_chain.invoke,
                {"query": query}
            )
            
            response_text = result.content if hasattr(result, 'content') else str(result)
            
            return {
                "success": True,
                "function": "provide_general_support",
                "data": {
                    "response": response_text,
                    "query": query
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "function": "provide_general_support",
                "error": str(e),
                "data": {
                    "response": "I'm here to help! I can show you our new arrivals, help with order questions, and provide store information. What would you like to know?",
                    "query": query
                }
            }
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        try:
            return (
                hasattr(self, 'llm') and self.llm is not None and
                hasattr(self, 'wix_client') and self.wix_client is not None and
                hasattr(self, 'available_functions') and self.available_functions
            )
        except:
            return False
