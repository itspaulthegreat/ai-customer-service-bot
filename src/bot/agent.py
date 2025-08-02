import asyncio
from typing import Dict, List, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.tools.base_tool import BaseTool
from src.tools.new_arrivals import NewArrivalsTool
from src.tools.general_support import GeneralSupportTool
from src.tools.order_status import OrderStatusTool
from src.config.settings import Settings

class CustomerServiceAgent:
    """Main customer service agent that orchestrates all tools and responses"""
    
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
        
        # Initialize tools
        self.tools = {
            "new_arrivals": NewArrivalsTool(wix_client),
            "order_status": OrderStatusTool(wix_client),
            "general_support": GeneralSupportTool(wix_client)
        }
        
        # Create agent chain
        self.agent_chain = self._create_agent_chain()
        print("✅ Customer service agent initialized with tools:", list(self.tools.keys()))
    
    def _create_agent_chain(self):
        """Create the main agent prompt and chain"""
        system_prompt = """You are a helpful and professional customer service assistant for an online clothing store.

Your primary capabilities:
- Show customers new arrivals and latest products
- Check order status and shipment tracking
- Provide general customer support
- Guide customers to appropriate resources

Guidelines:
- Be friendly, professional, and concise
- Use emojis appropriately to make responses engaging
- When customers ask about new arrivals, latest products, or what's new, use your new arrivals tool
- When customers ask about order status, tracking, or shipments, use your order status tool
- For other inquiries, provide helpful general support
- If you can't help with something specific, politely explain your limitations and suggest alternatives
- Always prioritize customer satisfaction and strive to provide the best possible assistance

For order status queries:
- Ask for the order ID if not provided
- Explain shipment status clearly
- Provide helpful next steps
- Direct customers to contact support for complex issues"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        return prompt | self.llm

    def is_healthy(self) -> bool:
        """Check if the agent and its components are healthy"""
        try:
            # Check if LLM is initialized
            if not hasattr(self, 'llm') or self.llm is None:
                return False
            
            # Check if tools are initialized
            if not self.tools or not all(isinstance(tool, BaseTool) for tool in self.tools.values()):
                return False
            
            # Optionally, add more specific checks (e.g., test LLM connection)
            return True
        except Exception:
            return False
    
    async def process_message(self, message: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process incoming user message and route to appropriate tool"""
        try:
            # Check which tool matches the intent - order matters for priority
            tool_priority = ["order_status", "new_arrivals", "general_support"]
            
            for tool_name in tool_priority:
                tool = self.tools[tool_name]
                if tool.matches_intent(message):
                    result = await tool.execute(message)
                    
                    # Handle different result formats
                    if isinstance(result, dict) and "data" in result:
                        response_text = result["data"]
                        if isinstance(response_text, dict):
                            response_text = response_text.get("response", str(response_text))
                    else:
                        response_text = str(result)
                    
                    return {
                        "response": response_text,
                        "confidence": result.get("confidence", 0.8) if isinstance(result, dict) else 0.8,
                        "intent": tool_name,
                        "tools_used": [tool_name]
                    }
            
            # If no specific tool matches, use LLM to generate a response
            try:
                llm_response = self.agent_chain.invoke({"input": message})
                response_text = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
                
                return {
                    "response": response_text,
                    "confidence": 0.7,
                    "intent": "llm_general",
                    "tools_used": ["llm"]
                }
            except Exception as llm_error:
                print(f"❌ LLM error: {llm_error}")
                # Fallback to general support tool
                result = await self.tools["general_support"].execute(message)
                response_text = result["data"] if isinstance(result, dict) and "data" in result else str(result)
                
                return {
                    "response": response_text,
                    "confidence": 0.6,
                    "intent": "general_support_fallback",
                    "tools_used": ["general_support"]
                }
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            return {
                "response": "I'm sorry, something went wrong. Please try again or contact support.",
                "confidence": 0.1,
                "intent": "error",
                "tools_used": []
            }