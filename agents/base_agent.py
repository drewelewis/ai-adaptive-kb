from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from agents.agent_types import AgentState, AgentMessage
import datetime


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system"""
    
    def __init__(self, name: str, llm: AzureChatOpenAI, system_prompt: str):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.tools = []
        
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state"""
        pass
    
    def increment_recursions(self, state: AgentState) -> None:
        """Increment the recursion counter"""
        current_recursions = state.get("recursions", 0)
        state["recursions"] = current_recursions + 1
    
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
