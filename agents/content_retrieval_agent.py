from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from tools.knowledge_base_tools import KnowledgeBaseTools
from prompts.knowledge_base_prompts import prompts as kb_prompts
from prompts.multi_agent_prompts import prompts as ma_prompts


class ContentRetrievalAgent(BaseAgent):
    """
    Content Retrieval Agent - Specialized agent for read-only knowledge base operations.
    Optimized for fast content retrieval, search, and analysis operations.
    
    Responsibilities:
    - Content search and retrieval
    - Knowledge base exploration
    - Content gap analysis
    - Hierarchy navigation
    - Read-only operations only
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Combine base KB prompts with specialized retrieval prompts
        base_prompt = kb_prompts.master_prompt()
        specialized_prompt = self._get_retrieval_prompt()
        system_prompt = f"{base_prompt}\n\n{specialized_prompt}"
        
        super().__init__("ContentRetrieval", llm, system_prompt)
        
        # Initialize knowledge base tools - only read operations
        kb_tools = KnowledgeBaseTools()
        all_tools = kb_tools.tools()
        
        # Filter to only read-only tools
        self.tools = self._filter_read_only_tools(all_tools)
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
    def _filter_read_only_tools(self, all_tools):
        """Filter tools to only include read-only operations"""
        read_only_tool_names = {
            "KnowledgeBaseGetKnowledgeBases",
            "KnowledgeBaseGetArticleHierarchy", 
            "KnowledgeBaseGetRootLevelArticles",
            "KnowledgeBaseGetArticleByArticleId",
            "KnowledgeBaseGetChildArticlesByParentIds",
            "KnowledgeBaseAnalyzeContentGaps"
        }
        
        return [tool for tool in all_tools if tool.name in read_only_tool_names]
    
    def _get_retrieval_prompt(self):
        """Get specialized prompt for content retrieval operations"""
        return """
        You are a Content Retrieval Specialist focused on efficient content discovery and analysis.
        
        Your core responsibilities:
        - Perform fast and accurate content searches
        - Navigate knowledge base hierarchies efficiently
        - Analyze content gaps and relationships
        - Provide comprehensive retrieval results
        - Optimize queries for performance
        
        Key principles:
        - READ-ONLY operations only - never modify content
        - Focus on comprehensive and accurate results
        - Use efficient querying strategies
        - Provide rich metadata with results
        - Structure responses for easy consumption by other agents
        
        When handling requests:
        1. Identify the most efficient retrieval strategy
        2. Execute searches with appropriate depth
        3. Format results with relevant metadata
        4. Highlight relationships and patterns
        5. Suggest related content when relevant
        """
    
    def process(self, state: AgentState) -> AgentState:
        """Process content retrieval requests"""
        self.log("Processing content retrieval request")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from Supervisor
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            self.log("No retrieval requests found")
            return state
        
        # Get the latest retrieval request
        latest_request = my_messages[-1]
        workflow_plan = latest_request.metadata.get("workflow_plan", {})
        
        self.log(f"Executing workflow: {workflow_plan.get('workflow_type', 'unknown')}")
        
        # Execute retrieval workflow
        result = self._execute_retrieval_workflow(
            latest_request.content,
            workflow_plan,
            state
        )
        
        # Send result back to Supervisor
        response_message = self.create_message(
            recipient="Supervisor",
            message_type="retrieval_complete",
            content=result,
            metadata={
                "original_request": latest_request.content,
                "workflow_plan": workflow_plan,
                "operation_type": "retrieval"
            }
        )
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(response_message)
        
        # Route back to Supervisor for coordination
        state["current_agent"] = "Supervisor"
        
        self.log("Content retrieval completed, returning to Supervisor")
        return state
    
    def _execute_retrieval_workflow(self, request: str, workflow_plan: Dict, state: AgentState) -> str:
        """Execute the specific retrieval workflow"""
        workflow_type = workflow_plan.get("workflow_type", "")
        
        if workflow_type == "content_search":
            return self._handle_content_search(request, workflow_plan, state)
        elif workflow_type == "content_analysis":
            return self._handle_content_analysis(request, workflow_plan, state)
        elif workflow_type == "hierarchy_exploration":
            return self._handle_hierarchy_exploration(request, workflow_plan, state)
        else:
            return self._handle_general_retrieval(request, workflow_plan, state)
    
    def _handle_content_search(self, request: str, workflow_plan: Dict, state: AgentState) -> str:
        """Handle content search requests"""
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
            Perform a comprehensive content search based on this request: {request}
            
            Use the available tools to:
            1. Search for relevant articles
            2. Explore related content
            3. Provide detailed results with metadata
            
            Workflow plan: {workflow_plan}
            """)
        ]
        
        try:
            response = self.llm_with_tools.invoke(messages)
            return self._process_tool_response(response, state)
        except Exception as e:
            return f"Error during content search: {str(e)}"
    
    def _handle_content_analysis(self, request: str, workflow_plan: Dict, state: AgentState) -> str:
        """Handle content gap analysis requests"""
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
            Perform content gap analysis based on this request: {request}
            
            Use the analyze content gaps tool to:
            1. Identify missing content areas
            2. Analyze existing content structure
            3. Provide actionable insights
            
            Workflow plan: {workflow_plan}
            """)
        ]
        
        try:
            response = self.llm_with_tools.invoke(messages)
            return self._process_tool_response(response, state)
        except Exception as e:
            return f"Error during content analysis: {str(e)}"
    
    def _handle_hierarchy_exploration(self, request: str, workflow_plan: Dict, state: AgentState) -> str:
        """Handle knowledge base hierarchy exploration"""
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
            Explore the knowledge base hierarchy based on this request: {request}
            
            Use hierarchy tools to:
            1. Navigate the content structure
            2. Show relationships between articles
            3. Provide a clear overview
            
            Workflow plan: {workflow_plan}
            """)
        ]
        
        try:
            response = self.llm_with_tools.invoke(messages)
            return self._process_tool_response(response, state)
        except Exception as e:
            return f"Error during hierarchy exploration: {str(e)}"
    
    def _handle_general_retrieval(self, request: str, workflow_plan: Dict, state: AgentState) -> str:
        """Handle general retrieval requests"""
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
            Handle this content retrieval request: {request}
            
            Determine the best approach and use appropriate tools to:
            1. Retrieve the requested content
            2. Provide comprehensive results
            3. Include relevant metadata
            
            Workflow plan: {workflow_plan}
            """)
        ]
        
        try:
            response = self.llm_with_tools.invoke(messages)
            return self._process_tool_response(response, state)
        except Exception as e:
            return f"Error during content retrieval: {str(e)}"
    
    def _process_tool_response(self, response, state: AgentState) -> str:
        """Process the LLM response and handle any tool calls"""
        # Handle tool calls if present
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute tool calls and format results
            results = []
            for tool_call in response.tool_calls:
                try:
                    # Find and execute the tool
                    tool = next((t for t in self.tools if t.name == tool_call['name']), None)
                    if tool:
                        result = tool.run(tool_call['args'])
                        results.append(f"Tool {tool_call['name']}: {result}")
                    else:
                        results.append(f"Tool {tool_call['name']} not found")
                except Exception as e:
                    results.append(f"Error executing {tool_call['name']}: {str(e)}")
            
            return "\n\n".join(results)
        
        # Return the direct response if no tool calls
        return response.content if hasattr(response, 'content') else str(response)
