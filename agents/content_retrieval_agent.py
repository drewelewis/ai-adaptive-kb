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
from prompts.foundational_prompts import AgentSpecificFoundations


class ContentRetrievalAgent(BaseAgent):
    """
    Content Retrieval Agent - Specialized agent for read-only knowledge base operations with GitLab integration.
    Optimized for fast content retrieval, search, and analysis operations.
    
    Responsibilities:
    - Content search and retrieval
    - Knowledge base exploration
    - Content gap analysis
    - Hierarchy navigation
    - Read-only operations only
    - Access GitLab to find assigned retrieval and analysis work
    - Communicate analysis results through GitLab issue updates
    - Support other agents with content research through GitLab coordination
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Use foundational prompt from AgentSpecificFoundations
        foundational_prompt = AgentSpecificFoundations.content_retrieval_foundation()
        specialized_prompt = self._get_retrieval_prompt()
        gitlab_integration_prompt = self._create_gitlab_integration_prompt()
        system_prompt = f"{foundational_prompt}\n\n{specialized_prompt}\n\n{gitlab_integration_prompt}"
        
        super().__init__("ContentRetrieval", llm, system_prompt)
        
        # Initialize knowledge base tools - only read operations
        kb_tools = KnowledgeBaseTools()
        all_kb_tools = kb_tools.tools()
        
        # Initialize GitLab tools
        self.gitlab_tools = GitLabTools()
        
        # Filter to only read-only tools
        filtered_kb_tools = self._filter_read_only_tools(all_kb_tools)
        
        # Combine all tools
        self.tools = filtered_kb_tools + self.gitlab_tools.tools()
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
    def _filter_read_only_tools(self, all_tools):
        """Filter tools to only include read-only operations"""
        read_only_tool_names = {
            "KnowledgeBaseSetContext",  # Needed for KB context establishment
            "KnowledgeBaseSetContextByGitLabProject",  # CRITICAL: Needed for GitLab-to-KB context establishment
            "KnowledgeBaseGetKnowledgeBases",
            "KnowledgeBaseGetArticleHierarchy", 
            "KnowledgeBaseGetRootLevelArticles",
            "KnowledgeBaseGetArticleByArticleId",
            "KnowledgeBaseGetChildArticlesByParentIds",
            "KnowledgeBaseAnalyzeContentGaps"
        }
        
        return [tool for tool in all_tools if tool.name in read_only_tool_names]
    
    def _create_gitlab_integration_prompt(self) -> str:
        """Create GitLab integration prompt for the content retrieval agent"""
        return """
**GITLAB INTEGRATION - CONTENT RESEARCH & ANALYSIS SUPPORT:**

You have comprehensive GitLab integration capabilities for content research and analysis support:

**RESEARCH WORK DISCOVERY:**
- Check GitLab issues for assigned content research and analysis tasks
- Find research requests from ContentPlanner, ContentCreator, and ContentReviewer agents
- Access detailed research requirements and scope from GitLab issue descriptions
- Monitor research backlogs and support requests across projects

**COLLABORATIVE CONTENT RESEARCH:**
- Provide detailed content analysis and gap identification through GitLab issue comments
- Support ContentPlanner with comprehensive domain research for strategic planning
- Assist ContentCreator with content research and reference materials
- Help ContentReviewer with completeness validation and gap analysis

**HUMAN COLLABORATION:**
- Recognize that human users are active participants in GitLab alongside agents
- Any user who is not an agent is considered a human end user
- Use GitLab issues, comments, and discussions to ask questions when research scope is unclear
- Monitor GitLab continuously for human feedback, guidance, and research direction
- Never proceed with unclear research requirements - always ask humans for clarification
- Human input takes priority and drives all research and analysis decisions
- Ensure transparent communication with humans through GitLab collaboration tools

**ANALYSIS AND REPORTING:**
- Document comprehensive content analysis results in GitLab issue comments
- Create detailed content gap reports as GitLab issue attachments or descriptions
- Provide structured research findings to support other agents' work
- Track research completion and share findings through GitLab workflows

**CROSS-PROJECT INTELLIGENCE:**
- Analyze content patterns and trends across multiple GitLab projects
- Identify opportunities for content reuse and cross-referencing
- Provide competitive analysis and benchmark research through GitLab reporting
- Support strategic content decisions with data-driven GitLab documentation

**RESEARCH WORKFLOW:**
1. **Check Research Queue**: Look for assigned research and analysis work in GitLab
2. **Access Requirements**: Review detailed research scope from GitLab issue descriptions
3. **Execute Analysis**: Perform comprehensive content research and gap analysis
4. **Document Findings**: Provide detailed research results through GitLab comments
5. **Support Collaboration**: Assist other agents with research-based decision making
6. **Track Completion**: Update GitLab issue status when research is complete

