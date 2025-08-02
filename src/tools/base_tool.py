from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool

class BaseTool(ABC):
    """Base class for all customer service tools"""
    
    def __init__(self, wix_client, name: str, description: str):
        self.wix_client = wix_client
        self.name = name
        self.description = description
        self.intent_patterns = []
        self.fallback_responses = []
    
    @abstractmethod
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    def get_intent_patterns(self) -> List[str]:
        """Return list of patterns that trigger this tool"""
        pass
    
    @abstractmethod
    def get_fallback_response(self) -> str:
        """Return fallback response when tool fails"""
        pass
    
    def matches_intent(self, message: str) -> bool:
        """Check if message matches this tool's intent patterns"""
        message_lower = message.lower()
        patterns = self.get_intent_patterns()
        return any(pattern in message_lower for pattern in patterns)
    
    async def test_tool(self) -> Dict[str, Any]:
        """Test tool functionality"""
        try:
            # Run a basic test of the tool
            result = await self.execute("test query")
            return {
                "tool": self.name,
                "status": "success" if result["success"] else "failed",
                "message": "Tool test completed",
                "details": result
            }
        except Exception as e:
            return {
                "tool": self.name,
                "status": "error", 
                "message": str(e),
                "details": None
            }
    
    def format_response(self, data: Any, success: bool = True) -> Dict[str, Any]:
        """Standard response formatting"""
        return {
            "success": success,
            "tool_used": self.name,
            "data": data,
            "confidence": 0.9 if success else 0.3
        }