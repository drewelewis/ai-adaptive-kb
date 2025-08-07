"""
PostgreSQL-Based Robust State Management System

This module provides a PostgreSQL-backed state management system that leverages
your existing database infrastructure for superior performance, ACID transactions,
and advanced JSON handling capabilities.
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import threading
from enum import Enum
from contextlib import contextmanager
import logging
from dotenv import load_dotenv

class DateTimeAwareJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)

def json_serial(obj):
    """JSON serializer function that handles datetime and set objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# Load environment variables
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class StateChangeType(Enum):
    """Types of state changes for auditing"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"
    ROLLBACK = "rollback"
    AGENT_SWITCH = "agent_switch"
    CONVERSATION_UPDATE = "conversation_update"

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
    current_workflow: Optional[str] = None
    workflow_step: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
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
    processed_workflow_messages: List[str] = field(default_factory=list)  # Changed from set to list
    last_agent_switch: Optional[str] = None  # ISO string instead of datetime
    agent_performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def reset_execution_state(self):
        """Reset execution-specific state while preserving conversation state"""
        self.recursions = 0
        self.consecutive_tool_calls = 0
        self.last_tool_result = None

class PostgreSQLStateManager:
    """
    PostgreSQL-backed robust state management with ACID transactions,
    JSONB storage, and advanced audit capabilities
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._lock = threading.RLock()
        
        # Database connection parameters from environment
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': os.getenv('POSTGRES_PORT', 5432),
            'dbname': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
        
        # Initialize database schema
        self._init_state_schema()
        
        # Initialize or load session
        self._initialize_session()
    
    def _get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(**self.db_config)
    
    def _init_state_schema(self):
        """Initialize state management tables if they don't exist"""
        schema_sql = """
        -- Session state management table
        CREATE TABLE IF NOT EXISTS session_states (
            session_id VARCHAR(255) PRIMARY KEY,
            session_context JSONB NOT NULL DEFAULT '{}',
            agent_context JSONB NOT NULL DEFAULT '{}',
            conversation_metadata JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Conversation messages table for better query performance
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) REFERENCES session_states(session_id) ON DELETE CASCADE,
            message_role VARCHAR(50) NOT NULL,
            message_content TEXT NOT NULL,
            message_metadata JSONB DEFAULT '{}',
            agent_name VARCHAR(100),
            tool_calls JSONB DEFAULT '[]',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            message_order INTEGER NOT NULL
        );
        
        -- State change audit log
        CREATE TABLE IF NOT EXISTS state_audit_log (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) REFERENCES session_states(session_id) ON DELETE CASCADE,
            change_type VARCHAR(50) NOT NULL,
            change_path VARCHAR(255) NOT NULL,
            old_value JSONB,
            new_value JSONB,
            agent_name VARCHAR(100),
            change_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            correlation_id UUID DEFAULT gen_random_uuid()
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_session_states_active ON session_states(is_active, updated_at);
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_session ON conversation_messages(session_id, message_order);
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_created ON conversation_messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_state_audit_session ON state_audit_log(session_id, change_timestamp);
        CREATE INDEX IF NOT EXISTS idx_session_context_gin ON session_states USING GIN (session_context);
        CREATE INDEX IF NOT EXISTS idx_agent_context_gin ON session_states USING GIN (agent_context);
        
        -- Trigger to auto-update the updated_at timestamp
        CREATE OR REPLACE FUNCTION update_session_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS trigger_update_session_timestamp ON session_states;
        CREATE TRIGGER trigger_update_session_timestamp
            BEFORE UPDATE ON session_states
            FOR EACH ROW
            EXECUTE FUNCTION update_session_updated_at();
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize state schema: {e}")
            raise
    
    def _initialize_session(self):
        """Initialize session state if it doesn't exist"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if session exists
                    cursor.execute(
                        "SELECT session_id FROM session_states WHERE session_id = %s",
                        (self.session_id,)
                    )
                    
                    if not cursor.fetchone():
                        # Create new session
                        initial_session_context = asdict(SessionContext(session_id=self.session_id))
                        initial_agent_context = asdict(AgentContext())
                        
                        cursor.execute("""
                            INSERT INTO session_states (session_id, session_context, agent_context)
                            VALUES (%s, %s, %s)
                        """, (
                            self.session_id,
                            Json(initial_session_context),
                            Json(initial_agent_context)
                        ))
                
                conn.commit()
                
                # Log session creation AFTER the session exists in database
                self._audit_change("CREATE", "session", None, {"session_id": self.session_id})
                
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            raise
    
    def initialize_session(self, knowledge_base_id: Optional[str] = None) -> SessionContext:
        """Initialize or get existing session context"""
        try:
            session_context = self.get_session_context()
            if not session_context:
                # Force initialization if session doesn't exist
                self._initialize_session()
                session_context = self.get_session_context()
            
            # Update with knowledge base if provided
            if knowledge_base_id and session_context.knowledge_base_id != knowledge_base_id:
                session_context = self.update_session_context(
                    agent="System",
                    knowledge_base_id=knowledge_base_id
                )
            
            return session_context
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            raise
    
    @contextmanager
    def state_transaction(self, agent: Optional[str] = None):
        """Context manager for atomic state operations with ACID guarantees"""
        conn = None
        try:
            conn = self._get_connection()
            conn.autocommit = False  # Start transaction
            
            with self._lock:
                yield conn
                conn.commit()
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"State transaction failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_session_context(self) -> Optional[SessionContext]:
        """Get current session context"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT session_context FROM session_states WHERE session_id = %s",
                        (self.session_id,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        session_data = row['session_context']
                        # Ensure session_id is included in the data
                        if 'session_id' not in session_data:
                            session_data['session_id'] = self.session_id
                        return SessionContext(**session_data)
                    return None
        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            return None
    
    def update_session_context(self, agent: str = "System", **kwargs) -> SessionContext:
        """Update session context with validation and audit"""
        with self.state_transaction(agent) as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get current context
            cursor.execute(
                "SELECT session_context FROM session_states WHERE session_id = %s FOR UPDATE",
                (self.session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Session {self.session_id} not found")
            
            session_data = row['session_context']
            # Ensure session_id is included in the data
            if 'session_id' not in session_data:
                session_data['session_id'] = self.session_id
            current_context = SessionContext(**session_data)
            old_context = asdict(current_context)
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(current_context, key):
                    old_value = getattr(current_context, key)
                    setattr(current_context, key, value)
                    
                    # Audit individual field changes
                    self._audit_change(
                        "UPDATE", f"session.{key}", old_value, value, agent, conn
                    )
            
            # Update timestamp and validate
            current_context.last_updated = datetime.now(timezone.utc).isoformat()
            
            if not current_context.validate():
                raise ValueError("Invalid session context update")
            
            # Save to database
            new_context = asdict(current_context)
            cursor.execute("""
                UPDATE session_states 
                SET session_context = %s 
                WHERE session_id = %s
            """, (Json(new_context), self.session_id))
            
            return current_context
    
    def get_agent_context(self) -> Optional[AgentContext]:
        """Get current agent context"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT agent_context FROM session_states WHERE session_id = %s",
                        (self.session_id,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        agent_dict = row['agent_context']
                        # Handle list format for processed_workflow_messages (stored as list in JSON)
                        if "processed_workflow_messages" in agent_dict and agent_dict["processed_workflow_messages"]:
                            # Keep as list for JSON compatibility
                            pass  # It's already a list from JSON
                        else:
                            agent_dict["processed_workflow_messages"] = []
                        
                        return AgentContext(**agent_dict)
                    return None
        except Exception as e:
            logger.error(f"Failed to get agent context: {e}")
            return None
    
    def update_agent_context(self, agent: str, **kwargs) -> AgentContext:
        """Update agent context with audit"""
        with self.state_transaction(agent) as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get current context
            cursor.execute(
                "SELECT agent_context FROM session_states WHERE session_id = %s FOR UPDATE",
                (self.session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Session {self.session_id} not found")
            
            agent_dict = row['agent_context']
            # Handle list format
            if "processed_workflow_messages" in agent_dict and agent_dict["processed_workflow_messages"]:
                # Keep as list for JSON compatibility
                pass  # It's already a list
            else:
                agent_dict["processed_workflow_messages"] = []
            
            current_context = AgentContext(**agent_dict)
            
            # Track agent switches
            if "current_agent" in kwargs and kwargs["current_agent"] != current_context.current_agent:
                current_context.last_agent_switch = datetime.now(timezone.utc).isoformat()
                self._audit_change(
                    "AGENT_SWITCH", "agent.current_agent", 
                    current_context.current_agent, kwargs["current_agent"], agent, conn
                )
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(current_context, key):
                    old_value = getattr(current_context, key)
                    setattr(current_context, key, value)
                    
                    if key != "current_agent":  # Already audited above
                        self._audit_change(
                            "UPDATE", f"agent.{key}", old_value, value, agent, conn
                        )
            
            # Save to database (ensure list format for JSON)
            context_dict = asdict(current_context)
            if "processed_workflow_messages" in context_dict:
                # Ensure it's a list (it should already be one)
                if not isinstance(context_dict["processed_workflow_messages"], list):
                    context_dict["processed_workflow_messages"] = list(context_dict["processed_workflow_messages"])
            
            cursor.execute("""
                UPDATE session_states 
                SET agent_context = %s 
                WHERE session_id = %s
            """, (Json(context_dict), self.session_id))
            
            return current_context
    
    def add_conversation_message(self, 
                               role: str, 
                               content: str, 
                               agent: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None,
                               tool_calls: Optional[List[Dict[str, Any]]] = None):
        """Add message to conversation history with proper indexing"""
        with self.state_transaction(agent) as conn:
            cursor = conn.cursor()
            
            # Get next message order
            cursor.execute("""
                SELECT COALESCE(MAX(message_order), 0) + 1 
                FROM conversation_messages 
                WHERE session_id = %s
            """, (self.session_id,))
            message_order = cursor.fetchone()[0]
            
            # Insert message
            cursor.execute("""
                INSERT INTO conversation_messages 
                (session_id, message_role, message_content, message_metadata, agent_name, tool_calls, message_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                self.session_id,
                role,
                content,
                Json(metadata or {}),
                agent,
                Json(tool_calls or []),
                message_order
            ))
            
            # Audit conversation update
            self._audit_change(
                "CONVERSATION_UPDATE", "conversation.message", None,
                {"role": role, "content": content[:100] + "..." if len(content) > 100 else content},
                agent, conn
            )
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT message_role, message_content, message_metadata, 
                               agent_name, tool_calls, created_at, message_order
                        FROM conversation_messages 
                        WHERE session_id = %s 
                        ORDER BY message_order DESC 
                        LIMIT %s
                    """, (self.session_id, limit))
                    
                    messages = cursor.fetchall()
                    return [dict(msg) for msg in reversed(messages)]  # Return in chronological order
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    def merge_langgraph_state(self, langgraph_state: Dict[str, Any], agent: str = "System"):
        """Merge state from LangGraph execution with atomic updates"""
        with self.state_transaction(agent) as conn:
            # Update session context from LangGraph state
            session_updates = {}
            for key in ["knowledge_base_id", "article_id", "user_intent", "task_context"]:
                if key in langgraph_state and langgraph_state[key] is not None:
                    session_updates[key] = langgraph_state[key]
            
            if session_updates:
                self.update_session_context(agent, **session_updates)
            
            # Update agent context
            agent_updates = {}
            for key in ["current_agent", "recursions", "consecutive_tool_calls", "last_tool_result"]:
                if key in langgraph_state:
                    agent_updates[key] = langgraph_state[key]
            
            # Handle processed workflow messages
            if "processed_workflow_messages" in langgraph_state:
                agent_updates["processed_workflow_messages"] = langgraph_state["processed_workflow_messages"]
            
            if agent_updates:
                self.update_agent_context(agent, **agent_updates)
            
            # Handle new messages
            if "messages" in langgraph_state:
                for msg in langgraph_state["messages"]:
                    if hasattr(msg, 'content') and hasattr(msg, '__class__'):
                        self.add_conversation_message(
                            role=msg.__class__.__name__,
                            content=msg.content,
                            agent=agent
                        )
    
    def to_langgraph_state(self) -> Dict[str, Any]:
        """Convert current state to LangGraph-compatible format"""
        state = {}
        
        # Get session context
        session_context = self.get_session_context()
        if session_context:
            state.update({
                "knowledge_base_id": session_context.knowledge_base_id,
                "article_id": session_context.article_id,
                "user_intent": session_context.user_intent,
                "task_context": session_context.task_context,
            })
        
        # Get agent context
        agent_context = self.get_agent_context()
        if agent_context:
            state.update({
                "current_agent": agent_context.current_agent,
                "agent_messages": agent_context.agent_messages,
                "recursions": agent_context.recursions,
                "consecutive_tool_calls": agent_context.consecutive_tool_calls,
                "last_tool_result": agent_context.last_tool_result,
                "processed_workflow_messages": agent_context.processed_workflow_messages,
            })
        
        # Add conversation history for context
        state["conversation_history"] = self.get_conversation_history(5)
        
        return state
    
    def _audit_change(self, change_type: str, change_path: str, old_value: Any, new_value: Any, 
                     agent: Optional[str] = None, conn=None):
        """Record state change in audit log"""
        should_close = False
        if conn is None:
            conn = self._get_connection()
            should_close = True
        
        try:
            cursor = conn.cursor()
            
            # Check if session exists before auditing
            cursor.execute("SELECT 1 FROM session_states WHERE session_id = %s", (self.session_id,))
            if cursor.fetchone():
                cursor.execute("""
                    INSERT INTO state_audit_log 
                    (session_id, change_type, change_path, old_value, new_value, agent_name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    self.session_id,
                    change_type,
                    change_path,
                    Json(old_value) if old_value is not None else None,
                    Json(new_value) if new_value is not None else None,
                    agent
                ))
                
                if should_close:
                    conn.commit()
            else:
                # Session doesn't exist yet, skip audit (will be done after session creation)
                pass
                
        except Exception as e:
            logger.error(f"Failed to audit change: {e}")
        finally:
            if should_close and conn:
                conn.close()
    
    def clear_session(self):
        """Clear session state with audit trail"""
        with self.state_transaction("System") as conn:
            cursor = conn.cursor()
            
            # Audit session deletion
            self._audit_change("DELETE", "session", {"session_id": self.session_id}, None, "System", conn)
            
            # Delete conversation messages
            cursor.execute("DELETE FROM conversation_messages WHERE session_id = %s", (self.session_id,))
            
            # Mark session as inactive rather than deleting (preserves audit trail)
            cursor.execute("""
                UPDATE session_states 
                SET is_active = FALSE, 
                    session_context = '{}', 
                    agent_context = %s
                WHERE session_id = %s
            """, (Json(asdict(AgentContext())), self.session_id))
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get comprehensive state summary for debugging"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get basic state info
                    cursor.execute("""
                        SELECT session_context, agent_context, created_at, updated_at, is_active
                        FROM session_states 
                        WHERE session_id = %s
                    """, (self.session_id,))
                    state_row = cursor.fetchone()
                    
                    # Get conversation count
                    cursor.execute("""
                        SELECT COUNT(*) as message_count,
                               MIN(created_at) as first_message,
                               MAX(created_at) as last_message
                        FROM conversation_messages 
                        WHERE session_id = %s
                    """, (self.session_id,))
                    conv_info = cursor.fetchone()
                    
                    # Get recent audit events
                    cursor.execute("""
                        SELECT COUNT(*) as change_count,
                               MAX(change_timestamp) as last_change
                        FROM state_audit_log 
                        WHERE session_id = %s
                    """, (self.session_id,))
                    audit_info = cursor.fetchone()
                    
                    return {
                        "session_id": self.session_id,
                        "is_active": state_row['is_active'] if state_row else False,
                        "session_context": state_row['session_context'] if state_row else None,
                        "agent_context": state_row['agent_context'] if state_row else None,
                        "created_at": state_row['created_at'] if state_row else None,
                        "updated_at": state_row['updated_at'] if state_row else None,
                        "conversation_stats": dict(conv_info) if conv_info else {},
                        "audit_stats": dict(audit_info) if audit_info else {}
                    }
        except Exception as e:
            logger.error(f"Failed to get state summary: {e}")
            return {"error": str(e)}
    
    def get_audit_trail(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent state changes for debugging and monitoring"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT change_type, change_path, old_value, new_value, 
                               agent_name, change_timestamp, correlation_id
                        FROM state_audit_log 
                        WHERE session_id = %s 
                        ORDER BY change_timestamp DESC 
                        LIMIT %s
                    """, (self.session_id, limit))
                    
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            return []
