from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from tools.knowledge_base_tools import KnowledgeBaseTools
from prompts.knowledge_base_prompts import prompts as kb_prompts
from prompts.multi_agent_prompts import prompts as ma_prompts


class ContentManagementAgent(BaseAgent):
    """
    Content Management Agent - Specialized agent for knowledge base operations.
    Implements robust content management strategies and executes all KB tools.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Combine base KB prompts with specialized multi-agent prompts
        base_prompt = kb_prompts.master_prompt()
        specialized_prompt = ma_prompts.content_management_prompt()
        system_prompt = f"{base_prompt}\n\n{specialized_prompt}"
        
        super().__init__("ContentManagement", llm, system_prompt)
        
        # Initialize knowledge base tools
        self.kb_tools = KnowledgeBaseTools()
        self.tools = self.kb_tools.tools()
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
    def process(self, state: AgentState) -> AgentState:
        """Process content management requests and execute operations"""
        self.log("Processing content management request")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from Supervisor
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            self.log("No workflow requests found")
            # If no specific workflow, check if this is a direct retrieve request
            last_message = state.get("messages", [])
            if last_message:
                last_user_msg = last_message[-1].content
                if "get_knowledge_bases_with_ids" in last_user_msg or "kbs =" in last_user_msg:
                    return self._handle_direct_retrieval_request(state, last_user_msg)
            return state
        
        # Get the latest workflow request
        latest_request = my_messages[-1]
        workflow_plan = latest_request.metadata.get("workflow_plan", {})
        
        # If no workflow plan, create one based on the request
        if not workflow_plan:
            self.log("No workflow plan found - creating one from request")
            workflow_plan = self._create_workflow_from_request(latest_request)
        
        self.log(f"Executing workflow: {workflow_plan.get('intent', 'unknown')}")
        
        # Execute the content management workflow
        try:
            result = self._execute_content_workflow(workflow_plan, state)
            
            # Extract intent from workflow plan for response metadata
            workflow_intent = workflow_plan.get("intent", "unknown")
            
            # Create success response for Supervisor
            response = self.create_message(
                recipient="Supervisor",
                message_type="workflow_response",
                content=result["message"],
                metadata={
                    "success": True, 
                    "results": result["data"],
                    "intent": workflow_intent  # Pass intent for proper response formatting
                }
            )
            
        except Exception as e:
            self.log(f"Error executing workflow: {str(e)}", "ERROR")
            
            # Extract intent from workflow plan for error response metadata
            workflow_intent = workflow_plan.get("intent", "unknown")
            
            # Create error response for Supervisor
            response = self.create_message(
                recipient="Supervisor", 
                message_type="workflow_response",
                content=f"Content management operation failed: {str(e)}",
                metadata={
                    "success": False, 
                    "error": str(e),
                    "intent": workflow_intent  # Pass intent for proper error formatting
                }
            )
        
        # Add response to agent messages
        state["agent_messages"].append(response)
        
        # Return control to Supervisor
        state["current_agent"] = "Supervisor"
        
        return state
    
    def _handle_direct_retrieval_request(self, state: AgentState, request: str) -> AgentState:
        """Handle direct retrieval requests like get_knowledge_bases_with_ids()"""
        self.log("Handling direct retrieval request")
        
        try:
            if "get_knowledge_bases_with_ids" in request:
                # Execute the KnowledgeBaseGetKnowledgeBases tool
                kb_tool = None
                for tool in self.tools:
                    if tool.name == "KnowledgeBaseGetKnowledgeBases":
                        kb_tool = tool
                        break
                
                if kb_tool:
                    result = kb_tool._run()
                    kbs_info = []
                    if result:
                        for kb in result:
                            kbs_info.append({
                                "id": kb.id,
                                "name": kb.title,
                                "description": kb.description,
                                "category": kb.category
                            })
                    
                    # Create response for user
                    response_content = f"Found {len(kbs_info)} knowledge bases:\n"
                    for kb in kbs_info:
                        response_content += f"• KB {kb['id']}: {kb['name']} ({kb['category']})\n"
                    
                    # Send response to UserProxy
                    user_response = self.create_message(
                        recipient="UserProxy",
                        message_type="direct_response",
                        content=response_content,
                        metadata={"kbs": kbs_info, "success": True}
                    )
                    
                    state["agent_messages"].append(user_response)
                    state["current_agent"] = "UserProxy"
                    
                else:
                    raise Exception("KnowledgeBaseGetKnowledgeBases tool not found")
            
        except Exception as e:
            self.log(f"Error handling direct request: {str(e)}", "ERROR")
            
            # Send error response to UserProxy
            error_response = self.create_message(
                recipient="UserProxy",
                message_type="direct_response",
                content=f"Error retrieving knowledge bases: {str(e)}",
                metadata={"success": False, "error": str(e)}
            )
            
            state["agent_messages"].append(error_response)
            state["current_agent"] = "UserProxy"
        
        return state
    
    def _create_workflow_from_request(self, request_message: AgentMessage) -> Dict[str, Any]:
        """Create a workflow plan from a request message"""
        content = request_message.content
        metadata = request_message.metadata or {}
        intent = metadata.get("intent", "retrieve_content")  # Get intent from metadata
        
        # Create basic workflow plan
        workflow_plan = {
            "intent": intent,
            "description": f"Execute knowledge base operation: {content}",
            "steps": [
                {
                    "action": "execute_kb_operation",
                    "description": content,
                    "tool_required": True
                }
            ],
            "original_request": content
        }
        
        return workflow_plan

    def _execute_content_workflow(self, workflow_plan: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute the content management workflow using available tools"""
        intent = workflow_plan.get("intent", "")
        steps = workflow_plan.get("steps", [])
        original_request = workflow_plan.get("original_request", "")
        
        self.log(f"Executing {len(steps)} workflow steps for intent: {intent}")
        
        # Special handling for set_knowledge_base_context intent
        if intent == "set_knowledge_base_context":
            self.log(f"DEBUG: Handling KB context setting for request: '{original_request}'")
            
            # Extract KB ID using regex before LLM processing
            import re
            kb_id_patterns = [
                r'kb\s+(\d+)',           # "kb 3", "kb  3"  
                r'use\s+kb\s+(\d+)',     # "use kb 3"
                r'switch\s+to\s+kb\s+(\d+)',  # "switch to kb 3"
                r'set\s+kb\s+(\d+)',     # "set kb 3"
                r'knowledge\s+base\s+(\d+)',  # "knowledge base 3"
            ]
            
            extracted_kb_id = None
            for pattern in kb_id_patterns:
                match = re.search(pattern, original_request.lower())
                if match:
                    extracted_kb_id = match.group(1)
                    self.log(f"DEBUG: Extracted KB ID '{extracted_kb_id}' using pattern '{pattern}'")
                    break
            
            if extracted_kb_id:
                # Call the tool directly with extracted ID
                self.log(f"DEBUG: Calling KnowledgeBaseSetContext directly with KB ID: {extracted_kb_id}")
                try:
                    set_context_tool = next((t for t in self.tools if t.name == 'KnowledgeBaseSetContext'), None)
                    if set_context_tool:
                        # Use correct tool input format
                        tool_input = {"knowledge_base_id": extracted_kb_id}
                        result = set_context_tool.run(tool_input)
                        self.log(f"DEBUG: Tool result: {result}")
                        
                        if result.get("success"):
                            # Update state
                            state["knowledge_base_id"] = result.get("knowledge_base_id")
                            state["knowledge_base_name"] = result.get("knowledge_base_name")
                            self.log(f"Updated knowledge base context to: {result.get('knowledge_base_name')} (ID: {result.get('knowledge_base_id')})")
                            
                            return {
                                "success": True,
                                "message": result.get("message", f"Knowledge base context set to KB {extracted_kb_id}"),
                                "data": result
                            }
                        else:
                            return {
                                "success": False,
                                "message": f"Failed to set KB context: {result.get('error', 'Unknown error')}",
                                "data": result
                            }
                    else:
                        self.log("DEBUG: KnowledgeBaseSetContext tool not found")
                        return {
                            "success": False,
                            "message": "KnowledgeBaseSetContext tool not available",
                            "data": {}
                        }
                except Exception as e:
                    self.log(f"DEBUG: Error calling tool directly: {str(e)}")
                    # Fall back to LLM processing
                    pass
            else:
                self.log(f"DEBUG: Could not extract KB ID from request: '{original_request}'")
                # Fall back to LLM processing
        
        # Original LLM-based processing for other intents or fallback
        # Create messages for LLM with tools
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
Execute the following content management workflow:

