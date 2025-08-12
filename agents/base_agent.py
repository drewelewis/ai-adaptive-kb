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
        
        # GitLab integration setup
        self.gitlab_info = GitLabAgentMapping.get_agent_gitlab_info(name)
        self.gitlab_username = self.gitlab_info.get("gitlab_username", "")
        self.has_gitlab_credentials = self.gitlab_info.get("has_credentials", False)
        
        # Log GitLab setup status
        if self.has_gitlab_credentials:
            self.log(f"✅ GitLab integration enabled - Username: {self.gitlab_username}")
        else:
            self.log(f"⚠️ GitLab credentials not configured for {name}")
    
    def get_gitlab_username(self) -> str:
        """Get this agent's GitLab username"""
        return self.gitlab_username
    
    def get_gitlab_credentials(self) -> Dict[str, Optional[str]]:
        """Get this agent's GitLab credentials"""
        return GitLabAgentMapping.get_gitlab_credentials(self.name)
    
    def is_gitlab_enabled(self) -> bool:
        """Check if GitLab integration is properly configured"""
        return self.has_gitlab_credentials
    
    def set_kb_context_with_gitlab_project(self, knowledge_base_id: str = None, gitlab_project_id: str = None) -> Dict[str, Any]:
        """Set knowledge base context and establish GitLab project association"""
        if knowledge_base_id:
            # Set context by KB ID and get GitLab project info
            kb_tools = [tool for tool in self.tools if tool.name == "KnowledgeBaseSetContext"]
            if kb_tools:
                context_result = kb_tools[0].run({"knowledge_base_id": knowledge_base_id})
                self.log(f"📋 KB Context set: {context_result.get('knowledge_base_name', 'Unknown')}")
                
                # Log GitLab project information
                gitlab_context = context_result.get('gitlab_project_context', {})
                if gitlab_context.get('project_id'):
                    self.log(f"🔗 GitLab Project: {gitlab_context['project_id']}")
                else:
                    self.log("⚠️ No GitLab project associated with this KB")
                
                return context_result
        
        elif gitlab_project_id:
            # Set context by GitLab project ID
            kb_tools = [tool for tool in self.tools if tool.name == "KnowledgeBaseSetContextByGitLabProject"]
            if kb_tools:
                context_result = kb_tools[0].run({"gitlab_project_id": gitlab_project_id})
                self.log(f"📋 KB Context set via GitLab project: {gitlab_project_id}")
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
