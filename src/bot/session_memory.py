# src/bot/session_memory.py - In-memory conversation storage for active sessions

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio 

class ConversationMessage:
    """Single message in conversation"""
    def __init__(self, content: str, sender: str, timestamp: datetime = None):
        self.content = content
        self.sender = sender  # 'user' or 'bot'
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat()
        }

class SessionMemory:
    """Manages conversation memory for active sessions"""
    
    def __init__(self, max_messages_per_session: int = 50, session_timeout_minutes: int = 60):
        self.sessions: Dict[str, List[ConversationMessage]] = {}
        self.session_last_activity: Dict[str, datetime] = {}
        self.max_messages = max_messages_per_session
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        print(f"✅ Session Memory initialized (max {max_messages_per_session} messages, {session_timeout_minutes}min timeout)")
    
    def get_session_id(self, user_id: str) -> str:
        """Generate session ID from user ID"""
        return f"session_{user_id}"
    
    def add_message(self, user_id: str, content: str, sender: str) -> None:
        """Add message to user's session"""
        session_id = self.get_session_id(user_id)
        
        # Initialize session if needed
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            print(f"🆕 New session created: {session_id}")
        
        # Add message
        message = ConversationMessage(content, sender)
        self.sessions[session_id].append(message)
        self.session_last_activity[session_id] = datetime.now()
        
        # Keep only recent messages to prevent memory overflow
        if len(self.sessions[session_id]) > self.max_messages:
            self.sessions[session_id] = self.sessions[session_id][-self.max_messages:]
        
        print(f"💬 Added {sender} message to {session_id}: {content[:50]}...")
    
    def get_conversation_history(self, user_id: str, last_n_messages: int = None) -> List[Dict[str, Any]]:
        """Get conversation history for user"""
        session_id = self.get_session_id(user_id)
        
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]
        
        if last_n_messages:
            messages = messages[-last_n_messages:]
        
        return [msg.to_dict() for msg in messages]
    
    def get_last_user_message(self, user_id: str) -> Optional[str]:
        """Get the last message from user"""
        session_id = self.get_session_id(user_id)
        
        if session_id not in self.sessions:
            return None
        
        # Find last user message
        for message in reversed(self.sessions[session_id]):
            if message.sender == 'user':
                return message.content
        
        return None
    
    def get_last_bot_message(self, user_id: str) -> Optional[str]:
        """Get the last message from bot"""
        session_id = self.get_session_id(user_id)
        
        if session_id not in self.sessions:
            return None
        
        # Find last bot message
        for message in reversed(self.sessions[session_id]):
            if message.sender == 'bot':
                return message.content
        
        return None
    
    def get_conversation_context(self, user_id: str, context_length: int = 6) -> str:
        """Get formatted conversation context for AI"""
        history = self.get_conversation_history(user_id, context_length)
        
        if not history:
            return "This is the start of the conversation."
        
        context_lines = []
        for msg in history:
            sender = "Customer" if msg["sender"] == "user" else "Assistant"
            context_lines.append(f"{sender}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def clear_session(self, user_id: str) -> bool:
        """Clear specific user session"""
        session_id = self.get_session_id(user_id)
        
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.session_last_activity:
                del self.session_last_activity[session_id]
            print(f"🧹 Cleared session: {session_id}")
            return True
        
        return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        total_sessions = len(self.sessions)
        total_messages = sum(len(msgs) for msgs in self.sessions.values())
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "active_sessions": list(self.sessions.keys()),
            "avg_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0
        }
    
    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []
                
                for session_id, last_activity in self.session_last_activity.items():
                    if current_time - last_activity > self.session_timeout:
                        expired_sessions.append(session_id)
                
                # Clean up expired sessions
                for session_id in expired_sessions:
                    if session_id in self.sessions:
                        del self.sessions[session_id]
                    if session_id in self.session_last_activity:
                        del self.session_last_activity[session_id]
                
                if expired_sessions:
                    print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
                
                # Wait 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                print(f"❌ Error in session cleanup: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def __del__(self):
        """Clean up on destruction"""
        if hasattr(self, '_cleanup_task'):
            self._cleanup_task.cancel()

# Global session memory instance
session_memory = SessionMemory()