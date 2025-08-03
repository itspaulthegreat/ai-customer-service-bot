# main.py - Completely restructured AI customer service system
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
from datetime import datetime

# Load environment variables
load_dotenv()

# Core imports
from src.core.memory_manager import ConversationMemoryManager
from src.core.ai_coordinator import AICoordinator
from src.tools.product_tools import ProductTools
from src.tools.order_tools import OrderTools
from src.tools.general_tools import GeneralTools
from src.api.wix_client import WixAPIClient
from src.utils.response_formatter import ResponseFormatter
from src.utils.logger import Logger

# Initialize logging
logger = Logger(__name__)

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WIX_BASE_URL = os.getenv("WIX_BASE_URL")
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(title="Enhanced AI Customer Service", version="4.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    response: str
    session_id: str
    confidence: float
    tools_used: List[str]
    conversation_context: Dict[str, Any]
    suggested_actions: List[str] = []

# Initialize core components
try:
    # Initialize Wix client
    wix_client = WixAPIClient(WIX_BASE_URL)
    
    # Initialize tools (specialized for different tasks)
    product_tools = ProductTools(wix_client)
    order_tools = OrderTools(wix_client)
    general_tools = GeneralTools()
    
    # Initialize memory manager for conversation history
    memory_manager = ConversationMemoryManager()
    
    # Initialize response formatter
    response_formatter = ResponseFormatter()
    
    # Initialize AI coordinator (manages all AI operations)
    ai_coordinator = AICoordinator(
        groq_api_key=GROQ_API_KEY,
        tools={
            'product': product_tools,
            'order': order_tools,
            'general': general_tools
        },
        memory_manager=memory_manager,
        response_formatter=response_formatter
    )
    
    logger.info("✅ Enhanced AI system initialized successfully")
    system_healthy = True
    
except Exception as e:
    logger.error(f"❌ Failed to initialize AI system: {e}")
    system_healthy = False

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Enhanced chat endpoint with memory and specialized tools"""
    if not system_healthy:
        raise HTTPException(status_code=503, detail="AI system unavailable")
    
    try:
        logger.info(f"💬 Processing message: {message.message[:100]}...")
        
        # Generate session ID if not provided
        session_id = message.session_id or f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Process message through AI coordinator
        result = await ai_coordinator.process_conversation(
            message=message.message,
            user_id=message.user_id,
            session_id=session_id,
            context=message.context or {}
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            confidence=result["confidence"],
            tools_used=result["tools_used"],
            conversation_context=result["conversation_context"],
            suggested_actions=result.get("suggested_actions", [])
        )
        
    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {e}")
        
        # Graceful error handling with memory
        fallback_response = await ai_coordinator.handle_error_gracefully(
            error=str(e),
            user_message=message.message,
            session_id=message.session_id or "error_session"
        )
        
        return ChatResponse(
            response=fallback_response["response"],
            session_id=message.session_id or "error_session",
            confidence=0.2,
            tools_used=["error_handler"],
            conversation_context={}
        )

@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = memory_manager.get_conversation_history(session_id)
        return {
            "session_id": session_id,
            "history": history,
            "message_count": len(history),
            "context": memory_manager.get_session_context(session_id)
        }
    except Exception as e:
        logger.error(f"❌ Error getting conversation history: {e}")
        raise HTTPException(status_code=404, detail="Conversation not found")

@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    try:
        memory_manager.clear_session(session_id)
        return {"message": f"Conversation {session_id} cleared successfully"}
    except Exception as e:
        logger.error(f"❌ Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear conversation")

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        health_status = {
            "status": "healthy" if system_healthy else "unhealthy",
            "system": "enhanced_ai_v4",
            "components": {},
            "capabilities": []
        }
        
        if system_healthy:
            # Test all components
            health_status["components"] = {
                "ai_coordinator": ai_coordinator.is_healthy(),
                "wix_client": await wix_client.test_connection(),
                "memory_manager": memory_manager.is_healthy(),
                "product_tools": product_tools.is_healthy(),
                "order_tools": order_tools.is_healthy(),
                "general_tools": general_tools.is_healthy()
            }
            
            health_status["capabilities"] = [
                "Conversation Memory",
                "Specialized Tool Routing", 
                "Natural Language Understanding",
                "Context Awareness",
                "Error Recovery",
                "Human-like Responses"
            ]
            
            # Overall health
            all_healthy = all(health_status["components"].values())
            health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/")
async def root():
    return {
        "message": "Enhanced AI Customer Service v4.0 - Now with memory, specialized tools, and human-like responses!",
        "features": [
            "🧠 Conversation Memory & Context",
            "🔧 Specialized Tool Routing",
            "💬 Human-like Natural Responses", 
            "🔄 Error Recovery & Graceful Handling",
            "📊 Advanced Intent Understanding",
            "🎯 No Regex - Pure AI Intelligence"
        ],
        "endpoints": {
            "/chat": "Main conversation endpoint",
            "/conversation/{session_id}": "Get conversation history",
            "/health": "System health check",
            "/test-tools": "Test individual tools"
        }
    }

@app.get("/test-tools")
async def test_tools():
    """Test all specialized tools"""
    if not system_healthy:
        return {"error": "System not healthy"}
    
    try:
        test_results = {}
        
        # Test product tools
        test_results["product_tools"] = await product_tools.run_diagnostics()
        
        # Test order tools  
        test_results["order_tools"] = await order_tools.run_diagnostics()
        
        # Test general tools
        test_results["general_tools"] = await general_tools.run_diagnostics()
        
        # Test AI coordinator
        test_results["ai_coordinator"] = await ai_coordinator.run_diagnostics()
        
        return {
            "test_status": "completed",
            "results": test_results,
            "overall_health": all(
                result.get("healthy", False) 
                for result in test_results.values()
            )
        }
        
    except Exception as e:
        logger.error(f"❌ Tool testing failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    print(f"\n🚀 Starting Enhanced AI Customer Service v4.0...")
    print(f"🧠 Features: Memory, Specialized Tools, Human-like Responses")
    print(f"📡 Wix URL: {WIX_BASE_URL}")
    print(f"🔑 Groq API: {'✅ Connected' if GROQ_API_KEY else '❌ Missing'}")
    print(f"💡 System: {'✅ Healthy' if system_healthy else '❌ Degraded'}")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)