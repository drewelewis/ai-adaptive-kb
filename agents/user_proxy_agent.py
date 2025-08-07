from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from agents.base_agent import BaseAgent
from agents.agent_types import AgentState, AgentMessage
from prompts.multi_agent_prompts import prompts
from utils.robust_intent_classifier import RobustIntentClassifier


class UserProxyAgent(BaseAgent):
    """
    User Proxy Agent - Handles direct user interactions and manages the conversation flow.
    This agent serves as the interface between the user and the multi-agent system.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        system_prompt = prompts.user_proxy_prompt()
        super().__init__("UserProxy", llm, system_prompt)
        # Initialize the robust intent classifier
        self.intent_classifier = RobustIntentClassifier()
    
    def process(self, state: AgentState) -> AgentState:
        """Process user input and coordinate with other agents"""
        self.log("Processing user interaction")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check what type of message we have
        messages = state.get("messages", [])
        if not messages:
            return state
            
        last_message = messages[-1]
        
        # CRITICAL: If the last message is an AIMessage, check if we have a new HumanMessage to process
        if hasattr(last_message, '__class__') and last_message.__class__.__name__ == 'AIMessage':
            # Look for any unprocessed HumanMessages after the last AI response
            human_messages = [msg for msg in messages if hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage']
            if not human_messages:
                self.log("No new user input to process, waiting for user interaction")
                return state
            
            # Get the most recent HumanMessage 
            last_human_message = human_messages[-1]
            
            # Check if this HumanMessage comes after our last AIMessage
            last_ai_message_index = len(messages) - 1 - messages[::-1].index(last_message)
            human_message_indices = [i for i, msg in enumerate(messages) if hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage']
            
            if human_message_indices and max(human_message_indices) <= last_ai_message_index:
                self.log("No new user input after last AI response, waiting")
                return state
            
            # There's a new HumanMessage to process - continue with processing
            last_message = last_human_message
            self.log(f"Found new user input after AI response: {last_human_message.content[:50]}...")
        
        # Only process HumanMessage (actual user input)
        if not (hasattr(last_message, '__class__') and last_message.__class__.__name__ == 'HumanMessage'):
            self.log(f"Unexpected message type: {last_message.__class__.__name__}")
            return state
        
        # Check for workflow completion messages from Supervisor first
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        # Get list of already processed message timestamps to avoid reprocessing
        processed_messages = state.get("processed_workflow_messages", [])
        
        if my_messages:
            # Handle workflow completion/error messages
            latest_supervisor_message = my_messages[-1]
            message_id = f"{latest_supervisor_message.sender}_{latest_supervisor_message.timestamp}_{latest_supervisor_message.message_type}"
            
            if (latest_supervisor_message.message_type in ["workflow_complete", "workflow_error"] and 
                message_id not in processed_messages):
                
                self.log(f"Processing workflow result: {latest_supervisor_message.message_type}")
                
                # Generate user-friendly response based on the workflow result
                user_friendly_response = self.format_response_for_user(
                    latest_supervisor_message.content,
                    latest_supervisor_message.metadata
                )
                
                # Add final AI message to conversation
                ai_message = AIMessage(content=user_friendly_response)
                state["messages"].append(ai_message)
                
                # Mark this specific message as processed
                if "processed_workflow_messages" not in state:
                    state["processed_workflow_messages"] = []
                if message_id not in state["processed_workflow_messages"]:
                    state["processed_workflow_messages"].append(message_id)
                
                self.log("Provided workflow result to user - conversation complete")
                return state
        
        # Process new user input
        user_message_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Check if we've already sent this message to supervisor (avoid duplicate routing)
        existing_supervisor_msgs = [msg for msg in agent_messages 
                                  if msg.sender == "UserProxy" and msg.recipient == "Supervisor" 
                                  and user_message_content in msg.content]
        
        if existing_supervisor_msgs:
            self.log("Message already sent to supervisor, waiting for response")
            return state
        
        # Analyze user intent for new messages using robust classifier
        user_intent, confidence = self.intent_classifier.classify_intent(user_message_content)
        state["user_intent"] = user_intent
        state["intent_confidence"] = confidence
        
        self.log(f"Intent classified as: {user_intent} (confidence: {confidence:.1f}%)")
        
        # Check if this is a follow-up request that needs conversation context
        if self._is_context_dependent_request(user_message_content, user_intent):
            self.log("Context-dependent request detected, including conversation history")
            recent_context = self._get_conversation_context(state)
            if recent_context:
                enhanced_message = f"Context from previous conversation: {recent_context}\n\nNew user request: {user_message_content}"
                user_message_content = enhanced_message
        
        # Handle conversation history requests directly (no need to involve other agents)
        if user_intent == "get_conversation_history":
            conversation_history = self._get_recent_conversation_history(state, 3)
            ai_message = AIMessage(content=conversation_history)
            state["messages"].append(ai_message)
            self.log("Provided conversation history to user")
            return state
        
        # Extract and track section context from user message
        section_context = self._extract_section_context(user_message_content, state)
        if section_context:
            state["current_section"] = section_context
            self.log(f"Updated section context: {section_context}")
        
        # Determine if we need to involve other agents
        if self._requires_knowledge_base_operation(user_intent):
            # Send request to supervisor
            supervisor_message = self.create_message(
                recipient="Supervisor",
                message_type="request",
                content=f"User request: {user_message_content}",
                metadata={"intent": user_intent, "original_message": str(last_message)}
            )
            
            # Add to agent messages
            if "agent_messages" not in state:
                state["agent_messages"] = []
            state["agent_messages"].append(supervisor_message)
            
            # Set supervisor as next agent
            state["current_agent"] = "Supervisor"
            
            self.log(f"Routing request to Supervisor Agent. Intent: {user_intent}")
            self.log(f"State updated: current_agent={state.get('current_agent')}, recursions={state.get('recursions')}")
        else:
            # Handle simple responses directly (help, general inquiries)
            response = self._generate_direct_response(user_message_content)
            ai_message = AIMessage(content=response)
            state["messages"].append(ai_message)
            
            self.log("Provided direct response to user - conversation complete")
        
        return state
    
    # OLD INTENT CLASSIFICATION METHOD - REPLACED WITH ROBUST CLASSIFIER
    # def _analyze_user_intent(self, user_message: str) -> str:
    #     """DEPRECATED: Old brittle intent classification - replaced with RobustIntentClassifier"""
    #     # This method has been replaced with the RobustIntentClassifier
    #     # which provides much better reliability and confidence scoring
    #     pass
    
    def _get_recent_conversation_history(self, state: AgentState, count: int = 3) -> str:
        """Get the last N user commands from conversation history"""
        messages = state.get("messages", [])
        human_messages = [msg for msg in messages if hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage']
        
        # Get the last N human messages
        recent_messages = human_messages[-count:] if len(human_messages) >= count else human_messages
        
        if not recent_messages:
            return "No previous commands found in this conversation."
        
        history_text = f"Here are your last {len(recent_messages)} commands:\n\n"
        for i, msg in enumerate(recent_messages, 1):
            content = msg.content if hasattr(msg, 'content') else str(msg)
            history_text += f"{i}. \"{content}\"\n"
        
        return history_text
    
    def _is_context_dependent_request(self, user_message: str, intent: str) -> bool:
        """Check if this request depends on previous conversation context"""
        context_indicators = [
            "these", "those", "them", "that", "this", "the above", "mentioned above",
            "all the additions", "make these", "implement all", "go ahead and",
            "the recommendations", "what you suggested", "your suggestions"
        ]
        
        # Personal/identity questions that require conversation context
        identity_questions = [
            "what is my name", "what's my name", "my name is", "who am i", 
            "what did i say", "what did i tell you", "remember me", "do you remember",
            "i told you", "i mentioned", "i said earlier", "as i said"
        ]
        
        message_lower = user_message.lower()
        has_context_indicators = any(indicator in message_lower for indicator in context_indicators)
        has_identity_questions = any(question in message_lower for question in identity_questions)
        
        # Also check if intent suggests follow-up action
        follow_up_intents = ["create_content", "update_content"]
        
        return has_context_indicators or has_identity_questions or (intent in follow_up_intents and len(message_lower.split()) < 10)
    
    def _get_conversation_context(self, state: AgentState, lookback_messages: int = 3) -> str:
        """Extract relevant context from recent conversation"""
        messages = state.get("messages", [])
        if len(messages) < 2:
            return ""
        
        # Look for recent messages that might contain relevant context
        recent_context = []
        for msg in messages[-lookback_messages:]:
            if hasattr(msg, '__class__'):
                content = msg.content if hasattr(msg, 'content') else str(msg)
                msg_type = "User" if msg.__class__.__name__ == 'HumanMessage' else "Assistant"
                
                # For personal/identity questions, include recent user introductions and AI acknowledgments
                if any(keyword in content.lower() for keyword in [
                    "my name is", "i am", "call me", "hello", "hi", "nice to meet you",
                    "gap analysis", "recommendations", "additions", "missing", 
                    "priority", "trending", "create", "add", "implement"
                ]):
                    recent_context.append(f"{msg_type}: {content}")
        
        if recent_context:
            # Return all relevant context messages
            context_text = "\n".join(recent_context)
            # Truncate to prevent context overflow
            if len(context_text) > 1000:
                context_text = context_text[:1000] + "... [truncated]"
            return context_text
        
        return ""
    
    def _extract_section_context(self, user_message: str, state: AgentState) -> Optional[str]:
        """Extract section context from user message"""
        user_message_lower = user_message.lower()
        
        # Define section keywords and their standardized names
        section_mappings = {
            'budget': 'budgeting',
            'budgeting': 'budgeting', 
            'invest': 'investment',
            'investment': 'investment',
            'investing': 'investment',
            'tax': 'tax',
            'taxes': 'tax',
            'insurance': 'insurance',
            'estate': 'estate planning',
            'debt': 'debt management', 
            'income': 'income',
            'retirement': 'retirement',
            'real estate': 'real estate',
            'healthcare': 'healthcare'
        }
        
        # Look for section keywords in the message
        for keyword, section_name in section_mappings.items():
            if keyword in user_message_lower:
                return section_name
        
        # If no section found, return current section from state (maintain context)
        return state.get("current_section")
    
    def _requires_knowledge_base_operation(self, intent: str) -> bool:
        """Determine if the intent requires knowledge base operations"""
        kb_operations = [
            "set_knowledge_base_context", "create_knowledge_base", "create_article", 
            "create_tag", "create_content", "update_content", "delete_content", 
            "search_content", "retrieve_content", "retrieve_filtered_content",
            "analyze_content_gaps"
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
