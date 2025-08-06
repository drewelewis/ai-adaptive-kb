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
                "end": END,
                "continue": "user_proxy_node"
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
        # Check recursion limit
        if state["recursions"] >= self.max_recursions:
            print(f"⚠ Recursion limit of {self.max_recursions} reached")
            return {
                "messages": [AIMessage(content=f"I've reached the maximum recursion limit of {self.max_recursions}. Please start a new conversation.")],
                "recursions": state["recursions"]
            }
        
        print(f"🗣 UserProxy processing... (recursion: {state['recursions']})")
        
        # Set current agent
        state["current_agent"] = "UserProxy"
        
        # Process with User Proxy Agent
        updated_state = self.user_proxy.process(state)
        
        # Increment recursion count
        updated_state["recursions"] = state["recursions"] + 1
        
        return updated_state
    
    def _supervisor_node(self, state: AgentState) -> AgentState:
        """Supervisor Agent node"""
        print(f"🎯 Supervisor coordinating... (recursion: {state['recursions']})")
        
        # Set current agent
        state["current_agent"] = "Supervisor"
        
        # Check if this is a response from Content Management
        agent_messages = state.get("agent_messages", [])
        cm_responses = [msg for msg in agent_messages if msg.sender == "ContentManagement" and msg.recipient == "Supervisor"]
        
        if cm_responses:
            # Process CM response
            latest_cm_response = cm_responses[-1]
            updated_state = self.supervisor.process_cm_response(state, latest_cm_response)
        else:
            # Process initial request
            updated_state = self.supervisor.process(state)
        
        # Increment recursion count
        updated_state["recursions"] = state["recursions"] + 1
        
        return updated_state
    
    def _content_management_node(self, state: AgentState) -> AgentState:
        """Content Management Agent node"""
        print(f"📚 ContentManagement executing... (recursion: {state['recursions']})")
        
        # Set current agent
        state["current_agent"] = "ContentManagement"
        
        # Process with Content Management Agent
        updated_state = self.content_manager.process(state)
        
        # Increment recursion count
        updated_state["recursions"] = state["recursions"] + 1
        
        return updated_state
    
    def _route_from_user_proxy(self, state: AgentState) -> str:
        """Route decisions from User Proxy Agent"""
        # Check if UserProxy sent a message to Supervisor
        agent_messages = state.get("agent_messages", [])
        supervisor_messages = [msg for msg in agent_messages if msg.recipient == "Supervisor" and msg.sender == "UserProxy"]
        
        if supervisor_messages:
            return "supervisor"
        
        # Check if there are new messages indicating conversation continuation
        messages = state.get("messages", [])
        if messages and hasattr(messages[-1], '__class__') and messages[-1].__class__.__name__ == 'AIMessage':
            return "end"
        
        return "continue"
    
    def _route_from_supervisor(self, state: AgentState) -> str:
        """Route decisions from Supervisor Agent"""
        # Check the most recent agent message to determine routing
        agent_messages = state.get("agent_messages", [])
        
        if not agent_messages:
            return "end"
        
        latest_message = agent_messages[-1]
        
        if latest_message.sender == "Supervisor":
            if latest_message.recipient == "ContentManagement":
                return "content_management"
            elif latest_message.recipient == "UserProxy":
                return "user_proxy"
        
        return "end"
    
    def _route_from_content_management(self, state: AgentState) -> str:
        """Route decisions from Content Management Agent"""
        # Content Management always routes back to Supervisor for coordination
        agent_messages = state.get("agent_messages", [])
        
        if agent_messages:
            latest_message = agent_messages[-1]
            if latest_message.sender == "ContentManagement" and latest_message.recipient == "Supervisor":
                return "supervisor"
        
        return "end"
    
    def stream_graph_updates(self, role: str, content: str) -> BaseMessage:
        """Stream graph updates and return the final message"""
        config = {"configurable": {"thread_id": "1"}}
        
        events = self.graph.stream(
            {
                "messages": [{"role": role, "content": content}],
                "recursions": 0,
                "current_agent": "UserProxy",
                "agent_messages": [],
                "user_intent": None,
                "knowledge_base_id": None,
                "task_context": None,
                "session_data": {}
            },
            config,
            stream_mode="values",
        )
        
        last_message = None
        
        for event in events:
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
        
        return last_message
    
    def clear_conversation_state(self):
        """Clear all conversation state from memory"""
        try:
            # Clear the memory saver by creating a new instance
            self.memory = MemorySaver()
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
