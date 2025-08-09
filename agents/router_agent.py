from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from prompts.multi_agent_prompts import prompts
from utils.llm_intent_classifier import LLMIntentClassifier


class RouterAgent(BaseAgent):
    """
    Router Agent - Handles intent classification and routing decisions.
    This agent analyzes user requests and determines which agent should handle them.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        system_prompt = self._create_router_prompt()
        super().__init__("Router", llm, system_prompt)
        # Initialize the LLM-based intent classifier
        self.intent_classifier = LLMIntentClassifier(llm)
    
    def _create_router_prompt(self) -> str:
        """Create the system prompt for the router agent"""
        return """You are the Router Agent for a multi-agent knowledge base system. Your responsibilities are:

1. **Intent Classification**: Analyze user messages to understand what they want to accomplish
2. **Routing Decisions**: Determine which agent should handle each request
3. **Context Management**: Maintain conversation context for better routing

**Available Agents:**
- **UserProxy**: Handles direct user communication and simple responses
- **ContentManagement**: Executes knowledge base operations (CRUD operations)
- **Supervisor**: Reviews and validates work from other agents

**Routing Rules:**
- Simple responses (help, explanations) → UserProxy
- Knowledge base operations → ContentManagement  
- Work validation/review → Supervisor
- Complex multi-step workflows → ContentManagement → Supervisor

You should be decisive and efficient in your routing decisions."""
    
    def process(self, state: AgentState) -> AgentState:
        """Process routing requests and classify intent"""
        self.log("Processing routing request")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from UserProxy
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            self.log("No messages found for Router")
            return state
        
        # Get the latest message
        latest_message = my_messages[-1]
        user_message_content = latest_message.content
        
        # Extract user message from the content
        if "User request: " in user_message_content:
            user_message_content = user_message_content.replace("User request: ", "").strip()
        
        # Build context for classification
        context = self._build_classification_context(state)
        
        # Classify intent using LLM
        user_intent, confidence = self.intent_classifier.classify_intent(user_message_content, context)
        
        # Update state with intent information
        state["user_intent"] = user_intent
        state["intent_confidence"] = confidence
        
        self.log(f"Intent classified as: {user_intent} (confidence: {confidence:.1f}%)")
        
        # Make routing decision
        target_agent = self._determine_target_agent(user_intent, confidence, state)
        
        # Create message for target agent
        if target_agent == "UserProxy":
            # Route back to UserProxy for direct response
            response_message = self.create_message(
                recipient="UserProxy",
                message_type="direct_response_request",
                content=user_message_content,
                metadata={
                    "intent": user_intent,
                    "confidence": confidence,
                    "routing_reason": "Simple response - no agent coordination needed"
                }
            )
        else:
            # Route to appropriate agent for processing
            response_message = self.create_message(
                recipient=target_agent,
                message_type="work_request",
                content=user_message_content,
                metadata={
                    "intent": user_intent,
                    "confidence": confidence,
                    "original_request": latest_message.content,
                    "routing_reason": f"Requires {target_agent} capabilities"
                }
            )
        
        # Add to agent messages
        state["agent_messages"].append(response_message)
        
        # Set next agent
        state["current_agent"] = target_agent
        
        self.log(f"Routed to {target_agent} for intent: {user_intent}")
        
        return state
    
    def _build_classification_context(self, state: AgentState) -> Dict[str, Any]:
        """Build context information to help with intent classification"""
        context = {}
        
        # Add current knowledge base context
        if "knowledge_base_id" in state and state["knowledge_base_id"]:
            context["current_kb"] = state["knowledge_base_id"]
        
        # Add current article context
        if "article_id" in state and state["article_id"]:
            context["current_article"] = state["article_id"]
        elif "current_section" in state and state["current_section"]:
            context["current_article"] = state["current_section"]
        
        # Add recent intent history
        if "user_intent" in state and state["user_intent"]:
            context["previous_intent"] = state["user_intent"]
        
        # Add recent actions from agent messages
        agent_messages = state.get("agent_messages", [])
        if agent_messages:
            recent_actions = []
            for msg in agent_messages[-5:]:  # Last 5 messages
                if msg.message_type in ["work_request", "workflow_complete"]:
                    intent = msg.metadata.get("intent", "unknown")
                    recent_actions.append(intent)
            context["recent_actions"] = recent_actions
        
        return context
    
    def _determine_target_agent(self, user_intent: str, confidence: float, state: AgentState) -> str:
        """Determine which agent should handle the request"""
        
        # Simple responses that UserProxy can handle directly
        simple_response_intents = [
            "general_inquiry",
            "get_conversation_history"
        ]
        
        # Intents for autonomous content creation (new specialized agents)
        content_creation_intents = [
            "create_content",
            "analyze_content_gaps"
        ]
        
        # Intents that require existing knowledge base operations
        kb_operation_intents = [
            "retrieve_content",
            "retrieve_filtered_content",
            "update_content",
            "search_content",
            "set_knowledge_base_context",
            "set_article_context"
        ]
        
        # Debug logging
        self.log(f"DEBUG: Checking intent '{user_intent}' against categories")
        self.log(f"DEBUG: content_creation_intents = {content_creation_intents}")
        self.log(f"DEBUG: user_intent in content_creation_intents = {user_intent in content_creation_intents}")
        
        if user_intent in simple_response_intents:
            self.log(f"DEBUG: Routing to UserProxy for simple response intent")
            return "UserProxy"
        elif user_intent in content_creation_intents:
            self.log(f"DEBUG: Routing to ContentPlanner for content creation intent")
            return "ContentPlanner"
        elif user_intent in kb_operation_intents:
            self.log(f"DEBUG: Routing to Supervisor for KB operation intent (will delegate to ContentManagement)")
            return "Supervisor"
        else:
            # Default to ContentPlanner for unknown content-related intents
            self.log(f"Unknown intent '{user_intent}', defaulting to ContentPlanner for autonomous handling")
            return "ContentPlanner"
    
    def _requires_supervision(self, user_intent: str) -> bool:
        """Determine if the intent requires supervisor review"""
        # Intents that should be reviewed by supervisor
        review_required_intents = [
            "create_content",
            "update_content", 
            "analyze_content_gaps"
        ]
        
        return user_intent in review_required_intents
