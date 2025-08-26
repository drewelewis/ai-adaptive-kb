import sys
import os
import datetime
import warnings
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Literal

# Suppress Pydantic warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')

# Import required agents for direct communication
from agents.user_proxy_agent import UserProxyAgent
from agents.supervisor_agent import SupervisorAgent
from agents.content_management_agent import ContentManagementAgent
from agents.postgresql_state_manager import PostgreSQLStateManager
from agents.agent_types import AgentState, AgentMessage
from config.model_config import ModelConfig

load_dotenv(override=True)

class SimplifiedMultiAgentChat:
    """Simplified multi-agent chat with direct UserProxy-Supervisor-ContentManagement communication."""
    
    def __init__(self):
        # Generate session ID first
        self.current_session_id = self._generate_session_id()
        # Initialize state manager with session ID
        self.state_manager = PostgreSQLStateManager(self.current_session_id)
        # Initialize model configuration
        self.model_config = ModelConfig()
        self.user_proxy = None
        self.supervisor = None
        self.content_management = None
        self.conversation_history = []
        self.current_state = AgentState()
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid
        return str(uuid.uuid4())
        
    def initialize_agents(self) -> None:
        """Initialize UserProxy, Supervisor, and ContentManagement agents with direct communication."""
        try:
            print("🔄 Initializing simplified chat system...")
            
            # Initialize UserProxy agent with LLM
            user_llm = self.model_config.get_standard_model()
            self.user_proxy = UserProxyAgent(llm=user_llm)
            
            # Initialize Supervisor agent with LLM
            supervisor_llm = self.model_config.get_premium_model()
            self.supervisor = SupervisorAgent(llm=supervisor_llm)
            
            # Initialize ContentManagement agent with LLM  
            content_llm = self.model_config.get_premium_model()
            self.content_management = ContentManagementAgent(llm=content_llm)
            
            # Initialize agent state with required fields
            self.current_state = {
                "messages": [],
                "current_agent": "UserProxy",
                "user_intent": None,
                "knowledge_base_id": None,
                "article_id": None,
                "current_section": None,
                "agent_messages": [],
                "recursions": 0,
                "consecutive_tool_calls": 0,
                "last_tool_result": None,
                "session_id": self.current_session_id,
                "conversation_history": []
            }
            
            print("✅ Agents initialized: UserProxy → Supervisor (direct communication)")
            
        except Exception as e:
            print(f"❌ Failed to initialize agents: {e}")
            raise
    
    def get_or_create_session(self) -> str:
        """Get the current session ID."""
        return self.current_session_id
    
    def process_user_message(self, user_input: str) -> str:
        """Process user message through simplified UserProxy → Supervisor flow."""
        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Update agent state with user message
            from langchain_core.messages import HumanMessage
            user_message = HumanMessage(content=user_input)
            self.current_state["messages"].append(user_message)
            self.current_state["user_intent"] = user_input
            self.current_state["conversation_history"] = self.conversation_history
            self.current_state["current_agent"] = "UserProxy"
            
            # UserProxy processes the user input
            print("👤 UserProxy processing user request...")
            try:
                user_proxy_state = self.user_proxy.process(self.current_state)
                
                # CRITICAL FIX: Check if UserProxy completed the workflow
                if user_proxy_state.get("workflow_completed"):
                    print("✅ Workflow completed by UserProxy, stopping processing")
                    final_state = user_proxy_state
                else:
                    # Update state and forward to Supervisor
                    print("👑 Supervisor coordinating response...")
                    user_proxy_state["current_agent"] = "Supervisor"
                    supervisor_state = self.supervisor.process(user_proxy_state)
                    
                    # Check if Supervisor delegated to ContentManagement
                    if supervisor_state.get("current_agent") == "ContentManagement":
                        print("🔧 ContentManagement executing request...")
                        supervisor_state["current_agent"] = "ContentManagement"
                        content_state = self.content_management.process(supervisor_state)
                        
                        # ContentManagement should route back to Supervisor for review
                        if content_state.get("current_agent") == "Supervisor":
                            print("👑 Supervisor reviewing ContentManagement work...")
                            final_state = self.supervisor.process(content_state)
                        else:
                            final_state = content_state
                    else:
                        final_state = supervisor_state
                
                # Extract response from final state
                final_response = self._extract_response_from_state(final_state)
                
                # Update current state
                self.current_state = final_state
                
            except Exception as agent_error:
                print(f"⚠️ Agent processing error: {agent_error}")
                # Fallback to direct LLM response
                final_response = f"I encountered an issue processing your request: {user_input}. The system is working but may need configuration. Error: {agent_error}"
            
            # Add response to conversation history
            self.conversation_history.append({
                "role": "assistant", 
                "content": final_response,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            return final_response
            
        except Exception as e:
            error_msg = f"❌ Error processing message: {e}"
            print(error_msg)
            return error_msg
    
    def _extract_response_from_state(self, state: AgentState) -> str:
        """Extract the response content from agent state."""
        try:
            # First check for agent messages to UserProxy (workflow completions)
            agent_messages = state.get("agent_messages", [])
            user_proxy_messages = [msg for msg in agent_messages if msg.recipient == "UserProxy"]
            
            if user_proxy_messages:
                latest_message = user_proxy_messages[-1]
                if latest_message.message_type in ["workflow_complete", "workflow_error"]:
                    return latest_message.content
            
            # Check for messages in state
            if "messages" in state and state["messages"]:
                last_message = state["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict) and 'content' in last_message:
                    return last_message['content']
                else:
                    return str(last_message)
            
            # Check for response field
            if "response" in state:
                return str(state["response"])
            
            # Check for current_agent_response
            if "current_agent_response" in state:
                return str(state["current_agent_response"])
            
            # Fallback to generic message
            return "Processing completed successfully."
            
        except Exception as e:
            return f"Error extracting response: {e}"
    
    def get_session_summary(self) -> Optional[Dict[str, Any]]:
        """Get current session summary."""
        try:
            if self.current_session_id:
                return {
                    "session_id": self.current_session_id,
                    "is_active": True,
                    "agents": ["UserProxy", "Supervisor"],
                    "conversation_stats": {
                        "message_count": len(self.conversation_history),
                        "user_messages": len([msg for msg in self.conversation_history if msg["role"] == "user"]),
                        "assistant_messages": len([msg for msg in self.conversation_history if msg["role"] == "assistant"])
                    }
                }
            return None
        except Exception as e:
            print(f"Error getting session summary: {e}")
            return None
    
    def clear_conversation_state(self) -> None:
        """Clear conversation state."""
        try:
            self.conversation_history.clear()
            if self.current_session_id:
                self.state_manager.clear_session_state(self.current_session_id)
            print("✅ Conversation state cleared")
        except Exception as e:
            print(f"Error clearing state: {e}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of active agents."""
        return {
            "total_agents": 2,
            "user_proxy": {
                "name": "UserProxy Agent",
                "status": "active" if self.user_proxy else "inactive",
                "tools_count": len(getattr(self.user_proxy, 'tools', [])) if self.user_proxy else 0
            },
            "supervisor": {
                "name": "Supervisor Agent", 
                "status": "active" if self.supervisor else "inactive",
                "tools_count": len(getattr(self.supervisor, 'tools', [])) if self.supervisor else 0
            }
        }

    def create_knowledge_base_interactive(self) -> str:
        """Interactive knowledge base creation through the chat system."""
        try:
            print("📝 Let's create a new Knowledge Base!")
            
            # Get KB details from user
            kb_name = input("📚 Enter Knowledge Base name: ").strip()
            if not kb_name:
                return "❌ Knowledge Base name is required."
            
            kb_description = input("📄 Enter Knowledge Base description: ").strip()
            if not kb_description:
                return "❌ Knowledge Base description is required."
            
            create_gitlab = input("🔗 Create GitLab project? (y/n, default: y): ").strip().lower()
            create_gitlab_project = create_gitlab in ['', 'y', 'yes']
            
            # Create the KB creation command
            kb_creation_command = f"Create a knowledge base titled '{kb_name}' with description '{kb_description}'"
            if create_gitlab_project:
                kb_creation_command += " and create a GitLab project for it"
            
            print(f"🚀 Processing KB creation: {kb_creation_command}")
            
            # Process through the agent system
            response = self.process_user_message(kb_creation_command)
            return response
            
        except Exception as e:
            return f"❌ Error creating Knowledge Base: {e}"

    def list_knowledge_bases(self) -> str:
        """List all knowledge bases through the agent system."""
        try:
            list_command = "Show me all available knowledge bases with their details"
            response = self.process_user_message(list_command)
            return response
        except Exception as e:
            return f"❌ Error listing Knowledge Bases: {e}"

    def set_knowledge_base_context(self, kb_id: str) -> str:
        """Set knowledge base context through the agent system."""
        try:
            context_command = f"Set knowledge base context to KB ID {kb_id}"
            response = self.process_user_message(context_command)
            return response
        except Exception as e:
            return f"❌ Error setting KB context: {e}"

def main():
    print("=" * 80)
    print("🔥 AI ADAPTIVE KNOWLEDGE BASE - SIMPLIFIED MULTI-AGENT CHAT")
    print("🚀 PostgreSQL State Management | Direct UserProxy-Supervisor Communication")
    print("=" * 80)
    print("🎯 Simplified System Architecture:")
    print("   • UserProxy Agent    → Direct user interaction & communication")
    print("   • Supervisor Agent   → Scrum Master coordination & GitLab orchestration")
    print("   • State Manager      → PostgreSQL persistence & session management")
    print("=" * 80)
    print("🎯 Communication Flow:")
    print("   • User → UserProxy → Supervisor → GitLab Coordination")
    print("   • Supervisor coordinates with other agents through GitLab issues")
    print("   • All agent work is tracked and managed through GitLab workflows")
    print("   • Direct, efficient communication without routing complexity")
    print("=" * 80)
    
    # Initialize the simplified chat system
    chat_system = SimplifiedMultiAgentChat()
    chat_system.initialize_agents()
    
    # Display session information
    session_summary = chat_system.get_session_summary()
    if session_summary:
        session_id = session_summary.get('session_id', 'unknown')[:12]
        is_active = session_summary.get('is_active', False)
        print(f"🔗 Session: {session_id}... | Active: {is_active}")
        
        # Show conversation stats if available
        conv_stats = session_summary.get('conversation_stats', {})
        if conv_stats:
            msg_count = conv_stats.get('message_count', 0)
            print(f"💬 Conversation: {msg_count} messages in history")
    
    # Display agent status
    status = chat_system.get_agent_status()
    print(f"📊 System Status: {status['total_agents']} agents active")
    for agent_name, agent_info in status.items():
        if isinstance(agent_info, dict) and 'name' in agent_info:
            print(f"   • {agent_info['name']}: {agent_info['status']} ({agent_info['tools_count']} tools)")
    
    print("=" * 80)
    print("💬 Commands:")
    print("   • Type your question or command to interact with the AI")
    print("   • Type '/kb create' to create a new knowledge base interactively")
    print("   • Type '/kb list' to list all knowledge bases")
    print("   • Type '/kb set <id>' to set context to a specific knowledge base")
    print("   • Type '/agents' to show agent status")
    print("   • Type '/session' to show session summary")
    print("   • Type '/reset' or '/r' to clear conversation state")
    print("   • Type '/q' or '/quit' to exit")
    print("=" * 80)
    
    while True:
        try:
            user_input = input("\n> ")
            print("")
            
            if user_input.lower() in ["/q", "/quit"]:
                print("👋 Simplified multi-agent system shutting down. Goodbye!")
                break
                
            elif user_input.lower() in ["/reset", "/r"]:
                print("🔄 Clearing conversation state...")
                chat_system.clear_conversation_state()
                print("✅ State cleared")
                print("=" * 80)
                continue
            
            elif user_input.lower() in ["/agents"]:
                print("🤖 Simplified Multi-Agent System Status:")
                status = chat_system.get_agent_status()
                for agent_name, agent_info in status.items():
                    if isinstance(agent_info, dict) and 'name' in agent_info:
                        print(f"   • {agent_info['name']}: {agent_info['status']} ({agent_info['tools_count']} tools)")
                continue
            
            elif user_input.lower() in ["/session"]:
                print("📊 Session Summary:")
                session_summary = chat_system.get_session_summary()
                if session_summary:
                    for key, value in session_summary.items():
                        if isinstance(value, dict):
                            print(f"   {key}:")
                            for sub_key, sub_value in value.items():
                                print(f"     {sub_key}: {sub_value}")
                        else:
                            print(f"   {key}: {value}")
                continue
            
            # Handle KB creation commands
            elif user_input.lower().startswith("/kb"):
                kb_command = user_input.lower().strip()
                
                if kb_command == "/kb create":
                    print("🔧 Creating Knowledge Base Interactively...")
                    kb_result = chat_system.create_knowledge_base_interactive()
                    print(f"✅ KB Creation Result: {kb_result}")
                    continue
                    
                elif kb_command == "/kb list":
                    print("📚 Listing Knowledge Bases...")
                    kb_list = chat_system.list_knowledge_bases()
                    print(f"📋 Knowledge Bases: {kb_list}")
                    continue
                    
                elif kb_command.startswith("/kb set"):
                    parts = kb_command.split()
                    if len(parts) >= 3:
                        kb_id = parts[2]
                        print(f"🎯 Setting KB context to ID: {kb_id}")
                        kb_context = chat_system.set_knowledge_base_context(kb_id)
                        print(f"✅ KB Context Result: {kb_context}")
                    else:
                        print("❌ Usage: /kb set <id>")
                    continue
                    
                else:
                    print("❌ Unknown KB command. Available: /kb create, /kb list, /kb set <id>")
                    continue
            
            # Process normal user input through simplified system
            print("🚀 Processing through UserProxy → Supervisor...")
            
            response = chat_system.process_user_message(user_input)
            print(f"\n� Response: {response}")

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user. Type '/q' to quit properly.")
            continue
        except Exception as e:
            print(f"❌ System error: {e}")
            print("💡 Tip: Type '/reset' to restart or '/q' to quit.")
            continue

if __name__ == "__main__":
    main()
