from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from .agent_types import AgentState, AgentMessage
import datetime
import os
import sys

# Add config path to imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.gitlab_agent_mapping import GitLabAgentMapping


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system"""
    
    def __init__(self, name: str, llm: AzureChatOpenAI, system_prompt: str):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.tools = []
        
        # Knowledge Base Context Storage
        self.kb_context = {
            "knowledge_base_id": None,
            "knowledge_base_name": None,
            "knowledge_base_description": None,
            "gitlab_project_id": None,
            "context_set": False,
            "last_updated": None
        }
        
        # GitLab integration setup
        self.gitlab_info = GitLabAgentMapping.get_agent_gitlab_info(name)
        self.gitlab_username = self.gitlab_info.get("gitlab_username", "")
        # All agents use centralized PAT token authentication via GitLabOperations
        self.has_gitlab_credentials = True  # Always true since we use PAT token
        
        # Log GitLab setup status
        self.log(f"GitLab integration enabled - Username: {self.gitlab_username}")
        
        # Initialize KB context from environment if available
        self._initialize_kb_context()
    
    def _initialize_kb_context(self):
        """Initialize KB context from environment variable if available"""
        try:
            default_kb_id = os.getenv('DEFAULT_KNOWLEDGE_BASE_ID', '13')
            if default_kb_id:
                self.log(f"Initializing KB context with default KB ID: {default_kb_id}")
                self.set_kb_context(default_kb_id)
        except Exception as e:
            self.log(f"Could not initialize KB context: {str(e)}")
    
    def set_kb_context(self, knowledge_base_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Set and store KB context information for this agent"""
        try:
            # If context is already set and hasn't been forced to refresh, return existing
            if (not force_refresh and 
                self.kb_context.get("context_set") and 
                self.kb_context.get("knowledge_base_id") == knowledge_base_id):
                return {
                    "success": True,
                    "cached": True,
                    "message": f"Using cached KB context: {self.kb_context.get('knowledge_base_name')}"
                }
            
            # Find and call KnowledgeBaseSetContext tool
            set_context_tool = next((t for t in self.tools if t.name == 'KnowledgeBaseSetContext'), None)
            if not set_context_tool:
                self.log("Warning: KnowledgeBaseSetContext tool not available")
                return {"success": False, "error": "KnowledgeBaseSetContext tool not available"}
            
            result = set_context_tool._run(knowledge_base_id=knowledge_base_id)
            
            if result.get("success"):
                # Store the context information
                self.kb_context.update({
                    "knowledge_base_id": knowledge_base_id,
                    "knowledge_base_name": result.get("knowledge_base_name"),
                    "knowledge_base_description": result.get("knowledge_base_description"),
                    "gitlab_project_id": result.get("gitlab_project_id"),
                    "context_set": True,
                    "last_updated": datetime.datetime.now()
                })
                
                self.log(f"✅ KB Context set: {self.kb_context['knowledge_base_name']} (ID: {knowledge_base_id})")
                if self.kb_context.get("gitlab_project_id"):
                    self.log(f"🔗 GitLab Project: {self.kb_context['gitlab_project_id']}")
                
                return result
            else:
                self.log(f"❌ Failed to set KB context: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            self.log(f"Error setting KB context: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_kb_context(self) -> Dict[str, Any]:
        """Get current KB context information"""
        return self.kb_context.copy()
    
    def get_kb_context_summary(self) -> str:
        """Get a formatted summary of current KB context for use in prompts"""
        if not self.kb_context.get("context_set"):
            return "No knowledge base context is currently set."
        
        summary = f"""
Current Knowledge Base Context:
- Name: {self.kb_context.get('knowledge_base_name', 'Unknown')}
- ID: {self.kb_context.get('knowledge_base_id', 'Unknown')}
- Description: {self.kb_context.get('knowledge_base_description', 'No description available')}
"""
        
        if self.kb_context.get('gitlab_project_id'):
            summary += f"- GitLab Project: {self.kb_context.get('gitlab_project_id')}\n"
        
        return summary.strip()
    
    def ensure_kb_context(self, preferred_kb_id: str = None) -> bool:
        """Ensure KB context is set, using preferred ID or environment default"""
        if self.kb_context.get("context_set") and not preferred_kb_id:
            return True  # Already have context
        
        kb_id = preferred_kb_id or os.getenv('DEFAULT_KNOWLEDGE_BASE_ID', '13')
        result = self.set_kb_context(kb_id)
        return result.get("success", False)
    
    def get_gitlab_username(self) -> str:
        """Get this agent's GitLab username"""
        return self.gitlab_username
    
    def get_gitlab_credentials(self) -> Dict[str, Optional[str]]:
        """Get this agent's GitLab credentials"""
        return GitLabAgentMapping.get_gitlab_credentials(self.name)
    
    def is_gitlab_enabled(self) -> bool:
        """Check if GitLab integration is properly configured"""
        # Always return True since all agents use centralized PAT token authentication
        return True
    
    def get_default_knowledge_base_id(self, state: AgentState = None) -> Optional[str]:
        """Get the knowledge base ID from context, state, environment, or current context"""
        try:
            # Priority 1: Use cached KB context if available
            if self.kb_context.get("context_set") and self.kb_context.get("knowledge_base_id"):
                kb_id = self.kb_context.get("knowledge_base_id")
                self.log(f"Using KB ID from cached context: {kb_id}")
                return str(kb_id)
            
            # Priority 2: Check if KB ID is in the agent state
            if state and state.get("knowledge_base_id"):
                kb_id = state.get("knowledge_base_id")
                self.log(f"Using KB ID from state: {kb_id}")
                # Update our context with this information
                self.set_kb_context(str(kb_id))
                return str(kb_id)
            
            # Priority 3: Try to get current context from tools
            try:
                current_context_tool = next((t for t in self.tools if t.name == 'KnowledgeBaseGetCurrentContext'), None)
                if current_context_tool:
                    context_result = current_context_tool._run()
                    if context_result.get("success") and context_result.get("knowledge_base_id"):
                        kb_id = context_result.get("knowledge_base_id")
                        self.log(f"Using KB ID from current context: {kb_id}")
                        self.set_kb_context(str(kb_id))
                        return str(kb_id)
            except Exception as e:
                self.log(f"Could not get current KB context: {str(e)}")
            
            # Priority 4: Fallback to environment variable and set context
            kb_id = os.getenv('DEFAULT_KNOWLEDGE_BASE_ID', '13')
            self.log(f"Using DEFAULT_KNOWLEDGE_BASE_ID from environment: {kb_id}")
            
            # Set the context using our new method
            result = self.set_kb_context(str(kb_id))
            if result.get("success"):
                # Update the state with the KB context if state is provided
                if state:
                    state["knowledge_base_id"] = kb_id
                    state["knowledge_base_name"] = self.kb_context.get('knowledge_base_name')
            
            return str(kb_id)
            
        except Exception as e:
            self.log(f"Error getting default knowledge base ID: {str(e)}")
            return "13"  # Ultimate fallback
    
    def set_kb_context_with_gitlab_project(self, knowledge_base_id: str = None, gitlab_project_id: str = None) -> Dict[str, Any]:
        """Set knowledge base context and establish GitLab project association"""
        if knowledge_base_id:
            # Use our enhanced context setting method
            return self.set_kb_context(knowledge_base_id)
        
        elif gitlab_project_id:
            # Set context by GitLab project ID
            kb_tools = [tool for tool in self.tools if tool.name == "KnowledgeBaseSetContextByGitLabProject"]
            if kb_tools:
                context_result = kb_tools[0]._run(gitlab_project_id=gitlab_project_id)
                self.log(f"📋 KB Context set via GitLab project: {gitlab_project_id}")
                
                # Update our internal context if successful
                if context_result.get("success"):
                    self.kb_context.update({
                        "knowledge_base_id": context_result.get("knowledge_base_id"),
                        "knowledge_base_name": context_result.get("knowledge_base_name"),
                        "knowledge_base_description": context_result.get("knowledge_base_description"),
                        "gitlab_project_id": context_result.get("gitlab_project_id"),
                        "context_set": True,
                        "last_updated": datetime.datetime.now()
                    })
                
                return context_result
        
        return {"success": False, "error": "No knowledge_base_id or gitlab_project_id provided"}
    
    def get_gitlab_project_for_current_work(self, issue_project_id: str) -> Dict[str, Any]:
        """Get GitLab project context for current work and set corresponding KB context"""
        self.log(f"🔍 Getting GitLab project context for project {issue_project_id}")
        
        # Try to set KB context based on GitLab project
        kb_context = self.set_kb_context_with_gitlab_project(gitlab_project_id=issue_project_id)
        
        if kb_context.get('success'):
            self.log(f"✅ Found KB for GitLab project {issue_project_id}: {kb_context.get('knowledge_base_name')}")
            return {
                "success": True,
                "knowledge_base_id": kb_context.get('knowledge_base_id'),
                "knowledge_base_name": kb_context.get('knowledge_base_name'),
                "gitlab_project_id": issue_project_id,
                "message": f"Working context established for GitLab project {issue_project_id}"
            }
        else:
            self.log(f"⚠️ No KB found for GitLab project {issue_project_id}")
            return {
                "success": False,
                "gitlab_project_id": issue_project_id,
                "message": f"No knowledge base associated with GitLab project {issue_project_id}",
                "suggestion": "Consider creating a KB for this project or linking an existing one"
            }
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging that includes KB context"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add KB context to log if available
        kb_info = ""
        if self.kb_context.get("context_set"):
            kb_name = self.kb_context.get("knowledge_base_name", "Unknown")
            kb_id = self.kb_context.get("knowledge_base_id", "Unknown")
            kb_info = f" [KB: {kb_name} ({kb_id})]"
        
        formatted_message = f"[{timestamp}] [{self.name}]{kb_info} [{level}] {message}"
        print(formatted_message)
        
        # Also log to file if logger is available
        try:
            import logging
            logger = logging.getLogger(self.name)
            getattr(logger, level.lower(), logger.info)(message)
        except:
            pass  # Fallback to print only if logging not configured
        
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state"""
        pass
    
    def increment_recursions(self, state: AgentState) -> None:
        """Increment recursion counter with loop detection"""
        current_recursions = state.get("recursions", 0)
        state["recursions"] = current_recursions + 1
        
        # Enhanced loop detection
        if current_recursions >= 5:  # Lower threshold for early detection
            self.log(f"WARNING: High recursion count ({current_recursions}) detected")
            
            # Check for specific loop patterns
            recent_agents = state.get("agent_sequence", [])[-5:]  # Last 5 agents
            if len(recent_agents) >= 4:
                # Check for alternating pattern (A->B->A->B)
                if (len(set(recent_agents)) <= 2 and 
                    recent_agents[0] == recent_agents[2] and 
                    recent_agents[1] == recent_agents[3]):
                    
                    self.log(f"LOOP DETECTED: Alternating pattern {recent_agents}")
                    # Force end of workflow
                    state["current_agent"] = None
                    state["loop_detected"] = True
                    return
                
                # Check for same agent repeating
                if len(set(recent_agents)) == 1:
                    self.log(f"LOOP DETECTED: Same agent repeating {recent_agents}")
                    state["current_agent"] = None 
                    state["loop_detected"] = True
                    return
        
        # Track agent sequence for loop detection
        agent_sequence = state.get("agent_sequence", [])
        agent_sequence.append(self.name)
        state["agent_sequence"] = agent_sequence[-10:]  # Keep last 10 agents
    
    def should_activate(self, state: AgentState) -> bool:
        """Determine if this agent should be activated given the current state"""
        return state.get("current_agent") == self.name
    
    def create_message(self, recipient: str, message_type: str, content: str, 
                      metadata: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Create a standardized message for inter-agent communication"""
        return AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.datetime.now().isoformat()
        )
    
    def log(self, message: str, level: str = "INFO"):
        """Log agent activity"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.name}] [{level}] {message}")
        
    def get_system_message(self) -> BaseMessage:
        """Get the system message for this agent"""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_prompt = f"Current date and time: {current_time}\n\n{self.system_prompt}"
        return HumanMessage(content=full_prompt)
    
    def get_messages_with_history(self, state: AgentState, current_user_message: str = None) -> List[BaseMessage]:
        """
        Construct message array including conversation history for better context retention.
        
        This method ensures agents have access to the full conversation context,
        preventing memory loss between interactions.
        """
        messages = [self.get_system_message()]
        
        # Include conversation history from state if available
        conversation_history = state.get("conversation_history", [])
        
        # Add conversation history (limit to last 10 exchanges to manage context window)
        recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
        
        for msg in recent_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current user message if provided and not already in history
        if current_user_message:
            # Check if this message is already the last user message in history
            last_user_msg = None
            for msg in reversed(recent_history):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break
            
            if last_user_msg != current_user_message:
                messages.append(HumanMessage(content=current_user_message))
        
        return messages
