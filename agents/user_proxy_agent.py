from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from prompts.multi_agent_prompts import prompts


class UserProxyAgent(BaseAgent):
    """
    User Proxy Agent - Handles direct user communication only.
    This agent serves as the interface between the user and the multi-agent system.
    
    Architecture Flow:
    User ↔ UserProxy → Router → Supervisor → ContentManager (Create/Update/Delete)
                              ↓              ↘
                         ContentRetrieval    Parallel Processing  
                           (Read/Search)           ↙
                              ↓                  ↙
                         Final Response ←──────┘
    
    Responsibilities:
    - Receive user input and route to Router for intent classification
    - Receive final responses from Supervisor (who coordinates all content agents)
    - Format technical responses into user-friendly messages
    - Handle simple direct responses for basic queries (via Router)
    - Provide conversation management and error handling
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        system_prompt = prompts.user_proxy_prompt()
        super().__init__("UserProxy", llm, system_prompt)

    def process(self, state: AgentState) -> AgentState:
        """Process user input and handle direct responses"""
        self.log("Processing user interaction")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Safety check for infinite loops
        recursions = state.get("recursions", 0)
        if recursions > 8:  # Increased limit to allow normal multi-agent workflows
            self.log(f"Maximum recursions ({recursions}) reached, stopping workflow to prevent infinite loop")
            state["current_agent"] = None
            # Add error message to user
            error_message = AIMessage(content="I apologize, but I encountered an issue processing your request. Please try rephrasing your question or starting a new conversation.")
            state["messages"].append(error_message)
            return state
        
        messages = state.get("messages", [])
        if not messages:
            return state
            
        last_message = messages[-1]
        
        # Check for messages from other agents first
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        # Get list of already processed message timestamps to avoid reprocessing
        processed_messages = state.get("processed_workflow_messages", [])
        
        # Check if we have any unprocessed messages directed to us
        has_unprocessed_messages = False
        if my_messages:
            for msg in my_messages:
                message_id = f"{msg.sender}_{msg.timestamp}_{msg.message_type}"
                if message_id not in processed_messages:
                    has_unprocessed_messages = True
                    break
        
        # Check if this is a new user message that needs routing
        is_new_user_message = False
        if (hasattr(last_message, '__class__') and 
            last_message.__class__.__name__ == 'HumanMessage'):
            
            # Check if this specific user message has already been routed
            user_message_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            existing_router_msgs = [msg for msg in agent_messages 
                                   if msg.sender == "UserProxy" and msg.recipient == "Router" 
                                   and msg.message_type == "routing_request"
                                   and user_message_content in msg.content]
            
            # Only consider it new if we haven't already routed it
            is_new_user_message = len(existing_router_msgs) == 0
        
        # If there are no unprocessed messages for us and no new user message to route, stop processing
        if not has_unprocessed_messages and not is_new_user_message:
            self.log("No new messages to process, stopping workflow")
            state["current_agent"] = None
            return state
        
        if my_messages:
            # Handle various types of messages directed to UserProxy
            latest_message = my_messages[-1]
            message_id = f"{latest_message.sender}_{latest_message.timestamp}_{latest_message.message_type}"
            
            if latest_message.message_type == "direct_response_request" and message_id not in processed_messages:
                # Handle direct response request from Router (for simple queries)
                self.log("Processing direct response request from Router")
                
                user_message = latest_message.content
                response = self._generate_direct_response(user_message, state)
                ai_message = AIMessage(content=response)
                state["messages"].append(ai_message)
                
                # Mark as processed
                if "processed_workflow_messages" not in state:
                    state["processed_workflow_messages"] = []
                state["processed_workflow_messages"].append(message_id)
                
                # Clear current_agent to stop the workflow
                state["current_agent"] = None
                
                self.log("Provided direct response to user - conversation complete")
                return state
                
            elif (latest_message.message_type in ["workflow_complete", "workflow_error", "supervisor_final_response"] and 
                  message_id not in processed_messages):
                
                self.log(f"Processing workflow result: {latest_message.message_type}")
                
                # Generate user-friendly response based on the workflow result
                # This handles responses from Supervisor who has managed the entire workflow
                user_friendly_response = self.format_response_for_user(
                    latest_message.content,
                    latest_message.metadata
                )
                
                # Add final AI message to conversation
                ai_message = AIMessage(content=user_friendly_response)
                state["messages"].append(ai_message)
                
                # Mark this specific message as processed
                if "processed_workflow_messages" not in state:
                    state["processed_workflow_messages"] = []
                state["processed_workflow_messages"].append(message_id)
                
                # Clear current_agent to stop the workflow
                state["current_agent"] = None
                
                self.log("Provided workflow result to user - conversation complete")
                return state
        
        # Handle new user input - route to Router for intent classification
        if is_new_user_message:
            user_message_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # Send request to Router for intent classification and routing
            router_message = self.create_message(
                recipient="Router",
                message_type="routing_request",
                content=f"User request: {user_message_content}",
                metadata={"original_message": str(last_message)}
            )
            
            # Add to agent messages
            if "agent_messages" not in state:
                state["agent_messages"] = []
            state["agent_messages"].append(router_message)
            
            # Set router as next agent
            state["current_agent"] = "Router"
            
            self.log("Sent user request to Router for classification and routing")
        
        return state

    def _generate_direct_response(self, user_message: str, state: AgentState) -> str:
        """Generate a direct response for simple queries with current context"""
        # Get current context information
        kb_id = state.get("knowledge_base_id")
        kb_name = state.get("knowledge_base_name", f"KB {kb_id}" if kb_id else None)
        
        # Build context for the response
        context_info = ""
        if kb_id:
            context_info = f"\n\nCurrent context: Knowledge Base {kb_name} (ID: {kb_id}) is active."
        else:
            context_info = "\n\nNo knowledge base is currently in context."
        
        # Use LLM for generating contextual responses
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""Provide a helpful response to this user message: {user_message}

Context Information:{context_info}

For questions about current knowledge base context, provide specific information about what is currently active.
If they ask about setting context, explain how to use "use kb [number]" commands.""")
        ]
        
        response = self.llm.invoke(messages)
        return response.content

    def format_response_for_user(self, agent_response: str, metadata: Dict[str, Any]) -> str:
        """Format agent responses into user-friendly messages"""
        intent = metadata.get("intent", "unknown")
        sender = metadata.get("sender", "")
        operation_type = metadata.get("operation_type", "")
        
        # Create contextual intro based on intent, sender, and operation type
        if intent == "create_content":
            intro = "✅ **Content Creation Complete**\n\n"
        elif intent == "analyze_content_gaps":
            intro = "🔍 **Content Gap Analysis Results**\n\n"
        elif intent == "retrieve_content" or operation_type == "retrieval":
            intro = "📋 **Content Retrieved**\n\n"
        elif intent == "search_content":
            intro = "🔍 **Search Results**\n\n"
        elif intent == "update_content":
            intro = "✏️ **Content Updated**\n\n"
        elif intent == "set_knowledge_base_context":
            intro = "🔧 **Knowledge Base Context Set**\n\n"
        elif intent == "set_article_context":
            intro = "📄 **Article Context Set**\n\n"
        elif intent == "parallel_content_operation":
            intro = "⚡ **Multi-Operation Complete**\n\n"
        elif sender == "Supervisor":
            intro = "🎯 **Task Supervised and Completed**\n\n"
        elif sender == "ContentRetrieval":
            intro = "📖 **Content Retrieved**\n\n"
        elif sender == "ContentManager" or sender == "ContentManagement":
            intro = "📝 **Content Operation Complete**\n\n"
        else:
            intro = "✅ **Task Complete**\n\n"
        
        # Clean up agent response - remove technical details but preserve actual content
        clean_response = agent_response
        
        # Remove common agent artifacts but keep meaningful content
        technical_patterns = [
            "Tool call successful",
            "Function executed:",
            "Database operation completed",
            "SQL query executed",
            "Operation successful",
            "Workflow step completed",
            "Agent message sent",
            "Processing complete",
            "Retrieval operation completed",
            "Content operation finished"
        ]
        
        for pattern in technical_patterns:
            clean_response = clean_response.replace(pattern, "")
        
        # If the response is too generic or empty, try to use metadata
        if not clean_response.strip() or clean_response.strip() in ["Task completed successfully", "Operation completed"]:
            # Try to extract meaningful information from metadata
            results = metadata.get("results", {})
            if results and isinstance(results, dict):
                # First try combined_results which has the raw tool output
                combined_results = results.get("combined_results", "")
                if combined_results and combined_results.strip():
                    clean_response = combined_results.strip()
                else:
                    # Check for tool results
                    tool_results = results.get("tool_results", [])
                    if tool_results:
                        result_content = []
                        for result in tool_results:
                            if isinstance(result, dict):
                                # Extract the actual result data
                                tool_result = result.get("result", result)
                                
                                # Handle string results from tools (like KnowledgeBaseGetArticleHierarchy)
                                if isinstance(tool_result, str) and tool_result.strip():
                                    result_content.append(tool_result.strip())
                                elif isinstance(tool_result, (list, tuple)) and len(tool_result) > 0:
                                    # Format list results (like article hierarchies)
                                    for item in tool_result:
                                        if isinstance(item, dict):
                                            # Format article entries
                                            if 'title' in item and 'id' in item:
                                                result_content.append(f"• {item['title']} (ID: {item['id']})")
                                            elif 'name' in item and 'id' in item:
                                                result_content.append(f"• {item['name']} (ID: {item['id']})")
                                            else:
                                                result_content.append(f"• {str(item)}")
                                        else:
                                            result_content.append(f"• {str(item)}")
                                elif isinstance(tool_result, dict) and tool_result:
                                    result_content.append(str(tool_result))
                        
                        if result_content:
                            clean_response = "\n".join(result_content)
                        elif not clean_response.strip():
                            # Fallback: show the count of results
                            count = sum(len(r.get("result", [])) if isinstance(r.get("result"), list) else 1 
                                      for r in tool_results if isinstance(r, dict))
                            if count > 0:
                                clean_response = f"Found {count} items."
        
        # Format the final response
        formatted_response = f"{intro}{clean_response.strip()}"
        
        return formatted_response
