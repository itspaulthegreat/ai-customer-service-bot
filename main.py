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
import sys
import traceback
print("🚀 DEBUG: Starting main.py initialization...")
print(f"🐍 Python version: {sys.version}")

# Test each import individually
try:
    print("📦 Testing imports...")
    
    print("  - Testing dotenv...")
    from dotenv import load_dotenv
    print("  ✅ dotenv imported")
    
    print("  - Testing FastAPI...")
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    print("  ✅ FastAPI imported")
    
    print("  - Testing core imports...")
    from src.core.memory_manager import ConversationMemoryManager
    print("  ✅ ConversationMemoryManager imported")
    
    from src.core.ai_coordinator import AICoordinator
    print("  ✅ AICoordinator imported")
    
    print("  - Testing tool imports...")
    from src.tools.product_tools import ProductTools
    print("  ✅ ProductTools imported")
    
    from src.tools.order_tools import OrderTools
    print("  ✅ OrderTools imported")
    
    from src.tools.general_tools import GeneralTools
    print("  ✅ GeneralTools imported")
    
    print("  - Testing API imports...")
    from src.api.wix_client import WixAPIClient
    print("  ✅ WixAPIClient imported")
    
    print("  - Testing utils imports...")
    from src.utils.response_formatter import ResponseFormatter
    print("  ✅ ResponseFormatter imported")
    
    from src.utils.logger import Logger
    print("  ✅ Logger imported")
    
    print("✅ All imports successful!")
    
except Exception as e:
    print(f"❌ IMPORT ERROR: {e}")
    print("Full traceback:")
    traceback.print_exc()
    print("Exiting due to import failure...")
    sys.exit(1)

# Test environment variables
try:
    print("🔧 Testing environment variables...")
    load_dotenv()
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    WIX_BASE_URL = os.getenv("WIX_BASE_URL")
    PORT = int(os.getenv("PORT", 8000))
    
    print(f"  - GROQ_API_KEY: {'✅ Found' if GROQ_API_KEY else '❌ Missing'}")
    print(f"  - WIX_BASE_URL: {WIX_BASE_URL or '❌ Missing'}")
    print(f"  - PORT: {PORT}")
    
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY is required!")
        print("Make sure your .env file contains: GROQ_API_KEY=your_key_here")
        
except Exception as e:
    print(f"❌ Environment variable error: {e}")
    traceback.print_exc()

# Test component initialization
try:
    print("🔧 Testing component initialization...")
    
    print("  - Initializing Wix client...")
    wix_client = WixAPIClient(WIX_BASE_URL)
    print("  ✅ Wix client created")
    
    print("  - Initializing tools...")
    product_tools = ProductTools(wix_client)
    print("    ✅ ProductTools created")
    
    order_tools = OrderTools(wix_client) 
    print("    ✅ OrderTools created")
    
    general_tools = GeneralTools()
    print("    ✅ GeneralTools created")
    
    print("  - Initializing memory manager...")
    memory_manager = ConversationMemoryManager()
    print("  ✅ ConversationMemoryManager created")
    
    print("  - Initializing response formatter...")
    response_formatter = ResponseFormatter()
    print("  ✅ ResponseFormatter created")
    
    print("  - Initializing AI coordinator...")
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
    print("  ✅ AICoordinator created")
    
    print("✅ All components initialized successfully!")
    system_healthy = True
    
except Exception as e:
    print(f"❌ COMPONENT INITIALIZATION ERROR: {e}")
    print("Full traceback:")
    traceback.print_exc()
    system_healthy = False
    print("⚠️ System marked as unhealthy, but continuing...")

print(f"🏥 System Health Status: {'✅ Healthy' if system_healthy else '❌ Unhealthy'}")

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

@app.post("/chat")
async def chat_debug(message: ChatMessage):
    """Debug version of chat endpoint"""
    print(f"\n🔄 === NEW CHAT REQUEST ===")
    print(f"📝 Message: {message.message}")
    print(f"👤 User ID: {message.user_id}")
    print(f"🆔 Session ID: {message.session_id}")
    print(f"📋 Context: {message.context}")
    print(f"🏥 System Healthy: {system_healthy}")
    
    if not system_healthy:
        print("❌ System unhealthy - returning error")
        raise HTTPException(status_code=503, detail="AI system unavailable")
    
    try:
        print("🤖 Starting AI processing...")
        
        # Generate session ID if not provided
        session_id = message.session_id or f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"🆔 Using session ID: {session_id}")
        
        print("🧠 Calling ai_coordinator.process_conversation...")
        result = await ai_coordinator.process_conversation(
            message=message.message,
            user_id=message.user_id,
            session_id=session_id,
            context=message.context or {}
        )
        
        print(f"✅ AI processing completed successfully!")
        print(f"📊 Result keys: {list(result.keys())}")
        print(f"🔧 Tools used: {result.get('tools_used', [])}")
        print(f"📈 Confidence: {result.get('confidence', 0)}")
        
        response = ChatResponse(
            response=result["response"],
            session_id=session_id,
            confidence=result["confidence"],
            tools_used=result["tools_used"],
            conversation_context=result["conversation_context"],
            suggested_actions=result.get("suggested_actions", [])
        )
        
        print(f"✅ Response created successfully")
        return response
        
    except Exception as e:
        print(f"❌ CHAT ERROR: {e}")
        print("Full error traceback:")
        traceback.print_exc()
        
        # Return the actual error instead of graceful handling
        error_detail = f"Debug Error: {str(e)}"
        print(f"🚨 Raising HTTPException with: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

print("🚀 Debug setup complete! Starting FastAPI server...")


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