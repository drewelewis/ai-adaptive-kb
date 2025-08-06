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
        processed_messages = state.get("processed_workflow_messages", set())
        
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
                    state["processed_workflow_messages"] = set()
                state["processed_workflow_messages"].add(message_id)
                
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
        
        # Handle special requests for conversation history
        if any(phrase in user_message_content.lower() for phrase in ['last 3 commands', 'recent commands', 'conversation history', 'what did i ask']):
            conversation_history = self._get_recent_conversation_history(state, 3)
            ai_message = AIMessage(content=conversation_history)
            state["messages"].append(ai_message)
            self.log("Provided conversation history to user")
            return state
        
        # Analyze user intent for new messages
        user_intent = self._analyze_user_intent(user_message_content)
        state["user_intent"] = user_intent
        
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
        else:
            # Handle simple responses directly (help, general inquiries)
            response = self._generate_direct_response(user_message_content)
            ai_message = AIMessage(content=response)
            state["messages"].append(ai_message)
            
            self.log("Provided direct response to user - conversation complete")
        
        return state
    
    def _analyze_user_intent(self, user_message: str) -> str:
        """Analyze user message to determine intent"""
        user_message_lower = user_message.lower()
        
        # Knowledge base context commands
        if any(keyword in user_message_lower for keyword in ['use kb', 'switch to kb', 'select kb']):
            return "set_knowledge_base_context"
        
        # Content analysis and recommendations (check BEFORE create patterns to avoid conflicts)
        analysis_patterns = [
            'suggest content', 'suggest articles', 'content gaps', 'gaps in coverage',
            'review the kb', 'assess the kb', 'analyze the kb', 'improve the kb',
            'what can be added', 'articles that can be added', 'suggestions on articles',
            'general assessment', 'content analysis', 'make the kb better',
            'offer up content', 'look at my current kb', 'suggest new articles',
            'analyze the knowledge base', 'analyze any gaps', 'gaps in the current content',
            'analyze.*gaps', 'what.*missing', 'areas.*missing'
        ]
        if any(pattern in user_message_lower for pattern in analysis_patterns):
            return "analyze_content_gaps"
        
        # Knowledge base management intents (check these after analysis to avoid conflicts)
        if any(keyword in user_message_lower for keyword in ['create', 'add', 'new', 'insert']):
            if 'knowledge base' in user_message_lower:
                return "create_knowledge_base"
            elif 'article' in user_message_lower:
                return "create_article"
            elif 'tag' in user_message_lower:
                return "create_tag"
            else:
                return "create_content"
        
        # Article context commands - when user wants to focus on a specific article
        if any(pattern in user_message_lower for pattern in [
            'work on category', 'focus on category', 'work on article', 'focus on article',
            'work on main category', 'focus on main category', 'category ', 'article ',
            'work with category', 'focus on item', 'work on id', 'focus on id'
        ]):
            return "set_article_context"
        
        if any(keyword in user_message_lower for keyword in ['update', 'edit', 'modify', 'change']):
            return "update_content"
            
        if any(keyword in user_message_lower for keyword in ['delete', 'remove']):
            return "delete_content"
            
        if any(keyword in user_message_lower for keyword in ['search', 'find', 'look for', 'query']):
            return "search_content"
        
        # Check for filtered section requests (specific section + focus/display words)
        section_keywords = ['budget', 'investment', 'tax', 'insurance', 'estate', 'debt', 'income', 'retirement', 'real estate', 'healthcare']
        display_keywords = ['show', 'display', 'list', 'get', 'articles under', 'articles in', 'focus on', 'work on']
        focus_keywords = ['focus', 'work', 'concentrate', 'articles', 'content', 'under', 'in', 'section']
        
        # Context reference patterns - when user refers to previous context with "that", "it", etc.
        context_reference_patterns = [
            'hierarchy under that', 'under that', 'articles under that', 'content under that',
            'under it', 'articles under it', 'content under it', 'hierarchy under it',
            'show me under', 'list under', 'get under', 'display under'
        ]
        
        has_section = any(section in user_message_lower for section in section_keywords)
        has_display = any(display in user_message_lower for display in display_keywords)
        has_focus = any(word in user_message_lower for word in focus_keywords)
        has_context_reference = any(pattern in user_message_lower for pattern in context_reference_patterns)
        
        # Match patterns like "focus on budgeting", "work on investment", "get budgeting articles", etc.
        # OR contextual references like "hierarchy under that", "articles under that"
        if (has_section and (has_display or has_focus)) or has_context_reference:
            return "retrieve_filtered_content"
            
        if any(keyword in user_message_lower for keyword in ['show', 'display', 'list', 'get', 'hierarchy']):
            return "retrieve_content"
            
        if any(keyword in user_message_lower for keyword in ['help', 'how', 'what', 'explain']):
            return "help_request"
            
        return "general_inquiry"
    
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
