# src/bot/simple_ai_agent.py - SIMPLIFIED & CLEAN
import asyncio
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class SimpleAIAgent:
    """Simplified AI agent with unified response handling"""
    
    def __init__(self, groq_api_key: str, wix_client):
        self.wix_client = wix_client
        
        # Initialize LLM
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1200,
            groq_api_key=groq_api_key
        )
        
        # Create AI chains
        self.intent_analyzer = self._create_intent_analyzer()
        self.response_generator = self._create_response_generator()
        
        print("✅ Simple AI Agent initialized!")
    
    def _create_intent_analyzer(self):
        """AI that understands what the customer wants"""
        
        system_prompt = """You are an AI that analyzes customer messages for an online store.

Determine what the customer wants and extract key information.

Available actions:
- "show_new_arrivals" - Show latest products
- "show_mens_products" - Show men's items  
- "show_womens_products" - Show women's items
- "search_products" - Search for specific items
- "check_order" - Check order status
- "general_help" - General questions or support

Extract parameters like:
- order_id: Extract from messages like "check order ABC123"
- query: Search terms like "red shoes" 
- limit: Number of items to show (default 8)

Respond with JSON only:
{{
    "action": "action_name",
    "parameters": {{"key": "value"}},
    "confidence": 0.95
}}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Customer message: {message}")
        ])
        
        return prompt | self.llm | JsonOutputParser()
    
    def _create_response_generator(self):
        """AI that creates natural customer responses"""
        
        system_prompt = """You are a helpful customer service representative.

Create natural, friendly responses based on the results you receive.

Guidelines:
- If success=True: Be positive and helpful
- If success=False: Be apologetic and offer alternatives
- For order status: Clearly explain what was found
- For products: List items with names and prices
- For errors: Suggest what the customer can do next

Be conversational and use emojis appropriately."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Customer asked: {original_message}

Action taken: {action}
Success: {success}
Result: {result}

Create a helpful response.""")
        ])
        
        return prompt | self.llm
    
    async def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process customer message - main entry point"""
        try:
            print(f"🤖 Processing: {message} (user: {user_id})")
            
            # Step 1: Understand what customer wants
            intent_result = await asyncio.to_thread(
                self.intent_analyzer.invoke,
                {"message": message}
            )
            
            action = intent_result.get("action", "general_help")
            parameters = intent_result.get("parameters", {})
            confidence = intent_result.get("confidence", 0.8)
            
            print(f"🧠 Intent: {action} with params: {parameters}")
            
            # Step 2: Execute the action
            if user_id:
                parameters["user_id"] = user_id
            
            result = await self._execute_action(action, parameters)
            
            # Step 3: Generate natural response
            response_text = await self._generate_response(message, action, result)
            
            return {
                "response": response_text,
                "confidence": confidence,
                "action": action,
                "success": result.get("success", True)
            }
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            return {
                "response": "I'm sorry, I encountered an error. Please try again or contact support.",
                "confidence": 0.5,
                "action": "error",
                "success": False
            }
    
    async def _execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the determined action"""
        user_id = params.get("user_id")
        
        try:
            if action == "show_new_arrivals":
                limit = params.get("limit", 8)
                return await self.wix_client.get_new_arrivals(limit)
            
            elif action == "show_mens_products":
                limit = params.get("limit", 8)
                return await self.wix_client.get_mens_products(limit)
            
            elif action == "show_womens_products":
                limit = params.get("limit", 8)
                return await self.wix_client.get_womens_products(limit)
            
            elif action == "search_products":
                query = params.get("query", "")
                limit = params.get("limit", 8)
                
                if not query:
                    return {
                        "success": False,
                        "code": "MISSING_QUERY",
                        "message": "Please tell me what you're looking for"
                    }
                
                return await self.wix_client.search_products(query, limit)
            
            elif action == "check_order":
                order_id = params.get("order_id", "")
                
                if not order_id:
                    return {
                        "success": False,
                        "code": "MISSING_ORDER_ID",
                        "message": "Please provide your order ID"
                    }
                
                if not user_id:
                    return {
                        "success": False,
                        "code": "MISSING_USER_ID",
                        "message": "Please make sure you're logged in to check your order"
                    }
                
                return await self.wix_client.get_order_items(order_id, user_id)
            
            elif action == "general_help":
                return {
                    "success": True,
                    "code": "SUCCESS",
                    "message": "I'm here to help with shopping, orders, and store questions!"
                }
            
            else:
                return {
                    "success": False,
                    "code": "UNKNOWN_ACTION",
                    "message": f"I'm not sure how to handle: {action}"
                }
                
        except Exception as e:
            print(f"❌ Error executing {action}: {e}")
            return {
                "success": False,
                "code": "EXECUTION_ERROR",
                "message": str(e)
            }
    
    async def _generate_response(self, original_message: str, action: str, result: Dict[str, Any]) -> str:
        """Generate natural response using AI"""
        try:
            response = await asyncio.to_thread(
                self.response_generator.invoke,
                {
                    "original_message": original_message,
                    "action": action,
                    "success": result.get("success", True),
                    "result": str(result)[:500]  # Truncate for AI context
                }
            )
            
            return response.content
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            
            # Fallback response generation
            if result.get("success", True):
                return self._create_success_fallback(action, result)
            else:
                return self._create_error_fallback(action, result)
    
    def _create_success_fallback(self, action: str, result: Dict[str, Any]) -> str:
        """Create fallback success response"""
        if action == "show_new_arrivals":
            count = result.get("data", {}).get("count", 0)
            return f"🆕 Here are {count} new arrivals from our latest collection!"
        
        elif action in ["show_mens_products", "show_womens_products"]:
            count = result.get("data", {}).get("count", 0)
            category = "men's" if "mens" in action else "women's"
            return f"👔 Here are {count} {category} products for you!"
        
        elif action == "search_products":
            count = result.get("data", {}).get("count", 0)
            return f"🔍 I found {count} products matching your search!"
        
        elif action == "check_order":
            order_id = result.get("data", {}).get("orderId", "your order")
            item_count = result.get("data", {}).get("itemCount", 0)
            return f"📦 Great! I found {order_id} with {item_count} item(s)!"
        
        else:
            return "✅ Here's what I found for you!"
    
    def _create_error_fallback(self, action: str, result: Dict[str, Any]) -> str:
        """Create fallback error response"""
        code = result.get("code", "ERROR")
        message = result.get("message", "Something went wrong")
        
        if code == "UNAUTHORIZED":
            return "🔐 I couldn't access that order. Please make sure you're logged in and the order ID is correct."
        
        elif code == "NOT_FOUND":
            return "❌ I couldn't find what you're looking for. Please double-check and try again."
        
        elif code == "MISSING_USER_ID":
            return "👤 Please make sure you're logged in to access your order information."
        
        elif code == "MISSING_ORDER_ID":
            return "📝 Please provide your order ID so I can check the status for you."
        
        else:
            return f"😔 Sorry, {message}. Please try again or contact support if you need help."
    
    def is_healthy(self) -> bool:
        """Check if agent is working properly"""
        try:
            return self.llm is not None and self.wix_client is not None
        except:
            return False