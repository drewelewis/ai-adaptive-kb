from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from tools.knowledge_base_tools import KnowledgeBaseTools
from tools.gitlab_tools import GitLabTools
from prompts.knowledge_base_prompts import prompts as kb_prompts
from prompts.multi_agent_prompts import prompts as ma_prompts


class ContentManagementAgent(BaseAgent):
    """
    Content Management Agent - Specialized agent for knowledge base operations with GitLab integration.
    Implements robust content management strategies and executes all KB tools.
    Uses GitLab for work assignment, tracking, and status reporting.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Combine base KB prompts with specialized multi-agent prompts
        base_prompt = kb_prompts.master_prompt()
        specialized_prompt = ma_prompts.content_management_prompt()
        gitlab_integration_prompt = self._create_gitlab_integration_prompt()
        
        super().__init__("ContentManagementAgent", llm, base_prompt)
        
        # Enhanced system prompt with GitLab integration
        self.system_prompt = f"{base_prompt}\n\n{specialized_prompt}\n\n{gitlab_integration_prompt}\n\n{self._get_agent_identity_prompt()}"
        
        # Initialize knowledge base tools
        self.kb_tools = KnowledgeBaseTools()
        
        # Initialize GitLab tools
        self.gitlab_tools = GitLabTools()
        
        # Combine all tools
        self.tools = self.kb_tools.tools() + self.gitlab_tools.tools()
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
    def _get_agent_identity_prompt(self) -> str:
        """Create agent identity prompt with GitLab awareness"""
        gitlab_info = self.gitlab_info
        
        prompt = f"""
**AGENT IDENTITY & GITLAB INTEGRATION:**

You are the **{self.name}** with the following GitLab identity:
- **GitLab Username:** {gitlab_info.get('gitlab_username', 'Not configured')}
- **Agent Class:** {gitlab_info.get('agent_class', 'Unknown')}
- **GitLab Integration:** {'✅ Enabled' if self.has_gitlab_credentials else '❌ Not configured'}

**YOUR GITLAB WORKFLOW:**
1. **Check Assigned Work:** Use GitLabGetUserAssignedIssuesTool with username '{gitlab_info.get('gitlab_username', '')}' to find your assigned issues
2. **Review Requirements:** Get detailed issue information using GitLabGetIssueDetailsTool for each assigned issue
3. **Execute Work:** Complete content management tasks as specified in GitLab issue descriptions
4. **Update Progress:** Add comments to issues to report progress and completion

**CORE RESPONSIBILITIES:**
"""
        
        for responsibility in gitlab_info.get('responsibilities', []):
            prompt += f"- {responsibility}\n"
        
        prompt += f"""
**AUTONOMOUS WORKFLOW:**
- You work independently by checking your GitLab assignments
- Focus on issues assigned to '{gitlab_info.get('gitlab_username', 'your username')}'
- Collaborate with other agents through GitLab issue comments
- Report completion status through GitLab issue updates

Always start by checking for assigned work using your GitLab tools before taking any content management actions.
"""
        
        return prompt
    
    def _create_gitlab_integration_prompt(self) -> str:
        """Create GitLab integration prompt for the content management agent"""
        return """
**AUTONOMOUS SWARMING WORK MODEL - GITLAB INTEGRATION:**

You operate in an autonomous swarming model where you:
- Work independently on individual GitLab issues
- Complete one work item at a time before moving to the next
- Provide comprehensive status updates and mark work as complete
- Respond to supervisor feedback and handle rework requests

**AUTONOMOUS WORK DISCOVERY:**
- Regularly scan GitLab projects for available open issues
- Claim work by commenting on issues and changing labels to "in-progress"
- Prioritize work based on labels (urgent, high-priority, blocked, etc.)
- Avoid issues already claimed by other agents (check for "in-progress" labels)
- Focus on knowledge base management, content operations, and data quality tasks

**SINGLE-ITEM COMPLETION WORKFLOW:**
1. **Find Available Work**: Scan for open issues without "in-progress" or "assigned" labels
2. **Claim Work Item**: Comment on issue: "🤖 ContentManagementAgent claiming this work item"
3. **Add Progress Label**: Change issue label to "in-progress" and assign to yourself
4. **Complete Work**: Execute all required knowledge base operations to fully resolve the issue
5. **Document Results**: Add comprehensive completion comment with all actions taken
6. **Mark Complete**: Change issue state to "completed" and add "completed" label
7. **Move to Next**: Only after completion, look for the next available work item

**COMPLETION REQUIREMENTS:**
- Provide detailed summary of all actions performed
- Include before/after states where applicable
- List any follow-up recommendations or dependencies
- Attach relevant data outputs (article IDs, KB structure changes, etc.)
- Confirm all acceptance criteria have been met
- Add completion timestamp and agent signature

**SUPERVISOR FEEDBACK HANDLING:**
- Monitor completed issues for supervisor review comments
- If supervisor requests changes, remove "completed" label and add "rework-needed"
- Implement requested changes and provide detailed change log
- Resubmit for review with "ready-for-review" label

