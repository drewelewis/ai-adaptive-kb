from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from agents.base_agent import BaseAgent
from agents.agent_types import AgentState, AgentMessage
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
            return state
        
        # Get the latest workflow request
        latest_request = my_messages[-1]
        workflow_plan = latest_request.metadata.get("workflow_plan", {})
        
        self.log(f"Executing workflow: {workflow_plan.get('intent', 'unknown')}")
        
        # Execute the content management workflow
        try:
            result = self._execute_content_workflow(workflow_plan, state)
            
            # Create success response for Supervisor
            response = self.create_message(
                recipient="Supervisor",
                message_type="workflow_response",
                content=result["message"],
                metadata={"success": True, "results": result["data"]}
            )
            
        except Exception as e:
            self.log(f"Error executing workflow: {str(e)}", "ERROR")
            
            # Create error response for Supervisor
            response = self.create_message(
                recipient="Supervisor", 
                message_type="workflow_response",
                content=f"Content management operation failed: {str(e)}",
                metadata={"success": False, "error": str(e)}
            )
        
        # Add response to agent messages
        state["agent_messages"].append(response)
        
        # Return control to Supervisor
        state["current_agent"] = "Supervisor"
        
        return state
    
    def _execute_content_workflow(self, workflow_plan: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute the content management workflow using available tools"""
        intent = workflow_plan.get("intent", "")
        steps = workflow_plan.get("steps", [])
        
        self.log(f"Executing {len(steps)} workflow steps for intent: {intent}")
        
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
Original Request: {workflow_plan.get('original_request', 'Not provided')}

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
- If intent is "set_knowledge_base_context" and original request contains "use kb X":
  * Extract the KB ID (X) from the original request: "{workflow_plan.get('original_request', 'Not provided')}"
  * Use the KnowledgeBaseSetContext tool with knowledge_base_id="X" (where X is the number from the request)
  * Do NOT use KnowledgeBaseGetKnowledgeBases for this purpose - that's only for listing available KBs
  * REQUIRED: Call KnowledgeBaseSetContext to actually set the context

Examples:
- Original request "use kb 1" → call KnowledgeBaseSetContext with knowledge_base_id="1"
- Original request "ok, let use kb 1" → call KnowledgeBaseSetContext with knowledge_base_id="1"  
- Original request "switch to kb 2" → call KnowledgeBaseSetContext with knowledge_base_id="2"

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
                    if tool_call.get("name") == "KnowledgeBaseSetContext" and tool_result.get("success"):
                        # KnowledgeBaseSetContext returns data directly, not nested under "result"
                        if tool_result.get("success"):
                            state["knowledge_base_id"] = tool_result.get("knowledge_base_id")
                            state["knowledge_base_name"] = tool_result.get("knowledge_base_name")
                            self.log(f"Updated knowledge base context to: {tool_result.get('knowledge_base_name')} (ID: {tool_result.get('knowledge_base_id')})")
                    
                    # Check if this was a KnowledgeBaseSetArticleContext call and update state
                    elif tool_call.get("name") == "KnowledgeBaseSetArticleContext" and tool_result.get("success"):
                        article_context = tool_result.get("result", {})
                        if article_context.get("success"):
                            state["knowledge_base_id"] = article_context.get("knowledge_base_id")
                            state["article_id"] = article_context.get("article_id")
                            self.log(f"Updated article context to: {article_context.get('article_id')} in KB {article_context.get('knowledge_base_id')}")
                            
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
                "message": response.content,
                "data": {
                    "tool_results": tool_results,
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
