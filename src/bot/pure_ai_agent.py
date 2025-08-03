# src/bot/pure_ai_agent.py - ENHANCED VERSION WITH NEW ORDER CAPABILITIES
import asyncio
import json
import re
from typing import Dict, Any, Optional, List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from .session_memory import session_memory

class PureAIAgent:
    """Enhanced Pure AI-driven customer service agent with advanced order management"""
    
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
            print("✅ Enhanced Pure AI Agent LLM initialized")
        except Exception as e:
            print(f"❌ Error initializing LLM in Pure AI Agent: {e}")
            raise
        
        # Create AI chains
        self.intent_analyzer = self._create_intent_analyzer()
        self.response_generator = self._create_response_generator()
        
        print("✅ Enhanced Pure AI Agent initialized with ADVANCED ORDER MANAGEMENT!")
    
    def _create_intent_analyzer(self):
        """Enhanced AI that understands customer intent including advanced order queries"""
        
        system_prompt = """You are an AI assistant that analyzes customer messages for an online clothing store.

You have access to conversation history and can handle complex order-related queries.

Available actions you can recommend:
1. "show_new_arrivals" - Customer wants to see new/latest products
2. "show_mens_products" - Customer specifically wants men's items
3. "show_womens_products" - Customer specifically wants women's items
4. "search_products" - Customer is looking for specific items with search terms
5. "check_order" - Customer wants status for a single specific order
6. "check_multiple_orders" - Customer wants status for multiple specific orders
7. "get_last_orders" - Customer wants their most recent orders (last 1-20)
8. "get_recent_orders" - Customer wants orders from recent time period (days/weeks)
9. "get_orders_by_status" - Customer wants orders filtered by status
10. "get_order_stats" - Customer wants statistics about their order history
11. "general_help" - General questions, greetings, store policies, support
12. "remember_context" - Customer is asking about previous messages or conversation context

For each message, respond with JSON only using this format:
{{
    "action": "action_name",
    "parameters": {{
        "key": "value"
    }},
    "confidence": 0.95,
    "reasoning": "Brief explanation"
}}

Enhanced Order Query Examples:

**Single Order Status:**
- "Check my order ABC123" → action: "check_order", parameters: {{"order_id": "ABC123"}}
- "Status of order_XYZ789" → action: "check_order", parameters: {{"order_id": "order_XYZ789"}}

**Multiple Order Status:**
- "Check orders ABC123, XYZ789, DEF456" → action: "check_multiple_orders", parameters: {{"order_ids": ["ABC123", "XYZ789", "DEF456"]}}
- "Status of my orders: order_123 and order_456" → action: "check_multiple_orders", parameters: {{"order_ids": ["order_123", "order_456"]}}

**Last Orders (Recent by Count):**
- "Show my last order" → action: "get_last_orders", parameters: {{"count": 1}}
- "My last 3 orders" → action: "get_last_orders", parameters: {{"count": 3}}
- "Show me my recent 5 purchases" → action: "get_last_orders", parameters: {{"count": 5}}

**Recent Orders (Time-based):**
- "Orders from last week" → action: "get_recent_orders", parameters: {{"days": 7}}
- "My orders from last month" → action: "get_recent_orders", parameters: {{"days": 30}}
- "Show orders from past 2 weeks" → action: "get_recent_orders", parameters: {{"days": 14}}

**Orders by Status:**
- "Show my pending orders" → action: "get_orders_by_status", parameters: {{"status": "pending"}}
- "My shipped orders" → action: "get_orders_by_status", parameters: {{"status": "shipped"}}
- "Cancelled orders" → action: "get_orders_by_status", parameters: {{"status": "cancelled"}}

**Order Statistics:**
- "How much have I spent?" → action: "get_order_stats", parameters: {{}}
- "My order history summary" → action: "get_order_stats", parameters: {{}}
- "Show my shopping statistics" → action: "get_order_stats", parameters: {{}}

**Context and Memory:**
- "What order IDs did I mention?" → action: "remember_context", parameters: {{"type": "order_id_history"}}
- "What was my last message?" → action: "remember_context", parameters: {{"type": "previous_user_message"}}

**General Help Without Specifics:**
- "Help with my orders" → action: "get_last_orders", parameters: {{"count": 6}}
- "I need help with an order" → action: "get_last_orders", parameters: {{"count": 3}}
- "Check my purchases" → action: "get_last_orders", parameters: {{"count": 5}}

**Complex Queries:**
- "Check my last 4 orders and see if any are shipped" → action: "get_last_orders", parameters: {{"count": 4}}
- "Orders I placed this week" → action: "get_recent_orders", parameters: {{"days": 7}}

Key Intelligence Guidelines:
- Extract multiple order IDs from text naturally (comma-separated, space-separated, etc.)
- Distinguish between "last N orders" (count-based) vs "recent orders" (time-based)
- Understand various status terms: pending, processing, shipped, delivered, cancelled, returned
- Default to reasonable limits: last_orders max 20, recent_orders max 365 days
- Handle context references using conversation history
- When user says "help with orders" without specifics, default to showing recent orders
- Be intelligent about understanding natural language variations

Conversation History Context:
{conversation_context}

Current Message: {message}

Analyze this customer message considering the conversation context above."""

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
        """Enhanced AI response generator for all order types"""
        
        system_prompt = """You are a customer service representative for an online clothing store.

Handle different types of responses based on the result type:

**1. Single Order Status (type = "order_status")**:
- If SUCCESS = TRUE: "Great! I found your order [order_id] with [total_items] items. [List items with status]"
- If SUCCESS = FALSE: "Sorry, I couldn't find order [order_id]. [Helpful error message based on error code]"

**2. Multiple Order Status (type = "multiple_order_status")**:
- If SUCCESS = TRUE: "I checked [requested_count] orders. [successful_count] found, [failed_count] not found."
- List successful orders with status
- List failed orders with reasons
- Example: "✅ order_123: Shipped (2 items)\n❌ order_456: Not found"

**3. Last Orders (type = "last_orders")**:
- If SUCCESS = TRUE: "Here are your last [count] orders:" + list with dates and status
- Example: "Your last 3 orders:\n• Order ABC123 - Jan 15 - Delivered\n• Order XYZ789 - Jan 10 - Shipped"

**4. Recent Orders (type = "recent_orders")**:
- If SUCCESS = TRUE: "You have [total_orders] orders from the last [days] days:" + list
- If no orders: "No orders found in the last [days] days."

**5. Orders by Status (type = "orders_by_status")**:
- If SUCCESS = TRUE: "You have [total_orders] [status] orders:" + list
- If no orders: "You don't have any [status] orders."

**6. Order Statistics (type = "order_statistics")**:
- If SUCCESS = TRUE: Show summary stats like total orders, total spent, average order value, status breakdown
- Example: "📊 Your order history:\n• Total orders: 15\n• Total spent: $450\n• Average order: $30"

**7. New Arrivals/Products (type = "new_arrivals", "mens_products", etc.)**:
- List products with names and prices (max 5 for readability)
- Be enthusiastic about new items

**8. Memory Responses (type = "memory_response")**:
- Return requested information from conversation history
- Be helpful and direct

**General Guidelines:**:
- Use emojis appropriately (🛍️ 📦 ✅ ❌ 📊)
- Be conversational and helpful
- For multi-item responses, use clear formatting (bullet points, numbering)
- Always provide context about what you're showing
- If there are errors, be helpful and suggest next steps
- Keep responses concise but informative
- When showing multiple orders, include key info: Order ID, Date, Status, Total (if available)

Response Format Examples:
- "✅ Order ABC123 (Jan 15) - Delivered - $45.99"
- "📦 Order XYZ789 (Jan 10) - Shipped - 3 items"
- "⏳ Order DEF456 (Jan 08) - Processing - $123.50"

Data Available:
- Order ID: {order_id}
- Order IDs: {order_ids}
- Total Items: {total_items}
- Success Status: {was_successful}
- Orders List: {orders_list}
- Statistics: {statistics}
- Error: {error}
- Context: {context}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Customer asked: {original_message}

SUCCESS STATUS: {was_successful}

Action Taken: {action_taken}

Result Details:
- Type: {result_type}
- Order ID: {order_id}
- Order IDs: {order_ids}
- Total Items: {total_items}
- Orders List: {orders_list}
- Statistics: {statistics}
- Error: {error}
- Context: {context}
- Memory Content: {memory_content}

Generate a response based on the information above.""")
        ])
        
        return prompt | self.llm
    
    async def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process customer message using enhanced AI intelligence"""
        try:
            print(f"🤖 Enhanced AI processing: {message} (user_id: {user_id})")
            
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
            
            print(f"🧠 Enhanced AI Intent Analysis: {intent_result}")
            
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
            
            # Step 3: Generate natural customer response
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
            print(f"❌ Error in Enhanced Pure AI Agent: {e}")
            import traceback
            traceback.print_exc()
            
            return await self._handle_error_intelligently(message, str(e))
    
    async def _execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the determined action using enhanced Wix API"""
        try:
            user_id = params.get("user_id")
            
            # Handle memory/context actions
            if action == "remember_context":
                return await self._handle_memory_request(params, user_id)
            
            # Product actions (unchanged)
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
            
            # Single order check (existing)
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
                
                print(f"🔍 Checking single order: {order_id} (user: {user_id})")
                order_info = await self.wix_client.get_order_items(order_id, user_id)
                
                if not order_info.get("success", False):
                    error_code = order_info.get("code", "UNKNOWN_ERROR")
                    error_message = order_info.get("error", "Unknown error occurred")
                    
                    return {
                        "success": False,
                        "type": "order_error",
                        "order_id": order_id,
                        "error": error_message,
                        "error_code": error_code
                    }
                
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
            
            # NEW: Multiple order check
            elif action == "check_multiple_orders":
                order_ids = params.get("order_ids", [])
                
                if not order_ids or len(order_ids) == 0:
                    return {
                        "success": False,
                        "error": "No order IDs provided",
                        "type": "order_error",
                        "help_message": "Please provide order IDs to check status"
                    }
                
                if not user_id:
                    return {
                        "success": False,
                        "error": "User authentication required",
                        "type": "auth_error"
                    }
                
                print(f"🔍 Checking multiple orders: {order_ids} (user: {user_id})")
                result = await self.wix_client.get_multiple_order_status(order_ids, user_id)
                
                if not result.get("success", False):
                    return {
                        "success": False,
                        "type": "multiple_order_error",
                        "error": result.get("error", "Failed to check multiple orders"),
                        "order_ids": order_ids
                    }
                
                return {
                    "success": True,
                    "type": "multiple_order_status",
                    "order_ids": order_ids,
                    "requested_count": result.get("requestedOrders", 0),
                    "successful_count": result.get("successfulOrders", 0),
                    "failed_count": result.get("failedOrders", 0),
                    "successful": result.get("successful", []),
                    "failed": result.get("failed", []),
                    "summary": result.get("summary", {})
                }
            
            # NEW: Get last N orders
            elif action == "get_last_orders":
                count = params.get("count", 1)
                
                if not user_id:
                    return {
                        "success": False,
                        "error": "User authentication required",
                        "type": "auth_error"
                    }
                
                print(f"🔍 Getting last {count} orders (user: {user_id})")
                result = await self.wix_client.get_last_orders(user_id, count)
                
                if not result.get("success", False):
                    return {
                        "success": False,
                        "type": "last_orders_error",
                        "error": result.get("error", "Failed to get last orders"),
                        "count": count
                    }
                
                return {
                    "success": True,
                    "type": "last_orders",
                    "orders": result.get("orders", []),
                    "requested_count": count,
                    "actual_count": result.get("actualCount", 0),
                    "context": result.get("context", "")
                }
            
            # NEW: Get recent orders (time-based)
            elif action == "get_recent_orders":
                days = params.get("days", 30)
                
                if not user_id:
                    return {
                        "success": False,
                        "error": "User authentication required",
                        "type": "auth_error"
                    }
                
                print(f"🔍 Getting recent orders (last {days} days, user: {user_id})")
                result = await self.wix_client.get_recent_orders(user_id, days)
                
                if not result.get("success", False):
                    return {
                        "success": False,
                        "type": "recent_orders_error",
                        "error": result.get("error", "Failed to get recent orders"),
                        "days": days
                    }
                
                return {
                    "success": True,
                    "type": "recent_orders",
                    "orders": result.get("orders", []),
                    "total_orders": result.get("totalOrders", 0),
                    "date_range": result.get("dateRange", {}),
                    "days": days
                }
            
            # NEW: Get orders by status
            elif action == "get_orders_by_status":
                status = params.get("status", "")
                limit = params.get("limit", 10)
                
                if not status:
                    return {
                        "success": False,
                        "error": "No status provided",
                        "type": "parameter_error"
                    }
                
                if not user_id:
                    return {
                        "success": False,
                        "error": "User authentication required",
                        "type": "auth_error"
                    }
                
                print(f"🔍 Getting orders by status: {status} (user: {user_id})")
                result = await self.wix_client.get_orders_by_status(user_id, status, limit)
                
                if not result.get("success", False):
                    return {
                        "success": False,
                        "type": "orders_by_status_error",
                        "error": result.get("error", "Failed to get orders by status"),
                        "status": status
                    }
                
                return {
                    "success": True,
                    "type": "orders_by_status",
                    "orders": result.get("orders", []),
                    "total_orders": result.get("totalOrders", 0),
                    "filter_status": status
                }
            
            # NEW: Get order statistics
            elif action == "get_order_stats":
                if not user_id:
                    return {
                        "success": False,
                        "error": "User authentication required",
                        "type": "auth_error"
                    }
                
                print(f"📊 Getting order statistics (user: {user_id})")
                result = await self.wix_client.get_user_order_stats(user_id)
                
                if not result.get("success", False):
                    return {
                        "success": False,
                        "type": "order_stats_error",
                        "error": result.get("error", "Failed to get order statistics")
                    }
                
                return {
                    "success": True,
                    "type": "order_statistics",
                    "statistics": result.get("statistics", {}),
                    "context": result.get("context", "")
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
        """Handle requests about conversation history (unchanged)"""
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
            history = self.memory.get_conversation_history(user_id, 50)
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
        
        else:
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "general",
                "memory_content": "I remember our conversation and I'm here to help! What would you like to know?"
            }
    
    async def _generate_natural_response(self, original_message: str, action_taken: str, function_result: Dict[str, Any], was_successful: bool, conversation_context: str) -> str:
        """Generate enhanced natural language response for all order types"""
        try:
            result_type = function_result.get("type", "general")
            
            # Prepare data for response generation
            order_id = function_result.get("order_id", "")
            order_ids = function_result.get("order_ids", [])
            total_items = function_result.get("totalItems", 0)
            error = function_result.get("error", "")
            memory_content = function_result.get("memory_content", "")
            context = function_result.get("context", "")
            statistics = function_result.get("statistics", {})
            
            # Format orders list for different result types
            orders_list = []
            
            if result_type == "order_status":
                # Single order items
                items_summary = function_result.get("itemsSummary", [])
                for item in items_summary:
                    options = item.get("options", {})
                    size = options.get("Size", "N/A")
                    orders_list.append(f"{item.get('name', 'Unknown')} (Size {size}) - {item.get('shipmentStatus', 'Unknown')}")
            
            elif result_type == "multiple_order_status":
                # Multiple order results
                successful = function_result.get("successful", [])
                failed = function_result.get("failed", [])
                
                for order in successful:
                    orders_list.append(f"✅ {order.get('orderId', 'Unknown')} - {order.get('status', 'Unknown')} - ${order.get('total', 'N/A')}")
                
                for order in failed:
                    orders_list.append(f"❌ {order.get('orderId', 'Unknown')} - {order.get('error', 'Error')}")
            
            elif result_type in ["last_orders", "recent_orders", "orders_by_status"]:
                # Order lists
                orders = function_result.get("orders", [])
                for order in orders:
                    formatted_date = order.get("formattedDate", "Unknown date")
                    status = order.get("orderStatus", "Unknown")
                    total = order.get("total", 0)
                    orders_list.append(f"📦 {order.get('_id', 'Unknown')} - {formatted_date} - {status} - ${total}")
            
            elif result_type in ["new_arrivals", "mens_products", "womens_products", "search_results"]:
                # Product lists
                products = function_result.get("products", [])
                for product in products[:5]:  # Limit to 5 for readability
                    price = product.get("formattedPrice", product.get("price", "N/A"))
                    orders_list.append(f"🛍️ {product.get('name', 'Unknown')} - {price}")
            
            # Generate response using AI
            response = await asyncio.to_thread(
                self.response_generator.invoke,
                {
                    "original_message": original_message,
                    "was_successful": was_successful,
                    "action_taken": action_taken,
                    "result_type": result_type,
                    "order_id": order_id,
                    "order_ids": order_ids,
                    "total_items": total_items,
                    "orders_list": orders_list,
                    "statistics": statistics,
                    "error": error,
                    "context": context,
                    "memory_content": memory_content
                }
            )
            
            return response.content
        
        except Exception as e:
            print(f"❌ Error generating enhanced natural response: {str(e)}")
            return await self._create_fallback_response(
                action=action_taken,
                result=function_result,
                original_message=original_message
            )
    
    async def _create_fallback_response(self, action: str, result: Dict[str, Any], original_message: str) -> str:
        """Create fallback response when AI generation fails"""
        if not result.get("success", False):
            error = result.get("error", "Unknown error")
            return f"I encountered an issue: {error}. Please try again or contact support for assistance."
        
        # Success fallbacks based on action
        if action == "check_order":
            order_id = result.get("order_id", "your order")
            total_items = result.get("totalItems", 0)
            return f"✅ I found {order_id} with {total_items} item{'s' if total_items != 1 else ''}!"
        
        elif action == "check_multiple_orders":
            successful_count = result.get("successful_count", 0)
            failed_count = result.get("failed_count", 0)
            return f"I checked your orders: {successful_count} found, {failed_count} not found."
        
        elif action == "get_last_orders":
            count = result.get("actual_count", 0)
            return f"Here are your last {count} order{'s' if count != 1 else ''}!"
        
        elif action == "get_recent_orders":
            total_orders = result.get("total_orders", 0)
            days = result.get("days", 30)
            return f"You have {total_orders} order{'s' if total_orders != 1 else ''} from the last {days} days."
        
        elif action == "get_orders_by_status":
            total_orders = result.get("total_orders", 0)
            status = result.get("filter_status", "unknown")
            return f"You have {total_orders} {status} order{'s' if total_orders != 1 else ''}."
        
        elif action == "get_order_stats":
            stats = result.get("statistics", {})
            total_orders = stats.get("totalOrders", 0)
            total_spent = stats.get("totalSpent", 0)
            return f"📊 You have {total_orders} total orders and spent ${total_spent:.2f}."
        
        elif action in ["show_new_arrivals", "show_mens_products", "show_womens_products"]:
            count = result.get("count", 0)
            category = result.get("category", "products")
            return f"Here are {count} {category} for you!"
        
        else:
            return "I've processed your request! Is there anything else I can help you with?"
    
    async def _generate_contextual_help(self, topic: str) -> Dict[str, Any]:
        """Generate help response based on topic (unchanged)"""
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
        """Handle errors with AI-generated responses (unchanged)"""
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
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        try:
            return bool(self.llm and self.intent_analyzer and self.response_generator)
        except Exception:
            return False