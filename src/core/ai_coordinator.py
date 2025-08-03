# src/core/ai_coordinator.py
import asyncio
from typing import Dict, List, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

class AICoordinator:
    """Coordinates all AI operations with memory and specialized tools"""
    
    def __init__(self, groq_api_key: str, tools: Dict, memory_manager, response_formatter):
        self.tools = tools
        self.memory_manager = memory_manager
        self.response_formatter = response_formatter
        
        # Initialize LLM
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,  # Slightly higher for more natural responses
            max_tokens=1500,
            groq_api_key=groq_api_key
        )
        
        # Create AI chains
        self.intent_analyzer = self._create_intent_analyzer()
        self.tool_router = self._create_tool_router()
        self.response_generator = self._create_response_generator()
        self.context_analyzer = self._create_context_analyzer()
    
    def _create_intent_analyzer(self):
        """AI that understands intent with conversation context"""
        system_prompt = """You are an expert at understanding customer intent in conversational context.

You have access to conversation history and must consider follow-ups, references, and context.

Available tool categories:
- "product": Product search, new arrivals, categories, recommendations
- "order": Order status, tracking, order history, returns
- "general": Store policies, help, greetings, complaints, general questions

Output JSON with:
{
    "primary_intent": "category_name",
    "confidence": 0.95,
    "context_clues": ["what indicates this intent"],
    "follow_up": true/false,
    "references_previous": true/false,
    "emotional_tone": "positive/neutral/negative/frustrated",
    "urgency_level": "low/medium/high"
}

Examples:
- "What about returns?" (after talking about orders) → order intent, follow_up: true
- "I'm frustrated with my order ABC123" → order intent, emotional_tone: frustrated, urgency: high
- "That doesn't help at all!" → general intent, emotional_tone: negative, references_previous: true"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Current message: {current_message}

Recent conversation:
{conversation_context}

Analyze the intent considering the full context.""")
        ])
        
        return prompt | self.llm | JsonOutputParser()
    
    def _create_tool_router(self):
        """AI that decides which specific tool to use"""
        system_prompt = """You are an expert at routing customer requests to the right specialized tools.

Based on the intent analysis and conversation context, determine exactly which tool method to use.

Product Tools:
- get_new_arrivals: Latest products, new items, what's new
- get_mens_products: Men's/male items specifically
- get_womens_products: Women's/female items specifically  
- search_products: Specific product search with keywords
- get_product_details: Information about a specific product

Order Tools:
- get_order_status: Check order status by ID
- get_order_items: List all items in an order
- get_user_orders: List user's order history
- track_shipment: Tracking information
- handle_return_request: Return/exchange requests

General Tools:
- provide_store_info: Store hours, policies, contact info
- handle_complaint: Customer complaints and issues
- provide_help: General assistance and guidance
- handle_greeting: Welcome messages and greetings

Output JSON:
{
    "tool_category": "product/order/general",
    "tool_method": "specific_method_name", 
    "parameters": {"key": "value"},
    "reasoning": "why this tool",
    "expected_outcome": "what this should accomplish"
}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Intent Analysis: {intent_analysis}
Current Message: {current_message}
Conversation Context: {conversation_context}
User ID: {user_id}

Route to the appropriate tool.""")
        ])
        
        return prompt | self.llm | JsonOutputParser()
    
    def _create_response_generator(self):
        """AI that generates human-like responses with personality"""
        system_prompt = """You are Sarah, a friendly and professional customer service representative for an online clothing store.

Personality traits:
- Warm and conversational, like talking to a helpful friend
- Professional but not robotic
- Empathetic and understanding
- Patient with difficult customers
- Enthusiastic about helping find solutions
- Uses natural language and appropriate emojis

Response Guidelines:
- Always acknowledge the customer's message and context
- Reference previous conversation when relevant
- Be specific and helpful with product/order information
- Show empathy for problems or frustrations
- Offer additional help or suggestions
- Use natural transitions and conversational flow
- Match the customer's energy level appropriately

For product information:
- Present attractively with clear formatting
- Highlight key details like price, availability
- Suggest alternatives if needed
- Ask follow-up questions to help narrow choices

For order issues:
- Be reassuring and proactive
- Explain status clearly in customer-friendly terms
- Provide next steps or timelines
- Offer to escalate if needed

For complaints or problems:
- Acknowledge frustration with genuine empathy
- Take ownership of finding solutions
- Be proactive in offering help
- Follow up to ensure satisfaction

Never:
- Be robotic or templated
- Ignore conversation context
- Give generic responses to specific questions
- Dismiss customer concerns
- Use overly formal language"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Customer's Current Message: {current_message}

Conversation History:
{conversation_context}

Tool Results: {tool_results}

Intent Analysis: {intent_analysis}

Customer's Emotional Tone: {emotional_tone}

Generate a natural, helpful response as Sarah the customer service representative.""")
        ])
        
        return prompt | self.llm
    
    def _create_context_analyzer(self):
        """AI that analyzes and updates conversation context"""
        system_prompt = """You analyze conversations to extract and update important context.

Extract key information that should be remembered:
- Customer preferences (sizes, colors, styles)
- Previous orders or issues mentioned
- Specific needs or requirements
- Emotional state and satisfaction level
- Unresolved issues or follow-ups needed

Output JSON:
{
    "context_updates": {
        "customer_preferences": {},
        "order_references": [],
        "unresolved_issues": [],
        "emotional_state": "current_mood",
        "needs_follow_up": true/false
    },
    "conversation_summary": "brief summary of interaction"
}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Current message: {current_message}
Recent conversation: {conversation_context}
Tool results: {tool_results}

Extract important context to remember.""")
        ])
        
        return prompt | self.llm | JsonOutputParser()
    
    async def process_conversation(self, message: str, user_id: Optional[str], 
                                 session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a complete conversation turn"""
        try:
            # Get conversation context
            conversation_context = self.memory_manager.get_recent_context(session_id, 5)
            
            # Step 1: Analyze intent with context
            intent_analysis = await asyncio.to_thread(
                self.intent_analyzer.invoke,
                {
                    "current_message": message,
                    "conversation_context": conversation_context
                }
            )
            
            # Step 2: Route to appropriate tool
            tool_routing = await asyncio.to_thread(
                self.tool_router.invoke,
                {
                    "intent_analysis": json.dumps(intent_analysis),
                    "current_message": message,
                    "conversation_context": conversation_context,
                    "user_id": user_id or "anonymous"
                }
            )
            
            # Step 3: Execute tool
            tool_results = await self._execute_tool(tool_routing, user_id)
            
            # Step 4: Generate natural response
            response_text = await self._generate_natural_response(
                current_message=message,
                conversation_context=conversation_context,
                tool_results=tool_results,
                intent_analysis=intent_analysis
            )
            
            # Step 5: Update conversation context
            context_updates = await self._analyze_context(
                message, conversation_context, tool_results
            )
            
            # Store in memory
            tools_used = [f"{tool_routing.get('tool_category', 'unknown')}.{tool_routing.get('tool_method', 'unknown')}"]
            confidence = intent_analysis.get('confidence', 0.8)
            
            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                user_message=message,
                bot_response=response_text,
                tools_used=tools_used,
                confidence=confidence,
                context=context_updates.get('context_updates', {})
            )
            
            # Update session context
            if context_updates.get('context_updates'):
                self.memory_manager.update_session_context(session_id, context_updates['context_updates'])
            
            return {
                "response": response_text,
                "confidence": confidence,
                "tools_used": tools_used,
                "conversation_context": self.memory_manager.get_session_context(session_id),
                "suggested_actions": self._generate_suggested_actions(intent_analysis, tool_results)
            }
            
        except Exception as e:
            print(f"❌ Error in conversation processing: {e}")
            raise
    
    async def _execute_tool(self, tool_routing: Dict, user_id: Optional[str]) -> Dict[str, Any]:
        """Execute the routed tool"""
        try:
            tool_category = tool_routing.get('tool_category', 'general')
            tool_method = tool_routing.get('tool_method', 'provide_help')
            parameters = tool_routing.get('parameters', {})
            
            # Add user_id to parameters if available
            if user_id:
                parameters['user_id'] = user_id
            
            # Get the appropriate tool
            tool = self.tools.get(tool_category)
            if not tool:
                return {"error": f"Tool category '{tool_category}' not found", "success": False}
            
            # Execute the tool method
            if hasattr(tool, tool_method):
                method = getattr(tool, tool_method)
                result = await method(**parameters)
                return result
            else:
                return {"error": f"Method '{tool_method}' not found in {tool_category} tools", "success": False}
                
        except Exception as e:
            print(f"❌ Error executing tool: {e}")
            return {"error": str(e), "success": False}
    
    async def _generate_natural_response(self, current_message: str, conversation_context: str, 
                                       tool_results: Dict, intent_analysis: Dict) -> str:
        """Generate natural, human-like response"""
        try:
            response = await asyncio.to_thread(
                self.response_generator.invoke,
                {
                    "current_message": current_message,
                    "conversation_context": conversation_context,
                    "tool_results": json.dumps(tool_results, indent=2),
                    "intent_analysis": json.dumps(intent_analysis, indent=2),
                    "emotional_tone": intent_analysis.get('emotional_tone', 'neutral')
                }
            )
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return self._create_fallback_response(tool_results, current_message)
    
    async def _analyze_context(self, message: str, conversation_context: str, tool_results: Dict) -> Dict:
        """Analyze and extract conversation context"""
        try:
            context_analysis = await asyncio.to_thread(
                self.context_analyzer.invoke,
                {
                    "current_message": message,
                    "conversation_context": conversation_context,
                    "tool_results": json.dumps(tool_results, indent=2)
                }
            )
            
            return context_analysis
            
        except Exception as e:
            print(f"❌ Error analyzing context: {e}")
            return {"context_updates": {}, "conversation_summary": "Context analysis failed"}
    
    def _generate_suggested_actions(self, intent_analysis: Dict, tool_results: Dict) -> List[str]:
        """Generate suggested follow-up actions"""
        suggestions = []
        
        intent = intent_analysis.get('primary_intent', '')
        success = tool_results.get('success', True)
        
        if intent == 'product' and success:
            suggestions.extend([
                "Would you like to see more details about any of these items?",
                "Can I help you find items in a specific size or color?",
                "Would you like to see similar products?"
            ])
        elif intent == 'order' and success:
            suggestions.extend([
                "Do you need help with anything else regarding this order?",
                "Would you like tracking information?",
                "Is there anything else I can help you with?"
            ])
        elif not success:
            suggestions.extend([
                "Let me try a different approach to help you",
                "Would you like me to connect you with a specialist?",
                "Can you provide more details so I can assist better?"
            ])
        
        return suggestions[:2]  # Limit to 2 suggestions
    
    def _create_fallback_response(self, tool_results: Dict, message: str) -> str:
        """Create fallback response when AI generation fails"""
        if tool_results.get('success'):
            return "I've found some information for you! Let me know if you need anything else or have other questions."
        else:
            return "I apologize, but I'm having trouble processing your request right now. Let me try to help you in a different way, or you can contact our customer service team directly."
    
    async def handle_error_gracefully(self, error: str, user_message: str, session_id: str) -> Dict[str, Any]:
        """Handle errors gracefully with context"""
        error_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Sarah, a customer service representative handling a technical issue.

Create a warm, apologetic response that:
- Acknowledges the problem without being too technical
- Shows genuine concern for the customer
- Offers practical alternatives or solutions
- Maintains confidence that you can still help
- Asks how else you can assist

Be natural and conversational, not robotic."""),
            ("human", "Customer asked: {message}\nTechnical issue: {error}\nCreate a helpful response.")
        ])
        
        try:
            chain = error_prompt | self.llm
            response = await asyncio.to_thread(
                chain.invoke,
                {"message": user_message, "error": error}
            )
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
        except Exception:
            response_text = "I'm really sorry, but I'm experiencing some technical difficulties right now. Let me try to help you in a different way - what specifically can I assist you with today?"
        
        # Still try to save the conversation
        try:
            self.memory_manager.add_conversation_turn(
                session_id=session_id,
                user_message=user_message,
                bot_response=response_text,
                tools_used=["error_handler"],
                confidence=0.3,
                context={"error_occurred": True, "error_type": "technical"}
            )
        except:
            pass  # Don't fail completely if memory fails too
        
        return {
            "response": response_text,
            "confidence": 0.3,
            "tools_used": ["error_handler"],
            "conversation_context": {},
            "suggested_actions": ["Let me try a different approach", "Contact customer service directly"]
        }
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run diagnostics on AI coordinator"""
        try:
            # Test intent analysis
            test_intent = await asyncio.to_thread(
                self.intent_analyzer.invoke,
                {
                    "current_message": "Show me new arrivals",
                    "conversation_context": ""
                }
            )
            
            return {
                "healthy": True,
                "llm_connected": True,
                "intent_analysis_working": bool(test_intent.get('primary_intent')),
                "components": ["intent_analyzer", "tool_router", "response_generator", "context_analyzer"],
                "memory_manager": self.memory_manager.is_healthy(),
                "test_intent_result": test_intent
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def is_healthy(self) -> bool:
        """Check if AI coordinator is healthy"""
        try:
            return (
                hasattr(self, 'llm') and self.llm is not None and
                hasattr(self, 'tools') and self.tools is not None and
                hasattr(self, 'memory_manager') and self.memory_manager is not None
            )
        except:
            return False