Intent: {intent}
Workflow Plan: {workflow_plan.get('description', '')}
Steps: {[step['description'] for step in steps]}

Current Knowledge Base ID: {state.get('knowledge_base_id', 'Not specified')}
Current Section Context: {state.get('current_section', 'Not specified')}
Original Request: {original_request}

CRITICAL INSTRUCTIONS FOR CONTENT CREATION:
- If intent is "create_content":
  * Analyze the original request to understand what content to create (categories, articles, topics)
  * First create any missing categories using KnowledgeBaseInsertArticle with parent_id=null
  * Then create sub-articles under the categories using KnowledgeBaseInsertArticle with appropriate parent_id
  * Use meaningful titles and comprehensive content for each article
  * Ensure proper hierarchical structure (categories as parent articles, topics as child articles)
  * For "Family Finance" category example: create category first, then create articles like "Family Budgeting", "Teaching Kids About Money", etc.
  * Always validate knowledge base context first before creating content
  * REQUIRED FIELDS for KnowledgeBaseInsertArticle tool:
    - title: Clear, descriptive title for the article/category
    - content: Comprehensive content with helpful information (minimum 200 characters)
    - author_id: Always use 1 (default system user for AI-generated content)
    - parent_id: Use null for main categories, or parent article ID for sub-articles
    - knowledge_base_id: Use the current knowledge base ID from state
  * DO NOT use KnowledgeBaseGetArticleHierarchy for creation - that's only for reading existing content
  * EXAMPLE for creating "Family Finance" category:
    article={{"title": "Family Finance", "content": "Comprehensive guide covering all aspects of family financial planning, including budgeting for families, teaching children about money, saving for family goals, and managing household finances effectively. This category includes strategies for dual-income families, single-parent financial planning, and teaching financial literacy to children of all ages.", "author_id": 1, "parent_id": null, "knowledge_base_id": 1}}
  * EXAMPLE for creating sub-article under Family Finance:
    article={{"title": "Family Budgeting Strategies", "content": "Effective budgeting techniques specifically designed for families, including methods for tracking family expenses, allocating funds for children's needs, planning for family activities, and managing variable family income. Topics include envelope budgeting for families, zero-based budgeting with kids, and emergency fund planning for households.", "author_id": 1, "parent_id": [Family Finance category ID], "knowledge_base_id": 1}}

