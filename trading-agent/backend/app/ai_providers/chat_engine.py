"""
Chat Engine Module
Persistent chat system with the AI trading agent
"""
import uuid
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json

from .ai_client import AIClient, ChatMessage, AIResponse
from ..config import settings

logger = logging.getLogger(__name__)


class ChatRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatSession:
    """Chat session structure"""
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessageData:
    """Chat message data structure"""
    message_id: str
    session_id: str
    role: str
    content: str
    image_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChatEngine:
    """
    Chat engine for persistent AI conversations
    """
    
    SYSTEM_PROMPT = """You are an expert AI Trading Assistant specializing in financial markets analysis.

Your capabilities include:
- Technical analysis of charts and price action
- Market sentiment interpretation
- Risk management guidance
- Trading strategy recommendations
- News and event analysis

Guidelines:
1. Always provide data-driven analysis
2. Include risk warnings when discussing trades
3. Be concise but thorough
4. Use professional trading terminology
5. Acknowledge uncertainty when appropriate
6. Never guarantee profits or specific price targets

When analyzing charts or images:
- Identify key support/resistance levels
- Note trend direction and strength
- Highlight any patterns or formations
- Suggest potential scenarios (not predictions)

Remember: This is educational analysis, not financial advice."""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.messages: Dict[str, ChatMessageData] = {}
        self.ai_client: Optional[AIClient] = None
    
    async def initialize(self):
        """Initialize chat engine"""
        self.ai_client = AIClient(
            provider=settings.DEFAULT_AI_PROVIDER,
            model=settings.DEFAULT_AI_MODEL
        )
    
    def create_session(
        self,
        title: str = None,
        metadata: Dict[str, Any] = None
    ) -> ChatSession:
        """Create new chat session"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = ChatSession(
            session_id=session_id,
            title=title or f"Chat {now.strftime('%Y-%m-%d %H:%M')}",
            created_at=now,
            updated_at=now,
            messages=[],
            metadata=metadata or {}
        )
        
        # Add system message
        system_message = ChatMessageData(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role=ChatRole.SYSTEM.value,
            content=self.SYSTEM_PROMPT,
            timestamp=now
        )
        
        session.messages.append(asdict(system_message))
        self.messages[system_message.message_id] = system_message
        self.sessions[session_id] = session
        
        logger.info(f"Created chat session: {session_id}")
        return session
    
    async def send_message(
        self,
        session_id: str,
        content: str,
        image_url: str = None,
        image_data: bytes = None
    ) -> Dict[str, Any]:
        """Send message and get AI response"""
        
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        
        session = self.sessions[session_id]
        
        # Create user message
        user_message = ChatMessageData(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role=ChatRole.USER.value,
            content=content,
            image_url=image_url,
            timestamp=datetime.now()
        )
        
        session.messages.append(asdict(user_message))
        self.messages[user_message.message_id] = user_message
        
        # Prepare messages for AI
        ai_messages = self._prepare_messages(session, image_data)
        
        # Get AI response
        try:
            if image_data and self.ai_client:
                # Use vision model for image analysis
                ai_response = await self.ai_client.analyze_image(
                    image_data=image_data,
                    prompt=content
                )
            elif self.ai_client:
                ai_response = await self.ai_client.chat_completion(ai_messages)
            else:
                raise RuntimeError("AI client not initialized")
            
            # Create assistant message
            assistant_message = ChatMessageData(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                role=ChatRole.ASSISTANT.value,
                content=ai_response.content,
                timestamp=datetime.now(),
                metadata={
                    "provider": ai_response.provider,
                    "model": ai_response.model,
                    "usage": ai_response.usage
                }
            )
            
            session.messages.append(asdict(assistant_message))
            self.messages[assistant_message.message_id] = assistant_message
            session.updated_at = datetime.now()
            
            return {
                "message": asdict(assistant_message),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"AI response error: {e}")
            raise
    
    def _prepare_messages(
        self,
        session: ChatSession,
        image_data: bytes = None
    ) -> List[ChatMessage]:
        """Prepare messages for AI client"""
        messages = []
        
        for msg_data in session.messages:
            msg = ChatMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                image_url=msg_data.get("image_url")
            )
            messages.append(msg)
        
        return messages
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        return asdict(session)
    
    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages for a session"""
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        # Return messages (excluding system message)
        return [
            msg for msg in session.messages
            if msg["role"] != ChatRole.SYSTEM.value
        ][-limit:]
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all chat sessions"""
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "message_count": len(s.messages)
            }
            for s in sorted(
                self.sessions.values(),
                key=lambda x: x.updated_at,
                reverse=True
            )
        ]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        if session_id in self.sessions:
            # Remove associated messages
            session = self.sessions[session_id]
            for msg in session.messages:
                self.messages.pop(msg.get("message_id"), None)
            
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def update_session_title(
        self,
        session_id: str,
        title: str
    ) -> bool:
        """Update session title"""
        if session_id in self.sessions:
            self.sessions[session_id].title = title
            self.sessions[session_id].updated_at = datetime.now()
            return True
        return False
    
    async def analyze_chart_image(
        self,
        session_id: str,
        image_data: bytes,
        symbol: str,
        timeframe: str,
        question: str = None
    ) -> Dict[str, Any]:
        """Analyze chart image in chat context"""
        
        if not self.ai_client:
            raise RuntimeError("AI client not initialized")
        
        # Create analysis prompt
        if not question:
            question = f"Analyze this {symbol} {timeframe} chart"
        
        # Analyze image
        analysis = await self.ai_client.analyze_chart(
            image_data=image_data,
            symbol=symbol,
            timeframe=timeframe
        )
        
        # Add to chat history
        content = f"[Chart Analysis: {symbol} {timeframe}]\n\n{question}"
        
        user_message = ChatMessageData(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role=ChatRole.USER.value,
            content=content,
            timestamp=datetime.now()
        )
        
        assistant_message = ChatMessageData(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role=ChatRole.ASSISTANT.value,
            content=analysis["analysis"],
            timestamp=datetime.now(),
            metadata={
                "type": "chart_analysis",
                "symbol": symbol,
                "timeframe": timeframe,
                "provider": analysis["provider"],
                "model": analysis["model"]
            }
        )
        
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.messages.append(asdict(user_message))
            session.messages.append(asdict(assistant_message))
            session.updated_at = datetime.now()
        
        return {
            "analysis": analysis["analysis"],
            "symbol": symbol,
            "timeframe": timeframe,
            "session_id": session_id
        }
    
    def export_session(self, session_id: str) -> Dict[str, Any]:
        """Export session as JSON"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        return {
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "messages": session.messages,
            "metadata": session.metadata
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chat engine statistics"""
        total_sessions = len(self.sessions)
        total_messages = len(self.messages)
        
        # Count messages by role
        role_counts = {}
        for msg in self.messages.values():
            role = msg.role
            role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "role_counts": role_counts,
            "ai_provider": settings.DEFAULT_AI_PROVIDER,
            "ai_model": settings.DEFAULT_AI_MODEL
        }


# Singleton instance
_chat_engine: Optional[ChatEngine] = None


async def get_chat_engine() -> ChatEngine:
    """Get or create chat engine singleton"""
    global _chat_engine
    if _chat_engine is None:
        _chat_engine = ChatEngine()
        await _chat_engine.initialize()
    return _chat_engine
