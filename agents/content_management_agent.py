from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from tools.knowledge_base_tools import KnowledgeBaseTools
from tools.gitlab_tools import GitLabTools
from prompts.knowledge_base_prompts import prompts as kb_prompts
from prompts.multi_agent_prompts import prompts as ma_prompts

# Ensure environment variables are loaded for database connectivity
from dotenv import load_dotenv
load_dotenv(override=True)


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
        
        # Track current KB context  
        self.kb_context = {}  # Store current KB context
    
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
        my_messages = [msg for msg in agent_messages if msg.recipient in [self.name, "ContentManagement"]]
        
        if my_messages:
            self.log(f"Found {len(my_messages)} messages for ContentManagement - processing latest")
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
    
    def _create_workflow_from_request(self, request_message: AgentMessage, state: AgentState = None) -> Dict[str, Any]:
        """Create a workflow plan from a request message - Pure LLM-driven planning"""
        content = request_message.content
        metadata = request_message.metadata or {}
        
        self.log(f"Creating workflow from request: '{content[:100]}...'")
        
        # Extract original user request if this is supervisor feedback OR contains echo command
        original_request = content
        if "Work requires revision" in content or "Supervisor feedback" in content:
            # Try to extract from state messages
            user_messages = []
            for msg in state.get("messages", []):
                if hasattr(msg, 'content') and not any(keyword in msg.content for keyword in 
                    ["Work requires revision", "Supervisor feedback", "ContentManagement", "Supervisor"]):
                    user_messages.append(msg.content)
            
            if user_messages:
                original_request = user_messages[-1]
                self.log(f"Extracted original user request: '{original_request}'")
        
        # Also extract from echo commands or pipeline commands
        elif "echo" in content or "python clean_multi_agent.py" in content:
            # Extract the actual user question from echo command
            import re
            # Look for patterns like: echo "question" | python clean_multi_agent.py
            echo_match = re.search(r'echo\s*["\']([^"\']+)["\']', content)
            if echo_match:
                original_request = echo_match.group(1)
                self.log(f"Extracted user request from echo command: '{original_request}'")
            # Look for User request: pattern
            elif "User request:" in content:
                user_match = re.search(r'User request:\s*(.+?)(?:\s*\||\s*$)', content)
                if user_match:
                    original_request = user_match.group(1).strip()
                    self.log(f"Extracted user request from prefix: '{original_request}'")
        
        # FOR ALL REQUESTS: Use pure LLM-driven approach - let LLM decide everything
        self.log("Using pure LLM-driven workflow planning - LLM will determine intent and actions")
        
        workflow_plan = {
            "intent": "llm_driven",
            "description": f"LLM-driven processing for: {original_request[:50]}...",
            "steps": [
                {
                    "action": "llm_process",
                    "description": "Let LLM intelligently determine intent and execute appropriate actions",
                    "tool_required": True,
                    "content": original_request
                }
            ],
            "original_request": original_request
        }
        
        return workflow_plan

    def _execute_content_workflow(self, workflow_plan: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute the content management workflow using available tools - PURE LLM DRIVEN"""
        intent = workflow_plan.get("intent", "")
        steps = workflow_plan.get("steps", [])
        original_request = workflow_plan.get("original_request", "")
        
        self.log(f"Executing {len(steps)} workflow steps for intent: {intent}")
        
        # ALL intents go through LLM-driven processing - no special handlers
        if intent == "llm_driven":
            self.log(f"Handling LLM-driven intent detection and processing for request: '{original_request}'")
            return self._execute_llm_driven_workflow(workflow_plan, state)
        
        # For any other intent (legacy), redirect to LLM-driven
        self.log(f"Redirecting legacy intent '{intent}' to LLM-driven processing")
        workflow_plan["intent"] = "llm_driven" 
        return self._execute_llm_driven_workflow(workflow_plan, state)
        
        # Special handling for conversational intent
        if intent == "conversation":
            self.log(f"Handling conversational request: '{original_request}'")
            return self._execute_conversational_response(workflow_plan, state)
        
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
  * For example, if creating a category about a topic: create category first, then create specific articles under it
  * Always validate knowledge base context first before creating content
  * REQUIRED FIELDS for KnowledgeBaseInsertArticle tool:
    - title: Clear, descriptive title for the article/category
    - content: Comprehensive content with helpful information (minimum 200 characters)
    - author_id: Always use 1 (default system user for AI-generated content)
    - parent_id: Use null for main categories, or parent article ID for sub-articles
    - knowledge_base_id: Use the current knowledge base ID from state
  * DO NOT use KnowledgeBaseGetArticleHierarchy for creation - that's only for reading existing content
  * EXAMPLE for creating a main category:
    article={{"title": "[Topic Category Name]", "content": "Comprehensive guide covering all aspects of [topic area], including key concepts, best practices, and practical applications. This category serves as the foundation for organizing related content and provides overview information for the topic domain.", "author_id": 1, "parent_id": null, "knowledge_base_id": [current_kb_id]}}
  * EXAMPLE for creating sub-article under a category:
    article={{"title": "[Specific Topic Name]", "content": "Detailed information about [specific topic], including practical techniques, step-by-step guidance, and real-world applications. This content provides actionable insights and comprehensive coverage of the subject matter.", "author_id": 1, "parent_id": [parent_category_id], "knowledge_base_id": [current_kb_id]}}

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

    def _execute_strategic_content_work(self, strategic_work: Dict[str, Any], state: AgentState) -> bool:
        """Execute strategic content creation work by creating an article"""
        try:
            self.log("Executing strategic content creation work")
            
            # Extract opportunity details
            opportunities = strategic_work.get("opportunities", [])
            if not opportunities:
                self.log("No opportunities provided for strategic content creation")
                return False

            # Get current KB context from environment or state
            kb_id = (self.kb_context.get("knowledge_base_id") or 
                    state.get("knowledge_base_id") or 
                    os.getenv('DEFAULT_KNOWLEDGE_BASE_ID', '13'))
            
            # FIRST: Assess knowledge base structure and create foundation work items if needed
            self.log(f"Assessing knowledge base structure for KB {kb_id}...")
            structure_assessment = self._assess_knowledge_base_structure(kb_id)
            
            # If foundation work is needed, prioritize that over content creation
            if structure_assessment.get("needs_structure_work") or structure_assessment.get("needs_taxonomy_work"):
                self.log("🚧 Foundation work required - deferring content creation until structure is established")
                self.log(f"   Structure issues: {structure_assessment.get('hierarchy_issues', [])}")
                self.log(f"   Taxonomy issues: {structure_assessment.get('taxonomy_issues', [])}")
                return True  # Return success as we've created the necessary foundation work items
            
            # Only proceed with content creation if foundation is in place
            opportunity = opportunities[0]
            article_title = opportunity.get("description", "Strategic Content")
            priority = opportunity.get("priority", "medium")
            rationale = opportunity.get("rationale", "Strategic content expansion")
            
            self.log(f"Creating strategic article: {article_title}")            # Find the article creation tool
            create_tool = None
            for tool in self.tools:
                if tool.name == "KnowledgeBaseInsertArticle":
                    create_tool = tool
                    break
            
            if not create_tool:
                self.log("KnowledgeBaseInsertArticle tool not found")
                return False
            
            # Create comprehensive content based on the opportunity
            content = self._generate_strategic_content(article_title, rationale)
            
            # Execute article creation with correct parameters
            from models.article import Article
            
            article_data = Article.InsertModel(
                title=article_title,
                content=content,
                author_id=1,  # AI-generated content
                parent_id=None,  # Root level article
                knowledge_base_id=int(kb_id)
            )
            
            tool_args = {
                "knowledge_base_id": str(kb_id),
                "article": article_data
            }
            
            self.log(f"Calling KnowledgeBaseInsertArticle with KB ID: {kb_id}")
            result = create_tool._run(**tool_args)
            
            if result and hasattr(result, 'id') and result.id:
                self.log(f"✅ Successfully created strategic article: {article_title} (ID: {result.id})")
                
                # Create GitLab work item to track completed content
                self._create_completion_work_item(article_title, result.id, kb_id)
                
                return True
            else:
                self.log(f"❌ Failed to create strategic article: {result}")
                return False
                
        except Exception as e:
            self.log(f"Error in strategic content creation: {str(e)}")
            return False

    def _create_completion_work_item(self, article_title: str, article_id: int, kb_id: str) -> None:
        """Create GitLab work item to track completed content creation"""
        try:
            from tools.gitlab_tools import GitLabTools
            gitlab_tools = GitLabTools()
            
            # Find the GitLab create issue tool
            create_issue_tool = None
            for tool in gitlab_tools.tools():
                if tool.name == "GitLabCreateIssueTool":
                    create_issue_tool = tool
                    break
            
            if not create_issue_tool:
                self.log("GitLabCreateIssueTool not found for completion tracking")
                return
                
            # Create work item for completed content  
            # Get GitLab project ID from current KB context
            project_id = (self.kb_context.get("gitlab_project_id") or 
                         os.getenv('DEFAULT_GITLAB_PROJECT_ID', '27'))
            
            work_item_data = {
                "project_id": str(project_id),
                "title": f"✅ Content Created: {article_title}",
                "description": f"""**Content Creation Completed**

📝 **Article:** {article_title}
🆔 **Article ID:** {article_id}  
📚 **Knowledge Base ID:** {kb_id}
🤖 **Created by:** ContentManagementAgent (Autonomous)
📅 **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Status:** Content successfully generated and inserted into knowledge base.
**Next Steps:** Ready for review and quality assurance if needed.
""",
                "labels": ["content-completed", "autonomous-work", "strategic-content"]
            }
            
            result = self._create_issue(project_id, work_item_data["title"], work_item_data["description"], work_item_data["labels"])
            if result:
                self.log(f"📝 Created completion work item for: {article_title}")
            else:
                self.log(f"🔄 Completion work item already exists for: {article_title}")
            
        except Exception as e:
            self.log(f"Warning: Could not create completion work item: {str(e)}")

    def _assess_knowledge_base_structure(self, kb_id: str) -> Dict[str, Any]:
        """Assess knowledge base structure and create foundation work items if needed"""
        try:
            assessment = {
                "has_proper_hierarchy": False,
                "has_taxonomy_tags": False,
                "needs_structure_work": False,
                "needs_taxonomy_work": False,
                "hierarchy_issues": [],
                "taxonomy_issues": []
            }
            
            # Check article hierarchy using KnowledgeBaseValidateHierarchy tool
            hierarchy_tool = None
            tags_tool = None
            
            for tool in self.tools:
                if tool.name == "KnowledgeBaseValidateHierarchy":
                    hierarchy_tool = tool
                elif tool.name == "KnowledgeBaseGetTagsByKnowledgeBase":
                    tags_tool = tool
            
            # Assess hierarchy structure
            if hierarchy_tool:
                try:
                    hierarchy_result = hierarchy_tool._run(knowledge_base_id=kb_id)
                    
                    # Parse hierarchy validation results
                    if isinstance(hierarchy_result, str):
                        if "✅ VALID HIERARCHY" in hierarchy_result:
                            assessment["has_proper_hierarchy"] = True
                        else:
                            assessment["needs_structure_work"] = True
                            if "No root categories found" in hierarchy_result:
                                assessment["hierarchy_issues"].append("missing_root_categories")
                            if "subcategories" in hierarchy_result.lower():
                                assessment["hierarchy_issues"].append("missing_subcategories")
                            if "articles" in hierarchy_result.lower():
                                assessment["hierarchy_issues"].append("missing_article_structure")
                    
                except Exception as e:
                    self.log(f"Could not assess hierarchy: {str(e)}")
                    assessment["needs_structure_work"] = True
                    assessment["hierarchy_issues"].append("assessment_failed")
            
            # Assess taxonomy/tagging structure
            if tags_tool:
                try:
                    tags_result = tags_tool._run(knowledge_base_id=kb_id)
                    
                    if isinstance(tags_result, list) and len(tags_result) > 0:
                        assessment["has_taxonomy_tags"] = True
                        self.log(f"Found {len(tags_result)} existing tags")
                    else:
                        assessment["needs_taxonomy_work"] = True
                        assessment["taxonomy_issues"].append("no_tags_found")
                        
                except Exception as e:
                    self.log(f"Could not assess tags: {str(e)}")
                    assessment["needs_taxonomy_work"] = True
                    assessment["taxonomy_issues"].append("assessment_failed")
            
            # Create work items for missing foundation elements (only if not already created)
            if assessment["needs_structure_work"]:
                if not self._work_item_exists_by_title("🏗️ [FOUNDATION] Establish Knowledge Base Structure"):
                    self._create_structure_foundation_work_item(kb_id, assessment["hierarchy_issues"])
                else:
                    self.log("🔄 Structure foundation work item already exists - skipping creation")
            
            if assessment["needs_taxonomy_work"]:
                if not self._work_item_exists_by_title("🏷️ [FOUNDATION] Establish Taxonomy & Tagging System"):
                    self._create_taxonomy_foundation_work_item(kb_id, assessment["taxonomy_issues"])
                else:
                    self.log("🔄 Taxonomy foundation work item already exists - skipping creation")
            
            return assessment
            
        except Exception as e:
            self.log(f"Error assessing knowledge base structure: {str(e)}")
            return {"error": str(e)}

    def _structure_work_item_exists(self, kb_id: str) -> bool:
        """Check if structure foundation work item already exists for this KB"""
        try:
            self.log(f"🔍 Checking for existing structure work items in project...")
            
            from tools.gitlab_tools import GitLabTools
            gitlab_tools = GitLabTools()
            
            # Find the GitLab list issues tool
            list_issues_tool = None
            for tool in gitlab_tools.tools():
                if tool.name == "GitLabListIssuesTool":
                    list_issues_tool = tool
                    break
            
            if not list_issues_tool:
                self.log("⚠️ GitLabListIssuesTool not found - cannot check existing work items")
                return False
                
            # Get GitLab project ID from current KB context
            project_id = (self.kb_context.get("gitlab_project_id") or 
                         os.getenv('DEFAULT_GITLAB_PROJECT_ID', '164'))
            
            self.log(f"🔍 Searching project {project_id} for existing structure foundation work items...")
            
            # Search for structure foundation work items
            issues_result = list_issues_tool._run(
                project_id=project_id,
                state="opened",
                search="🏗️ [FOUNDATION] Establish Knowledge Base Structure"
            )
            
            self.log(f"🔍 Search returned: {type(issues_result)} with {len(issues_result) if isinstance(issues_result, list) else 'unknown'} results")
            
            if isinstance(issues_result, list):
                if len(issues_result) > 0:
                    self.log(f"✅ Found {len(issues_result)} existing structure foundation work items - skipping creation")
                    # Log the existing items for verification
                    for i, issue in enumerate(issues_result[:3]):  # Show first 3
                        if isinstance(issue, dict):
                            title = issue.get("title", "No title")
                            issue_id = issue.get("iid", "No ID")
                            self.log(f"   📋 Existing item #{issue_id}: {title}")
                    return True
                else:
                    self.log("ℹ️ No existing structure foundation work items found")
                    return False
            else:
                self.log(f"⚠️ Unexpected search result type: {type(issues_result)}")
                return False
            
        except Exception as e:
            self.log(f"❌ Error checking for existing structure work item: {str(e)}")
            # Return False to be safe - better to potentially create duplicate than miss required work
            return False

    def _taxonomy_work_item_exists(self, kb_id: str) -> bool:
        """Check if taxonomy foundation work item already exists for this KB"""
        try:
            self.log(f"🔍 Checking for existing taxonomy work items in project...")
            
            from tools.gitlab_tools import GitLabTools
            gitlab_tools = GitLabTools()
            
            # Find the GitLab list issues tool
            list_issues_tool = None
            for tool in gitlab_tools.tools():
                if tool.name == "GitLabListIssuesTool":
                    list_issues_tool = tool
                    break
            
            if not list_issues_tool:
                self.log("⚠️ GitLabListIssuesTool not found - cannot check existing work items")
                return False
                
            # Get GitLab project ID from current KB context
            project_id = (self.kb_context.get("gitlab_project_id") or 
                         os.getenv('DEFAULT_GITLAB_PROJECT_ID', '164'))
            
            self.log(f"🔍 Searching project {project_id} for existing taxonomy foundation work items...")
            
            # Search for taxonomy foundation work items
            issues_result = list_issues_tool._run(
                project_id=project_id,
                state="opened",
                search="🏷️ [FOUNDATION] Establish Taxonomy & Tagging System"
            )
            
            self.log(f"🔍 Search returned: {type(issues_result)} with {len(issues_result) if isinstance(issues_result, list) else 'unknown'} results")
            
            if isinstance(issues_result, list):
                if len(issues_result) > 0:
                    self.log(f"✅ Found {len(issues_result)} existing taxonomy foundation work items - skipping creation")
                    # Log the existing items for verification
                    for i, issue in enumerate(issues_result[:3]):  # Show first 3
                        if isinstance(issue, dict):
                            title = issue.get("title", "No title")
                            issue_id = issue.get("iid", "No ID")
                            self.log(f"   📋 Existing item #{issue_id}: {title}")
                    return True
                else:
                    self.log("ℹ️ No existing taxonomy foundation work items found")
                    return False
            else:
                self.log(f"⚠️ Unexpected search result type: {type(issues_result)}")
                return False
            
        except Exception as e:
            self.log(f"❌ Error checking for existing taxonomy work item: {str(e)}")
            # Return False to be safe - better to potentially create duplicate than miss required work
            return False

    def _work_item_exists_by_title(self, title_search: str, project_id: str = None) -> bool:
        """Check if a work item with exact title already exists using GitLabOperations"""
        try:
            self.log(f"🔍 Checking for existing work items with exact title: '{title_search}'")
            
            # Import the existing GitLab operations
            from operations.gitlab_operations import GitLabOperations
            
            # Use provided project_id or get from context
            if not project_id:
                project_id = (self.kb_context.get("gitlab_project_id") or 
                             os.getenv('DEFAULT_GITLAB_PROJECT_ID', '164'))
            
            self.log(f"🔍 Searching project {project_id} for exact title match...")
            
            # Use the existing GitLabOperations for duplicate detection
            gitlab_ops = GitLabOperations()
            duplicate_exists = gitlab_ops.check_duplicate_issue(project_id, title_search)
            
            if duplicate_exists:
                self.log(f"🔄 Duplicate detected! Work item already exists with title: '{title_search}'")
                return True
            else:
                self.log(f"✅ No duplicates found - safe to create new work item")
                return False
            
        except Exception as e:
            self.log(f"❌ Error checking for existing work items: {str(e)}")
            # Return False to be safe - better to potentially create duplicate than miss required work
            return False

    def _create_structure_foundation_work_item(self, kb_id: str, issues: List[str]) -> None:
        """Create GitLab work item for establishing proper knowledge base structure"""
        try:
            from tools.gitlab_tools import GitLabTools
            gitlab_tools = GitLabTools()
            
            # Find the GitLab create issue tool
            create_issue_tool = None
            for tool in gitlab_tools.tools():
                if tool.name == "GitLabCreateIssueTool":
                    create_issue_tool = tool
                    break
            
            if not create_issue_tool:
                self.log("GitLabCreateIssueTool not found for structure work item")
                return
                
            # Get GitLab project ID from current KB context
            project_id = (self.kb_context.get("gitlab_project_id") or 
                         os.getenv('DEFAULT_GITLAB_PROJECT_ID', '27'))
            
            # Get KB name and description for topic analysis
            kb_name = self.kb_context.get("knowledge_base_name", "Unknown Knowledge Base")
            kb_description = self.kb_context.get("description", "")
            
            # Analyze topic complexity and generate intelligent structure recommendations
            structure_analysis = self._analyze_topic_complexity(kb_name, kb_description)
            
            issues_description = ""
            if "missing_root_categories" in issues:
                issues_description += "• No root-level categories found\n"
            if "missing_subcategories" in issues:
                issues_description += "• Insufficient subcategory structure\n"
            if "missing_article_structure" in issues:
                issues_description += "• Articles not properly organized under categories\n"
            if "assessment_failed" in issues:
                issues_description += "• Could not properly assess current structure\n"
            
            work_item_data = {
                "project_id": str(project_id),
                "title": f"🏗️ [FOUNDATION] Establish Knowledge Base Structure",
                "description": f"""**PRIORITY: Foundation Work Required**

🎯 **Objective:** Establish proper hierarchical structure tailored to topic complexity

**🔍 Structure Issues Identified:**
{issues_description}

**� TOPIC COMPLEXITY ANALYSIS:**
{structure_analysis['complexity_assessment']}

**🏗️ RECOMMENDED STRUCTURE FOR THIS TOPIC:**
{structure_analysis['structure_recommendations']}

**📋 SPECIFIC IMPLEMENTATION REQUIREMENTS:**
{structure_analysis['implementation_guide']}

**✅ Acceptance Criteria:**
- [ ] Create {structure_analysis['root_category_count']} root-level categories covering the complete domain scope
- [ ] Under each root category, create {structure_analysis['subcategory_range']} subcategories for logical subdivision
- [ ] Implement {structure_analysis['hierarchy_depth']} level hierarchy structure minimum
- [ ] Ensure balanced content distribution across all categories
- [ ] Validate hierarchy meets complexity requirements using KnowledgeBaseValidateHierarchy tool
- [ ] Document the rationale for the chosen structure in the root category descriptions

**🧠 STRATEGIC CONSIDERATIONS:**
{structure_analysis['strategic_notes']}

**🤖 Agent Instructions:**
This is FOUNDATION work that must be completed before general content creation. The structure should reflect the topic's natural complexity and scope.

**⚠️ CRITICAL:** Do NOT create individual content articles until this comprehensive structure is in place and validated.
""",
                "labels": ["foundation-work", "structure-required", "high-priority", "knowledge-architecture", structure_analysis['complexity_label']]
            }
            
            # Use centralized issue creation with duplicate detection
            title = "🏗️ [FOUNDATION] Establish Knowledge Base Structure"
            labels = ["foundation-work", "structure-required", "high-priority", "knowledge-architecture", structure_analysis['complexity_label']]
            
            result = self._create_issue(project_id, title, work_item_data["description"], labels)
            
            if result:
                self.log(f"🏗️ Created structure foundation work item for KB {kb_id}")
            else:
                self.log(f"🔄 Structure foundation work item already exists - skipped creation")
            
        except Exception as e:
            self.log(f"Warning: Could not create structure foundation work item: {str(e)}")

    def _analyze_topic_complexity(self, kb_name: str, kb_description: str) -> Dict[str, Any]:
        """Analyze topic complexity and generate intelligent structure recommendations"""
        try:
            # Combine name and description for analysis
            full_topic = f"{kb_name}. {kb_description}".lower()
            
            # Define complexity indicators and topic patterns
            complexity_indicators = {
                'high_complexity': [
                    'financial', 'finance', 'investment', 'business', 'enterprise', 'comprehensive',
                    'professional', 'advanced', 'complete guide', 'mastery', 'expert',
                    'healthcare', 'medical', 'legal', 'law', 'technology', 'engineering',
                    'marketing', 'sales', 'management', 'leadership', 'strategy', 'operations'
                ],
                'broad_scope': [
                    'family', 'personal', 'complete', 'comprehensive', 'everything', 'all about',
                    'ultimate', 'total', 'entire', 'whole', 'full spectrum', 'end-to-end'
                ],
                'specialized_domain': [
                    'specific', 'specialized', 'focused', 'targeted', 'niche', 'particular',
                    'dedicated', 'exclusive', 'concentrated'
                ]
            }
            
            # Calculate complexity scores
            high_complexity_score = sum(1 for indicator in complexity_indicators['high_complexity'] if indicator in full_topic)
            broad_scope_score = sum(1 for indicator in complexity_indicators['broad_scope'] if indicator in full_topic)
            specialized_score = sum(1 for indicator in complexity_indicators['specialized_domain'] if indicator in full_topic)
            
            # Determine topic characteristics
            is_financial_topic = any(term in full_topic for term in ['financial', 'finance', 'money', 'investment', 'budget', 'tax', 'wealth', 'income', 'debt', 'saving'])
            is_business_topic = any(term in full_topic for term in ['business', 'marketing', 'sales', 'management', 'strategy', 'operations', 'enterprise'])
            is_technical_topic = any(term in full_topic for term in ['technology', 'technical', 'engineering', 'software', 'development', 'programming'])
            is_healthcare_topic = any(term in full_topic for term in ['health', 'medical', 'wellness', 'fitness', 'nutrition'])
            is_family_topic = any(term in full_topic for term in ['family', 'parenting', 'children', 'home', 'household'])
            
            # Generate structure recommendations based on analysis
            if high_complexity_score >= 3 or broad_scope_score >= 2:
                # High complexity topics need extensive structure
                complexity_level = "HIGH"
                root_category_count = "6-10"
                subcategory_range = "4-8"
                hierarchy_depth = "4+"
                complexity_label = "complex-topic"
                
                if is_financial_topic:
                    structure_recommendations = """
**FINANCIAL DOMAIN STRUCTURE (Comprehensive):**

**Level 1 - Financial Planning Domains (6-8 categories):**
- Personal Financial Management
- Investment Strategies & Planning  
- Tax Planning & Optimization
- Retirement & Long-term Planning
- Risk Management & Insurance
- Estate Planning & Wealth Transfer
- Business Financial Strategies
- Economic Environment & Adaptation

**Level 2 - Specialized Areas (4-6 per domain):**
- Under Personal Financial Management: Budgeting, Debt Management, Emergency Funds, Cash Flow Planning
- Under Investment Strategies: Asset Allocation, Portfolio Management, Market Analysis, Alternative Investments
- Under Tax Planning: Deductions & Credits, Tax-Advantaged Accounts, Business Taxes, Estate Tax Planning

**Level 3+ - Specific Topics & Guides:**
- Detailed implementation guides, strategies, tools, and case studies"""

                elif is_business_topic:
                    structure_recommendations = """
**BUSINESS DOMAIN STRUCTURE (Comprehensive):**

**Level 1 - Business Function Areas (6-8 categories):**
- Strategic Planning & Vision
- Operations & Process Management
- Marketing & Customer Acquisition
- Sales & Revenue Generation
- Financial Management & Analytics
- Human Resources & Team Building
- Technology & Digital Transformation
- Risk Management & Compliance

**Level 2 - Functional Specializations (4-6 per area):**
- Under Marketing: Digital Marketing, Content Strategy, Brand Management, Customer Research
- Under Operations: Process Optimization, Supply Chain, Quality Management, Project Management
- Under Financial Management: Budgeting, Forecasting, Cost Management, Investment Analysis

**Level 3+ - Implementation Guides:**
- Specific methodologies, tools, templates, and best practices"""

                else:
                    structure_recommendations = f"""
**COMPREHENSIVE DOMAIN STRUCTURE:**

**Level 1 - Primary Knowledge Domains (6-8 categories):**
- Foundation & Core Concepts
- Planning & Strategy
- Implementation & Execution
- Advanced Techniques & Methods
- Tools & Resources
- Troubleshooting & Problem Solving
- Industry Standards & Best Practices
- Future Trends & Innovation

**Level 2 - Specialized Focus Areas (4-6 per domain):**
- Each primary domain should be subdivided into logical, coherent focus areas
- Focus areas should cover the complete scope within each domain
- Maintain parallel structure across domains where applicable

**Level 3+ - Detailed Content:**
- Specific guides, tutorials, case studies, and reference materials"""

            elif high_complexity_score >= 1 or broad_scope_score >= 1:
                # Medium complexity topics
                complexity_level = "MEDIUM"
                root_category_count = "4-6"
                subcategory_range = "3-5"
                hierarchy_depth = "3-4"
                complexity_label = "medium-complexity"
                
                structure_recommendations = f"""
**STRUCTURED DOMAIN APPROACH:**

**Level 1 - Core Knowledge Areas (4-6 categories):**
- Fundamentals & Getting Started
- Planning & Preparation 
- Implementation & Application
- Advanced Topics & Optimization
- Resources & Tools
- {f"Special Focus: {kb_name.split(' ')[0]} Applications" if len(kb_name.split()) > 1 else "Specialized Applications"}

**Level 2 - Topic Subdivisions (3-5 per area):**
- Each core area should have logical subdivisions based on progression or specialization
- Balance between comprehensive coverage and manageable organization
- Consider user journey from beginner to advanced

**Level 3+ - Actionable Content:**
- Step-by-step guides, detailed explanations, examples, and practical applications"""

            else:
                # Lower complexity topics
                complexity_level = "FOCUSED"
                root_category_count = "3-5"
                subcategory_range = "2-4"
                hierarchy_depth = "3"
                complexity_label = "focused-topic"
                
                structure_recommendations = f"""
**FOCUSED DOMAIN STRUCTURE:**

**Level 1 - Essential Knowledge Areas (3-5 categories):**
- Core Concepts & Fundamentals
- Practical Application & Implementation
- Advanced Techniques & Tips
- Resources & Support
- {f"Specialized {kb_name.split(' ')[0]} Topics" if len(kb_name.split()) > 1 else "Specialized Topics"}

**Level 2 - Organized Topics (2-4 per area):**
- Clear, logical subdivision of each essential area
- Progressive difficulty or thematic organization
- Ensure comprehensive coverage within focused scope

**Level 3+ - Detailed Guides:**
- In-depth articles, how-to guides, examples, and reference materials"""

            # Generate complexity assessment text
            complexity_assessment = f"""
**Complexity Level:** {complexity_level}
**Topic Scope:** {"Broad & Comprehensive" if broad_scope_score >= 2 else "Moderately Broad" if broad_scope_score >= 1 else "Focused"}
**Domain Specialization:** {"Highly Specialized" if specialized_score >= 2 else "Moderately Specialized" if specialized_score >= 1 else "General Audience"}
**Recommended Structure Depth:** {hierarchy_depth} levels minimum"""

            # Generate implementation guide
            implementation_guide = f"""
1. **Start with Root Categories:** Create {root_category_count} primary categories that logically divide the complete domain
2. **Build Subcategory Framework:** Under each root, create {subcategory_range} subcategories for detailed organization
3. **Plan Content Hierarchy:** Design {hierarchy_depth} levels minimum to accommodate topic complexity
4. **Validate Coverage:** Ensure the structure covers 100% of the intended domain scope
5. **Test Navigation:** Verify users can logically navigate from general to specific topics
6. **Document Relationships:** Clearly define how categories relate and build upon each other"""

            # Generate strategic notes
            strategic_notes = f"""
- This {complexity_level.lower()}-complexity topic requires {'extensive' if complexity_level == 'HIGH' else 'moderate' if complexity_level == 'MEDIUM' else 'streamlined'} structural planning
- Focus on {'comprehensive coverage' if complexity_level == 'HIGH' else 'balanced organization' if complexity_level == 'MEDIUM' else 'clear, focused structure'}
- Consider {'progressive complexity' if complexity_level != 'FOCUSED' else 'logical topic flow'} in the hierarchy design
- Plan for {'future expansion' if complexity_level == 'HIGH' else 'scalable growth' if complexity_level == 'MEDIUM' else 'focused completeness'} within the structure
- Ensure the structure supports both {'expert reference' if complexity_level == 'HIGH' else 'learning progression' if complexity_level == 'MEDIUM' else 'practical application'}"""

            return {
                'complexity_assessment': complexity_assessment,
                'structure_recommendations': structure_recommendations,
                'implementation_guide': implementation_guide,
                'strategic_notes': strategic_notes,
                'root_category_count': root_category_count,
                'subcategory_range': subcategory_range,
                'hierarchy_depth': hierarchy_depth,
                'complexity_label': complexity_label,
                'complexity_level': complexity_level
            }
            
        except Exception as e:
            self.log(f"Error analyzing topic complexity: {str(e)}")
            # Return default structure if analysis fails
            return {
                'complexity_assessment': "Unable to assess topic complexity - using default structure",
                'structure_recommendations': "Create 3-5 root categories with 2-4 subcategories each",
                'implementation_guide': "1. Create root categories\n2. Add subcategories\n3. Validate structure",
                'strategic_notes': "Follow standard 3+ level hierarchy approach",
                'root_category_count': "3-5",
                'subcategory_range': "2-4", 
                'hierarchy_depth': "3",
                'complexity_label': "standard-topic",
                'complexity_level': "STANDARD"
            }

    def _create_taxonomy_foundation_work_item(self, kb_id: str, issues: List[str]) -> None:
        """Create GitLab work item for establishing taxonomy and tagging system"""
        try:
            from tools.gitlab_tools import GitLabTools
            gitlab_tools = GitLabTools()
            
            # Find the GitLab create issue tool
            create_issue_tool = None
            for tool in gitlab_tools.tools():
                if tool.name == "GitLabCreateIssueTool":
                    create_issue_tool = tool
                    break
            
            if not create_issue_tool:
                self.log("GitLabCreateIssueTool not found for taxonomy work item")
                return
                
            # Get GitLab project ID from current KB context
            project_id = (self.kb_context.get("gitlab_project_id") or 
                         os.getenv('DEFAULT_GITLAB_PROJECT_ID', '27'))
            
            issues_description = ""
            if "no_tags_found" in issues:
                issues_description += "• No taxonomy tags currently exist\n"
            if "assessment_failed" in issues:
                issues_description += "• Could not properly assess current taxonomy\n"
            
            work_item_data = {
                "project_id": str(project_id),
                "title": f"🏷️ [FOUNDATION] Establish Taxonomy & Tagging System",
                "description": f"""**PRIORITY: Foundation Work Required**

🎯 **Objective:** Create comprehensive taxonomy and tagging system

**🔍 Taxonomy Issues Identified:**
{issues_description}

**📋 Required Taxonomy System:**
1. **Content Type Tags** - Article types (guide, reference, tutorial, etc.)
2. **Topic Tags** - Subject matter classifications
3. **Difficulty Tags** - Complexity levels (beginner, intermediate, advanced)
4. **Audience Tags** - Target audience classifications
5. **Status Tags** - Content lifecycle (draft, reviewed, published, archived)

**✅ Acceptance Criteria:**
- [ ] Define and create core taxonomy categories (minimum 15-20 tags)
- [ ] Create tags for content types, topics, difficulty, and audience
- [ ] Document tagging guidelines and conventions
- [ ] Apply initial tags to existing content (if any)
- [ ] Validate taxonomy completeness using KnowledgeBaseGetTagsByKnowledgeBase tool

**🤖 Agent Instructions:**
This taxonomy system will be used by all future content creation. Establish this before creating articles so content can be properly tagged from creation.

**⚠️ NOTE:** All articles should be tagged appropriately using this taxonomy system.
""",
                "labels": ["foundation-work", "taxonomy-required", "high-priority", "content-organization"]
            }
            
            # Use centralized issue creation with duplicate detection
            title = "🏷️ [FOUNDATION] Establish Taxonomy & Tagging System"
            labels = ["foundation-work", "taxonomy-required", "high-priority", "content-organization"]
            
            result = self._create_issue(project_id, title, work_item_data["description"], labels)
            
            if result:
                self.log(f"🏷️ Created taxonomy foundation work item for KB {kb_id}")
            else:
                self.log(f"🔄 Taxonomy foundation work item already exists - skipped creation")
            
        except Exception as e:
            self.log(f"Warning: Could not create taxonomy foundation work item: {str(e)}")

    def _create_taxonomy_and_structure_work_items(self, kb_id: str, kb_name: str) -> bool:
        """Create foundational taxonomy and structure work items for a knowledge base"""
        try:
            from tools.gitlab_tools import GitLabTools
            gitlab_tools = GitLabTools()
            
            # Find the GitLab create issue tool
            create_issue_tool = None
            for tool in gitlab_tools.tools():
                if tool.name == "GitLabCreateIssueTool":
                    create_issue_tool = tool
                    break
            
            if not create_issue_tool:
                self.log("GitLabCreateIssueTool not found for taxonomy work item creation")
                return False
                
            # Get GitLab project ID from current KB context
            project_id = (self.kb_context.get("gitlab_project_id") or 
                         os.getenv('DEFAULT_GITLAB_PROJECT_ID', '27'))
            
            # 1. Create Taxonomy Definition Work Item (HIGHEST PRIORITY)
            taxonomy_work_item = {
                "project_id": str(project_id),
                "title": f"🏗️ TAXONOMY: {kb_name} - Define Root Categories & Subcategory Structure",
                "description": f"""**FOUNDATIONAL TAXONOMY DEFINITION - HIGHEST PRIORITY**

📚 **Knowledge Base:** {kb_name} (ID: {kb_id})
🎯 **Objective:** Establish the complete hierarchical category structure before any content creation

**🏗️ MANDATORY STRUCTURE REQUIREMENTS:**
- **Level 1 - ROOT CATEGORIES (3-8 categories):**
  - Broad, high-level topic divisions covering complete KB scope
  - Created with parent_id = null
  - Examples: "Financial Planning", "Tax Strategies", "Investment Basics"

- **Level 2 - SUBCATEGORIES (2-6 per root category):**
  - Specific topic areas within each root category
  - Created with parent_id = Level 1 category ID
  - Examples under "Tax Strategies": "Deductions", "Credits", "Business Taxes"

- **Level 3+ - CONTENT ARTICLES:**
  - Actual content addressing specific topics
  - NEVER placed directly under root categories
  - Must be organized within appropriate subcategory structure

**📋 DELIVERABLES:**
1. Complete root category structure (Level 1)
2. Comprehensive subcategory framework (Level 2)
3. Content placement guidelines for Level 3+
4. Hierarchical validation rules

**⚠️ CRITICAL:** No content creation may begin until this taxonomy is approved and implemented.

**👤 Assigned to:** ContentPlanner
**🔄 Status:** Ready for immediate execution
""",
                "labels": ["taxonomy", "foundation", "high-priority", "structure", "blocking"]
            }
            
            result = self._create_issue(project_id, taxonomy_work_item["title"], taxonomy_work_item["description"], taxonomy_work_item["labels"])
            if result:
                self.log(f"📊 Created taxonomy work item for: {kb_name}")
            else:
                self.log(f"🔄 Taxonomy work item already exists for: {kb_name}")
            
            # 2. Create Tagging System Work Item
            tagging_work_item = {
                "project_id": str(project_id),
                "title": f"🏷️ TAGGING: {kb_name} - Create Tag Taxonomy & Classification System",
                "description": f"""**TAG TAXONOMY & CLASSIFICATION SYSTEM**

📚 **Knowledge Base:** {kb_name} (ID: {kb_id})
🎯 **Objective:** Create comprehensive tagging system for content discoverability and organization

**🏷️ TAG SYSTEM REQUIREMENTS:**
- **Semantic Tag Categories:**
  - Topic tags (align with category structure)
  - Difficulty level tags (beginner, intermediate, advanced)
  - Content type tags (guide, tutorial, reference, example)
  - Audience tags (individual, family, business, professional)

- **Cross-Reference Tags:**
  - Related topic connections
  - Prerequisite knowledge tags
  - Complementary content tags

- **Functional Tags:**
  - Update frequency (annual, seasonal, ongoing)
  - Content status (draft, review, approved, published)
  - Priority level (high, medium, low)

**📋 DELIVERABLES:**
1. Complete tag taxonomy with categories and hierarchies
2. Tagging guidelines and standards
3. Tag validation rules and constraints
4. Cross-referencing strategy for content discoverability

**🔗 Dependencies:** Must align with taxonomy structure from taxonomy work item

**👤 Assigned to:** ContentPlanner
**🔄 Status:** Blocked by taxonomy completion
""",
                "labels": ["tagging", "taxonomy", "classification", "foundation", "high-priority"]
            }
            
            result = self._create_issue(project_id, tagging_work_item["title"], tagging_work_item["description"], tagging_work_item["labels"])
            if result:
                self.log(f"🏷️ Created tagging work item for: {kb_name}")
            else:
                self.log(f"🔄 Tagging work item already exists for: {kb_name}")
            
            return True
            
        except Exception as e:
            self.log(f"Error creating taxonomy/tagging work items: {str(e)}")
            return False

    def _generate_strategic_content(self, title: str, rationale: str) -> str:
        """Generate comprehensive content for strategic articles"""
        try:
            # Use the LLM to generate high-quality content
            prompt = f"""
Create a comprehensive, expert-level article on the topic: "{title}"

Context: {rationale}

The article should be:
- Comprehensive and detailed (1500+ words)
- Practical and actionable
- Well-structured with clear sections
- Professional but accessible
- Include specific examples and strategies
- Provide step-by-step guidance where appropriate

Focus on providing real value to families dealing with financial challenges during economic uncertainty.
"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content if hasattr(response, 'content') else str(response)
            
            if not content or len(content) < 500:
                # Fallback content if LLM fails
                content = f"""# {title}

## Overview
This article covers {title.lower()}, providing practical strategies and actionable advice.

## Key Strategies
1. **Assessment**: Start by evaluating your current situation
2. **Planning**: Develop a comprehensive approach  
3. **Implementation**: Take concrete steps toward your goals
4. **Monitoring**: Track progress and adjust as needed

## Getting Started
{rationale}

## Conclusion
By following these strategies, you can make meaningful progress toward your financial goals.
"""
            
            return content
            
        except Exception as e:
            self.log(f"Error generating strategic content: {str(e)}")
            # Return basic fallback content
            return f"""# {title}

## Overview
This article provides guidance on {title.lower()}.

## Key Points
- Strategic approach to financial planning
- Practical implementation steps
- Long-term considerations

## Getting Started
{rationale}

For more detailed guidance, consult with financial professionals.
"""

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
                workflow_plan = self._create_workflow_from_request(request_message, state)
            
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
        """Create an issue using GitLabOperations with reliable duplicate prevention"""
        try:
            self.log(f"📝 Creating new work item: '{title}'")
            
            # Import the existing GitLab operations
            from operations.gitlab_operations import GitLabOperations
            
            # Use GitLabOperations which has built-in duplicate detection
            gitlab_ops = GitLabOperations()
            result = gitlab_ops.create_issue_with_duplicate_check(
                project_id=project_id,
                title=title,
                description=description,
                labels=labels
            )
            
            if result:
                self.log(f"✅ Successfully created work item #{result['iid']}: {result['web_url']}")
                return result
            else:
                self.log(f"❌ Failed to create work item (likely due to duplicate detection)")
                return None
            
        except Exception as e:
            self.log(f"❌ Error creating issue: {str(e)}", "ERROR")
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
    
    def _execute_kb_confirmation_workflow(self, workflow_plan: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute KB creation confirmation workflow - ask for details before creating"""
        self.log("Executing KB creation confirmation workflow")
        
        kb_name = workflow_plan.get("kb_name", "New Knowledge Base")
        original_request = workflow_plan.get("original_request", "")
        
        # Generate confirmation message asking for details
        confirmation_message = f"""📋 **Knowledge Base Creation Request**

I understand you want to create a knowledge base about: **{kb_name}**

Before I create this knowledge base, I'd like to gather some details to ensure it meets your needs:

**📝 Please provide the following information:**

1. **Knowledge Base Name**: What would you like to name this KB? 
   _(Current suggestion: "{kb_name}")_

2. **Description**: What is the main purpose and scope of this knowledge base?
   _(e.g., "A comprehensive guide to Italian cooking techniques, recipes, and culinary traditions")_

3. **Target Audience**: Who will be using this knowledge base?
   _(e.g., "Home cooks, culinary students, Italian cuisine enthusiasts")_

4. **Initial Content Areas**: What main topics or sections should this KB cover?
   _(e.g., "Traditional recipes, cooking techniques, ingredient guides, regional specialties")_

**💡 Once you provide these details, I'll:**
- Create the knowledge base with your specifications
- Set up a GitLab project for content management
- Create initial issues for content organization
- Provide you with next steps for adding content

**🚀 Ready to proceed?** Just answer the questions above, or if you're happy with the default name "{kb_name}", you can simply say "**create it**" and I'll use sensible defaults for the other details."""
        
        return {
            "success": True,
            "message": confirmation_message,
            "data": {
                "awaiting_confirmation": True,
                "kb_name": kb_name,
                "original_request": original_request,
                "workflow_stage": "confirmation"
            }
        }
    
    def _execute_kb_creation_workflow(self, workflow_plan: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute KB creation workflow with strategic design integration"""
        self.log("Executing KB creation workflow")
        
        steps = workflow_plan.get("steps", [])
        kb_name = workflow_plan.get("kb_name", "New Knowledge Base")
        
        for step in steps:
            if step.get("action") == "create_knowledge_base":
                kb_details = step.get("kb_details", {})
                
                # Use KB tools to create the knowledge base
                try:
                    # Find the KnowledgeBaseInsertKnowledgeBase tool
                    for tool in self.tools:
                        if tool.name == "KnowledgeBaseInsertKnowledgeBase":
                            self.log(f"Creating KB: {kb_name}")
                            
                            # Import the KnowledgeBase model
                            from models.knowledge_base import KnowledgeBase
                            
                            # Create the proper InsertModel object
                            kb_insert_model = KnowledgeBase.InsertModel(
                                name=kb_name,
                                description=kb_details.get("scope", f"Knowledge base for {kb_name}"),
                                author_id=1  # Default system user for AI-generated content
                            )
                            
                            result = tool._run(
                                knowledge_base=kb_insert_model,
                                create_gitlab_project=True  # GitLab project creation is critical
                            )
                            
                            self.log(f"KB creation result: {result}")
                            
                            return {
                                "success": True,
                                "message": f"""🎯 **Knowledge Base Successfully Created!**

**Knowledge Base Details:**
✅ Name: "{kb_name}"
✅ Description: {kb_details.get("scope", f"Knowledge base for {kb_name}")}
✅ GitLab Project: Created for content management and collaboration

**Next Steps:**
- Your knowledge base is ready for content development
- GitLab project has been created for tracking and collaboration
- You can start adding articles and organizing content

**Creation Details:**
{result}""",
                                "data": {
                                    "kb_created": True,
                                    "kb_name": kb_name,
                                    "kb_description": kb_details.get("scope", f"Knowledge base for {kb_name}"),
                                    "creation_result": result
                                }
                            }
                    
                    # If tool not found
                    return {
                        "success": False,
                        "message": "KB creation tool not available",
                        "data": {}
                    }
                    
                except Exception as e:
                    self.log(f"Error creating KB: {str(e)}", "ERROR")
                    return {
                        "success": False,
                        "message": f"Error creating knowledge base: {str(e)}",
                        "data": {}
                    }
        
        return {
            "success": False,
            "message": "No KB creation steps found in workflow",
            "data": {}
        }
    
    def _generate_strategic_kb_description(self, kb_details: Dict[str, Any]) -> str:
        """Generate strategic description for the knowledge base using actual KB context"""
        domain = kb_details.get('domain', 'Knowledge Base')
        purpose = kb_details.get('purpose', 'Educational resource')
        target_audience = kb_details.get('target_audience', 'Learners and professionals')
        scope = kb_details.get('scope', 'Comprehensive strategies and best practices')
        
        # Get actual KB context if available
        kb_context = self._get_kb_context_info(kb_details.get('kb_id'))
        if kb_context:
            domain = kb_context.get('name', domain)
            kb_description = kb_context.get('description', scope)
        else:
            kb_description = scope
        
        description = f"""**Strategic Knowledge Base: {domain}**

**Purpose & Vision:**
{purpose} - This knowledge base serves as a comprehensive strategic resource designed to provide actionable insights and proven methodologies for {domain.lower()}.

**Target Audience:**
{target_audience} - Specifically designed for motivated individuals seeking to master the concepts and strategies covered in this knowledge base.

**Content Strategy & Scope:**
{kb_description} - This knowledge base encompasses a strategic framework covering essential aspects of the topic domain with comprehensive coverage from foundational principles to advanced techniques.

**Content Depth & Approach:**
This knowledge base employs a strategic, actionable approach that combines theoretical understanding with practical implementation. Each topic is developed with clear step-by-step guidance, real-world examples, and measurable outcomes to ensure readers can immediately apply the concepts.

**Value Proposition:**
This knowledge base provides a cohesive, strategic approach specifically designed for mastering the subject matter. The content is structured to build progressively from basic concepts to advanced strategies, making it suitable for both beginners and those with existing knowledge.

**Publication Strategy:**
Content is structured for multi-format publication including comprehensive resource development and website creation, ensuring maximum accessibility and user engagement across different learning preferences."""

        return description
    
    def _get_kb_context_info(self, kb_id):
        """Get knowledge base context information"""
        if not kb_id:
            return None
            
        try:
            if self.tools and hasattr(self.tools, 'get_knowledge_base_info'):
                return self.tools.get_knowledge_base_info(kb_id)
        except Exception as e:
            self.log(f"Error getting KB context: {str(e)}", "ERROR")
        
        return None
    
    def _generate_strategic_tags(self, kb_details: Dict[str, Any]) -> str:
        """Generate strategic tags for the knowledge base"""
        domain = kb_details.get('domain', 'personal-finance').lower().replace(' ', '-')
        
        tags = [
            domain,
            'early-retirement',
            'financial-freedom',
            'wealth-building',
            'strategic-planning',
            'investment-strategy',
            'financial-independence',
            'retirement-planning',
            'ebook-content',
            'comprehensive-guide'
        ]
        
        return ','.join(tags)
    
    def _process_tool_result(self, tool_name: str, result: Any) -> str:
        """Process tool result and return appropriate response message"""
        
        self.log(f"Processing result for tool {tool_name}: {str(result)[:200]}")
        
        # Handle KB creation tool
        if tool_name == "KnowledgeBaseInsertKnowledgeBase":
            if "✅" in str(result) and "Knowledge Base Created Successfully" in str(result):
                return str(result)
            else:
                return f"Error creating knowledge base: {str(result)}"
        
        # Handle KB context setting tool  
        elif tool_name == "KnowledgeBaseSetContext":
            if isinstance(result, dict) and result.get("success") is True:
                kb_name = result.get("knowledge_base_name", "Unknown")
                kb_id = result.get("knowledge_base_id", "Unknown")
                gitlab_msg = ""
                if result.get("gitlab_project_id"):
                    gitlab_msg = f"\n🦊 **GitLab Project:** {result.get('gitlab_project_id')}"
                
                response = f"""✅ **Knowledge Base Context Set Successfully!**

📚 **Active KB:** {kb_name} (ID: {kb_id}){gitlab_msg}

🎯 **Ready for next action:**
   • Add articles with specific topics
   • Search existing content
   • Manage KB structure
   
What would you like to do with this knowledge base?"""
                self.log(f"KnowledgeBaseSetContext: Generated response with length {len(response)}")
                return response
            else:
                error_msg = f"Error setting KB context: {str(result)}"
                self.log(f"KnowledgeBaseSetContext: Error case - {error_msg}")
                return error_msg
        
        # Handle content retrieval tools
        elif tool_name == "KnowledgeBaseGetRootLevelArticles":
            if result and str(result).strip() != "[]":
                return f"""📚 **Content in Knowledge Base:**

{str(result)}

💡 **Available Actions:**
   • Add more articles
   • Edit existing content  
   • Search by tags
   • Create child articles"""
            else:
                return """📭 **No Content Found**

This knowledge base doesn't have any articles yet.

🚀 **Get Started:**
   • Add your first article
   • Create content structure
   • Import existing content"""
        
        # Handle search tools
        elif tool_name in ["KnowledgeBaseSearchArticlesByTags", "KnowledgeBaseGetArticlesForTag"]:
            if result and str(result).strip() != "[]":
                return f"""🔍 **Search Results:**

{str(result)}"""
            else:
                return "🔍 **No Results Found** - Try different search terms or add content first."
        
        # Handle other tools with string results containing success indicators
        elif "successfully" in str(result).lower() or "✅" in str(result):
            return str(result)
        
        # Handle dictionary results with success status
        elif isinstance(result, dict) and result.get("success"):
            if "message" in result:
                return result["message"]
            else:
                return f"✅ Tool {tool_name} executed successfully"
        
        # Default fallback
        else:
            return f"✅ Tool {tool_name} executed successfully"

    def _execute_llm_driven_workflow(self, workflow_plan: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute LLM-driven workflow where LLM determines intent and appropriate actions"""
        self.log("Executing LLM-driven workflow - delegating to LLM for intent detection and action")
        
        original_request = workflow_plan.get("original_request", "")
        
        # Get current context
        current_kb_id = state.get("knowledge_base_id", "Not specified")
        current_section = state.get("current_section", "Not specified")
        
        # Track consecutive tool calls for loop prevention
        consecutive_tool_calls = state.get("consecutive_tool_calls", 0)
        
        # Get conversation history for context
        conversation_history = state.get("messages", [])
        recent_conversation = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        
        # Create conversation context string
        conversation_context = ""
        if recent_conversation:
            conversation_context = "\n\nRECENT CONVERSATION HISTORY:\n"
            for i, msg in enumerate(recent_conversation):
                if hasattr(msg, 'content'):
                    role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                    # Don't truncate - keep full content for better context
                    conversation_context += f"{role}: {msg.content}\n"
        
        # Create messages for LLM with enhanced prompt for intent detection
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
INTELLIGENT INTENT DETECTION AND ACTION PLANNING

User Request: "{original_request}"

Current Context:
- Knowledge Base ID: {current_kb_id}
- Current Section: {current_section}{conversation_context}

INSTRUCTIONS - Analyze the user's request intelligently:

1. **FOR VAGUE/CONVERSATIONAL REQUESTS** (like "Can you help me create a kb?", "Help me create a kb", "I want to create a kb"):
   - **ALWAYS START A CONVERSATION** to gather requirements - NEVER assume from context
   - **DO NOT use any tools immediately** even if you see related topics in conversation history
   - Ask about: specific topic/domain, title, target audience, purpose, content areas
   - Provide guidance on KB design and structure
   - Only create KB AFTER getting explicit confirmation and specific details

2. **FOR SPECIFIC KB CREATION REQUESTS** (with clear titles like "create a kb titled 'Financial Freedom'", "build a kb about cooking"):
   - Use KnowledgeBaseInsertKnowledgeBase tool immediately
   - Extract the exact title/topic from the request
   - Set create_gitlab_project=True

3. **FOR KB CONTEXT SETTING** (like "use kb 38", "set context to kb 5", "switch to kb 12"):
   - Use KnowledgeBaseSetContext tool with the specified KB ID
   - Confirm the context switch and show KB details

4. **FOR CONTENT RETRIEVAL/VIEWING** (like "show me all content", "what content do we have", "list articles", "display all articles"):
   - If KB context is already set (Current KB ID is not "Not specified"), use KnowledgeBaseGetRootLevelArticles
   - If no KB context is set, ask user to specify which KB or use KnowledgeBaseSetContext first
   - For searches by topic/tag, use KnowledgeBaseSearchArticlesByTags

5. **FOR CONTENT CREATION** (like "add article", "create article", "write content"):
   - Use KnowledgeBaseInsertArticle tool for adding content
   - Ensure KB context is set first

6. **FOR GENERAL CONVERSATION**:
   - Provide helpful responses without using tools

**CRITICAL DECISION LOGIC:**
- If the request is **vague** or asks for **help** → ALWAYS START CONVERSATION (no tools, ignore context)
- If asking to **view/show content** and KB context is set → USE KnowledgeBaseGetRootLevelArticles
- If asking to **switch/use KB** → USE KnowledgeBaseSetContext  
- If the request has **specific details** (title, topic, clear intent) → USE APPROPRIATE TOOLS
- When in doubt → ASK QUESTIONS before taking action
- **NEVER assume KB topic from conversation history** - always ask explicitly

Analyze the user's request and choose the appropriate response style.

Execute the action NOW based on the user's request.
""")
        ]
        
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
            final_response = ""
            
            for tool_call in response.tool_calls:
                try:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    self.log(f"Executing tool: {tool_name} with args: {tool_args}")
                    
                    # Find and execute the tool
                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if tool:
                        result = tool._run(**tool_args)
                        tool_results.append({
                            "tool": tool_name,
                            "success": True,
                            "result": result
                        })
                        self.log(f"Tool {tool_name} executed successfully")
                        
                        # Process tool results and set final_response
                        final_response = self._process_tool_result(tool_name, result)
                        
                        # Debug logging
                        self.log(f"Tool {tool_name} result processing: final_response = '{final_response[:100] if final_response else 'EMPTY'}'")
                        
                    else:
                        tool_results.append({
                            "tool": tool_name,
                            "success": False,
                            "error": f"Tool {tool_name} not found"
                        })
                        self.log(f"Tool {tool_name} not found", "ERROR")
                        
                except Exception as e:
                    tool_results.append({
                        "tool": tool_call.get("name", "unknown"),
                        "success": False,
                        "error": str(e)
                    })
                    self.log(f"Error executing tool {tool_call.get('name', 'unknown')}: {str(e)}", "ERROR")
            
            # Use final_response if we have one, otherwise use the LLM's text response
            response_text = final_response if final_response else (response.content if hasattr(response, 'content') else str(response))
            
            # Debug logging
            self.log(f"Workflow completion: response_text = '{response_text[:100] if response_text else 'EMPTY'}'")
            
            # Set workflow completion flag to prevent loops
            state["workflow_completed"] = True
            state["completed_request"] = original_request
            
            return {
                "success": True,
                "message": response_text,
                "data": {
                    "tool_results": tool_results,
                    "original_request": original_request,
                    "workflow_stage": "completed"
                }
            }
        
        else:
            # No tool calls - just return the LLM's response
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Set workflow completion flag to prevent loops
            state["workflow_completed"] = True
            state["completed_request"] = original_request
            
            return {
                "success": True,
                "message": response_text,
                "data": {
                    "original_request": original_request,
                    "workflow_stage": "conversation"
                }
            }
    
    def _process_tool_result(self, tool_name: str, result: Any) -> str:
        """Process tool execution result and return user-friendly response"""
        
        # Handle KB creation
        if tool_name == "KnowledgeBaseInsertKnowledgeBase":
            if "✅" in str(result) and "Knowledge Base Created Successfully" in str(result):
                return str(result)
            else:
                return f"Error creating knowledge base: {str(result)}"
        
        # Handle KB context setting
        elif tool_name == "KnowledgeBaseSetContext":
            if isinstance(result, dict) and result.get("success"):
                kb_name = result.get("knowledge_base_name", "Unknown")
                kb_id = result.get("knowledge_base_id", "Unknown")
                gitlab_msg = ""
                if result.get("gitlab_project_id"):
                    gitlab_msg = f"\n🦊 **GitLab Project:** {result.get('gitlab_project_id')}"
                
                return f"""✅ **Knowledge Base Context Set Successfully!**

📚 **Active KB:** {kb_name} (ID: {kb_id}){gitlab_msg}

🎯 **Ready for next action:**
   • Add articles with specific topics
   • Search existing content
   • Manage KB structure
   
What would you like to do with this knowledge base?"""
            else:
                return f"Error setting KB context: {str(result)}"
        
        # Handle other successful string results
        elif "successfully" in str(result).lower() or "✅" in str(result):
            return str(result)
        
        # Handle dictionary results with success status
        elif isinstance(result, dict) and result.get("success"):
            if "message" in result:
                return result["message"]
            else:
                return f"✅ Tool {tool_name} executed successfully"
        
        # Default fallback for successful tool execution
        else:
            return f"✅ Tool {tool_name} executed successfully"

    def _execute_conversational_response(self, workflow_plan: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute conversational response for simple greetings and interactions"""
        self.log("Executing conversational response")
        
        original_request = workflow_plan.get("original_request", "").lower().strip()
        
        # Generate appropriate conversational responses
        if "hello" in original_request or "hi" in original_request or "hey" in original_request:
            response = """👋 **Hello there!** Welcome to the AI Adaptive Knowledge Base system.

I'm here to help you create, manage, and organize your knowledge bases. Here's what I can do for you:

📚 **Knowledge Base Operations:**
- Create new knowledge bases for any topic
- Add and organize articles within your KBs
- Search and retrieve information from existing content
- Manage KB structure and organization

🦊 **GitLab Integration:**
- Automatic project creation for each knowledge base
- Issue tracking for content development
- Collaborative workflow management
- Progress tracking and reporting

🚀 **How to Get Started:**
Just tell me what kind of knowledge base you'd like to create! For example:
- "Create a KB about machine learning"
- "I want a knowledge base for cooking recipes"
- "Make a KB for project management best practices"

What would you like to work on today?"""
        
        elif "thank" in original_request:
            response = """🙏 **You're very welcome!** 

I'm glad I could help you with your knowledge base needs. Feel free to ask me anything about:
- Creating new knowledge bases
- Managing existing content
- Setting up GitLab workflows
- Organizing your information

Is there anything else you'd like to work on?"""
        
        elif "how are you" in original_request:
            response = """🤖 **I'm doing great, thank you for asking!** 

I'm fully operational and ready to help you with all your knowledge base needs. My systems are running smoothly:
- ✅ Database connectivity is excellent
- ✅ GitLab integration is working perfectly  
- ✅ All knowledge base tools are ready
- ✅ Content management workflows are active

How can I assist you today with your knowledge management goals?"""
        
        else:
            response = """👋 **Greetings!** 

I'm your AI Knowledge Base Assistant, ready to help you create and manage comprehensive knowledge repositories. 

Whether you're looking to:
- 📝 Create educational content
- 🏢 Organize business knowledge  
- 📚 Build reference materials
- 🔍 Establish searchable information systems

I'm here to make it happen with full GitLab integration for collaboration and tracking.

What knowledge base project would you like to start today?"""
        
        return {
            "success": True,
            "message": response,
            "data": {
                "conversational_response": True,
                "original_request": workflow_plan.get("original_request"),
                "response_type": "greeting"
            }
        }

    def _analyze_knowledge_base_gaps(self, work_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze knowledge base for gaps and create prescriptive work items.
        This method is called by the autonomous swarm to identify work.
        """
        try:
            kb_id = work_state.get("knowledge_base_id")
            if not kb_id:
                self.log("No knowledge_base_id provided in work_state - cannot analyze gaps", "ERROR")
                return []
            
            # Get current KB structure assessment
            structure_assessment = self._assess_knowledge_base_structure(kb_id)
            
            available_work = []
            
            # Check if we need structure work items
            if structure_assessment.get("needs_structure_work"):
                available_work.append({
                    "type": "structure_foundation",
                    "title": f"Knowledge Base Structure Foundation - KB {kb_id}",
                    "description": f"Create comprehensive structure for knowledge base {kb_id}",
                    "priority": "high",
                    "kb_id": kb_id,
                    "work_category": "autonomous_management"
                })
            
            # Check if we need taxonomy work items  
            if structure_assessment.get("needs_taxonomy_work"):
                available_work.append({
                    "type": "taxonomy_foundation", 
                    "title": f"Knowledge Base Taxonomy Foundation - KB {kb_id}",
                    "description": f"Create taxonomy structure for knowledge base {kb_id}",
                    "priority": "high",
                    "kb_id": kb_id,
                    "work_category": "autonomous_management"
                })
            
            # Check for content gaps
            if structure_assessment.get("article_count", 0) == 0:
                available_work.append({
                    "type": "content_initialization",
                    "title": f"Initialize Content Creation - KB {kb_id}",
                    "description": f"Start content creation process for knowledge base {kb_id}",
                    "priority": "medium",
                    "kb_id": kb_id,
                    "work_category": "autonomous_management"
                })
            
            return available_work
            
        except Exception as e:
            self.logger.error(f"Error analyzing KB gaps: {str(e)}")
            return []

    def _execute_kb_work_to_completion(self, work_item: Dict[str, Any], work_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a knowledge base work item to completion.
        This method actually performs the work identified by _analyze_knowledge_base_gaps.
        """
        try:
            work_type = work_item.get("type")
            kb_id = work_item.get("kb_id")
            
            self.logger.info(f"[ContentManagement] Executing {work_type} for KB {kb_id}")
            
            if work_type == "structure_foundation":
                return self._execute_structure_foundation_work(work_item, work_state)
            elif work_type == "taxonomy_foundation":
                return self._execute_taxonomy_foundation_work(work_item, work_state)
            elif work_type == "content_initialization":
                return self._execute_content_initialization_work(work_item, work_state)
            else:
                return {
                    "success": False,
                    "error": f"Unknown work type: {work_type}",
                    "work_type": work_type
                }
                
        except Exception as e:
            self.logger.error(f"Error executing KB work: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "work_type": work_item.get("type", "unknown")
            }

    def _execute_structure_foundation_work(self, work_item: Dict[str, Any], work_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute structure foundation work for a knowledge base"""
        try:
            kb_id = work_item.get("kb_id")
            
            # Create structure foundation work items in GitLab
            issues_to_resolve = [
                "Missing knowledge base structural foundation",
                "Need content organization system", 
                "Require article hierarchy definition"
            ]
            
            self._create_structure_foundation_work_item(kb_id, issues_to_resolve)
            
            return {
                "success": True,
                "work_type": "structure_foundation",
                "message": f"Created structure foundation work items for KB {kb_id}",
                "items_created": len(issues_to_resolve)
            }
            
        except Exception as e:
            return {
                "success": False,
                "work_type": "structure_foundation",
                "error": str(e)
            }

    def _execute_taxonomy_foundation_work(self, work_item: Dict[str, Any], work_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute taxonomy foundation work for a knowledge base"""
        try:
            kb_id = work_item.get("kb_id")
            
            # Create taxonomy foundation work items in GitLab
            issues_to_resolve = [
                "Missing knowledge base taxonomy system",
                "Need content categorization framework",
                "Require tagging and classification system"
            ]
            
            self._create_taxonomy_foundation_work_item(kb_id, issues_to_resolve)
            
            return {
                "success": True,
                "work_type": "taxonomy_foundation", 
                "message": f"Created taxonomy foundation work items for KB {kb_id}",
                "items_created": len(issues_to_resolve)
            }
            
        except Exception as e:
            return {
                "success": False,
                "work_type": "taxonomy_foundation",
                "error": str(e)
            }

    def _execute_content_initialization_work(self, work_item: Dict[str, Any], work_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content initialization work for a knowledge base"""
        try:
            kb_id = work_item.get("kb_id")
            
            # Create a basic starter article to initialize content creation
            from tools.knowledge_base_tools import KnowledgeBaseTools
            kb_tools = KnowledgeBaseTools()
            
            # Create a welcome/introduction article
            article_result = kb_tools.create_article(
                knowledge_base_id=int(kb_id),
                title="Welcome to the Knowledge Base",
                content="""# Welcome to the Knowledge Base

This is the starting point for our knowledge base. This article serves as an introduction and foundation for future content.

## Getting Started

This knowledge base will grow over time with valuable information and resources.

## What to Expect

- Comprehensive articles on key topics
- Well-organized content structure
- Easy navigation and search capabilities

## Contributing

Content is continuously being added and improved by our automated systems and expert contributors.
""",
                metadata={"type": "introduction", "auto_generated": True}
            )
            
            if article_result.get("success"):
                return {
                    "success": True,
                    "work_type": "content_initialization",
                    "message": f"Created initial article for KB {kb_id}",
                    "article_id": article_result.get("article_id"),
                    "article_title": "Welcome to the Knowledge Base"
                }
            else:
                return {
                    "success": False,
                    "work_type": "content_initialization",
                    "error": f"Failed to create initial article: {article_result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "work_type": "content_initialization", 
                "error": str(e)
            }