CRITICAL INSTRUCTIONS FOR KNOWLEDGE BASE CONTEXT SETTING:
- If intent is "set_knowledge_base_context":
  * Look at the original request to extract the knowledge base ID number
  * Common patterns: "use kb 4", "switch to kb 2", "set kb 1", "kb 3"
  * Extract just the number (e.g., "4" from "use kb 4")
  * Call KnowledgeBaseSetContext with knowledge_base_id="[extracted_number]"
  * REQUIRED: Must call KnowledgeBaseSetContext tool to actually set the context
  * Do NOT use KnowledgeBaseGetKnowledgeBases - that's only for listing available KBs

Step-by-step process:
1. Look at original request: "{workflow_plan.get('original_request', 'Not provided')}"
2. Extract the KB ID number from the request
3. Call KnowledgeBaseSetContext with that number as a string

Examples:
- Original request "use kb 1" → extract "1" → call KnowledgeBaseSetContext(knowledge_base_id="1")
- Original request "switch to kb 4" → extract "4" → call KnowledgeBaseSetContext(knowledge_base_id="4")  
- Original request "kb 2" → extract "2" → call KnowledgeBaseSetContext(knowledge_base_id="2")

CRITICAL INSTRUCTIONS FOR CONTENT GAP ANALYSIS:
- If intent is "analyze_content_gaps":
  * Use the KnowledgeBaseAnalyzeContentGaps tool with the current knowledge_base_id
  * This dedicated tool performs comprehensive gap analysis and provides specific recommendations
  * DO NOT just retrieve and display the hierarchy - use the specialized analysis tool
  * The tool will analyze content structure, identify missing topics, and suggest improvements
  * Present the analysis results clearly to the user with actionable recommendations
  * Focus on providing value through specific, practical content suggestions

Please execute the appropriate knowledge base operations to fulfill this request.
Use the available tools to complete all necessary steps.

