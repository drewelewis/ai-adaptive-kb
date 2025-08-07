"""
Robust State Management System for Multi-Agent Knowledge Base

This module provides a centralized, persistent, and validated state management
system that ensures consistency across user interactions and agent operations.
"""

from typing import Dict, Any, Optional, List, TypedDict, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import os
import sqlite3
import threading
from enum import Enum
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class StateChangeType(Enum):
    """Types of state changes for auditing"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"
    ROLLBACK = "rollback"

@dataclass
class StateChange:
    """Record of a state change for auditing and rollback"""
    timestamp: datetime
    change_type: StateChangeType
    key: str
    old_value: Any
    new_value: Any
    agent: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class SessionContext:
    """Core session context with validation"""
    session_id: str
    knowledge_base_id: Optional[str] = None
    article_id: Optional[str] = None
    user_intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    task_context: Dict[str, Any] = field(default_factory=dict)
    conversation_state: str = "active"  # active, waiting, completed, error
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        """Validate session context"""
        if not self.session_id:
            return False
        if self.intent_confidence is not None and not 0.0 <= self.intent_confidence <= 1.0:
            return False
        if self.conversation_state not in ["active", "waiting", "completed", "error"]:
            return False
        return True

@dataclass
class AgentContext:
    """Agent-specific context with persistence"""
    current_agent: str = "UserProxy"
    agent_messages: List[Dict[str, Any]] = field(default_factory=list)
    recursions: int = 0
    consecutive_tool_calls: int = 0
    last_tool_result: Optional[str] = None
    processed_workflow_messages: list = field(default_factory=list)
    
    def reset_execution_state(self):
        """Reset execution-specific state while preserving conversation state"""
        self.recursions = 0
        self.consecutive_tool_calls = 0
        self.last_tool_result = None

@dataclass
class ConversationMemory:
    """Structured conversation memory"""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context_window: int = 10  # Number of recent messages to keep in active memory
    
    def add_message(self, message: Dict[str, Any]):
        """Add message to memory with automatic pruning"""
        self.messages.append({
            **message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent messages in active memory
        if len(self.messages) > self.context_window * 2:
            # Keep recent messages and some historical context
            self.messages = self.messages[-self.context_window:]
    
    def get_recent_context(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        return self.messages[-count:] if count <= len(self.messages) else self.messages

class RobustStateManager:
    """
    Centralized state management with persistence, validation, and rollback capabilities
    """
    
    def __init__(self, session_id: str, persistence_dir: str = "session_data"):
        self.session_id = session_id
        self.persistence_dir = persistence_dir
        self._lock = threading.RLock()
        
        # Initialize storage
        os.makedirs(persistence_dir, exist_ok=True)
        self.db_path = os.path.join(persistence_dir, "state_storage.db")
        self._init_database()
        
        # State components
        self._session_context: Optional[SessionContext] = None
        self._agent_context = AgentContext()
        self._conversation_memory = ConversationMemory()
        self._change_history: List[StateChange] = []
        
        # Load existing state if available
        self._load_state()
    
    def _init_database(self):
        """Initialize SQLite database for state persistence"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_states (
                    session_id TEXT PRIMARY KEY,
                    session_context TEXT,
                    agent_context TEXT,
                    conversation_memory TEXT,
                    created_at TIMESTAMP,
                    last_updated TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP,
                    change_type TEXT,
                    key_path TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    agent TEXT,
                    FOREIGN KEY (session_id) REFERENCES session_states (session_id)
                )
            """)
            conn.commit()
    
    @contextmanager
    def state_transaction(self, agent: Optional[str] = None):
        """Context manager for atomic state operations"""
        with self._lock:
            try:
                # Create a checkpoint before changes
                checkpoint = self._create_checkpoint()
                yield self
                # Auto-save after successful transaction
                self._save_state()
            except Exception as e:
                # Rollback to checkpoint on error
                logger.error(f"State transaction failed: {e}")
                self._restore_checkpoint(checkpoint)
                raise
    
    def _create_checkpoint(self) -> Dict[str, Any]:
        """Create a state checkpoint for rollback"""
        return {
            "session_context": asdict(self._session_context) if self._session_context else None,
            "agent_context": asdict(self._agent_context),
            "conversation_memory": asdict(self._conversation_memory),
            "timestamp": datetime.now()
        }
    
    def _restore_checkpoint(self, checkpoint: Dict[str, Any]):
        """Restore state from checkpoint"""
        if checkpoint["session_context"]:
            self._session_context = SessionContext(**checkpoint["session_context"])
        self._agent_context = AgentContext(**checkpoint["agent_context"])
        self._conversation_memory = ConversationMemory(**checkpoint["conversation_memory"])
    
    def initialize_session(self, knowledge_base_id: Optional[str] = None) -> SessionContext:
        """Initialize or get existing session context"""
        with self._lock:
            if not self._session_context:
                self._session_context = SessionContext(
                    session_id=self.session_id,
                    knowledge_base_id=knowledge_base_id
                )
                self._record_change(StateChangeType.CREATE, "session", None, asdict(self._session_context))
            return self._session_context
    
    def update_session_context(self, **kwargs) -> SessionContext:
        """Update session context with validation"""
        with self._lock:
            if not self._session_context:
                self.initialize_session()
            
            old_context = asdict(self._session_context)
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(self._session_context, key):
                    old_value = getattr(self._session_context, key)
                    setattr(self._session_context, key, value)
                    self._record_change(StateChangeType.UPDATE, f"session.{key}", old_value, value)
            
            # Update timestamp and validate
            self._session_context.last_updated = datetime.now()
            
            if not self._session_context.validate():
                # Rollback invalid changes
                self._session_context = SessionContext(**old_context)
                raise ValueError("Invalid session context update")
            
            return self._session_context
    
    def update_agent_context(self, agent: str, **kwargs) -> AgentContext:
        """Update agent context"""
        with self._lock:
            old_context = asdict(self._agent_context)
            
            for key, value in kwargs.items():
                if hasattr(self._agent_context, key):
                    old_value = getattr(self._agent_context, key)
                    setattr(self._agent_context, key, value)
                    self._record_change(StateChangeType.UPDATE, f"agent.{key}", old_value, value, agent)
            
            return self._agent_context
    
    def add_conversation_message(self, message: Dict[str, Any], agent: Optional[str] = None):
        """Add message to conversation memory"""
        with self._lock:
            self._conversation_memory.add_message(message)
            self._record_change(StateChangeType.CREATE, "conversation.message", None, message, agent)
    
    def get_conversation_context(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        with self._lock:
            return self._conversation_memory.get_recent_context(count)
    
    def merge_langgraph_state(self, langgraph_state: Dict[str, Any], agent: str = "System"):
        """Merge state from LangGraph execution"""
        with self._lock:
            # Update session context from LangGraph state
            session_updates = {}
            for key in ["knowledge_base_id", "article_id", "user_intent", "task_context"]:
                if key in langgraph_state and langgraph_state[key] is not None:
                    session_updates[key] = langgraph_state[key]
            
            if session_updates:
                self.update_session_context(**session_updates)
            
            # Update agent context
            agent_updates = {}
            for key in ["current_agent", "recursions", "consecutive_tool_calls", "last_tool_result"]:
                if key in langgraph_state:
                    agent_updates[key] = langgraph_state[key]
            
            if agent_updates:
                self.update_agent_context(agent, **agent_updates)
            
            # Handle messages
            if "messages" in langgraph_state:
                for msg in langgraph_state["messages"]:
                    if hasattr(msg, 'content'):
                        self.add_conversation_message({
                            "role": msg.__class__.__name__,
                            "content": msg.content
                        }, agent)
    
    def to_langgraph_state(self) -> Dict[str, Any]:
        """Convert to LangGraph-compatible state"""
        with self._lock:
            state = {}
            
            # Session context
            if self._session_context:
                state.update({
                    "knowledge_base_id": self._session_context.knowledge_base_id,
                    "article_id": self._session_context.article_id,
                    "user_intent": self._session_context.user_intent,
                    "task_context": self._session_context.task_context,
                })
            
            # Agent context
            state.update({
                "current_agent": self._agent_context.current_agent,
                "agent_messages": self._agent_context.agent_messages,
                "recursions": self._agent_context.recursions,
                "consecutive_tool_calls": self._agent_context.consecutive_tool_calls,
                "last_tool_result": self._agent_context.last_tool_result,
                "processed_workflow_messages": self._agent_context.processed_workflow_messages,
            })
            
            # Add conversation messages (converted to LangChain format would be done by caller)
            state["conversation_history"] = self.get_conversation_context()
            
            return state
    
    def _record_change(self, change_type: StateChangeType, key: str, old_value: Any, new_value: Any, agent: Optional[str] = None):
        """Record a state change for auditing"""
        change = StateChange(
            timestamp=datetime.now(),
            change_type=change_type,
            key=key,
            old_value=old_value,
            new_value=new_value,
            agent=agent,
            session_id=self.session_id
        )
        self._change_history.append(change)
        
        # Persist change to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO state_changes 
                (session_id, timestamp, change_type, key_path, old_value, new_value, agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.session_id,
                change.timestamp,
                change.change_type.value,
                key,
                json.dumps(old_value, default=str) if old_value is not None else None,
                json.dumps(new_value, default=str) if new_value is not None else None,
                agent
            ))
            conn.commit()
    
    def _save_state(self):
        """Persist current state to database"""
        with sqlite3.connect(self.db_path) as conn:
            session_data = asdict(self._session_context) if self._session_context else None
            agent_data = asdict(self._agent_context)
            memory_data = asdict(self._conversation_memory)
            
            conn.execute("""
                INSERT OR REPLACE INTO session_states 
                (session_id, session_context, agent_context, conversation_memory, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.session_id,
                json.dumps(session_data, default=str) if session_data else None,
                json.dumps(agent_data, default=str),
                json.dumps(memory_data, default=str),
                self._session_context.created_at if self._session_context else datetime.now(),
                datetime.now()
            ))
            conn.commit()
    
    def _load_state(self):
        """Load existing state from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT session_context, agent_context, conversation_memory 
                    FROM session_states WHERE session_id = ?
                """, (self.session_id,))
                row = cursor.fetchone()
                
                if row:
                    session_data, agent_data, memory_data = row
                    
                    if session_data:
                        self._session_context = SessionContext(**json.loads(session_data))
                    
                    if agent_data:
                        agent_dict = json.loads(agent_data)
                        # Handle list format for processed_workflow_messages
                        if "processed_workflow_messages" in agent_dict:
                            # Ensure it's a list (it should already be one)
                            if not isinstance(agent_dict["processed_workflow_messages"], list):
                                agent_dict["processed_workflow_messages"] = list(agent_dict["processed_workflow_messages"])
                        self._agent_context = AgentContext(**agent_dict)
                    
                    if memory_data:
                        self._conversation_memory = ConversationMemory(**json.loads(memory_data))
        
        except Exception as e:
            logger.warning(f"Could not load existing state: {e}")
            # Initialize with defaults if loading fails
            pass
    
    def clear_session(self):
        """Clear all session state"""
        with self._lock:
            self._record_change(StateChangeType.DELETE, "session", asdict(self._session_context) if self._session_context else None, None)
            
            self._session_context = None
            self._agent_context = AgentContext()
            self._conversation_memory = ConversationMemory()
            
            # Clear from database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM session_states WHERE session_id = ?", (self.session_id,))
                conn.commit()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state for debugging"""
        with self._lock:
            return {
                "session_id": self.session_id,
                "session_context": asdict(self._session_context) if self._session_context else None,
                "agent_context": asdict(self._agent_context),
                "conversation_messages": len(self._conversation_memory.messages),
                "change_history_count": len(self._change_history),
                "last_updated": self._session_context.last_updated if self._session_context else None
            }
    
    def get_change_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent state changes for debugging"""
        with self._lock:
            recent_changes = self._change_history[-limit:] if limit else self._change_history
            return [asdict(change) for change in recent_changes]
