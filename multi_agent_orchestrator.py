import os
import datetime
from typing import Annotated, Dict, Any
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from agents.agent_types import AgentState, AgentMessage
from agents.user_proxy_agent import UserProxyAgent
from agents.supervisor_agent import SupervisorAgent
from agents.content_management_agent import ContentManagementAgent
from utils.langgraph_utils import save_graph
from dotenv import load_dotenv

load_dotenv(override=True)


class MultiAgentOrchestrator:
    """
    Multi-Agent Orchestrator for the AI Adaptive Knowledge Base system.
    Coordinates between UserProxy, Supervisor, and ContentManagement agents.
    """
    
    def __init__(self):
        self.max_recursions = 25
        self.current_recursion = 0
        
        # Initialize persistent session state
        self.session_state = {
            "knowledge_base_id": None,
            "article_id": None,
            "user_intent": None,
            "task_context": None,
            "session_data": {},
            "kb_selection_completed": False,  # Track if initial KB selection is done
        }
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv('OPENAI_API_ENDPOINT'),
            azure_deployment=os.getenv('OPENAI_API_MODEL_DEPLOYMENT_NAME'),
            api_version=os.getenv('OPENAI_API_VERSION'),
            streaming=True
        )
        
        # Initialize agents
        self.user_proxy = UserProxyAgent(self.llm)
        self.supervisor = SupervisorAgent(self.llm)
        self.content_manager = ContentManagementAgent(self.llm)
        
        # Initialize memory and build graph
        self.memory = MemorySaver()
        self.graph = self._build_graph()
        
        print("🤖 Multi-Agent Knowledge Base System initialized!")
        print("Agents loaded: UserProxy, Supervisor, ContentManagement")
        
        # Prompt for KB selection immediately after initialization
        self._initialize_knowledge_base_context()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for multi-agent coordination"""
        graph_builder = StateGraph(AgentState)
        
        # Add agent nodes
        graph_builder.add_node("user_proxy_node", self._user_proxy_node)
        graph_builder.add_node("supervisor_node", self._supervisor_node)
        graph_builder.add_node("content_management_node", self._content_management_node)
        
        # Set entry point
        graph_builder.add_edge(START, "user_proxy_node")
        
        # Add conditional edges for agent routing
        graph_builder.add_conditional_edges(
            "user_proxy_node",
            self._route_from_user_proxy,
            {
                "supervisor": "supervisor_node",
                "end": END
            }
        )
        
        graph_builder.add_conditional_edges(
            "supervisor_node", 
            self._route_from_supervisor,
            {
                "content_management": "content_management_node",
                "user_proxy": "user_proxy_node",
                "end": END
            }
        )
        
        graph_builder.add_conditional_edges(
            "content_management_node",
            self._route_from_content_management,
            {
                "supervisor": "supervisor_node",
                "user_proxy": "user_proxy_node", 
                "end": END
            }
        )
        
        # Compile graph with memory
        graph = graph_builder.compile(checkpointer=self.memory)
        
        # Save graph visualization
        image_path = __file__.replace(".py", ".png")
        save_graph(image_path, graph)
        
        return graph
    
    def _user_proxy_node(self, state: AgentState) -> AgentState:
        """User Proxy Agent node"""
        consecutive_calls = state.get("consecutive_tool_calls", 0)
        
        # Check recursion limit
        if state["recursions"] >= self.max_recursions:
            print(f"⚠ Recursion limit of {self.max_recursions} reached")
            return {
                "messages": [AIMessage(content=f"I've reached the maximum recursion limit of {self.max_recursions}. Please start a new conversation.")],
                "recursions": state["recursions"]
            }
        
        # Check for too many consecutive tool calls (loop prevention)
        if consecutive_calls >= 4:
            print(f"⚠ Stopping due to {consecutive_calls} consecutive tool calls (likely loop)")
            return {
                "messages": [AIMessage(content="I've detected potential loop behavior with repeated tool calls. Please start a new conversation or try a different approach.")],
                "recursions": state["recursions"]
            }
        
        print(f"🗣 UserProxy processing... (recursion: {state['recursions']}, consecutive calls: {consecutive_calls})")
        
        # Set current agent
        state["current_agent"] = "UserProxy"
        
        # Process with User Proxy Agent
        updated_state = self.user_proxy.process(state)
        
        # Increment recursion count
        updated_state["recursions"] = state["recursions"] + 1
        
        return updated_state
    
    def _supervisor_node(self, state: AgentState) -> AgentState:
        """Supervisor Agent node"""
        consecutive_calls = state.get("consecutive_tool_calls", 0)
        
        # Loop prevention check
        if consecutive_calls >= 4:
            print(f"⚠ Supervisor stopping due to {consecutive_calls} consecutive tool calls")
            return {
                "messages": [AIMessage(content="I've detected potential loop behavior. Please try a different approach.")],
                "recursions": state["recursions"]
            }
        
        print(f"🎯 Supervisor coordinating... (recursion: {state['recursions']}, consecutive calls: {consecutive_calls})")
        
        # Set current agent
        state["current_agent"] = "Supervisor"
        
        # Check if this is a response from Content Management
        agent_messages = state.get("agent_messages", [])
        
        # Look for the most recent message to determine what the Supervisor should do
        if agent_messages:
            latest_message = agent_messages[-1]
            # If the latest message is FROM ContentManagement TO Supervisor, process the response
            if latest_message.sender == "ContentManagement" and latest_message.recipient == "Supervisor":
                updated_state = self.supervisor.process_cm_response(state, latest_message)
            # If the latest message is FROM UserProxy TO Supervisor, process the initial request
            elif latest_message.sender == "UserProxy" and latest_message.recipient == "Supervisor":
                updated_state = self.supervisor.process(state)
            else:
                # No relevant messages for Supervisor
                return state
        else:
            # Process initial request
            updated_state = self.supervisor.process(state)
        
        # Increment recursion count
        updated_state["recursions"] = state["recursions"] + 1
        
        return updated_state
    
    def _content_management_node(self, state: AgentState) -> AgentState:
        """Content Management Agent node"""
        consecutive_calls = state.get("consecutive_tool_calls", 0)
        
        # Loop prevention check  
        if consecutive_calls >= 4:
            print(f"⚠ ContentManagement stopping due to {consecutive_calls} consecutive tool calls")
            return {
                "messages": [AIMessage(content="I've detected potential loop behavior in content operations. Please try a different approach.")],
                "recursions": state["recursions"]
            }
        
        print(f"📚 ContentManagement executing... (recursion: {state['recursions']}, consecutive calls: {consecutive_calls})")
        
        # Set current agent
        state["current_agent"] = "ContentManagement"
        
        # Process with Content Management Agent
        updated_state = self.content_manager.process(state)
        
        # Increment recursion count
        updated_state["recursions"] = state["recursions"] + 1
        
        return updated_state
    
    def _route_from_user_proxy(self, state: AgentState) -> str:
        """Route decisions from User Proxy Agent"""
        # Get the latest message
        messages = state.get("messages", [])
        if not messages:
            print("🔄 UserProxy routing: No messages, ending")
            return "end"
        
        last_message = messages[-1]
        message_type = last_message.__class__.__name__ if hasattr(last_message, '__class__') else type(last_message).__name__
        
        # Check if UserProxy sent a new message to Supervisor 
        agent_messages = state.get("agent_messages", [])
        supervisor_messages = [msg for msg in agent_messages if msg.recipient == "Supervisor" and msg.sender == "UserProxy"]
        
        # Only route to supervisor if there's a new unprocessed message and it's a HumanMessage
        if supervisor_messages and message_type == 'HumanMessage':
            print(f"🔄 UserProxy routing: Found supervisor message for HumanMessage, routing to supervisor")
            return "supervisor"
        
        # If the last message is an AIMessage (response from AI), END to wait for new user input
        # This prevents infinite loops and allows the chat interface to handle the next user input
        if message_type == 'AIMessage':
            print(f"🔄 UserProxy routing: Last message is AIMessage, ENDING conversation (waiting for user input)")
            return "end"  # End the conversation to wait for new user input
        
        # For other message types, continue with UserProxy
        print(f"🔄 UserProxy routing: Continuing with UserProxy (message type: {message_type})")
        return "user_proxy"
    
    def _route_from_supervisor(self, state: AgentState) -> str:
        """Route decisions from Supervisor Agent"""
        # Check the most recent agent message to determine routing
        agent_messages = state.get("agent_messages", [])
        
        if not agent_messages:
            print("🔄 Supervisor routing: No agent messages, ending")
            return "end"
        
        latest_message = agent_messages[-1]
        
        if latest_message.sender == "Supervisor":
            if latest_message.recipient == "ContentManagement":
                print("🔄 Supervisor routing: Routing to ContentManagement")
                return "content_management"
            elif latest_message.recipient == "UserProxy":
                print("🔄 Supervisor routing: Routing to UserProxy")
                return "user_proxy"
        
        print(f"🔄 Supervisor routing: Default case, ending (latest sender: {latest_message.sender})")
        return "end"
    
    def _route_from_content_management(self, state: AgentState) -> str:
        """Route decisions from Content Management Agent"""
        # Content Management always routes back to Supervisor for coordination
        agent_messages = state.get("agent_messages", [])
        
        if agent_messages:
            latest_message = agent_messages[-1]
            if latest_message.sender == "ContentManagement" and latest_message.recipient == "Supervisor":
                print("🔄 ContentManagement routing: Routing back to Supervisor")
                return "supervisor"
        
        print("🔄 ContentManagement routing: Default case, ending")
        return "end"
    
    def _initialize_knowledge_base_context(self):
        """Initialize knowledge base context immediately after system startup"""
        print("\n" + "=" * 80)
        print("📚 KNOWLEDGE BASE INITIALIZATION")
        print("=" * 80)
        
        kb_selection_result = self.prompt_kb_selection()
        
        if kb_selection_result == "session_cancelled":
            print("👋 Session cancelled. Exiting system...")
            exit(0)
        elif kb_selection_result in ["kb_context_failed", "kb_creation_failed"]:
            print("❌ Unable to set up knowledge base context.")
            print("💡 Continuing in demo mode - some features may not work.")
            self.session_state["kb_selection_completed"] = True
            self.session_state["knowledge_base_id"] = "demo"
        elif kb_selection_result == "demo_mode_enabled":
            print("✅ Demo mode enabled - you can continue without a real knowledge base.")
        
        print("=" * 80)
        print("🎉 System ready! You can now interact with the AI assistant.")
        print("=" * 80)

    def prompt_kb_selection(self) -> str:
        """Prompt user to select a knowledge base or create a new one"""
        try:
            print("🔄 Initializing knowledge base tools...")
            # Use the ContentManagement agent to get available knowledge bases
            from tools.knowledge_base_tools import KnowledgeBaseTools
            
            print("🔄 Retrieving available knowledge bases...")
            kb_tool = KnowledgeBaseTools.KnowledgeBaseGetKnowledgeBases()
            
            # Get available knowledge bases with timeout/error handling
            try:
                kb_list_result = kb_tool._run()
            except Exception as db_error:
                print(f"❌ Database connection error: {db_error}")
                print("💡 This likely means the PostgreSQL database is not running or configured.")
                print("❌ Unable to retrieve knowledge bases due to database connectivity issues.")
                print("Would you like to create a new knowledge base? (y/n): ", end="")
                try:
                    create_new = input().strip().lower()
                    if create_new in ['y', 'yes']:
                        return self._create_new_kb_workflow()
                    else:
                        return "session_cancelled"
                except KeyboardInterrupt:
                    print("\n👋 Session cancelled by user.")
                    return "session_cancelled"
            
            if "Error" in str(kb_list_result) or not kb_list_result:
                print("❌ Unable to retrieve knowledge bases.")
                print("Would you like to create a new knowledge base? (y/n): ", end="")
                try:
                    create_new = input().strip().lower()
                    if create_new in ['y', 'yes']:
                        return self._create_new_kb_workflow()
                    else:
                        return "session_cancelled"
                except KeyboardInterrupt:
                    print("\n👋 Session cancelled by user.")
                    return "session_cancelled"
            
            print("\n" + "=" * 60)
            print("📚 KNOWLEDGE BASE SELECTION")
            print("=" * 60)
            print(kb_list_result)
            print("\n💡 Options:")
            print("   • Enter KB ID to use existing knowledge base")
            print("   • Type 'new' to create a new knowledge base")
            print("   • Type 'cancel' to exit")
            print("=" * 60)
            
            while True:
                try:
                    choice = input("\n📋 Your choice: ").strip()
                    
                    if choice.lower() == 'cancel':
                        return "session_cancelled"
                    elif choice.lower() == 'new':
                        return self._create_new_kb_workflow()
                    elif choice.isdigit():
                        # User selected existing KB
                        kb_id = choice
                        return self._set_kb_context(kb_id)
                    else:
                        print("❌ Invalid choice. Please enter a KB ID number, 'new', or 'cancel'.")
                except KeyboardInterrupt:
                    print("\n👋 Session cancelled by user.")
                    return "session_cancelled"
                    
        except ImportError as import_error:
            print(f"❌ Import error during KB selection: {import_error}")
            print("💡 This suggests there's an issue with the knowledge base tools module.")
            print("🔄 Enabling demo mode without database connectivity...")
            self.session_state["kb_selection_completed"] = True
            self.session_state["knowledge_base_id"] = "demo"
            print("✅ Demo mode enabled - you can continue without a real knowledge base.")
            return "demo_mode_enabled"
        except Exception as e:
            print(f"❌ Unexpected error during KB selection: {e}")
            print("💡 Please check your database configuration and try again.")
            print("🔄 Enabling demo mode without database connectivity...")
            self.session_state["kb_selection_completed"] = True
            self.session_state["knowledge_base_id"] = "demo"
            print("✅ Demo mode enabled - you can continue without a real knowledge base.")
            return "demo_mode_enabled"
    
    def _create_new_kb_workflow(self) -> str:
        """Handle new knowledge base creation workflow"""
        try:
            print("\n📝 Creating New Knowledge Base")
            print("-" * 40)
            name = input("📋 Knowledge Base Name: ").strip()
            if not name:
                print("❌ Name is required.")
                return "session_cancelled"
                
            description = input("📋 Description (optional): ").strip()
            
            # Use the system to create the KB
            create_message = f"create knowledge base named '{name}'"
            if description:
                create_message += f" with description '{description}'"
                
            print(f"\n🔄 Creating knowledge base: {name}")
            result = self._process_kb_creation(create_message)
            return result
            
        except KeyboardInterrupt:
            print("\n👋 KB creation cancelled by user.")
            return "session_cancelled"
    
    def _set_kb_context(self, kb_id: str) -> str:
        """Set knowledge base context"""
        try:
            from tools.knowledge_base_tools import KnowledgeBaseTools
            context_tool = KnowledgeBaseTools.KnowledgeBaseSetContext()
            
            result = context_tool._run(knowledge_base_id=kb_id)
            
            # Handle dictionary response from the tool
            if isinstance(result, dict):
                if result.get("success", False):
                    self.session_state["knowledge_base_id"] = kb_id
                    self.session_state["kb_selection_completed"] = True
                    print(f"✅ {result.get('message', 'KB context set successfully')}")
                    return "kb_context_set"
                else:
                    error_msg = result.get("error", "Unknown error setting KB context")
                    print(f"❌ Failed to set KB context: {error_msg}")
                    return "kb_context_failed"
            elif isinstance(result, str):
                # Handle string response (fallback)
                if "successfully set" in result.lower():
                    self.session_state["knowledge_base_id"] = kb_id
                    self.session_state["kb_selection_completed"] = True
                    print(f"✅ {result}")
                    return "kb_context_set"
                else:
                    print(f"❌ Failed to set KB context: {result}")
                    return "kb_context_failed"
            else:
                print(f"❌ Unexpected response type from KB context tool: {type(result)}")
                return "kb_context_failed"
                
        except Exception as e:
            print(f"❌ Error setting KB context: {e}")
            return "kb_context_failed"
    
    def _process_kb_creation(self, create_message: str) -> str:
        """Process knowledge base creation through the agent system"""
        try:
            # Process the creation message through our system
            result = self.stream_graph_updates("user", create_message)
            
            # Check if creation was successful by looking at session state
            if self.session_state.get("knowledge_base_id"):
                self.session_state["kb_selection_completed"] = True
                return "kb_created_and_set"
            else:
                return "kb_creation_failed"
                
        except Exception as e:
            print(f"❌ Error creating KB: {e}")
            return "kb_creation_failed"

    def stream_graph_updates(self, role: str, content: str) -> BaseMessage:
        """Stream graph updates and return the final message"""
        
        # KB selection is now handled during initialization, so we can proceed directly
        config = {"configurable": {"thread_id": "1"}}
        
        # Create proper LangChain message based on role
        if role == "user":
            message = HumanMessage(content=content)
        else:
            message = AIMessage(content=content)
        
        # Use persistent session state instead of resetting everything
        initial_state = {
            "messages": [message],
            "recursions": 0,
            "current_agent": "UserProxy",
            "agent_messages": [],
            "consecutive_tool_calls": 0,  # Initialize loop prevention tracking
            "last_tool_result": None,  # Initialize tool result tracking
            "user_intent": self.session_state.get("user_intent"),
            "knowledge_base_id": self.session_state.get("knowledge_base_id"),
            "article_id": self.session_state.get("article_id"),
            "task_context": self.session_state.get("task_context"),
            "session_data": self.session_state.get("session_data", {}),
            "processed_workflow_messages": []
        }
        
        events = self.graph.stream(
            initial_state,
            config,
            stream_mode="values",
        )
        
        last_message = None
        final_state = None
        
        for event in events:
            final_state = event  # Keep track of final state
            if "messages" in event:
                last_message = event["messages"][-1]
                
                # Only print non-tool messages (hide tool calls and tool responses)
                if hasattr(last_message, '__class__'):
                    message_type = last_message.__class__.__name__
                    if message_type in ['ToolMessage']:
                        continue  # Skip tool messages
                
                # Skip AI messages that contain tool calls (but show the final response)
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    continue
                    
                # Print all other messages (user messages and AI responses without tool calls)
                if hasattr(last_message, 'pretty_print'):
                    last_message.pretty_print()
                else:
                    print(f"{last_message.__class__.__name__}: {last_message.content}")
        
        # Update persistent session state with final values
        if final_state:
            self.session_state["knowledge_base_id"] = final_state.get("knowledge_base_id")
            self.session_state["article_id"] = final_state.get("article_id")
            self.session_state["user_intent"] = final_state.get("user_intent")
            self.session_state["task_context"] = final_state.get("task_context")
            self.session_state["session_data"] = final_state.get("session_data", {})
        
        return last_message
    
    def clear_conversation_state(self):
        """Clear all conversation state from memory"""
        try:
            # Clear the memory saver by creating a new instance
            self.memory = MemorySaver()
            
            # Clear persistent session state
            self.session_state = {
                "knowledge_base_id": None,
                "article_id": None,
                "user_intent": None,
                "task_context": None,
                "session_data": {},
                "kb_selection_completed": False,  # Reset KB selection requirement
            }
            
            print("✅ Conversation state and knowledge base context cleared.")
            # Rebuild the graph with the new memory
            self.graph = self._build_graph()
            print("✓ Multi-agent conversation state cleared successfully.")
            print("✓ All agent memories reset complete.")
            print("✓ Ready for new conversation.")
        except Exception as e:
            print(f"⚠ Error clearing multi-agent state: {e}")
            print("You may need to restart the application for a complete reset.")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status information about all agents"""
        return {
            "user_proxy": {
                "name": self.user_proxy.name,
                "tools_count": len(self.user_proxy.tools),
                "status": "active"
            },
            "supervisor": {
                "name": self.supervisor.name,
                "tools_count": len(self.supervisor.tools),
                "status": "active"
            },
            "content_manager": {
                "name": self.content_manager.name,
                "tools_count": len(self.content_manager.tools),
                "status": "active"
            },
            "total_agents": 3,
            "max_recursions": self.max_recursions
        }
