# src/bot/pure_ai_agent.py
import asyncio
import json
import re
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from .session_memory import session_memory

class PureAIAgent:
    """Pure AI-driven customer service agent with session memory"""
    
    def __init__(self, groq_api_key: str, wix_client):
        self.wix_client = wix_client
        self.memory = session_memory
        
        # Initialize LLM
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
        
        # Create AI chains
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
6. "general_help" - General questions, greetings, store policies, support
7. "remember_context" - Customer is asking about previous messages or conversation context

For each message, respond with JSON only using this format:
{{
    "action": "action_name",
    "parameters": {{
        "key": "value"
    }},
    "confidence": 0.95,
    "reasoning": "Brief explanation"
}}

Context awareness examples:
- "What was my previous message?" → action: "remember_context", parameters: {{"type": "previous_user_message"}}
- "What did you just tell me?" → action: "remember_context", parameters: {{"type": "previous_bot_message"}}
- "What were we talking about?" → action: "remember_context", parameters: {{"type": "conversation_summary"}}
- "What order IDs did I give you?" or "List all order IDs I mentioned" → action: "remember_context", parameters: {{"type": "order_id_history", "filter": "order_ids"}}
- "What products did I ask about?" → action: "remember_context", parameters: {{"type": "entity_history", "filter": "product_queries"}}

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
    """AI response generator optimized for multi-item orders, memory requests, and new arrivals"""
    
    system_prompt = """You are a customer service representative for an online clothing store.

CRITICAL: Multi-item orders and product lists are NORMAL and EXPECTED!

When handling requests, follow these guidelines based on the result type:

1. **Order Status Requests (type = "order_status")**:
   - **Check Success First**: Look at the "was_successful" field.
   - **If SUCCESS = TRUE**:
     - The order WAS FOUND successfully.
     - Multiple items in one order are normal.
     - Each item can have different sizes, colors, and shipping statuses.
     - Respond positively and helpfully.
     - For Multi-Item Orders (totalItems > 1):
       - Congratulate them: "Great news! I found your order [order_id] with [total_items] items! 🛍️"
       - List items clearly with names, sizes, and status from items_list.
       - Group by status if multiple statuses exist in all_status.
       - Example: "Your order includes:\n• Item 1 (Size M) - Pending\n• Item 2 (Size L) - Shipped"
     - For Single-Item Orders (totalItems = 1):
       - Provide detailed info: "I found your order [order_id] with 1 item! Your '[item_name] (Size [size])' is [status]."
   - **If SUCCESS = FALSE**:
     - Say the order wasn't found.
     - Handle specific errors:
       - "MISSING_USER_ID": Prompt user to log in.
       - "UNAUTHORIZED": Suggest checking account or order ID.
       - "NOT_FOUND": Suggest verifying order ID.
     - Example: "I'm sorry, I couldn't find order [order_id]. Please double-check the ID."

2. **New Arrivals Requests (type = "new_arrivals")**:
   - **If SUCCESS = TRUE**:
     - List the products from items_list (up to 5 for brevity).
     - Include product name and price for each item.
     - Format as a bulleted list for clarity.
     - Be enthusiastic: "Check out our latest arrivals! 🛍️"
     - Example: "Here are our newest arrivals:\n• [Product Name 1] - $[Price 1]\n• [Product Name 2] - $[Price 2]"
     - If more than 5 products, add: "There are more new arrivals! Want to see the full list?"
   - **If SUCCESS = FALSE**:
     - Inform the user no new arrivals were found.
     - Suggest alternatives: "No new arrivals right now. Want to see men's or women's products?"

3. **Memory Requests (type = "memory_response")**:
   - If request_type = "order_id_history":
     - List all order IDs from memory_content as a bulleted list.
     - Example: "You mentioned these order IDs:\n• order_ABC123\n• cod_XYZ789"
     - If memory_content is a string, use it directly.
   - If request_type = "previous_user_message":
     - Return the last user message: "Your last message was: [message]"
   - If request_type = "previous_bot_message":
     - Return the last bot message: "I last said: [message]"
   - If request_type = "conversation_summary":
     - Summarize the conversation: "We've been talking about [summary]."

4. **Other Product Requests (type = "mens_products", "womens_products", "search_results")**:
   - **If SUCCESS = TRUE**:
     - List products from items_list (up to 5).
     - Include name and price.
     - Example: "Here are some [result_type]:\n• [Product Name 1] - $[Price 1]\n• [Product Name 2] - $[Price 2]"
   - **If SUCCESS = FALSE**:
     - Suggest alternatives: "No products found for [result_type]. Try searching for something else!"

Be conversational, positive, and helpful. Use emojis appropriately (e.g., 🛍️ for products, 🔐 for auth issues). Ensure responses are clear and concise. If items_list is provided, always include it in the response when relevant."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """
Customer asked: {original_message}