IMPORTANT: 
- Always validate knowledge base context first
- Use proper error handling for all operations
- Include the actual tool results in your response to the user
- For retrieval operations, show the complete list of items found
- For context setting, confirm the operation with specific details
- Provide comprehensive feedback on results
- Maintain content organization best practices
            """)
        ]
        
        # Check for loop prevention - track consecutive tool calls
        consecutive_tool_calls = state.get("consecutive_tool_calls", 0)
        last_tool_result = state.get("last_tool_result", "")
        
        # Add loop prevention warning if too many consecutive tool calls
        if consecutive_tool_calls >= 3:
            tool_warning = "\n\nWARNING: You've made several consecutive tool calls. Consider providing a comprehensive final answer instead of calling more tools."
            messages.append(HumanMessage(content=tool_warning))
        
        # Invoke LLM with tools to execute the workflow
        response = self.llm_with_tools.invoke(messages)
        
        # Track if this response has tool calls for loop prevention
        has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
        new_consecutive_calls = consecutive_tool_calls + 1 if has_tool_calls else 0
        
        # Update state with loop prevention tracking
        state["consecutive_tool_calls"] = new_consecutive_calls
        
        # Check if the response contains tool calls
        if has_tool_calls:
            self.log(f"Executing {len(response.tool_calls)} tool calls")
            
            # Execute tool calls and collect results
            tool_results = []
            combined_results = []
            
            for tool_call in response.tool_calls:
                try:
                    tool_result = self._execute_tool_call(tool_call)
                    tool_results.append(tool_result)
                    combined_results.append(str(tool_result))
                    
                    # Check if this was a KnowledgeBaseSetContext call and update state
                    if tool_call.get("name") == "KnowledgeBaseSetContext":
                        # Tool result is wrapped in "result" field by _execute_tool_call
                        kb_result = tool_result.get("result", {})
                        if kb_result.get("success"):
                            state["knowledge_base_id"] = kb_result.get("knowledge_base_id")
                            state["knowledge_base_name"] = kb_result.get("knowledge_base_name")
                            self.log(f"Updated knowledge base context to: {kb_result.get('knowledge_base_name')} (ID: {kb_result.get('knowledge_base_id')})")
                    
                    # Check if this was a KnowledgeBaseSetArticleContext call and update state
                    elif tool_call.get("name") == "KnowledgeBaseSetArticleContext":
                        # Tool result is wrapped in "result" field by _execute_tool_call
                        article_result = tool_result.get("result", {})
                        if article_result.get("success"):
                            state["knowledge_base_id"] = article_result.get("knowledge_base_id")
                            state["article_id"] = article_result.get("article_id")
                            self.log(f"Updated article context to: {article_result.get('article_id')} in KB {article_result.get('knowledge_base_id')}")
                            
                except Exception as e:
                    self.log(f"Tool execution error: {str(e)}", "ERROR")
                    combined_results.append(f"Error: {str(e)}")
            
            # Store last tool result for repetition detection
            combined_result_str = " | ".join(combined_results)
            state["last_tool_result"] = combined_result_str[:500]  # Truncate for memory
            
            # Check for result repetition (simple detection)
            if last_tool_result and combined_result_str == last_tool_result:
                repetition_warning = "\n\nNote: This appears to be a repeated operation. Consider providing a final answer."
                response.content = response.content + repetition_warning if response.content else repetition_warning
            
            return {
                "message": response.content if response.content.strip() else combined_result_str,
                "data": {
                    "tool_results": tool_results,
                    "combined_results": combined_result_str,
                    "workflow_completed": True,
                    "intent": intent
                }
            }
        else:
            # No tool calls, return the response content
            return {
                "message": response.content,
                "data": {
                    "workflow_completed": True,
                    "intent": intent,
                    "note": "No tool operations required"
                }
            }
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool call"""
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        
        self.log(f"Executing tool: {tool_name}")
        
        # Find the tool by name
        tool = None
        for available_tool in self.tools:
            if available_tool.name == tool_name:
                tool = available_tool
                break
        
        if not tool:
            raise Exception(f"Tool not found: {tool_name}")
        
        # Execute the tool
        try:
            result = tool._run(**tool_args)
            return {
                "tool": tool_name,
                "success": True,
                "result": result
            }
        except Exception as e:
            raise Exception(f"Tool execution failed for {tool_name}: {str(e)}")
    
    def validate_knowledge_base_context(self, state: AgentState) -> bool:
        """Validate that knowledge base context is properly established"""
        kb_id = state.get("knowledge_base_id")
        
        if not kb_id:
            self.log("No knowledge base context established", "WARNING")
            return False
        
        # Validate KB exists using tools
        try:
            # Use get knowledge base tool to validate
            kb_tool = None
            for tool in self.tools:
                if tool.name == "KnowledgeBaseGetKnowledgeBases":
                    kb_tool = tool
                    break
            
            if kb_tool:
                kb_list = kb_tool._run()
                valid_ids = [str(kb.id) for kb in kb_list] if kb_list else []
                
                if kb_id not in valid_ids:
                    self.log(f"Invalid knowledge base ID: {kb_id}", "ERROR")
                    return False
                
            return True
            
        except Exception as e:
            self.log(f"Error validating KB context: {str(e)}", "ERROR")
            return False
    
    def get_content_management_strategies(self) -> Dict[str, str]:
        """Return available content management strategies"""
        return {
            "hierarchical_organization": "Organize content in logical hierarchical structures",
            "strategic_tagging": "Implement comprehensive tagging for discoverability",
            "content_lifecycle": "Manage content from creation to archival",
            "quality_assurance": "Ensure content meets quality and consistency standards",
            "relationship_mapping": "Map and maintain content relationships",
            "search_optimization": "Optimize content for search and discovery",
            "structure_validation": "Validate and maintain knowledge base structure"
        }
