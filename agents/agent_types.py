from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AgentMessage(BaseModel):
    """Standard message format for inter-agent communication"""
    sender: str  # Agent name that sent the message
    recipient: str  # Agent name that should receive the message  
    message_type: str  # Type of message (request, response, notification, etc.)
    content: str  # The actual message content
    metadata: Optional[Dict[str, Any]] = None  # Additional context/data
    timestamp: Optional[str] = None


class AgentState(TypedDict):
    """Shared state between all agents"""
    messages: List[BaseMessage]  # LangGraph message history
    current_agent: str  # Which agent is currently active
    user_intent: Optional[str]  # Extracted user intent
    knowledge_base_id: Optional[str]  # Current KB being worked with
    agent_messages: List[AgentMessage]  # Inter-agent communications
    recursions: int  # Track recursion count
    task_context: Optional[Dict[str, Any]]  # Current task context
    session_data: Optional[Dict[str, Any]]  # Session-level data
