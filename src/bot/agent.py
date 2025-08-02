import asyncio
from typing import Dict, List, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.tools.base_tool import BaseTool
from src.tools.new_arrivals import NewArrivalsTool
from src.tools.general_support import GeneralSupportTool
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
- Provide general customer support
- Guide customers to appropriate resources

Guidelines:
- Be friendly, professional, and concise
- Use emojis appropriately to make responses engaging
- When customers ask about new arrivals, latest products, or what's new, use your new arrivals tool
- For other inquiries, provide helpful general support
- If you can't help with something specific, politely explain your limitations and suggest alternatives
- Always prioritize customer satisfaction and strive to provide the best possible assistance."""
        # Note: The chain creation is incomplete in your code; we'll leave it as is for now
        return None  # Placeholder, as the original code doesn't implement the chain

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
            # Check which tool matches the intent
            for tool_name, tool in self.tools.items():
                if tool.matches_intent(message):
                    result = await tool.execute(message)
                    return {
                        "response": result["data"] if isinstance(result["data"], str) else result["data"].get("response", tool.get_fallback_response()),
                        "confidence": result["confidence"],
                        "intent": tool_name,
                        "tools_used": [tool_name]
                    }
            
            # Default to general support tool if no specific intent matches
            result = await self.tools["general_support"].execute(message)
            return {
                "response": result["data"],
                "confidence": result["confidence"],
                "intent": "general_support",
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