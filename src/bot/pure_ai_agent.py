import asyncio
import json
import re
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from .session_memory import session_memory
from .response_formatter import ResponseFormatter

class ActionHandler:
    """Base class for action handlers"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        raise NotImplementedError

class ShowNewArrivalsHandler(ActionHandler):
    """Handler for showing new arrivals"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        limit = params.get("limit", 8)
        result = await wix_client.get_new_arrivals(limit)
        return {
            "success": result["success"],
            "type": "new_arrivals",
            "data": result["data"],
            "error": result["error"],
            "code": result["code"]
        }

class ShowMensProductsHandler(ActionHandler):
    """Handler for showing men's products"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        limit = params.get("limit", 8)
        result = await wix_client.get_mens_products(limit)
        return {
            "success": result["success"],
            "type": "mens_products",
            "data": result["data"],
            "error": result["error"],
            "code": result["code"]
        }

class ShowWomensProductsHandler(ActionHandler):
    """Handler for showing women's products"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        limit = params.get("limit", 8)
        result = await wix_client.get_womens_products(limit)
        return {
            "success": result["success"],
            "type": "womens_products",
            "data": result["data"],
            "error": result["error"],
            "code": result["code"]
        }

class SearchProductsHandler(ActionHandler):
    """Handler for searching products"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        query = params.get("query", "")
        limit = params.get("limit", 8)
        if not query:
            return {
                "success": False,
                "type": "search_error",
                "data": {},
                "error": "No search query provided",
                "code": "MISSING_QUERY"
            }
        result = await wix_client.search_products(query, limit)
        return {
            "success": result["success"],
            "type": "search_results",
            "data": result["data"],
            "error": result["error"],
            "code": result["code"]
        }

class CheckOrderHandler(ActionHandler):
    """Handler for checking order status"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        order_id = params.get("order_id", "")
        user_id = params.get("user_id")
        if not order_id:
            return {
                "success": False,
                "type": "order_error",
                "data": {},
                "error": "No order ID provided",
                "code": "MISSING_ORDER_ID",
                "help_message": "Please provide your order ID to check status"
            }
        if not user_id:
            return {
                "success": False,
                "type": "auth_error",
                "data": {},
                "error": "User authentication required to check order status",
                "code": "MISSING_USER_ID",
                "help_message": "Please make sure you're logged in to check your order status"
            }
        print(f"🔍 Checking order status for: {order_id} (user: {user_id})")
        result = await wix_client.get_order_items(order_id, user_id)
        return {
            "success": result["success"],
            "type": "order_status",
            "data": result["data"],
            "error": result["error"],
            "code": result["code"],
            "order_id": order_id,
            "is_unauthorized": result["code"] == "UNAUTHORIZED",
            "is_not_found": result["code"] == "NOT_FOUND"
        }