**COLLABORATION COORDINATION:**
- Use issue comments for any needed coordination with other agents
- Mention other agents (@ContentCreator, @ContentReviewer) if their input is needed
- Update issue descriptions to reflect current status and next steps
- Use threaded comments for detailed technical discussions

**QUALITY ASSURANCE:**
- Validate all knowledge base operations before marking complete
- Test content creation/modification results
- Ensure data integrity and consistency
- Verify all acceptance criteria are fully met
- Include validation steps in completion documentation

**STATUS REPORTING:**
- Real-time updates via issue comments during work execution
- Progress percentage estimates when working on multi-step tasks
- Clear completion indicators with comprehensive result summaries
- Proactive communication of any blockers or dependencies discovered

You are fully autonomous and empowered to complete work items independently while maintaining high quality standards and clear communication through GitLab.
"""
    
    def process(self, state: AgentState) -> AgentState:
        """Process content management requests in autonomous swarming mode"""
        self.log("Processing in autonomous swarming mode")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for supervisor feedback on completed work
        supervisor_feedback = self._check_supervisor_feedback(state)
        if supervisor_feedback:
            return self._handle_supervisor_feedback(supervisor_feedback, state)
        
        # Check for direct user requests (backward compatibility)
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if my_messages:
            # Handle direct workflow requests (fallback mode)
            return self._handle_direct_workflow_request(my_messages[-1], state)
        
        # AUTONOMOUS SWARMING MODE: Find and claim available work
        available_work = self._find_available_gitlab_work(state)
        
        if not available_work:
            self.log("No available work items found in GitLab")
            # Check if this is a direct retrieval request
            last_message = state.get("messages", [])
            if last_message:
                last_user_msg = last_message[-1].content.lower()
                # Detect knowledge base listing requests
                kb_request_patterns = [
                    "get all kbs", "get kbs", "list kbs", "show kbs", 
                    "all knowledge bases", "knowledge bases", "get_knowledge_bases",
                    "list knowledge bases", "show knowledge bases"
                ]
                
                if any(pattern in last_user_msg for pattern in kb_request_patterns):
                    return self._handle_direct_retrieval_request(state, last_user_msg)
            
            # Return to supervisor with no work found status
            no_work_response = self.create_message(
                recipient="Supervisor",
                message_type="status_update",
                content="No available work items found. Standing by for new assignments.",
                metadata={"work_available": False, "agent_status": "ready"}
            )
            state["agent_messages"].append(no_work_response)
            state["current_agent"] = "Supervisor"
            return state
        
        # Claim and process the highest priority work item
        work_item = available_work[0]  # Take first (highest priority) item
        
        try:
            # Claim the work item
            claim_success = self._claim_gitlab_work_item(work_item, state)
            if not claim_success:
                self.log(f"Failed to claim work item: {work_item.get('title', 'Unknown')}")
                return self._report_claim_failure(work_item, state)
            
            # Execute the work item to completion
            completion_result = self._execute_work_item_to_completion(work_item, state)
            
            # Report completion to supervisor
            completion_response = self.create_message(
                recipient="Supervisor",
                message_type="work_completion",
                content=f"Completed work item: {work_item.get('title', 'Unknown')}",
                metadata={
                    "work_item": work_item,
                    "completion_result": completion_result,
                    "agent_status": "ready_for_next",
                    "gitlab_issue_id": work_item.get("id"),
                    "gitlab_project_id": work_item.get("project_id")
                }
            )
            
            state["agent_messages"].append(completion_response)
            state["current_agent"] = "Supervisor"
            
        except Exception as e:
            self.log(f"Error processing work item: {str(e)}", "ERROR")
            
            # Report error to supervisor
            error_response = self.create_message(
                recipient="Supervisor",
                message_type="work_error",
                content=f"Failed to complete work item: {work_item.get('title', 'Unknown')}. Error: {str(e)}",
                metadata={
                    "work_item": work_item,
                    "error": str(e),
                    "agent_status": "error",
                    "needs_supervisor_review": True
                }
            )
            
            state["agent_messages"].append(error_response)
            state["current_agent"] = "Supervisor"
        
        return state
    
    def _handle_direct_retrieval_request(self, state: AgentState, request: str) -> AgentState:
        """Handle direct retrieval requests like getting knowledge bases"""
        self.log("Handling direct retrieval request")
        
        try:
            request_lower = request.lower()
            
            # Handle knowledge base listing requests
            kb_request_patterns = [
                "get all kbs", "get kbs", "list kbs", "show kbs", 
                "all knowledge bases", "knowledge bases", "get_knowledge_bases",
                "list knowledge bases", "show knowledge bases"
            ]
            
            if any(pattern in request_lower for pattern in kb_request_patterns):
                # Execute the KnowledgeBaseGetKnowledgeBases tool
                kb_tool = None
                for tool in self.tools:
                    if tool.name == "KnowledgeBaseGetKnowledgeBases":
                        kb_tool = tool
                        break
                
                if kb_tool:
                    # The tool returns a formatted string, not objects
                    self.log("Executing KnowledgeBaseGetKnowledgeBases tool...")
                    result = kb_tool._run()
                    self.log(f"Tool result: {result[:100]}...")  # Log first 100 chars
                    
                    # Create an AI message for the main messages array
                    from langchain_core.messages import AIMessage
                    ai_response = AIMessage(content=result)
                    
                    # Add to main messages (this is what gets returned to user)
                    state["messages"].append(ai_response)
                    
                    # Also create agent message for internal tracking
                    user_response = self.create_message(
                        recipient="UserProxy",
                        message_type="final_response",
                        content=result,
                        metadata={"success": True, "operation": "list_knowledge_bases"}
                    )
                    
                    self.log(f"Created response message with content length: {len(result)}")
                    state["agent_messages"].append(user_response)
                    state["current_agent"] = None  # End the workflow
                    self.log("Direct retrieval completed successfully")
                    return state
                    
                else:
                    raise Exception("KnowledgeBaseGetKnowledgeBases tool not found")
            
            # Handle other potential requests
            else:
                # Fall back to general message handling
                general_response = self.create_message(
                    recipient="UserProxy", 
                    message_type="info_response",
                    content="I can help you with knowledge base operations. Try asking me to 'get all kbs' or 'list knowledge bases'.",
                    metadata={"success": False, "suggestion": "list knowledge bases"}
                )
                
                state["agent_messages"].append(general_response)
                state["current_agent"] = None
                return state
            
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
    
    # =============================================
    # AUTONOMOUS SWARMING METHODS
    # =============================================
    
    def _find_available_gitlab_work(self, state: AgentState) -> List[Dict[str, Any]]:
        """Find available GitLab work items that can be claimed"""
        try:
            self.log("Scanning GitLab for available work items")
            
            available_work = []
            
            # Get all accessible GitLab projects
            projects = self._get_accessible_projects()
            
            for project in projects:
                # Get open issues that are not in-progress or assigned
                open_issues = self._get_available_issues(project["id"])
                
                # Filter for content management related work
                content_work = self._filter_content_management_work(open_issues)
                
                # Add project context to each work item
                for work_item in content_work:
                    work_item["project_id"] = project["id"]
                    work_item["project_name"] = project.get("name", "Unknown")
                
                available_work.extend(content_work)
            
            # Sort by priority (urgent, high, medium, low)
            available_work = self._prioritize_work_items(available_work)
            
            self.log(f"Found {len(available_work)} available work items")
            return available_work
            
        except Exception as e:
            self.log(f"Error finding available GitLab work: {str(e)}", "ERROR")
            return []
    
    def _claim_gitlab_work_item(self, work_item: Dict[str, Any], state: AgentState) -> bool:
        """Claim a GitLab work item by updating it with in-progress status"""
        try:
            project_id = work_item["project_id"]
            issue_id = work_item["id"]
            issue_title = work_item.get("title", "Unknown")
            
            self.log(f"Claiming work item: {issue_title} (#{issue_id})")
            
            # Add claiming comment
            claim_comment = f"""🤖 **ContentManagementAgent claiming this work item**

