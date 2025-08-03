# src/core/memory_manager.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict

@dataclass
class ConversationTurn:
    """Single conversation turn"""
    timestamp: str
    user_message: str
    bot_response: str
    tools_used: List[str]
    confidence: float
    context: Dict[str, Any]

class ConversationMemoryManager:
    """Manages conversation history and context"""
    
    def __init__(self, max_history_length: int = 20, session_timeout_hours: int = 24):
        self.conversations: Dict[str, List[ConversationTurn]] = {}
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
        self.max_history_length = max_history_length
        self.session_timeout = timedelta(hours=session_timeout_hours)
    
    def add_conversation_turn(self, session_id: str, user_message: str, 
                            bot_response: str, tools_used: List[str], 
                            confidence: float, context: Dict[str, Any] = None):
        """Add a conversation turn to memory"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            bot_response=bot_response,
            tools_used=tools_used,
            confidence=confidence,
            context=context or {}
        )
        
        self.conversations[session_id].append(turn)
        
        # Keep only recent history
        if len(self.conversations[session_id]) > self.max_history_length:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history_length:]
    
    def get_conversation_history(self, session_id: str, last_n: Optional[int] = None) -> List[Dict]:
        """Get conversation history for a session"""
        if session_id not in self.conversations:
            return []
        
        history = self.conversations[session_id]
        if last_n:
            history = history[-last_n:]
        
        return [asdict(turn) for turn in history]
    
    def get_recent_context(self, session_id: str, turns_back: int = 3) -> str:
        """Get recent conversation context as text"""
        if session_id not in self.conversations:
            return ""
        
        recent_turns = self.conversations[session_id][-turns_back:]
        context_parts = []
        
        for turn in recent_turns:
            context_parts.append(f"User: {turn.user_message}")
            context_parts.append(f"Assistant: {turn.bot_response}")
        
        return "\n".join(context_parts)
    
    def update_session_context(self, session_id: str, context_updates: Dict[str, Any]):
        """Update session context with new information"""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {}
        
        self.session_contexts[session_id].update(context_updates)
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        return self.session_contexts.get(session_id, {})
    
    def clear_session(self, session_id: str):
        """Clear all data for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
    
    def cleanup_old_sessions(self):
        """Remove expired sessions"""
        cutoff = datetime.now() - self.session_timeout
        sessions_to_remove = []
        
        for session_id, turns in self.conversations.items():
            if turns and datetime.fromisoformat(turns[-1].timestamp) < cutoff:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.clear_session(session_id)
    
    def is_healthy(self) -> bool:
        """Check if memory manager is working"""
        return hasattr(self, 'conversations') and hasattr(self, 'session_contexts')