class GetUserOrdersHandler(ActionHandler):
    """Handler for fetching all user orders"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        user_id = params.get("user_id")
        limit = params.get("limit", 20)
        if not user_id:
            return {
                "success": False,
                "type": "auth_error",
                "data": {},
                "error": "User authentication required to view orders",
                "code": "MISSING_USER_ID"
            }
        result = await wix_client.get_user_orders(user_id, limit)
        return {
            "success": result["success"],
            "type": "user_orders",
            "data": result["data"],
            "error": result["error"],
            "code": result["code"]
        }

class MemoryRequestHandler(ActionHandler):
    """Handler for memory-related requests"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        user_id = params.get("user_id")
        if not user_id:
            return {
                "success": False,
                "type": "memory_error",
                "data": {},
                "error": "Cannot access conversation history without user context",
                "code": "MISSING_USER_ID"
            }
        
        request_type = params.get("type", "conversation_summary")
        
        if request_type == "previous_user_message":
            last_message = memory.get_last_user_message(user_id)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "previous_user_message",
                "memory_content": last_message or "I don't see any previous messages from you in this conversation.",
                "found": last_message is not None
            }
        
        elif request_type == "previous_bot_message":
            last_bot_message = memory.get_last_bot_message(user_id)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "previous_bot_message",
                "memory_content": last_bot_message or "I haven't responded to anything yet in this conversation.",
                "found": last_bot_message is not None
            }
        
        elif request_type == "conversation_summary":
            history = memory.get_conversation_history(user_id, 10)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "conversation_summary",
                "memory_content": f"We've had {len(history)} messages in our conversation. You can ask about specific details, like orders or products, if you want to dive deeper!",
                "found": bool(history)
            }
        
        elif request_type == "order_id_history":
            history = memory.get_conversation_history(user_id, 50)
            order_ids = set()
            order_id_pattern = r'\b(order_\w+|cod_\w+)\b'
            for message in history:
                if message.get("sender") == "user":
                    matches = re.findall(order_id_pattern, message.get("content", ""))
                    order_ids.update(matches)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "order_id_history",
                "memory_content": list(order_ids) if order_ids else "You haven't mentioned any order IDs in our conversation yet.",
                "found": bool(order_ids)
            }
        
        elif request_type == "entity_history":
            filter_type = params.get("filter", "unknown")
            history = memory.get_conversation_history(user_id, 50)
            entities = set()
            if filter_type == "product_queries":
                product_pattern = r'\b(search|find|show)\s+(.+?)(?:$|\s+(?:under|below|less than|more than))'
                for message in history:
                    if message.get("sender") == "user":
                        matches = re.findall(product_pattern, message.get("content", ""), re.IGNORECASE)
                        entities.update(match[1] for match in matches)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "entity_history",
                "memory_content": list(entities) if entities else f"You haven't mentioned any {filter_type.replace('_', ' ')} in our conversation yet.",
                "found": bool(entities)
            }
        
        else:
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "general",
                "memory_content": "I remember our conversation and I'm here to help! What would you like to know?"
            }

class GeneralHelpHandler(ActionHandler):
    """Handler for general help requests"""
    async def handle(self, params: Dict[str, Any], wix_client, memory) -> Dict[str, Any]:
        topic = params.get("topic", params.get("query", "general help"))
        help_topics = {
            "general help": "I'm here to assist with shopping, order tracking, or store policies! What do you need help with? You can ask about new arrivals, specific products, or check an order status.",
            "returns": "Our return policy allows returns within 30 days of delivery. Items must be unworn and in original condition. Want to start a return or need more details?",
            "shipping": "We offer standard and express shipping options. Standard shipping takes 5-7 business days. Need to check your order's shipping status or learn more?",
            "payment": "We accept all major credit cards, PayPal, and Apple Pay. Having trouble with a payment or need help with something specific?"
        }
        response = help_topics.get(topic.lower(), help_topics["general help"])
        return {
            "success": True,
            "type": "help_response",
            "data": {"content": response},
            "error": None,
            "code": None
        }

ACTION_REGISTRY = {
    "show_new_arrivals": ShowNewArrivalsHandler(),
    "show_mens_products": ShowMensProductsHandler(),
    "show_womens_products": ShowWomensProductsHandler(),
    "search_products": SearchProductsHandler(),
    "check_order": CheckOrderHandler(),
    "get_user_orders": GetUserOrdersHandler(),
    "remember_context": MemoryRequestHandler(),
    "general_help": GeneralHelpHandler()
}

