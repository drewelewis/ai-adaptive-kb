"""
Multi-Agent Orchestrator with PostgreSQL State Management

This module integrates the robust PostgreSQL state manager with the multi-agent system,
providing persistent, transactional state management with audit trails and recovery capabilities.
"""

import os
import uuid
import warnings
from typing import Dict, Any, Optional, List
from datetime import datetime

# Suppress Pydantic warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')

from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, AIMessage
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    try:
        from langgraph import StateGraph, END
    except ImportError:
        from langgraph.graph.state import StateGraph
        from langgraph.constants import END
try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    from langgraph.checkpoint import MemorySaver

# Import existing agents
from .user_proxy_agent import UserProxyAgent
from .supervisor_agent import SupervisorAgent
from .content_management_agent import ContentManagementAgent
from .router_agent import RouterAgent
from .agent_types import AgentState

# Import new autonomous content creation agents
from .content_planner_agent import ContentPlannerAgent
from .content_creator_agent import ContentCreatorAgent
from .content_reviewer_agent import ContentReviewerAgent

# Import PostgreSQL state manager
from .postgresql_state_manager import PostgreSQLStateManager

# Import existing operations
from operations.knowledge_base_operations import KnowledgeBaseOperations

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

class Orchestrator:
    """
    Multi-agent orchestrator with PostgreSQL-backed state management
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        
        print(f"🚀 Initializing Multi-Agent System (Session: {self.session_id[:8]}...)")
        
        # Initialize PostgreSQL state manager
        try:
            self.state_manager = PostgreSQLStateManager(self.session_id)
            print("✅ PostgreSQL state management initialized")
        except Exception as e:
            print(f"❌ Failed to initialize PostgreSQL state manager: {e}")
            print("💡 Please ensure PostgreSQL is running and properly configured")
            raise
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv('OPENAI_API_ENDPOINT'),
            azure_deployment=os.getenv('OPENAI_API_MODEL_DEPLOYMENT_NAME'),
            api_version=os.getenv('OPENAI_API_VERSION'),
            streaming=True
        )
        
        # Initialize agents
        self.router = RouterAgent(self.llm)
        self.user_proxy = UserProxyAgent(self.llm)
        self.supervisor = SupervisorAgent(self.llm)
        self.content_manager = ContentManagementAgent(self.llm)
        
        # Initialize new autonomous content creation agents
        self.content_planner = ContentPlannerAgent(self.llm)
        self.content_creator = ContentCreatorAgent(self.llm)
        self.content_reviewer = ContentReviewerAgent(self.llm)
        
        # Initialize knowledge base operations
        self.kb_ops = KnowledgeBaseOperations()
        
        # Initialize LangGraph components
        self.memory = MemorySaver()
        self.graph = self._build_graph()
        
        print("🤖 Autonomous Content Creation System initialized!")
        print("Agents loaded: Router, UserProxy, Supervisor, ContentManagement")
        print("Content Creation: ContentPlanner, ContentCreator, ContentReviewer")
        print("State management: PostgreSQL with ACID transactions")
        
        # Initialize session if needed
        self._ensure_session_initialized()
    
    def _ensure_session_initialized(self):
        """Ensure session is properly initialized with knowledge base selection"""
        session_context = self.state_manager.get_session_context()
        
        if not session_context or not session_context.knowledge_base_id:
            print("\n🔍 Initializing knowledge base selection...")
            try:
                # Get available knowledge bases with their IDs
                knowledge_bases = self.kb_ops.get_knowledge_bases_with_ids()
                
                if not knowledge_bases:
                    print("⚠️  No knowledge bases found. Creating demo knowledge base...")
                    self._create_demo_kb()
                    kb_id = "1"  # Assume demo KB gets ID 1
                else:
                    # Format knowledge base list for display
                    kb_list = ", ".join([f"{kb['name']} (ID: {kb['id']})" for kb in knowledge_bases])
                    print(f"📚 Available knowledge bases: {kb_list}")
                    # Use the first available knowledge base ID
                    kb_id = knowledge_bases[0]["id"]
                    kb_name = knowledge_bases[0]["name"]
                    print(f"🎯 Auto-selecting knowledge base: {kb_name} (ID: {kb_id})")
                
                # Update session with selected knowledge base ID (not name!)
                self.state_manager.update_session_context(
                    agent="System",
                    knowledge_base_id=kb_id,  # Store the actual ID, not the name
                    conversation_state="active"
                )
                
                print(f"✅ Session initialized with knowledge base ID: {kb_id}")
                
            except Exception as e:
                print(f"❌ Failed to initialize knowledge base: {e}")
                print("💡 This likely means the PostgreSQL database is not running or configured.")
                raise
    
    def _create_demo_kb(self):
        """Create a demo knowledge base if none exists"""
        try:
            self.kb_ops.create_knowledge_base(
                name="demo",
                description="Demo knowledge base for testing",
                author_id=1  # Assuming a default user exists
            )
            print("✅ Demo knowledge base created")
        except Exception as e:
            print(f"⚠️  Could not create demo knowledge base: {e}")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with PostgreSQL state management and autonomous content creation"""
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent including new content creation agents
        workflow.add_node("UserProxy", self._process_user_proxy)
        workflow.add_node("Router", self._process_router)
        workflow.add_node("Supervisor", self._process_supervisor)
        workflow.add_node("ContentManagement", self._process_content_management)
        workflow.add_node("ContentPlanner", self._process_content_planner)
        workflow.add_node("ContentCreator", self._process_content_creator)
        workflow.add_node("ContentReviewer", self._process_content_reviewer)
        
        # Set entry point - UserProxy handles initial user input
        workflow.set_entry_point("UserProxy")
        
        # Add routing logic with autonomous content creation workflow
        workflow.add_conditional_edges(
            "UserProxy",
            self._route_from_user_proxy,
            {
                "Router": "Router",
                "UserProxy": "UserProxy", 
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "Router",
            self._route_from_router,
            {
                "UserProxy": "UserProxy",
                "Supervisor": "Supervisor", 
                "ContentManagement": "ContentManagement",
                "ContentPlanner": "ContentPlanner",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "Supervisor", 
            self._route_from_supervisor,
            {
                "UserProxy": "UserProxy",
                "ContentManagement": "ContentManagement",
                "ContentPlanner": "ContentPlanner",
                "ContentCreator": "ContentCreator",
                "ContentReviewer": "ContentReviewer",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "ContentPlanner",
            self._route_from_content_planner,
            {
                "UserProxy": "UserProxy",
                "ContentCreator": "ContentCreator",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "ContentCreator", 
            self._route_from_content_creator,
            {
                "ContentReviewer": "ContentReviewer",
                "ContentCreator": "ContentCreator",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "ContentReviewer",
            self._route_from_content_reviewer,
            {
                "UserProxy": "UserProxy",
                "ContentCreator": "ContentCreator", 
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "ContentManagement",
            self._route_from_content_management,
            {
                "UserProxy": "UserProxy", 
                "Supervisor": "Supervisor",
                "END": END
            }
        )
        
        return workflow.compile(checkpointer=self.memory)
    
    def _process_user_proxy(self, state: AgentState) -> AgentState:
        """Process UserProxy agent with simplified state management"""
        # Process with agent (no pre-sync to avoid deadlocks)
        result_state = self.user_proxy.process(state)
        return result_state
    
    def _process_router(self, state: AgentState) -> AgentState:
        """Process Router agent for intent classification and routing"""
        result_state = self.router.process(state)
        # Update PostgreSQL state with intent classification results
        if "user_intent" in result_state:
            # Convert percentage confidence to decimal (0-100 -> 0.0-1.0)
            raw_confidence = result_state.get("intent_confidence", 0.0)
            print(f"🔍 Raw confidence from router: {raw_confidence} (type: {type(raw_confidence)})")
            
            confidence = raw_confidence
            if confidence > 1.0:  # If it's a percentage, convert to decimal
                confidence = confidence / 100.0
                print(f"🔄 Converted confidence: {confidence} (type: {type(confidence)})")
            else:
                print(f"📌 Using confidence as-is: {confidence} (type: {type(confidence)})")
            
            user_intent = result_state["user_intent"]
            print(f"🔍 Updating session context: user_intent='{user_intent}', intent_confidence={confidence}")
            
            try:
                self.state_manager.update_session_context(
                    agent="Router",
                    user_intent=user_intent,
                    intent_confidence=confidence
                )
                print(f"✅ Session context updated successfully")
            except Exception as e:
                print(f"❌ Failed to update session context: {e}")
                # Don't re-raise - let the system continue
                print("⚠️ Continuing without session context update")
        return result_state
    
    def _process_supervisor(self, state: AgentState) -> AgentState:
        """Process Supervisor agent with simplified state management"""
        result_state = self.supervisor.process(state)
        return result_state
    
    def _process_content_management(self, state: AgentState) -> AgentState:
        """Process ContentManagement agent with simplified state management"""
        result_state = self.content_manager.process(state)
        return result_state
    
    def _route_from_user_proxy(self, state: AgentState) -> str:
        """Routing from UserProxy - route to Router for intent classification"""
        current_agent = state.get("current_agent")
        recursions = state.get("recursions", 0)
        
        print(f"🔀 UserProxy routing: current_agent={current_agent}, recursions={recursions}")
        
        # Check for termination conditions with PostgreSQL state
        session_context = self.state_manager.get_session_context()
        if session_context and session_context.conversation_state == "completed":
            print("🛑 Ending due to completed conversation state")
            return "END"
        
        if recursions >= 50:  # Prevent infinite loops
            print("🛑 Maximum recursions reached. Ending conversation.")
            self.state_manager.update_session_context(
                agent="System",
                conversation_state="completed"
            )
            return "END"
        
        # Route to Router for intent classification, or handle agent messages
        if current_agent == "Router":
            print("➡️ Routing to Router for intent classification")
            return "Router"
        elif current_agent == "UserProxy":
            # Check if there are agent messages to process
            agent_messages = state.get("agent_messages", [])
            my_messages = [msg for msg in agent_messages if msg.recipient == "UserProxy"]
            if my_messages:
                # Handle workflow completion messages
                print("📥 UserProxy processing agent messages")
                return "UserProxy"
            else:
                print("🏁 UserProxy ending workflow - no messages to process")
                return "END"
        else:
            print(f"🏁 Ending workflow (current_agent={current_agent})")
            return "END"
    
    def _route_from_router(self, state: AgentState) -> str:
        """Routing from Router based on intent classification"""
        current_agent = state.get("current_agent")
        recursions = state.get("recursions", 0)
        user_intent = state.get("user_intent", "general_inquiry")
        
        print(f"🔀 Router routing: current_agent={current_agent}, intent={user_intent}, recursions={recursions}")
        
        if recursions >= 50:
            print("🛑 Router: Maximum recursions reached")
            self.state_manager.update_session_context(
                agent="Router",
                conversation_state="completed"
            )
            return "END"
        
        # Route based on the determined target agent from Router
        if current_agent == "UserProxy":
            print("➡️ Router routing back to UserProxy for direct response")
            return "UserProxy"
        elif current_agent == "Supervisor":
            print("➡️ Router routing to Supervisor for workflow management")
            return "Supervisor"
        elif current_agent == "ContentManagement":
            print("➡️ Router routing to ContentManagement for KB operations")
            return "ContentManagement"
        elif current_agent == "ContentPlanner":
            print("➡️ Router routing to ContentPlanner for autonomous content creation")
            return "ContentPlanner"
        else:
            print(f"🏁 Router ending workflow (current_agent={current_agent})")
            return "END"
    
    def _route_from_supervisor(self, state: AgentState) -> str:
        """Routing from Supervisor"""
        current_agent = state.get("current_agent")
        recursions = state.get("recursions", 0)
        
        print(f"🔀 Supervisor routing: current_agent={current_agent}, recursions={recursions}")
        
        if recursions >= 50:
            print("🛑 Supervisor: Maximum recursions reached")
            self.state_manager.update_session_context(
                agent="Supervisor",
                conversation_state="completed"
            )
            return "END"
        
        if current_agent == "UserProxy":
            print("➡️ Supervisor routing to UserProxy")
            return "UserProxy"
        elif current_agent == "ContentManagement":
            print("➡️ Supervisor routing to ContentManagement")
            return "ContentManagement"
        else:
            print(f"🏁 Supervisor ending workflow (current_agent={current_agent})")
            return "END"
    
    def _route_from_content_management(self, state: AgentState) -> str:
        """Routing from ContentManagement"""
        current_agent = state.get("current_agent")
        recursions = state.get("recursions", 0)
        
        if recursions >= 50:
            self.state_manager.update_session_context(
                agent="ContentManagement",
                conversation_state="completed"
            )
            return "END"
        
        if current_agent == "UserProxy":
            return "UserProxy"
        elif current_agent == "Supervisor":
            return "Supervisor"
        else:
            return "END"
    
    def process_message(self, content: str, role: str = "user") -> Any:
        """Process a message with PostgreSQL state management"""
        print(f"\\n🎯 Processing {role} message: {content[:100]}...")
        
        # Update session state
        self.state_manager.update_session_context(
            agent="System",
            conversation_state="active"
        )
        
        # Add message to conversation history
        self.state_manager.add_conversation_message(
            role=role,
            content=content,
            agent="System"
        )
        
        # Configure LangGraph execution
        config = {"configurable": {"thread_id": self.session_id}}
        
        # Create LangChain message for current input
        if role == "user":
            current_message = HumanMessage(content=content)
        else:
            current_message = AIMessage(content=content)
        
        # Get conversation history from PostgreSQL (excluding the message we just added)
        conversation_history = self.state_manager.get_conversation_history(limit=50)
        
        # Debug: Show conversation history being loaded
        print(f"🔍 Loading {len(conversation_history)} messages from conversation history")
        for i, msg in enumerate(conversation_history[-3:]):  # Show last 3 messages
            role = msg['message_role']
            content = msg['message_content'][:50] + "..." if len(msg['message_content']) > 50 else msg['message_content']
            print(f"   {i+1}. {role}: {content}")
        
        # Convert PostgreSQL messages to LangChain format (excluding the current message we just added)
        langchain_messages = []
        for i, msg in enumerate(conversation_history):
            # Skip the very last message (which is the current user input we just added)
            if i < len(conversation_history) - 1:
                msg_role = msg['message_role']
                msg_content = msg['message_content']
                
                if msg_role == 'user':
                    langchain_messages.append(HumanMessage(content=msg_content))
                elif msg_role == 'assistant':
                    langchain_messages.append(AIMessage(content=msg_content))
        
        # Add current message to history
        langchain_messages.append(current_message)
        
        print(f"📋 Passing {len(langchain_messages)} messages to LangGraph agents")
        if len(langchain_messages) > 1:
            print(f"🔍 Previous messages in conversation:")
            for i, msg in enumerate(langchain_messages[:-1]):  # Don't show current message
                msg_type = "👤 User" if isinstance(msg, HumanMessage) else "🤖 Assistant"
                content_preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
                print(f"   {i+1}. {msg_type}: {content_preview}")
        
        # Get current state from PostgreSQL
        postgres_state = self.state_manager.to_langgraph_state()
        
        # Create initial LangGraph state with full conversation history
        initial_state = {
            "messages": langchain_messages,  # Full conversation history
            "recursions": 0,  # Always reset recursions for new user message
            "current_agent": "UserProxy",
            "agent_messages": [],
            "consecutive_tool_calls": 0,
            "last_tool_result": None,
            "processed_workflow_messages": [],  # Use list instead of set for JSON serialization
            **postgres_state  # Merge in PostgreSQL state
        }
        
        # Force reset recursions to 0 even if PostgreSQL has stale value
        initial_state["recursions"] = 0
        
        # Execute workflow
        try:
            print(f"🔄 Starting LangGraph execution with initial state: current_agent={initial_state.get('current_agent')}")
            
            events = self.graph.stream(
                initial_state,
                config,
                stream_mode="values",
            )
            
            final_state = None
            last_message = None
            event_count = 0
            
            for event in events:
                event_count += 1
                final_state = event
                current_agent = event.get("current_agent", "Unknown")
                print(f"📊 Event {event_count}: current_agent={current_agent}, messages={len(event.get('messages', []))}")
                
                if "messages" in event and event["messages"]:
                    last_message = event["messages"][-1]
                    if hasattr(last_message, 'content'):
                        print(f"💬 Last message: {last_message.content[:100]}...")
            
            print(f"🏁 LangGraph execution completed. Total events: {event_count}")
            
            if final_state:
                print(f"📈 Final state: current_agent={final_state.get('current_agent')}, recursions={final_state.get('recursions', 0)}")
            else:
                print("⚠️ No final state returned from LangGraph execution")
            
            # Update PostgreSQL with final state
            if final_state:
                self.state_manager.merge_langgraph_state(final_state, "System")
            
            # Save AI response to conversation history
            if last_message and hasattr(last_message, 'content'):
                self.state_manager.add_conversation_message(
                    role="assistant",
                    content=last_message.content,
                    agent="System"
                )
            
            # Print the response
            if last_message:
                if hasattr(last_message, 'pretty_print'):
                    last_message.pretty_print()
                else:
                    print(f"{last_message.__class__.__name__}: {last_message.content}")
            
            return last_message
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            self.state_manager.update_session_context(
                agent="System",
                conversation_state="error"
            )
            raise
    
    def clear_conversation_state(self):
        """Clear conversation state with PostgreSQL persistence and create new session"""
        try:
            # Clear PostgreSQL session
            self.state_manager.clear_session()
            
            # Generate new session ID to ensure completely fresh start
            old_session_id = self.session_id
            self.session_id = str(uuid.uuid4())
            
            print(f"🧹 Conversation state cleared (Old session: {old_session_id[:8]}..., New session: {self.session_id[:8]}...)")
            
            # Create new state manager with new session ID
            self.state_manager = PostgreSQLStateManager(self.session_id)
            
            # Clear LangGraph memory with new session
            self.memory = MemorySaver()
            
            # Re-initialize session with fresh context
            self._ensure_session_initialized()
            
            print("✅ Fresh session created - all conversation memory cleared")
            
        except Exception as e:
            print(f"❌ Error clearing conversation state: {e}")
            raise
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        return self.state_manager.get_state_summary()
    
    # ============================================================================
    # NEW AUTONOMOUS CONTENT CREATION AGENT PROCESSORS
    # ============================================================================
    
    def _process_content_planner(self, state: AgentState) -> AgentState:
        """Process ContentPlanner agent for strategic planning and structure design"""
        try:
            return self.content_planner.process(state)
        except Exception as e:
            print(f"❌ Error in ContentPlanner processing: {e}")
            state["error"] = str(e)
            return state
    
    def _process_content_creator(self, state: AgentState) -> AgentState:
        """Process ContentCreator agent for expert content generation"""
        try:
            return self.content_creator.process(state)
        except Exception as e:
            print(f"❌ Error in ContentCreator processing: {e}")
            state["error"] = str(e)
            return state
    
    def _process_content_reviewer(self, state: AgentState) -> AgentState:
        """Process ContentReviewer agent for quality assurance and optimization"""
        try:
            return self.content_reviewer.process(state)
        except Exception as e:
            print(f"❌ Error in ContentReviewer processing: {e}")
            state["error"] = str(e)
            return state
    
    # ============================================================================
    # NEW ROUTING METHODS FOR AUTONOMOUS CONTENT CREATION
    # ============================================================================
    
    def _route_from_content_planner(self, state: AgentState) -> str:
        """Route from ContentPlanner based on planning result"""
        current_agent = state.get("current_agent")
        
        if current_agent == "UserProxy":
            return "UserProxy"  # Clarification needed
        elif current_agent == "ContentCreator":
            return "ContentCreator"  # Proceed with content creation
        else:
            return "END"
    
    def _route_from_content_creator(self, state: AgentState) -> str:
        """Route from ContentCreator based on creation result"""
        current_agent = state.get("current_agent")
        
        if current_agent == "ContentReviewer":
            return "ContentReviewer"  # Send for review
        elif current_agent == "ContentCreator":
            return "ContentCreator"  # Continue creation (revision cycle)
        else:
            return "END"
    
    def _route_from_content_reviewer(self, state: AgentState) -> str:
        """Route from ContentReviewer based on review result"""
        current_agent = state.get("current_agent")
        
        if current_agent == "UserProxy":
            return "UserProxy"  # Final result ready
        elif current_agent == "ContentCreator":
            return "ContentCreator"  # Needs revision
        else:
            return "END"
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history from PostgreSQL"""
        return self.state_manager.get_conversation_history(limit)
    
    def get_audit_trail(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get state change audit trail"""
        return self.state_manager.get_audit_trail(limit)
    
    def debug_state(self):
        """Print comprehensive state debugging information"""
        print("\\n🔍 STATE DEBUGGING INFORMATION")
        print("=" * 60)
        
        # Session summary
        summary = self.get_session_summary()
        print("📊 Session Summary:")
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        print("\\n💬 Recent Conversation History:")
        history = self.get_conversation_history(5)
        for i, msg in enumerate(history):
            print(f"  {i+1}. [{msg['message_role']}] {msg['message_content'][:100]}...")
        
        print("\\n📋 Recent State Changes:")
        audit = self.get_audit_trail(5)
        for change in audit:
            print(f"  {change['change_timestamp']} - {change['change_type']} - {change['change_path']} by {change['agent_name']}")
        
        print("=" * 60)