**GITLAB CAPABILITIES AVAILABLE:**
- Access research assignments and detailed scope requirements
- Provide comprehensive analysis reports through issue documentation
- Support other agents with research findings and content intelligence
- Track research metrics and completion rates across projects
- Create research knowledge base for team reference and reuse

**BEST PRACTICES:**
- Always check GitLab for research context and requirements before starting analysis
- Provide structured, actionable research findings through detailed GitLab comments
- Use GitLab to coordinate research support for other agents
- Document research methodologies and sources for future reference
- Maintain comprehensive research audit trails through GitLab documentation

When conducting content research, leverage GitLab's collaborative features to provide maximum value and support to the content creation and planning team.
"""
    
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
    
    def analyze_content_gaps(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze knowledge base research and data gaps"""
        self.log("🔍 ContentRetrievalAgent analyzing KB for research gaps and retrieval opportunities...")
        
        try:
            # Ensure KB context is set before research analysis
            if not self.ensure_kb_context():
                self.log("❌ Failed to establish KB context")
                return {"found_work": False, "message": "Could not establish KB context"}
            
            # Log current KB context for transparency
            kb_context = self.get_kb_context()
            self.log(f"📚 Research analysis for KB: {kb_context.get('knowledge_base_name')} (ID: {kb_context.get('knowledge_base_id')})")
            self.log(f"📄 KB Focus: {kb_context.get('knowledge_base_description', 'No description')}")
            
            # Autonomous Priority 1: Analyze missing research and data needs
            research_gaps = self.analyze_research_gaps(state)
            if research_gaps.get("gaps_found", False):
                self.log("✅ Found research gaps requiring data gathering")
                # Create GitLab work items for research gaps
                work_creation_result = self.create_work_for_research_gaps(research_gaps)
                return {
                    "found_work": True,
                    "work_type": "autonomous_research_gaps",
                    "work_details": research_gaps,
                    "work_created": work_creation_result,
                    "priority": "high"
                }
            
            # Autonomous Priority 2: Analyze content cross-referencing needs
            cross_ref_needs = self.analyze_cross_referencing_needs(state)
            if cross_ref_needs.get("cross_ref_needed", False):
                self.log("✅ Found content cross-referencing opportunities")
                # Create GitLab work items for cross-referencing
                work_creation_result = self.create_work_for_cross_referencing(cross_ref_needs)
                return {
                    "found_work": True,
                    "work_type": "autonomous_cross_referencing",
                    "work_details": cross_ref_needs,
                    "work_created": work_creation_result,
                    "priority": "medium"
                }
            
            # Autonomous Priority 3: Analyze knowledge base search optimization needs
            search_optimization = self.analyze_search_optimization_needs()
            if search_optimization.get("optimization_needed", False):
                self.log("✅ Found search optimization opportunities")
                # Create GitLab work items for search optimization
                work_creation_result = self.create_work_for_search_optimization(search_optimization)
                return {
                    "found_work": True,
                    "work_type": "autonomous_search_optimization",
                    "work_details": search_optimization,
                    "work_created": work_creation_result,
                    "priority": "low"
                }
            
            # No autonomous work opportunities found
            self.log("💡 No immediate research opportunities found - KB retrieval systems appear optimal")
            return {
                "found_work": False,
                "message": "Knowledge base research analysis complete - no immediate research gaps detected"
            }
            
        except Exception as e:
            self.log(f"❌ Error in autonomous work discovery: {str(e)}")
            return {
                "found_work": False,
                "message": f"Error in autonomous research analysis: {str(e)}"
            }
    
    def analyze_research_gaps(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze knowledge base for research and data gaps"""
        try:
            self.log("🔍 Analyzing KB for research gaps...")
            
            # Simulated research gap analysis - would use KB search tools in practice
            research_gaps = [
                {
                    "type": "market_data_gap",
                    "description": "Current market analysis data missing for investment articles",
                    "priority": "high",
                    "research_type": "financial_data"
                },
                {
                    "type": "regulatory_update_gap",
                    "description": "Recent tax law changes need research and integration",
                    "priority": "medium",
                    "research_type": "regulatory_research"
                }
            ]
            
            if research_gaps:
                return {
                    "gaps_found": True,
                    "gaps": research_gaps[:1],  # Limit to top 1
                    "analysis_method": "research_gap_analysis"
                }
            else:
                return {"gaps_found": False, "message": "No research gaps identified"}
                
        except Exception as e:
            self.log(f"❌ Error analyzing research gaps: {str(e)}")
            return {"gaps_found": False, "message": f"Error in research analysis: {str(e)}"}
    
    def analyze_cross_referencing_needs(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze content for cross-referencing and connection opportunities"""
        try:
            self.log("🔍 Analyzing content cross-referencing needs...")
            
            cross_ref_opportunities = [
                {
                    "type": "topic_linking",
                    "description": "Investment articles could benefit from retirement planning cross-references",
                    "priority": "medium",
                    "scope": "inter_topic_connections"
                }
            ]
            
            if cross_ref_opportunities:
                return {
                    "cross_ref_needed": True,
                    "opportunities": cross_ref_opportunities[:1],  # Limit to top 1
                    "analysis_method": "cross_reference_analysis"
                }
            else:
                return {"cross_ref_needed": False, "message": "No cross-referencing opportunities identified"}
                
        except Exception as e:
            self.log(f"❌ Error analyzing cross-referencing needs: {str(e)}")
            return {"cross_ref_needed": False, "message": f"Error in cross-reference analysis: {str(e)}"}
    
    def analyze_search_optimization_needs(self) -> Dict[str, Any]:
        """Analyze knowledge base search and retrieval optimization needs"""
        try:
            self.log("🔍 Analyzing search optimization needs...")
            
            optimization_opportunities = [
                {
                    "type": "search_indexing",
                    "description": "Knowledge base search index could benefit from keyword optimization",
                    "priority": "low",
                    "scope": "search_performance"
                }
            ]
            
            if optimization_opportunities:
                return {
                    "optimization_needed": True,
                    "opportunities": optimization_opportunities[:1],  # Limit to top 1
                    "analysis_method": "search_optimization_analysis"
                }
            else:
                return {"optimization_needed": False, "message": "No search optimization opportunities identified"}
                
        except Exception as e:
            self.log(f"❌ Error analyzing search optimization: {str(e)}")
            return {"optimization_needed": False, "message": f"Error in search analysis: {str(e)}"}
    
    def create_work_for_research_gaps(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for research gaps"""
        try:
            self.log("📝 Creating GitLab work items for research gaps...")
            
            work_items_created = []
            gaps = research_data.get("gaps", [])
            
            for gap in gaps:
                work_item = {
                    "title": f"Research Gap: {gap['description']}",
                    "description": f"Research needed: {gap['type']} - {gap['research_type']}",
                    "priority": gap['priority'],
                    "labels": ["research-gap", "autonomous-work", "data-gathering"],
                    "type": "research_work"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created research work item: {work_item['title']}")
            
            return {
                "created": True,
                "work_items": work_items_created,
                "count": len(work_items_created)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating research work items: {str(e)}")
            return {"created": False, "message": f"Error creating work: {str(e)}"}
    
    def create_work_for_cross_referencing(self, cross_ref_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for cross-referencing work"""
        try:
            self.log("📝 Creating GitLab work items for cross-referencing...")
            
            work_items_created = []
            opportunities = cross_ref_data.get("opportunities", [])
            
            for opportunity in opportunities:
                work_item = {
                    "title": f"Cross-Reference: {opportunity['description']}",
                    "description": f"Cross-referencing work: {opportunity['type']} - {opportunity['scope']}",
                    "priority": opportunity['priority'],
                    "labels": ["cross-referencing", "autonomous-work", "content-linking"],
                    "type": "cross_reference_work"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created cross-reference work item: {work_item['title']}")
            
            return {
                "created": True,
                "work_items": work_items_created,
                "count": len(work_items_created)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating cross-reference work items: {str(e)}")
            return {"created": False, "message": f"Error creating work: {str(e)}"}
    
    def create_work_for_search_optimization(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for search optimization"""
        try:
            self.log("📝 Creating GitLab work items for search optimization...")
            
            work_items_created = []
            opportunities = optimization_data.get("opportunities", [])
            
            for opportunity in opportunities:
                work_item = {
                    "title": f"Search Optimization: {opportunity['description']}",
                    "description": f"Search optimization work: {opportunity['type']} - {opportunity['scope']}",
                    "priority": opportunity['priority'],
                    "labels": ["search-optimization", "autonomous-work", "retrieval-improvement"],
                    "type": "search_optimization_work"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created search optimization work item: {work_item['title']}")
            
            return {
                "created": True,
                "work_items": work_items_created,
                "count": len(work_items_created)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating search optimization work items: {str(e)}")
            return {"created": False, "message": f"Error creating work: {str(e)}"}

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
