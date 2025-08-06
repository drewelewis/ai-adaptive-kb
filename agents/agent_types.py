from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


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
    messages: Annotated[List[BaseMessage], add_messages]  # LangGraph message history with automatic accumulation
    current_agent: str  # Which agent is currently active
    user_intent: Optional[str]  # Extracted user intent
    knowledge_base_id: Optional[str]  # Current KB being worked with
    article_id: Optional[str]  # Current article being focused on
    current_section: Optional[str]  # Current section context (e.g., "budgeting", "investment")
    agent_messages: List[AgentMessage]  # Inter-agent communications
    recursions: int  # Track recursion count
    consecutive_tool_calls: Optional[int]  # Track consecutive tool calls for loop prevention
    last_tool_result: Optional[str]  # Track the last tool result to avoid repetition
    task_context: Optional[Dict[str, Any]]  # Current task context
    session_data: Optional[Dict[str, Any]]  # Session-level data
    processed_workflow_messages: Optional[set]  # Track processed workflow message IDs