SUCCESS STATUS: {was_successful}

Action Taken: {action_taken}

Result Details:
- Type: {result_type}
- Order ID (if applicable): {order_id}
- Total Items (if applicable): {total_items}
- All Items Status (if applicable): {all_status}
- Items List (if applicable): {items_list}
- Error (if applicable): {error}
- Memory Content (if applicable): {memory_content}

Generate a response based on the information above.""")
    ])
    
    return prompt | self.llm
    
    async def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process customer message using pure AI intelligence with memory"""
        try:
            print(f"🤖 Pure AI processing: {message} (user_id: {user_id})")
            
            # Add user message to memory
            if user_id:
                self.memory.add_message(user_id, message, 'user')
            
            # Get conversation context
            conversation_context = self.memory.get_conversation_context(user_id) if user_id else "This is the start of the conversation."
            
            # Step 1: AI analyzes intent and extracts parameters with context
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
            
            # Pass user_id to action execution
            if user_id:
                parameters["user_id"] = user_id
            
            # Step 2: Execute the appropriate action
            action_result = await self._execute_action(action, parameters)
            
            print(f"🔧 Action '{action}' executed: {action_result.get('success', False)}")
            
            # Log order check details
            if action == "check_order":
                print(f"📋 ORDER CHECK DETAILS:")
                print(f"   - Success: {action_result.get('success')}")
                print(f"   - Error: {action_result.get('error')}")
                print(f"   - Error Code: {action_result.get('error_code')}")
                print(f"   - Type: {action_result.get('type')}")
                print(f"   - Order ID: {action_result.get('order_id')}")
            
            # Step 3: AI generates natural customer response with context
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
            
            # Add bot response to memory
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
            
            # Even error handling uses AI
            return await self._handle_error_intelligently(message, str(e))
    
    async def _execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the determined action using Wix API"""
        try:
            user_id = params.get("user_id")
            
            # Handle memory/context actions
            if action == "remember_context":
                return await self._handle_memory_request(params, user_id)
            
            elif action == "show_new_arrivals":
                limit = params.get("limit", 8)
                products = await self.wix_client.get_new_arrivals(limit)
                return {
                    "success": True,
                    "type": "new_arrivals",
                    "products": products,
                    "count": len(products),
                    "limit_requested": limit
                }
            
            elif action == "show_mens_products":
                limit = params.get("limit", 8)
                products = await self.wix_client.get_mens_products(limit)
                return {
                    "success": True,
                    "type": "mens_products",
                    "products": products,
                    "count": len(products),
                    "category": "men's"
                }
            
            elif action == "show_womens_products":
                limit = params.get("limit", 8)
                products = await self.wix_client.get_womens_products(limit)
                return {
                    "success": True,
                    "type": "womens_products",
                    "products": products,
                    "count": len(products),
                    "category": "women's"
                }
            
            elif action == "search_products":
                query = params.get("query", "")
                limit = params.get("limit", 8)
                
                if not query:
                    return {
                        "success": False,
                        "error": "No search query provided",
                        "type": "search_error"
                    }
                
                products = await self.wix_client.search_products(query, limit)
                return {
                    "success": True,
                    "type": "search_results",
                    "products": products,
                    "count": len(products),
                    "search_query": query
                }
            
            elif action == "check_order":
                order_id = params.get("order_id", "")
                
                if not order_id:
                    return {
                        "success": False,
                        "error": "No order ID provided",
                        "type": "order_error",
                        "help_message": "Please provide your order ID to check status"
                    }
                
                if not user_id:
                    return {
                        "success": False,
                        "error": "User authentication required to check order status",
                        "type": "auth_error",
                        "help_message": "Please make sure you're logged in to check your order status"
                    }
                
                print(f"🔍 Checking order status for: {order_id} (user: {user_id})")
                order_info = await self.wix_client.get_order_items(order_id, user_id)
                
                print(f"📋 Raw API Response: {order_info}")
                
                if not order_info.get("success", False):
                    error_code = order_info.get("code", "UNKNOWN_ERROR")
                    error_message = order_info.get("error", "Unknown error occurred")
                    
                    print(f"❌ Order API failed: {error_code} - {error_message}")
                    
                    return {
                        "success": False,
                        "type": "order_error",
                        "order_id": order_id,
                        "error": error_message,
                        "error_code": error_code,
                        "is_unauthorized": error_code == "UNAUTHORIZED",
                        "is_not_found": error_code == "NOT_FOUND"
                    }
                
                print(f"✅ Order API succeeded for {order_id}")
                return {
                    "success": True,
                    "type": "order_status", 
                    "order_id": order_id,
                    "order_data": order_info,
                    "items": order_info.get("items", []),
                    "totalItems": order_info.get("totalItems", 0),
                    "itemsSummary": order_info.get("itemsSummary", []),
                    "statusGroups": order_info.get("statusGroups", {}),
                    "hasMultipleItems": order_info.get("hasMultipleItems", False),
                    "uniqueStatuses": order_info.get("uniqueStatuses", [])
                }
            
            elif action == "general_help":
                topic = params.get("topic", params.get("query", "general help"))
                help_response = await self._generate_contextual_help(topic)
                return help_response
            
            else:
                # Fallback to general help
                return await self._generate_contextual_help("general assistance")
                
        except Exception as e:
            print(f"❌ Error executing action '{action}': {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action,
                "type": "execution_error"
            }
    async def _handle_memory_request(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle requests about conversation history"""
        if not user_id:
            return {
                "success": False,
                "error": "Cannot access conversation history without user context",
                "type": "memory_error"
            }
        
        request_type = params.get("type", "conversation_summary")
        
        if request_type == "previous_user_message":
            last_message = self.memory.get_last_user_message(user_id)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "previous_user_message",
                "memory_content": last_message or "I don't see any previous messages from you in this conversation.",
                "found": last_message is not None
            }
        
        elif request_type == "previous_bot_message":
            last_bot_message = self.memory.get_last_bot_message(user_id)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "previous_bot_message",
                "memory_content": last_bot_message or "I haven't responded to anything yet in this conversation.",
                "found": last_bot_message is not None
            }
        
        elif request_type == "conversation_summary":
            history = self.memory.get_conversation_history(user_id, 10)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "conversation_summary",
                "memory_content": f"We've had {len(history)} messages in our conversation. You can ask about specific details, like orders or products, if you want to dive deeper!",
                "found": bool(history)
            }
        
        elif request_type == "order_id_history":
            # Extract order IDs from conversation history
            history = self.memory.get_conversation_history(user_id, 50)  # Increased limit to capture more messages
            order_ids = set()
            order_id_pattern = r'\b(order_\w+|cod_\w+)\b'  # Match order IDs like order_QgO4LkXqXu3RQs or cod_1753128467135_1soovmd4g
            
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
            # Handle other entity types (e.g., product queries)
            filter_type = params.get("filter", "unknown")
            history = self.memory.get_conversation_history(user_id, 50)
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
    
    async def _generate_natural_response(self, original_message: str, action_taken: str, function_result: Dict[str, Any], was_successful: bool, conversation_context: str) -> str:
        """Generate a natural language response based on action results"""
        try:
            result_type = function_result.get("type", "general")
            order_id = function_result.get("order_id", "")
            total_items = function_result.get("totalItems", 0)
            items_list = function_result.get("itemsSummary", [])
            all_status = ", ".join(function_result.get("uniqueStatuses", [])) if function_result.get("uniqueStatuses") else "Unknown"
            error = function_result.get("error", "")
            memory_content = function_result.get("memory_content", "")
            
            # Format items list for orders
            formatted_items = []
            if result_type == "order_status":
                for item in items_list:
                    options = item.get("options", {})
                    size = options.get("Size", "N/A")
                    formatted_items.append(f"{item.get('name', 'Unknown')} (Size {size}) - {item.get('shipmentStatus', 'Unknown')}")
            elif result_type in ["new_arrivals", "mens_products", "womens_products", "search_results"]:
                # Format products for new arrivals and other product types
                products = function_result.get("products", [])
                formatted_items = [f"{p.get('name', 'Unknown')} - ${p.get('price', 'N/A')}" for p in products]
            
            response = await asyncio.to_thread(
                self.response_generator.invoke,
                {
                    "original_message": original_message,
                    "was_successful": was_successful,
                    "action_taken": action_taken,
                    "result_type": result_type,
                    "order_id": order_id,
                    "total_items": total_items,
                    "items_list": formatted_items,
                    "all_status": all_status,
                    "error": error,
                    "memory_content": memory_content
                }
            )
            
            return response.content
        
        except Exception as e:
            print(f"❌ Error generating natural response: {str(e)}")
            return await self._create_fallback_response(
                action=action_taken,
                result=function_result,
                original_message=original_message
            )  
    async def _create_fallback_response(self, action: str, result: Dict[str, Any], original_message: str) -> str:
        """Create a fallback response when AI generation fails"""
        result_type = result.get("type", "general")
        
        if result_type == "order_status" and result.get("success", False):
            total_items = result.get("totalItems", 0)
            order_id = result.get("order_id", "")
            items_summary = result.get("itemsSummary", [])
            
            items_text = []
            for item in items_summary:
                options = item.get("options", {})
                size = options.get("Size", "N/A")
                items_text.append(f"• {item.get('name', 'Unknown')} (Size {size}) - {item.get('shipmentStatus', 'Unknown')}")
            
            items_str = "\n".join(items_text) if items_text else "No items found."
            if total_items > 1:
                return f"Great news! I found your order {order_id} with {total_items} items! 🛍️\n\nYour order includes:\n{items_str}\n\nAll items are currently being prepared. You'll receive tracking information once they ship. Anything else I can help with?"
            else:
                return f"🎉 I found your order {order_id} with 1 item! Your {items_text[0]}. You'll receive tracking information once it's shipped. Anything else I can help with?"
        
        elif result_type == "order_error":
            error_code = result.get("error_code", "")
            if error_code == "MISSING_USER_ID":
                return "🔐 Please make sure you're logged in to check your order status. Once logged in, I'll be happy to help you track your orders!"
            elif error_code == "UNAUTHORIZED":
                return "🔐 I'm sorry, but I couldn't find that order for your account. This could mean:\n• The order ID might be incorrect\n• The order belongs to a different account\n• You might need to log in first\nPlease double-check your order ID and make sure you're logged into the correct account."
            elif error_code == "NOT_FOUND":
                return f"🤔 I couldn't find order {result.get('order_id', 'unknown')}. Please double-check the order ID and try again. If you need help, let me know!"
            else:
                return f"😔 Sorry, I ran into an issue checking your order: {result.get('error', 'Unknown error')}. Please try again or contact support for assistance."
        
        elif result_type == "memory_response":
            request_type = result.get("request_type", "general")
            memory_content = result.get("memory_content", "")
            
            if request_type == "order_id_history":
                if isinstance(memory_content, list):
                    if memory_content:
                        return f"💭 You asked for the order IDs you've mentioned. Here they are:\n" + "\n".join([f"• {oid}" for oid in memory_content]) + "\nWould you like me to check the status of any of these orders?"
                    else:
                        return "💭 You haven't mentioned any order IDs in our conversation yet. If you share one, I can check its status for you!"
                else:
                    return memory_content  # Use string message directly
            elif request_type == "previous_user_message":
                return f"💭 Your last message was: {memory_content}" if result.get("found", False) else memory_content
            elif request_type == "previous_bot_message":
                return f"💭 I last said: {memory_content}" if result.get("found", False) else memory_content
            elif request_type == "conversation_summary":
                return memory_content
            else:
                return "💭 I remember our conversation and I'm here to help! What would you like to know?"
        
        elif result_type in ["new_arrivals", "mens_products", "womens_products", "search_results"]:
            products = result.get("products", [])
            if products:
                products_text = "\n".join([f"• {p.get('name', 'Unknown')} - ${p.get('price', 'N/A')}" for p in products[:5]])
                return f"Here are some {result_type.replace('_', ' ')}:\n{products_text}\nWould you like to see more details about any of these?"
            else:
                return f"Sorry, I couldn't find any {result_type.replace('_', ' ')}. Try a different search or ask for something else!"
        
        else:
            return "I'm here to help! Could you clarify what you're looking for, or would you like to see our latest products?"
    
    async def _generate_contextual_help(self, topic: str) -> Dict[str, Any]:
        """Generate help response based on topic"""
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
            "content": response
        }
    
    async def _handle_error_intelligently(self, message: str, error: str) -> Dict[str, Any]:
        """Handle errors with AI-generated responses"""
        error_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a customer service bot. An error occurred: {error}. Respond politely and helpfully, suggesting next steps."),
            ("human", "Customer message: {message}")
        ])
        
        try:
            response = await asyncio.to_thread(
                error_prompt | self.llm,
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