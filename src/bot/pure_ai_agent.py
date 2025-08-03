# src/bot/pure_ai_agent.py - Updated with session memory

import asyncio
import json
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

Parameter extraction examples:
- Order queries: Extract order IDs naturally
  * "Check my order ABC123" → order_id: "ABC123"
  * "Status of #order_XYZ789" → order_id: "order_XYZ789"  
  * "Where is order_QsItdDdq8jJJMT" → order_id: "order_QsItdDdq8jJJMT"

- Product searches: Extract search terms and filters
  * "Red Nike shoes" → query: "red Nike shoes"
  * "Blue dresses under $50" → query: "blue dresses", price_filter: "under 50"
  * "Men's winter jackets" → query: "winter jackets", category: "mens"

- Quantity limits: Extract from natural language
  * "Show me 10 items" → limit: 10
  * "First 5 products" → limit: 5
  * Default to 8 if not specified

Be intelligent about understanding context and variations in language. Use conversation history to understand references."""

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
        """AI that generates natural customer service responses"""
        
        system_prompt = """You are a friendly, professional customer service representative for an online clothing store.

You have access to conversation history and should use it to provide contextual, personalized responses.

Create natural, engaging responses based on the function results provided and conversation context.

Guidelines:
- Be warm, conversational, and helpful
- Reference previous conversation naturally when relevant
- Use appropriate emojis to make responses engaging (but don't overdo it)
- Format product information attractively with prices and availability
- Explain order status clearly with next steps for customers
- For errors, be apologetic and suggest helpful alternatives
- Always end with an offer to help further

For memory/context questions:
- Answer directly about what was said before
- Be specific and helpful when referencing previous messages
- Show that you remember and understand the conversation flow

For product listings:
- Use clean formatting with bullet points or numbers
- Include product name, price, and stock status
- Add direct product links when available
- Highlight any sales or special offers with emphasis

For order status:
- Clearly explain what each status means in customer-friendly terms
- Provide expected timeframes when possible
- Offer next steps or contact information if needed
- Be reassuring and professional

For errors or issues:
- Acknowledge the problem apologetically
- Suggest practical alternatives or solutions
- Maintain a helpful and positive tone

Response should be natural conversation, not JSON or structured data."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Conversation History:
{conversation_context}

Customer originally asked: {original_message}
Action taken: {action_taken}
Function result: {function_result}
Success: {was_successful}

Generate a natural, helpful customer service response that considers the conversation history.""")
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
            
            # CRITICAL: Pass user_id to action execution
            if user_id:
                parameters["user_id"] = user_id
            
            # Step 2: Execute the appropriate action
            action_result = await self._execute_action(action, parameters)
            
            print(f"🔧 Action '{action}' executed: {action_result.get('success', False)}")
            
            # Step 3: AI generates natural customer response with context
            response_text = await self._generate_natural_response(
                original_message=message,
                action_taken=action,
                function_result=action_result,
                was_successful=action_result.get("success", True),
                conversation_context=conversation_context
            )
            
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
            user_id = params.get("user_id")  # Extract user_id from params
            
            # NEW: Handle memory/context actions
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
                
                return {
                    "success": order_info.get("success", False),
                    "type": "order_status",
                    "order_id": order_id,
                    "order_data": order_info,
                    "error": order_info.get("error") if not order_info.get("success") else None
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
    
    # NEW: Handle memory/context requests
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
                "content": last_message or "I don't see any previous messages from you in this conversation.",
                "found": last_message is not None
            }
        
        elif request_type == "previous_bot_message":
            last_bot_message = self.memory.get_last_bot_message(user_id)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "previous_bot_message",
                "content": last_bot_message or "I haven't responded to anything yet in this conversation.",
                "found": last_bot_message is not None
            }
        
        elif request_type == "conversation_summary":
            history = self.memory.get_conversation_history(user_id, 10)
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "conversation_summary",
                "history": history,
                "message_count": len(history)
            }
        
        else:
            return {
                "success": True,
                "type": "memory_response",
                "request_type": "general",
                "content": "I remember our conversation and I'm here to help! What would you like to know?"
            }
    
    async def _generate_natural_response(self, original_message: str, action_taken: str, function_result: Dict, was_successful: bool, conversation_context: str = "") -> str:
        """Use AI to generate natural customer service response with conversation context"""
        try:
            response = await asyncio.to_thread(
                self.response_generator.invoke,
                {
                    "original_message": original_message,
                    "action_taken": action_taken,
                    "function_result": json.dumps(function_result, indent=2),
                    "was_successful": was_successful,
                    "conversation_context": conversation_context
                }
            )
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"❌ Error generating natural response: {e}")
            # Fallback to structured response
            return await self._create_fallback_response(function_result, was_successful)
    
    async def _generate_contextual_help(self, topic: str) -> Dict[str, Any]:
        """Generate contextual help using AI"""
        help_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful customer service representative for an online clothing store.

Generate informative, friendly responses about our store and services.

Topics you can help with:
- New arrivals and latest fashion trends
- Store policies (shipping, returns, exchanges, sizing)
- How to browse and find products
- Order tracking and customer support
- General shopping guidance and store information
- Product categories and recommendations

Be warm, professional, and informative. Use appropriate emojis and provide actionable advice."""),
            ("human", "Customer needs help with: {topic}")
        ])
        
        try:
            chain = help_prompt | self.llm
            result = await asyncio.to_thread(
                chain.invoke,
                {"topic": topic or "general store information"}
            )
            
            help_text = result.content if hasattr(result, 'content') else str(result)
            
            return {
                "success": True,
                "type": "help_response",
                "response": help_text,
                "topic": topic
            }
            
        except Exception as e:
            print(f"❌ Error generating contextual help: {e}")
            return {
                "success": True,
                "type": "help_response",
                "response": "👋 I'm here to help! I can show you our new arrivals, assist with order questions, provide store information, and help you find what you're looking for. What would you like to know?",
                "topic": topic
            }
    
    async def _create_fallback_response(self, result: Dict, success: bool) -> str:
        """Create fallback response when AI generation fails"""
        # Handle memory responses specifically
        if result.get("type") == "memory_response":
            request_type = result.get("request_type")
            content = result.get("content")
            
            if request_type == "previous_user_message":
                if result.get("found"):
                    return f"💭 Your previous message was: \"{content}\""
                else:
                    return "🤔 I don't see any previous messages from you in our current conversation."
            
            elif request_type == "previous_bot_message":
                if result.get("found"):
                    return f"💬 I just told you: \"{content}\""
                else:
                    return "🤔 I haven't responded to anything yet in this conversation."
            
            elif request_type == "conversation_summary":
                message_count = result.get("message_count", 0)
                return f"💭 We've exchanged {message_count} messages so far in this conversation. I remember everything we've discussed!"
            
            else:
                return "💭 I remember our conversation and I'm here to help! What would you like to know?"
        
        # Handle other response types
        if success:
            result_type = result.get("type", "unknown")
            
            if result_type in ["new_arrivals", "mens_products", "womens_products", "search_results"]:
                count = result.get("count", 0)
                if count > 0:
                    return f"🛍️ Great! I found {count} products for you. Take a look and let me know if you need anything else!"
                else:
                    return "😔 I couldn't find any products matching your request right now. Would you like to try a different search or see our new arrivals instead?"
            
            elif result_type == "order_status":
                order_id = result.get("order_id", "")
                return f"📦 I found information about your order {order_id}. Let me know if you need more details or have other questions!"
            
            elif result_type == "help_response":
                return result.get("response", "I'm here to help! What can I assist you with today?")
            
            else:
                return "✅ I've processed your request! How else can I help you today?"
        
        else:
            error = result.get("error", "")
            result_type = result.get("type", "")
            
            if "order" in result_type or "order" in error.lower():
                return "❌ I couldn't find that order. Please double-check your order ID and make sure you're logged in, or contact our customer service team for assistance."
            elif "auth" in result_type:
                return "🔐 Please make sure you're logged in to check your order status. Once logged in, I'll be happy to help you track your orders!"
            elif "search" in result_type:
                return "🔍 I couldn't find products matching that search. Would you like to try different keywords or browse our new arrivals instead?"
            else:
                return "😔 I encountered an issue processing your request. Please try again or let me know how else I can help!"
    
    async def _handle_error_intelligently(self, message: str, error: str) -> Dict[str, Any]:
        """Use AI to handle errors gracefully"""
        error_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a customer service representative handling a technical error. Generate a helpful, apologetic response that maintains customer confidence and suggests alternatives. Be warm and professional."),
            ("human", "Customer asked: {message}\nTechnical error occurred: {error}\nGenerate a helpful response.")
        ])
        
        try:
            chain = error_prompt | self.llm
            result = await asyncio.to_thread(
                chain.invoke,
                {"message": message, "error": error}
            )
            
            response_text = result.content if hasattr(result, 'content') else str(result)
            
        except Exception:
            # Ultimate fallback
            response_text = "I apologize for the technical difficulty. Our team is working to resolve this. Please try again in a moment, or contact our customer service team for immediate assistance. I'm here to help in any way I can!"
        
        return {
            "response": response_text,
            "confidence": 0.3,
            "action": "error_handling",
            "success": False,
            "error": error
        }
    
    def is_healthy(self) -> bool:
        """Check if the Pure AI agent is working properly"""
        try:
            # Check if all components are initialized
            return (
                hasattr(self, 'llm') and self.llm is not None and
                hasattr(self, 'wix_client') and self.wix_client is not None and
                hasattr(self, 'intent_analyzer') and self.intent_analyzer is not None and
                hasattr(self, 'response_generator') and self.response_generator is not None and
                hasattr(self, 'memory') and self.memory is not None
            )
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False