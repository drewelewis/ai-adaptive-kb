from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from agents.base_agent import BaseAgent
from agents.agent_types import AgentState, AgentMessage
from prompts.multi_agent_prompts import prompts


class UserProxyAgent(BaseAgent):
    """
    User Proxy Agent - Handles direct user interactions and manages the conversation flow.
    This agent serves as the interface between the user and the multi-agent system.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        system_prompt = prompts.user_proxy_prompt()
        super().__init__("UserProxy", llm, system_prompt)
    
    def process(self, state: AgentState) -> AgentState:
        """Process user input and coordinate with other agents"""
        self.log("Processing user interaction")
        
        # Get the latest user message
        messages = state["messages"]
        if not messages:
            return state
            
        last_message = messages[-1]
        
        # Analyze user intent
        user_intent = self._analyze_user_intent(last_message.content if hasattr(last_message, 'content') else str(last_message))
        
        # Update state with user intent
        state["user_intent"] = user_intent
        
        # Determine if we need to involve other agents
        if self._requires_knowledge_base_operation(user_intent):
            # Send request to supervisor
            supervisor_message = self.create_message(
                recipient="Supervisor",
                message_type="request",
                content=f"User request: {last_message.content if hasattr(last_message, 'content') else str(last_message)}",
                metadata={"intent": user_intent, "original_message": str(last_message)}
            )
            
            # Add to agent messages
            if "agent_messages" not in state:
                state["agent_messages"] = []
            state["agent_messages"].append(supervisor_message)
            
            # Set supervisor as next agent
            state["current_agent"] = "Supervisor"
            
            self.log(f"Routing request to Supervisor Agent. Intent: {user_intent}")
        else:
            # Handle simple responses directly
            response = self._generate_direct_response(last_message.content if hasattr(last_message, 'content') else str(last_message))
            ai_message = AIMessage(content=response)
            state["messages"].append(ai_message)
            
            self.log("Provided direct response to user")
        
        return state
    
    def _analyze_user_intent(self, user_message: str) -> str:
        """Analyze user message to determine intent"""
        user_message_lower = user_message.lower()
        
        # Knowledge base management intents
        if any(keyword in user_message_lower for keyword in ['create', 'add', 'new', 'insert']):
            if 'knowledge base' in user_message_lower:
                return "create_knowledge_base"
            elif 'article' in user_message_lower:
                return "create_article"
            elif 'tag' in user_message_lower:
                return "create_tag"
            else:
                return "create_content"
        
        if any(keyword in user_message_lower for keyword in ['update', 'edit', 'modify', 'change']):
            return "update_content"
            
        if any(keyword in user_message_lower for keyword in ['delete', 'remove']):
            return "delete_content"
            
        if any(keyword in user_message_lower for keyword in ['search', 'find', 'look for', 'query']):
            return "search_content"
            
        if any(keyword in user_message_lower for keyword in ['show', 'display', 'list', 'get', 'hierarchy']):
            return "retrieve_content"
            
        if any(keyword in user_message_lower for keyword in ['help', 'how', 'what', 'explain']):
            return "help_request"
            
        return "general_inquiry"
    
    def _requires_knowledge_base_operation(self, intent: str) -> bool:
        """Determine if the intent requires knowledge base operations"""
        kb_operations = [
            "create_knowledge_base", "create_article", "create_tag", "create_content",
            "update_content", "delete_content", "search_content", "retrieve_content"
        ]
        return intent in kb_operations
    
    def _generate_direct_response(self, user_message: str) -> str:
        """Generate a direct response for simple queries"""
        # Use LLM for generating contextual responses
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"Provide a helpful response to this user message: {user_message}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def format_response_for_user(self, technical_response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Convert technical responses to user-friendly format"""
        # Use LLM to convert technical responses to user-friendly language
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
Convert this technical response into user-friendly language:

Technical Response: {technical_response}

Context: {context if context else 'No additional context'}

Make it conversational and easy to understand while preserving the important information.
            """)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