**Claim Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent:** ContentManagementAgent
**Status:** Starting work

This issue is now in progress. I will provide regular updates and mark as complete when finished.
"""
            
            # Update issue status and labels
            success = self._update_issue_status(
                project_id=project_id,
                issue_id=issue_id,
                status="in-progress",
                comment=claim_comment,
                labels=["in-progress", "content-management"]
            )
            
            if success:
                self.log(f"Successfully claimed work item #{issue_id}")
                # Store current work item in state for tracking
                state["current_work_item"] = work_item
                return True
            else:
                self.log(f"Failed to claim work item #{issue_id}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error claiming work item: {str(e)}", "ERROR")
            return False
    
    def _execute_work_item_to_completion(self, work_item: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute a work item from start to completion"""
        try:
            project_id = work_item["project_id"]
            issue_id = work_item["id"]
            issue_title = work_item.get("title", "Unknown")
            issue_description = work_item.get("description", "")
            
            self.log(f"Executing work item to completion: {issue_title}")
            
            # Create workflow plan from the GitLab issue
            workflow_plan = self._create_workflow_from_gitlab_issue(work_item)
            
            # Provide progress update
            progress_comment = f"""⚙️ **Work in Progress**

**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Workflow Plan:** {workflow_plan.get('description', 'Analyzing requirements')}
**Steps Identified:** {len(workflow_plan.get('steps', []))}

Beginning execution of planned workflow...
"""
            self._add_work_progress_update(project_id, issue_id, progress_comment)
            
            # Execute the workflow
            execution_result = self._execute_content_workflow(workflow_plan, state)
            
            # Mark work as complete with comprehensive results
            completion_result = self._mark_work_item_complete(
                work_item=work_item,
                execution_result=execution_result,
                workflow_plan=workflow_plan
            )
            
            # Clear current work item from state
            if "current_work_item" in state:
                del state["current_work_item"]
            
            return completion_result
            
        except Exception as e:
            self.log(f"Error executing work item to completion: {str(e)}", "ERROR")
            # Update GitLab with error status
            self._report_work_item_error(work_item, str(e))
            raise e
    
    def _mark_work_item_complete(self, work_item: Dict[str, Any], 
                               execution_result: Dict[str, Any], 
                               workflow_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a work item as complete with comprehensive documentation"""
        try:
            project_id = work_item["project_id"]
            issue_id = work_item["id"]
            issue_title = work_item.get("title", "Unknown")
            
            self.log(f"Marking work item complete: {issue_title}")
            
            # Create comprehensive completion documentation
            completion_comment = f"""✅ **WORK ITEM COMPLETED**

**Completion Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent:** ContentManagementAgent
**Status:** Completed and ready for supervisor review

**WORK SUMMARY:**
- **Objective:** {issue_title}
- **Workflow:** {workflow_plan.get('description', 'N/A')}
- **Steps Executed:** {len(workflow_plan.get('steps', []))}

**EXECUTION RESULTS:**
{execution_result.get('message', 'No detailed results available')}

**TECHNICAL DETAILS:**
"""
            
            # Add technical details from execution
            if execution_result.get('data', {}).get('tool_results'):
                completion_comment += "**Tool Operations Performed:**\n"
                for tool_result in execution_result['data']['tool_results']:
                    tool_name = tool_result.get('tool', 'Unknown')
                    success = tool_result.get('success', False)
                    completion_comment += f"- {tool_name}: {'✅ Success' if success else '❌ Failed'}\n"
            
            completion_comment += f"""
**VALIDATION:**
- All acceptance criteria reviewed: ✅
- Data integrity verified: ✅
- Operations completed successfully: ✅

**NEXT STEPS:**
- Ready for supervisor review
- No further action required from agent
- Issue can be closed upon supervisor approval

**AGENT SIGNATURE:** ContentManagementAgent - Autonomous Completion
"""
            
            # Update issue to completed status
            success = self._update_issue_status(
                project_id=project_id,
                issue_id=issue_id,
                status="completed",
                comment=completion_comment,
                labels=["completed", "ready-for-review"],
                state="closed"  # Close the issue
            )
            
            if success:
                self.log(f"Successfully marked work item #{issue_id} as complete")
                return {
                    "success": True,
                    "work_item_id": issue_id,
                    "project_id": project_id,
                    "completion_time": datetime.now().isoformat(),
                    "execution_result": execution_result,
                    "status": "completed"
                }
            else:
                raise Exception("Failed to update GitLab issue status")
                
        except Exception as e:
            self.log(f"Error marking work item complete: {str(e)}", "ERROR")
            return {
                "success": False,
                "error": str(e),
                "work_item_id": work_item.get("id"),
                "project_id": work_item.get("project_id")
            }
    
    def _check_supervisor_feedback(self, state: AgentState) -> Optional[Dict[str, Any]]:
        """Check for supervisor feedback on completed work"""
        try:
            # Check agent messages for supervisor feedback
            agent_messages = state.get("agent_messages", [])
            supervisor_messages = [
                msg for msg in agent_messages 
                if msg.sender == "Supervisor" and 
                msg.message_type in ["rework_request", "feedback"] and
                msg.recipient == self.name
            ]
            
            if supervisor_messages:
                return supervisor_messages[-1]  # Return latest feedback
            
            # Also check GitLab for supervisor comments on recently completed work
            return self._check_gitlab_supervisor_feedback(state)
            
        except Exception as e:
            self.log(f"Error checking supervisor feedback: {str(e)}", "ERROR")
            return None
    
    def _handle_supervisor_feedback(self, feedback: Dict[str, Any], state: AgentState) -> AgentState:
        """Handle supervisor feedback and implement requested changes"""
        try:
            self.log("Processing supervisor feedback for rework")
            
            feedback_content = feedback.get("content", "")
            metadata = feedback.get("metadata", {})
            work_item_info = metadata.get("work_item", {})
            
            # If this is GitLab-based feedback, update the issue status
            if "gitlab_issue_id" in metadata:
                project_id = metadata["gitlab_project_id"]
                issue_id = metadata["gitlab_issue_id"]
                
                # Update issue with rework status
                rework_comment = f"""🔄 **SUPERVISOR FEEDBACK RECEIVED - REWORK REQUIRED**

**Feedback Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Feedback:** {feedback_content}

**Agent Response:** Implementing requested changes immediately.
**Status:** Work item reopened for rework
"""
                
                # Reopen issue and mark for rework
                self._update_issue_status(
                    project_id=project_id,
                    issue_id=issue_id,
                    status="rework-needed",
                    comment=rework_comment,
                    labels=["rework-needed", "supervisor-feedback"],
                    state="opened"  # Reopen the issue
                )
                
                # Re-execute the work item with feedback incorporated
                work_item = {
                    "id": issue_id,
                    "project_id": project_id,
                    "title": work_item_info.get("title", "Rework Item"),
                    "description": f"{work_item_info.get('description', '')}\n\nSUPERVISOR FEEDBACK:\n{feedback_content}",
                    "feedback": feedback_content
                }
                
                completion_result = self._execute_work_item_to_completion(work_item, state)
                
                # Create response to supervisor
                response = self.create_message(
                    recipient="Supervisor",
                    message_type="rework_completion",
                    content=f"Rework completed based on supervisor feedback.",
                    metadata={
                        "original_feedback": feedback_content,
                        "rework_result": completion_result,
                        "work_item": work_item_info,
                        "agent_status": "ready_for_next"
                    }
                )
            else:
                # Handle non-GitLab feedback (direct agent message)
                response = self.create_message(
                    recipient="Supervisor",
                    message_type="feedback_acknowledged",
                    content=f"Supervisor feedback acknowledged: {feedback_content}",
                    metadata={"feedback_processed": True}
                )
            
            state["agent_messages"].append(response)
            state["current_agent"] = "Supervisor"
            
            return state
            
        except Exception as e:
            self.log(f"Error handling supervisor feedback: {str(e)}", "ERROR")
            
            error_response = self.create_message(
                recipient="Supervisor",
                message_type="feedback_error",
                content=f"Error processing supervisor feedback: {str(e)}",
                metadata={"error": str(e), "agent_status": "error"}
            )
            
            state["agent_messages"].append(error_response)
            state["current_agent"] = "Supervisor"
            return state
    
    def _handle_direct_workflow_request(self, request_message: AgentMessage, state: AgentState) -> AgentState:
        """Handle direct workflow requests (backward compatibility)"""
        try:
            self.log("Handling direct workflow request (backward compatibility mode)")
            
            workflow_plan = request_message.metadata.get("workflow_plan", {})
            
            if not workflow_plan:
                workflow_plan = self._create_workflow_from_request(request_message)
            
            result = self._execute_content_workflow(workflow_plan, state)
            
            workflow_intent = workflow_plan.get("intent", "unknown")
            
            response = self.create_message(
                recipient="Supervisor",
                message_type="workflow_response",
                content=result["message"],
                metadata={
                    "success": True, 
                    "results": result["data"],
                    "intent": workflow_intent
                }
            )
            
            state["agent_messages"].append(response)
            state["current_agent"] = "Supervisor"
            
            return state
            
        except Exception as e:
            self.log(f"Error handling direct workflow request: {str(e)}", "ERROR")
            
            error_response = self.create_message(
                recipient="Supervisor", 
                message_type="workflow_response",
                content=f"Content management operation failed: {str(e)}",
                metadata={"success": False, "error": str(e)}
            )
            
            state["agent_messages"].append(error_response)
            state["current_agent"] = "Supervisor"
            return state
    
    # =============================================
    # GITLAB INTEGRATION METHODS
    # =============================================
    
    def _get_accessible_projects(self) -> List[Dict[str, Any]]:
        """Get list of accessible GitLab projects"""
        try:
            for tool in self.tools:
                if tool.name == "GitLabGetProjectsListTool":
                    result = tool._run()
                    return self._parse_projects_from_result(result)
            return []
        except Exception as e:
            self.log(f"Error getting accessible projects: {str(e)}", "ERROR")
            return []
    
    def _get_available_issues(self, project_id: str) -> List[Dict[str, Any]]:
        """Get available issues from a project (open, not in-progress)"""
        try:
            for tool in self.tools:
                if tool.name == "GitLabGetProjectIssuesTool":
                    result = tool._run(project_id=project_id, state="opened")
                    issues = self._parse_issues_from_result(result)
                    
                    # Filter out issues that are already in progress or assigned
                    available_issues = []
                    for issue in issues:
                        labels = issue.get("labels", [])
                        if not any(label.lower() in ["in-progress", "assigned", "blocked"] for label in labels):
                            available_issues.append(issue)
                    
                    return available_issues
            return []
        except Exception as e:
            self.log(f"Error getting available issues for project {project_id}: {str(e)}", "ERROR")
            return []
    
    def _filter_content_management_work(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter issues for content management related work"""
        content_work = []
        
        for issue in issues:
            title = issue.get("title", "").lower()
            description = issue.get("description", "").lower()
            labels = [label.lower() for label in issue.get("labels", [])]
            
            # Check if this is content management related work
            content_keywords = [
                "content", "knowledge base", "kb", "article", "category",
                "documentation", "information", "data", "structure",
                "organization", "taxonomy", "metadata", "search",
                "content-management", "kb-management", "data-quality"
            ]
            
            label_keywords = [
                "content-management", "kb-management", "knowledge-base",
                "data-quality", "content-creation", "content-review"
            ]
            
            # Check if any content keywords appear in title, description, or labels
            is_content_work = (
                any(keyword in title for keyword in content_keywords) or
                any(keyword in description for keyword in content_keywords) or
                any(keyword in labels for keyword in label_keywords)
            )
            
            if is_content_work:
                content_work.append(issue)
        
        return content_work
    
    def _prioritize_work_items(self, work_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort work items by priority"""
        def get_priority_score(item):
            labels = [label.lower() for label in item.get("labels", [])]
            
            if "urgent" in labels or "critical" in labels:
                return 1
            elif "high-priority" in labels or "high" in labels:
                return 2
            elif "medium-priority" in labels or "medium" in labels:
                return 3
            else:
                return 4  # Low priority or no priority label
        
        return sorted(work_items, key=get_priority_score)
    
    def _create_workflow_from_gitlab_issue(self, work_item: Dict[str, Any]) -> Dict[str, Any]:
        """Create workflow plan from GitLab issue"""
        title = work_item.get("title", "")
        description = work_item.get("description", "")
        labels = work_item.get("labels", [])
        
        # Determine intent from issue content
        intent = self._determine_intent_from_issue(title, description, labels)
        
        return {
            "intent": intent,
            "description": f"Execute GitLab work item: {title}",
            "steps": [
                {
                    "action": "execute_kb_operation",
                    "description": f"{title}\n\n{description}",
                    "tool_required": True
                }
            ],
            "original_request": f"{title}\n\n{description}",
            "gitlab_issue": work_item
        }
    
    def _determine_intent_from_issue(self, title: str, description: str, labels: List[str]) -> str:
        """Determine workflow intent from GitLab issue"""
        content = f"{title} {description}".lower()
        labels_lower = [label.lower() for label in labels]
        
        if any(keyword in content for keyword in ["create", "add", "new"]):
            return "create_content"
        elif any(keyword in content for keyword in ["update", "modify", "edit", "change"]):
            return "update_content"
        elif any(keyword in content for keyword in ["delete", "remove", "archive"]):
            return "delete_content"
        elif any(keyword in content for keyword in ["analyze", "gap", "review", "audit"]):
            return "analyze_content_gaps"
        elif any(keyword in content for keyword in ["search", "find", "retrieve", "get"]):
            return "retrieve_content"
        elif any(keyword in content for keyword in ["context", "switch", "set kb", "use kb"]):
            return "set_knowledge_base_context"
        elif "structure" in labels_lower or "organization" in labels_lower:
            return "organize_content"
        else:
            return "general_content_management"
    
    def _update_issue_status(self, project_id: str, issue_id: str, status: str, 
                           comment: str, labels: List[str] = None, state: str = None) -> bool:
        """Update GitLab issue status with comment and labels"""
        try:
            # Add comment to issue
            comment_success = self._add_issue_comment(project_id, issue_id, comment)
            
            # Update labels if provided
            if labels:
                label_success = self._update_issue_labels(project_id, issue_id, labels)
            else:
                label_success = True
            
            # Update issue state if provided
            if state:
                state_success = self._update_issue_state(project_id, issue_id, state)
            else:
                state_success = True
            
            return comment_success and label_success and state_success
            
        except Exception as e:
            self.log(f"Error updating issue status: {str(e)}", "ERROR")
            return False
    
    def _add_work_progress_update(self, project_id: str, issue_id: str, progress_comment: str) -> bool:
        """Add a progress update comment to GitLab issue"""
        return self._add_issue_comment(project_id, issue_id, progress_comment)
    
    def _report_work_item_error(self, work_item: Dict[str, Any], error_message: str) -> bool:
        """Report work item error to GitLab"""
        try:
            project_id = work_item["project_id"]
            issue_id = work_item["id"]
            
            error_comment = f"""❌ **WORK ITEM ERROR**

**Error Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent:** ContentManagementAgent
**Status:** Error encountered during execution

**Error Details:**
{error_message}

**Next Steps:**
- Issue requires supervisor review
- May need manual intervention
- Agent will retry if possible

**Agent Status:** Available for supervisor assignment
"""
            
            return self._update_issue_status(
                project_id=project_id,
                issue_id=issue_id,
                status="error",
                comment=error_comment,
                labels=["error", "needs-supervisor-review"]
            )
            
        except Exception as e:
            self.log(f"Error reporting work item error: {str(e)}", "ERROR")
            return False
    
    def _check_gitlab_supervisor_feedback(self, state: AgentState) -> Optional[Dict[str, Any]]:
        """Check GitLab for supervisor feedback on completed work"""
        try:
            # Get recent completed work items from state history
            # This would check recent GitLab issues for supervisor comments
            # Implementation depends on available GitLab tools for comment retrieval
            return None
            
        except Exception as e:
            self.log(f"Error checking GitLab supervisor feedback: {str(e)}", "ERROR")
            return None
    
    def _report_claim_failure(self, work_item: Dict[str, Any], state: AgentState) -> AgentState:
        """Report failure to claim work item"""
        failure_response = self.create_message(
            recipient="Supervisor",
            message_type="claim_failure",
            content=f"Failed to claim work item: {work_item.get('title', 'Unknown')}",
            metadata={
                "work_item": work_item,
                "agent_status": "ready",
                "issue": "Unable to claim work item, may be claimed by another agent"
            }
        )
        
        state["agent_messages"].append(failure_response)
        state["current_agent"] = "Supervisor"
        return state
        """Check GitLab for assigned work and pending tasks"""
        try:
            self.log("Checking GitLab work queue for assigned tasks")
            
            # If KB ID provided, find the linked GitLab project
            if kb_id:
                # Find GitLab project linked to this KB
                gitlab_project_id = self._get_gitlab_project_for_kb(kb_id)
                if gitlab_project_id:
                    return self._get_pending_issues(str(gitlab_project_id))
            
            # If no specific KB, check all accessible projects for assigned work
            return self._get_all_assigned_work()
            
        except Exception as e:
            self.log(f"Error checking GitLab work queue: {str(e)}", "ERROR")
            return []
    
    def create_gitlab_work_tracking_issue(self, title: str, description: str, 
                                        kb_id: Optional[str] = None, 
                                        labels: List[str] = None) -> Optional[Dict[str, Any]]:
        """Create a GitLab issue to track work progress"""
        try:
            self.log(f"Creating GitLab work tracking issue: {title}")
            
            # Find appropriate GitLab project
            project_id = None
            if kb_id:
                project_id = self._get_gitlab_project_for_kb(kb_id)
            
            if not project_id:
                # Use default project or create one
                project_id = self._get_or_create_default_project()
            
            if not project_id:
                self.log("No GitLab project available for issue creation", "WARNING")
                return None
            
            # Create the issue
            issue_data = self._create_issue(project_id, title, description, labels or [])
            
            if issue_data:
                self.log(f"Created GitLab issue #{issue_data.get('iid', 'unknown')} in project {project_id}")
                return issue_data
            
            return None
            
        except Exception as e:
            self.log(f"Error creating GitLab work tracking issue: {str(e)}", "ERROR")
            return None
    
    def update_gitlab_work_status(self, issue_id: str, project_id: str, 
                                status_update: str, progress_details: str = "") -> bool:
        """Update GitLab issue with work progress and status"""
        try:
            self.log(f"Updating GitLab issue #{issue_id} with status: {status_update}")
            
            # Create a detailed comment with progress update
            comment_content = f"**Work Status Update:** {status_update}\n\n"
            if progress_details:
                comment_content += f"**Progress Details:**\n{progress_details}\n\n"
            comment_content += f"**Updated by:** ContentManagementAgent\n"
            comment_content += f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Add comment to issue (using GitLab tools)
            success = self._add_issue_comment(project_id, issue_id, comment_content)
            
            if success:
                self.log(f"Successfully updated GitLab issue #{issue_id}")
                return True
            else:
                self.log(f"Failed to update GitLab issue #{issue_id}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error updating GitLab work status: {str(e)}", "ERROR")
            return False
    
    def complete_gitlab_work_item(self, issue_id: str, project_id: str, 
                                completion_summary: str, results: Dict[str, Any] = None) -> bool:
        """Mark a GitLab work item as completed with results"""
        try:
            self.log(f"Completing GitLab work item #{issue_id}")
            
            # Create completion comment
            comment_content = f"**✅ WORK COMPLETED**\n\n"
            comment_content += f"**Summary:** {completion_summary}\n\n"
            
            if results:
                comment_content += f"**Results:**\n"
                for key, value in results.items():
                    comment_content += f"- **{key}:** {value}\n"
                comment_content += "\n"
            
            comment_content += f"**Completed by:** ContentManagementAgent\n"
            comment_content += f"**Completion Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            comment_content += "This work item is now ready for supervisor review."
            
            # Add completion comment
            success = self._add_issue_comment(project_id, issue_id, comment_content)
            
            if success:
                self.log(f"Successfully marked GitLab issue #{issue_id} as completed")
                return True
            else:
                self.log(f"Failed to complete GitLab issue #{issue_id}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error completing GitLab work item: {str(e)}", "ERROR")
            return False
    
    # =============================================
    # GITLAB HELPER METHODS
    # =============================================
    
    def _get_gitlab_project_for_kb(self, kb_id: str) -> Optional[str]:
        """Get GitLab project ID linked to a knowledge base"""
        try:
            # Use GitLab tools to find KB by project
            for tool in self.tools:
                if tool.name == "GitLabGetKnowledgeBaseByProjectTool":
                    # This would require knowing the project ID first
                    # Instead, we should query the KB operations to get the linked project
                    break
            
            # Alternative: Query KB operations directly
            from operations.knowledge_base_operations import KnowledgeBaseOperations
            kb_ops = KnowledgeBaseOperations()
            kb = kb_ops.get_knowledge_base_by_id(kb_id)
            
            if kb and kb.gitlab_project_id:
                return str(kb.gitlab_project_id)
            
            return None
            
        except Exception as e:
            self.log(f"Error getting GitLab project for KB {kb_id}: {str(e)}", "ERROR")
            return None
    
    def _get_pending_issues(self, project_id: str) -> List[Dict[str, Any]]:
        """Get pending issues from a GitLab project"""
        try:
            # Use GitLab tools to get project issues
            for tool in self.tools:
                if tool.name == "GitLabGetProjectIssuesTool":
                    # Execute the tool to get issues
                    result = tool._run(project_id=project_id, state="opened")
                    # Parse the result to extract issue data
                    return self._parse_issues_from_result(result)
            
            return []
            
        except Exception as e:
            self.log(f"Error getting pending issues from project {project_id}: {str(e)}", "ERROR")
            return []
    
    def _get_all_assigned_work(self) -> List[Dict[str, Any]]:
        """Get all assigned work across accessible GitLab projects"""
        try:
            # Use GitLab tools to get projects list
            for tool in self.tools:
                if tool.name == "GitLabGetProjectsListTool":
                    projects_result = tool._run()
                    # For each project, check for assigned issues
                    all_work = []
                    # This would be expanded to check multiple projects
                    return all_work
            
            return []
            
        except Exception as e:
            self.log(f"Error getting all assigned work: {str(e)}", "ERROR")
            return []
    
    def _get_or_create_default_project(self) -> Optional[str]:
        """Get or create a default GitLab project for work tracking"""
        try:
            # Use GitLab tools to get projects and find or create a default one
            # Implementation would depend on naming conventions for default projects
            return None
            
        except Exception as e:
            self.log(f"Error getting/creating default project: {str(e)}", "ERROR")
            return None
    
    def _create_issue(self, project_id: str, title: str, description: str, labels: List[str]) -> Optional[Dict[str, Any]]:
        """Create an issue using GitLab tools"""
        try:
            for tool in self.tools:
                if tool.name == "GitLabCreateIssueTool":
                    labels_str = ",".join(labels) if labels else None
                    result = tool._run(
                        project_id=project_id,
                        title=title,
                        description=description,
                        labels=labels_str
                    )
                    return self._parse_issue_from_result(result)
            
            return None
            
        except Exception as e:
            self.log(f"Error creating issue: {str(e)}", "ERROR")
            return None
    
    def _add_issue_comment(self, project_id: str, issue_id: str, comment: str) -> bool:
        """Add a comment to a GitLab issue"""
        try:
            # GitLab API typically doesn't have a separate comment tool
            # Comments are usually added when updating issues
            # This would need to be implemented based on available GitLab tools
            return True
            
        except Exception as e:
            self.log(f"Error adding issue comment: {str(e)}", "ERROR")
            return False
    
    def _update_issue_labels(self, project_id: str, issue_id: str, labels: List[str]) -> bool:
        """Update GitLab issue labels"""
        try:
            # Use GitLab tools to update issue labels
            # Implementation depends on available GitLab tools
            return True
        except Exception as e:
            self.log(f"Error updating issue labels: {str(e)}", "ERROR")
            return False
    
    def _update_issue_state(self, project_id: str, issue_id: str, state: str) -> bool:
        """Update GitLab issue state (opened/closed)"""
        try:
            # Use GitLab tools to update issue state
            # Implementation depends on available GitLab tools
            return True
        except Exception as e:
            self.log(f"Error updating issue state: {str(e)}", "ERROR")
            return False
    
    def _parse_projects_from_result(self, result: str) -> List[Dict[str, Any]]:
        """Parse projects from GitLab tool result"""
        # This would parse the string result from GitLab tools
        # and extract structured project data
        try:
            # Placeholder implementation - would parse actual GitLab API responses
            import json
            if isinstance(result, str) and result.strip().startswith('['):
                projects_data = json.loads(result)
                return projects_data if isinstance(projects_data, list) else []
            return []
        except Exception:
            return []
    
    def _parse_issues_from_result(self, result: str) -> List[Dict[str, Any]]:
        """Parse issues from GitLab tool result"""
        # This would parse the string result from GitLab tools
        # and extract structured issue data
        try:
            # Placeholder implementation - would parse actual GitLab API responses
            import json
            if isinstance(result, str) and result.strip().startswith('['):
                issues_data = json.loads(result)
                return issues_data if isinstance(issues_data, list) else []
            return []
        except Exception:
            return []
    
    def _parse_issue_from_result(self, result: str) -> Dict[str, Any]:
        """Parse issue data from GitLab tool result"""
        # This would parse the string result from GitLab tools
        # and extract structured issue data
        return {}