class PureAIAgent:
    """Pure AI-driven customer service agent with session memory"""
    
    def __init__(self, groq_api_key: str, wix_client):
        self.wix_client = wix_client
        self.memory = session_memory
        try:
            self.llm = ChatGroq(
                model_name="gemma2-9b-it",
                temperature=0.1,
                max_tokens=1200,
                groq_api_key=groq_api_key
            )
            print("✅ Pure AI Agent LLM initialized")
        except Exception as e:
            print(f"❌ Error initializing LLM in Pure AI Agent: {e}")
            raise
        self.intent_analyzer = self._create_intent_analyzer()
        self.response_generator = self._create_response_generator()
        print("✅ Pure AI Agent initialized with SESSION MEMORY!")
    
    def _create_intent_analyzer(self):
        """AI that understands customer intent and extracts parameters"""
        system_prompt = """You are an AI assistant that analyzes customer messages for an online clothing store.

You have access to the conversation history to understand context and references to previous messages.

Your job is to understand what the customer wants and extract relevant information intelligently.

Available actions you can recommend:
1. "show_new_arrivals" - Customer wants to see new/latest products
2. "show_mens_products" - Customer specifically wants men's items
3. "show_womens_products" - Customer specifically wants women's items
4. "search_products" - Customer is looking for specific items with search terms
5. "check_order" - Customer wants order status/tracking information
6. "get_user_orders" - Customer wants to see all their orders
7. "general_help" - General questions, greetings, store policies, support
8. "remember_context" - Customer is asking about previous messages or conversation context

For each message, respond with JSON only using this format:
{
    "action": "action_name",
    "parameters": {
        "key": "value"
    },
    "confidence": 0.95,
    "reasoning": "Brief explanation"
}

Context awareness examples:
- "What was my previous message?" → action: "remember_context", parameters: {"type": "previous_user_message"}
- "What did you just tell me?" → action: "remember_context", parameters: {"type": "previous_bot_message"}
- "What were we talking about?" → action: "remember_context", parameters: {"type": "conversation_summary"}
- "What order IDs did I give you?" or "List all order IDs I mentioned" → action: "remember_context", parameters: {"type": "order_id_history", "filter": "order_ids"}
- "What products did I ask about?" → action: "remember_context", parameters: {"type": "entity_history", "filter": "product_queries"}
- "Show my orders" → action: "get_user_orders", parameters: {"limit": 20}

Parameter extraction examples:
- Order queries: Extract order IDs naturally
  * "Check my order ABC123" → order_id: "ABC123"
  * "Status of #order_XYZ789" → order_id: "order_XYZ789"  
  * "Where is order_QsItdDdq8jJJMT" → order_id: "order_QsItdDdq8jJJMT"
  * "cod_1753128467135_1soovmd4g status" → order_id: "cod_1753128467135_1soovmd4g"

- Product searches: Extract search terms and filters
  * "Red Nike shoes" → query: "red Nike shoes"
  * "Blue dresses under $50" → query: "blue dresses", price_filter: "under 50"
  * "Men's winter jackets" → query: "winter jackets", category: "mens"

- Quantity limits: Extract from natural language
  * "Show me 10 items" → limit: 10
  * "First 5 products" → limit: 5
  * Default to 8 if not specified

Be intelligent about understanding context and variations in language (e.g., "order IDs I gave you" = "order IDs I mentioned"). Use conversation history to understand references."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Conversation History:
{conversation_context}

Current Message: {message}

Analyze this customer message considering the conversation context above.""")
        ])
        return prompt | self.llm | JsonOutputParser()
    
    def _create_response_generator(self):
        """AI response generator for cases requiring natural language flexibility"""
        system_prompt = """You are a customer service representative for an online clothing store.
Be conversational, positive, and helpful. Use emojis appropriately (e.g., 🛍️ for products, 🔐 for auth issues).
If a formatted response is provided, use it directly. Otherwise, generate a natural response based on the result type and data."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Customer asked: {original_message}

SUCCESS STATUS: {was_successful}

Action Taken: {action_taken}

Result Details:
- Type: {result_type}
- Data: {data}
- Error: {error}
- Code: {code}

Formatted Response (if available): {formatted_response}

Generate a response based on the information above. If formatted_response is provided, use it directly.""")
        ])
        return prompt | self.llm
    
    async def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process customer message using pure AI intelligence with memory"""
        try:
            print(f"🤖 Pure AI processing: {message} (user_id: {user_id})")
            if user_id:
                self.memory.add_message(user_id, message, 'user')
            conversation_context = self.memory.get_conversation_context(user_id) if user_id else "This is the start of the conversation."
            intent_result = await asyncio.to_thread(
                self.intent_analyzer.invoke,
                {
                    "message": message,
                    "conversation_context": conversation_context
                }
            )
            print(f"🧠 AI Intent Analysis: {intent_result}")
            action = intent_result.get("action", "general_help")
            parameters = intent_result.get("parameters", {})
            confidence = intent_result.get("confidence", 0.8)
            reasoning = intent_result.get("reasoning", "")
            if user_id:
                parameters["user_id"] = user_id
            action_result = await self._execute_action(action, parameters)
            print(f"🔧 Action '{action}' executed: {action_result.get('success', False)}")
            if action == "check_order":
                print(f"📋 ORDER CHECK DETAILS:")
                print(f"   - Success: {action_result.get('success')}")
                print(f"   - Error: {action_result.get('error')}")
                print(f"   - Error Code: {action_result.get('code')}")
                print(f"   - Type: {action_result.get('type')}")
                print(f"   - Order ID: {action_result.get('order_id')}")
            was_successful = action_result.get("success", True)
            print(f"🤖 Telling AI that success = {was_successful}")
            response_text = await self._generate_natural_response(
                original_message=message,
                action_taken=action,
                function_result=action_result,
                was_successful=was_successful,
                conversation_context=conversation_context
            )
            print(f"💬 AI generated response (first 100 chars): {response_text[:100]}...")
            if user_id:
                self.memory.add_message(user_id, response_text, 'bot')
            return {
                "response": response_text,
                "confidence": confidence,
                "action": action,
                "success": action_result.get("success", True),
                "reasoning": reasoning
            }
        except Exception as e:
            print(f"❌ Error in Pure AI Agent: {e}")
            import traceback
            traceback.print_exc()
            return await self._handle_error_intelligently(message, str(e))
    
    async def _execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the determined action using the action registry"""
        handler = ACTION_REGISTRY.get(action)
        if handler:
            return await handler.handle(params, self.wix_client, self.memory)
        return await ACTION_REGISTRY["general_help"].handle(params, self.wix_client, self.memory)

    async def _generate_natural_response(self, original_message: str, action_taken: str, function_result: Dict[str, Any], was_successful: bool, conversation_context: str) -> str:
        """Generate a natural language response using ResponseFormatter"""
        try:
            result_type = function_result.get("type", "general")
            formatter_methods = {
                "new_arrivals": ResponseFormatter.format_new_arrivals,
                "mens_products": ResponseFormatter.format_mens_products,
                "womens_products": ResponseFormatter.format_womens_products,
                "search_results": ResponseFormatter.format_search_results,
                "order_status": ResponseFormatter.format_order_status,
                "user_orders": ResponseFormatter.format_user_orders,
                "memory_response": ResponseFormatter.format_memory_response,
                "help_response": ResponseFormatter.format_help_response
            }
            formatter = formatter_methods.get(result_type, ResponseFormatter.format_error)
            formatted_response = formatter(function_result)
            if result_type in formatter_methods:
                return formatted_response
            response = await asyncio.to_thread(
                self.response_generator.invoke,
                {
                    "original_message": original_message,
                    "was_successful": was_successful,
                    "action_taken": action_taken,
                    "result_type": result_type,
                    "data": function_result.get("data", {}),
                    "error": function_result.get("error", ""),
                    "code": function_result.get("code", ""),
                    "formatted_response": formatted_response
                }
            )
            return response.content
        except Exception as e:
            print(f"❌ Error generating natural response: {str(e)}")
            return ResponseFormatter.format_error(function_result, original_message)

    async def _handle_error_intelligently(self, message: str, error: str) -> Dict[str, Any]:
        """Handle errors with AI-generated responses"""
        error_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a customer service bot. An error occurred: {error}. Respond politely and helpfully, suggesting next steps."),
            ("human", "Customer message: {message}")
        ])
        try:
            response = await asyncio.to_thread(
                (error_prompt | self.llm).invoke,
                {
                    "error": error,
                    "message": message
                }
            )
            return {
                "response": response.content,
                "confidence": 0.8,
                "action": "error_handling",
                "success": False,
                "reasoning": f"Error occurred: {error}"
            }
        except Exception:
            return {
                "response": "😔 Something went wrong on my end. Please try again or contact support for assistance!",
                "confidence": 0.5,
                "action": "error_handling",
                "success": False,
                "reasoning": f"Error in error handling: {error}"
            }