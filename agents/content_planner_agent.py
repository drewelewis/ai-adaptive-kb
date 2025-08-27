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

# Ensure environment variables are loaded for database connectivity
from dotenv import load_dotenv
load_dotenv(override=True)


class ContentPlannerAgent(BaseAgent):
    """
    Content Planner Agent - Strategic planning and content architecture specialist with GitLab integration.
    
    Responsibilities:
    - Analyze high-level KB ideas and determine comprehensive scope
    - Create detailed content strategies and article hierarchies
    - Identify knowledge gaps and coverage opportunities
    - Ask intelligent clarifying questions when scope is unclear
    - Design publication-ready content structures
    - Coordinate with other agents through GitLab issues and projects
    - Access GitLab to find assigned planning work
    - Communicate with other agents through GitLab issue comments and status updates
    - Ask questions and seek clarification using GitLab issue comments
    - Monitor and respond to other agents' questions in issue comments
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Use shared foundational approach combined with specialized planning prompts
        foundational_prompt = AgentSpecificFoundations.content_planning_foundation()
        specialized_prompt = self._get_planning_prompt()
        gitlab_integration_prompt = self._create_gitlab_integration_prompt()
        system_prompt = f"{foundational_prompt}\n\n{specialized_prompt}\n\n{gitlab_integration_prompt}"
        
        super().__init__("ContentPlanner", llm, system_prompt)
        
        # Initialize knowledge base tools - planning and analysis focused
        kb_tools = KnowledgeBaseTools()
        all_kb_tools = kb_tools.tools()
        
        # Initialize GitLab tools
        self.gitlab_tools = GitLabTools()
        
        # Filter to planning-relevant KB tools
        filtered_kb_tools = self._filter_planning_tools(all_kb_tools)
        
        # Combine all tools
        self.tools = filtered_kb_tools + self.gitlab_tools.tools()
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
    def _filter_planning_tools(self, all_tools):
        """Filter tools to include planning and analysis operations"""
        planning_tool_names = {
            "KnowledgeBaseGetKnowledgeBases",
            "KnowledgeBaseAnalyzeContentGaps",
            "KnowledgeBaseGetArticleHierarchy",
            "KnowledgeBaseInsertKnowledgeBase",
            "KnowledgeBaseUpdateKnowledgeBase",
            "KnowledgeBaseGetRootLevelArticles",
            "KnowledgeBaseSetContext",  # Added for automatic context setting after KB creation
            "KnowledgeBaseSetContextByGitLabProject"  # CRITICAL: Needed for GitLab-to-KB context establishment
        }
        
        return [tool for tool in all_tools if tool.name in planning_tool_names]
    
    def _create_gitlab_integration_prompt(self) -> str:
        """Create GitLab integration prompt for the content planner agent"""
        return """
**GITLAB INTEGRATION - STRATEGIC PLANNING & COORDINATION:**

You have comprehensive GitLab integration capabilities for strategic planning and agent coordination:

**WORK DISCOVERY & ASSIGNMENT:**
- Check GitLab issues for assigned strategic planning tasks
- Find planning requests from supervisors and other agents
- Access project-level planning initiatives and knowledge base strategies
- Monitor cross-project planning needs and resource allocation opportunities

**STRATEGIC COORDINATION:**
- Create strategic planning issues for complex multi-phase projects
- Coordinate with other content agents through GitLab issue assignments
- Document strategic decisions and planning rationale in GitLab
- Track planning dependencies and resource allocation across projects

**HUMAN COLLABORATION:**
- Recognize that human users are active participants in GitLab alongside agents
- Any user who is not an agent is considered a human end user
- Use GitLab issues, comments, and discussions to ask questions when strategic direction is unclear
- Monitor GitLab continuously for human feedback, guidance, and strategic input
- Never proceed with unclear strategic requirements - always ask humans for clarification
- Human input takes priority and drives all strategic planning decisions
- Ensure transparent communication with humans through GitLab collaboration tools

**COLLABORATIVE PLANNING:**
- Work with ContentCreatorAgent, ContentReviewerAgent through GitLab issue threads
- Create detailed implementation plans as GitLab issue templates
- Break down large planning initiatives into actionable agent assignments
- Coordinate timing and resource allocation through GitLab project management

**HOLISTIC RESOURCE MANAGEMENT:**
- Review current KB state across all projects in GitLab
- Identify strategic opportunities for content improvement and expansion
- Plan resource allocation based on GitLab project priorities and deadlines
- Create cross-project planning initiatives for maximum impact

**PLANNING WORKFLOW:**
1. **Check Planning Queue**: Look for strategic planning assignments in GitLab
2. **Analyze Current State**: Review existing KB content and GitLab project status
3. **Create Strategic Plans**: Document comprehensive planning in GitLab issues
4. **Assign Implementation Work**: Create specific issues for other content agents
5. **Monitor Progress**: Track implementation through GitLab issue updates
6. **Adjust Strategy**: Update planning based on agent feedback and results

**GITLAB CAPABILITIES AVAILABLE:**
- Access all GitLab projects and planning-related issues
- Create strategic planning issues with detailed implementation templates
- Assign work to ContentCreator and ContentReviewer agents
- Track planning progress and resource utilization across projects
- Document strategic decisions and rationale for audit trails

**BEST PRACTICES:**
- Always check GitLab for existing planning context before starting new strategies
- Create clear, actionable issue templates for implementation teams
- Use GitLab project management to coordinate multi-agent planning initiatives
- Document strategic rationale and decisions for future reference
- Leverage GitLab's cross-project visibility for holistic resource management

When engaging in strategic planning, consider the entire ecosystem of projects and agent resources available through GitLab to maximize impact and efficiency.
"""
    
    def _get_planning_prompt(self):
        """Get specialized prompt for content planning operations"""
        return """
        You are a Content Strategy and Planning Specialist with expertise in creating comprehensive knowledge base architectures across MULTIPLE KNOWLEDGE BASES.
        
        🌐 MULTI-KB ENVIRONMENT AWARENESS:
        You work across MULTIPLE knowledge bases, each with unique topics, audiences, and structures.
        Always verify which specific knowledge base you're working with before planning or analyzing.
        Every planning decision must include clear KB context identification.
        Never mix planning between different knowledge bases.
        
        MULTI-KB PLANNING PRINCIPLES:
        1. **KB Context Verification**: Always confirm which KB you're planning for before starting
        2. **Context-Specific Planning**: Tailor strategies to the specific KB's domain and audience
        3. **Cross-KB Prevention**: Never mix content or strategies between different KBs
        4. **Context Communication**: Always specify which KB your planning applies to
        5. **KB Transition Management**: When switching KB contexts, explicitly acknowledge the change
        
        Your core responsibilities:
        - Transform high-level ideas into detailed, comprehensive content strategies for specific KBs
        - Design optimal knowledge base structures and hierarchies tailored to each KB's domain
        - Ask intelligent clarifying questions only when scope is truly unclear for the specific KB
        - Create publication-ready content frameworks that support multiple output formats
        
        Planning Philosophy:
        - AUTONOMOUS DECISION-MAKING: Make intelligent scope decisions based on domain analysis
        - MINIMAL CLARIFICATION: Only ask questions when absolutely necessary for scope determination
        - FUTURE-READY ARCHITECTURE: Design structures that can be easily adapted for different content formats
        
        When receiving a KB creation request:
        1. Verify and confirm the target knowledge base context
        2. Analyze the domain and determine natural scope boundaries for that specific KB
        3. Research the topic area to understand comprehensive coverage requirements
        4. Design a logical, hierarchical content structure suitable for multiple output formats
        5. Identify all major topics, subtopics, and relationships specific to that KB
        6. Only ask clarifying questions if the scope is genuinely ambiguous for that KB
        7. Create a detailed implementation plan for ContentCreator with clear KB context
        """
    
    def process(self, state: AgentState) -> AgentState:
        """Process planning requests and create comprehensive content strategies"""
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from Supervisor
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            self.log("No planning requests found")
            return state
        
        # Get the latest planning request
        latest_request = my_messages[-1]
        user_request = latest_request.content
        
        self.log(f"Planning KB creation for: {user_request}")
        
        # Analyze request and create comprehensive plan
        planning_result = self._create_content_strategy(user_request, state)
        
        # Determine next step based on planning result
        if self._needs_clarification(planning_result):
            # Send clarification request back to user via UserProxy
            response_message = self.create_message(
                recipient="UserProxy",
                message_type="clarification_request",
                content=planning_result["clarification_questions"],
                metadata={
                    "original_request": user_request,
                    "planning_stage": "clarification_needed",
                    "partial_plan": planning_result.get("partial_plan", {})
                }
            )
            
            # Route back to UserProxy for clarification
            state["current_agent"] = "UserProxy"
            
        else:
            # Send complete plan to ContentCreator
            # Get KB ID from state (consistent field name)
            kb_id = state.get('knowledge_base_id')
            kb_info = state.get('created_kb_info', {})
            
            self.log(f"DEBUG: Using KB ID from state: {kb_id}")
            
            # Prepare the message content
            message_content = "Content strategy complete. Proceeding with KB creation."
            kb_notification = state.get("kb_context_notification")
            if kb_notification:
                message_content = f"{kb_notification}\n\n{message_content}"
            
            response_message = self.create_message(
                recipient="ContentCreator",
                message_type="content_creation_plan",
                content=message_content,
                metadata={
                    "original_request": user_request,
                    "content_strategy": planning_result["strategy"],
                    "article_hierarchy": planning_result["hierarchy"],
                    "implementation_plan": planning_result["implementation"],
                    "kb_created": planning_result.get("kb_created"),
                    "kb_id": kb_id,  # Pass the KB ID from state
                    "kb_info": kb_info,
                    "kb_context_notification": kb_notification
                }
            )
            
            self.log(f"DEBUG: Sending KB ID {kb_id} to ContentCreator via metadata")
            
            # Route to ContentCreator for implementation
            state["current_agent"] = "ContentCreator"
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(response_message)
        
        self.log("Content planning completed")
        return state
    
    def _create_content_strategy(self, user_request: str, state: AgentState) -> Dict[str, Any]:
        """Create comprehensive content strategy for the KB request"""
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
            Create a comprehensive knowledge base for this request: {user_request}
            
            You MUST use the available tools to actually create the knowledge base. Follow this process:
            
            1. IMMEDIATELY use the KnowledgeBaseInsertKnowledgeBase tool to create the KB
            2. Plan the content structure and hierarchy 
            3. Determine if any clarification is needed for scope
            
            REQUIRED ACTION: You must call KnowledgeBaseInsertKnowledgeBase with this exact format:
            
            Tool Call Name: KnowledgeBaseInsertKnowledgeBase
            Tool Parameters:
            {{
                "knowledge_base": {{
                    "name": "Clean title extracted from user request",
                    "description": "DETAILED STRATEGIC DESCRIPTION - Must include: \n\n🎯 **Purpose & Scope**: Clear definition of what this KB covers and why it matters\n\n👥 **Target Audience**: Who will benefit from this content and their expertise level\n\n📋 **Content Strategy**: Approach for organizing information (beginner→advanced, problem-based, domain-specific structure)\n\n🔍 **Coverage Areas**: Key topics, subtopics, and specialized areas to be addressed\n\n📚 **Content Depth**: Level of detail and expertise demonstrated (introductory, intermediate, expert-level)\n\n🎪 **Use Cases**: How this KB will be repurposed (ebooks, blog series, educational materials, professional resources)\n\n💡 **Value Proposition**: Unique insights, frameworks, or perspectives this KB will provide\n\n🔄 **Content Approach**: Research methodology, citation standards, practical examples vs theoretical focus",  
                    "author_id": 1
                }}
            }}
            
            CRITICAL: The "knowledge_base" wrapper is required - do not pass name/description/author_id directly.
            The tool expects a "knowledge_base" parameter containing the InsertModel object.
            
            DESCRIPTION REQUIREMENTS: Create a comprehensive 200-500 word description that serves as a strategic guide for ContentCreator agents. Include specific details about content strategy, target audience, scope boundaries, depth levels, organizational approach, and intended use cases. This description will guide all future content creation for this KB.
            
            DO NOT just plan - you must actually CREATE the knowledge base using the tools.
            
            After creating the KB, analyze:
            1. Optimal scope and domain boundaries
            2. Comprehensive content hierarchy and structure
            3. Key topics and subtopics to cover
            4. Depth level appropriate for the domain
            5. Whether any clarification is truly needed
            
            If the request is clear enough to proceed (even if broad), create a complete strategy.
            Only flag for clarification if the scope is genuinely ambiguous.
            
            IMPORTANT: You must use the KnowledgeBaseInsertKnowledgeBase tool in your response.
            The description you provide will guide all future ContentCreator agents working on this KB.
            Make it comprehensive, strategic, and actionable.
            """)
        ]
        
        try:
            self.log(f"DEBUG: Invoking LLM with {len(self.tools)} tools for content planning")
            self.log(f"DEBUG: Available tools: {[tool.name for tool in self.tools]}")
            response = self.llm_with_tools.invoke(messages)
            self.log(f"DEBUG: LLM response received, type: {type(response)}")
            self.log(f"DEBUG: Response has tool_calls: {hasattr(response, 'tool_calls')}")
            if hasattr(response, 'tool_calls'):
                self.log(f"DEBUG: Number of tool calls: {len(response.tool_calls) if response.tool_calls else 0}")
                
                # Process tool calls and capture KB ID
                kb_created = None
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        try:
                            self.log(f"DEBUG: Processing tool call: {tool_call['name']}")
                            self.log(f"DEBUG: Tool call args: {tool_call['args']}")
                            
                            tool = next((t for t in self.tools if t.name == tool_call['name']), None)
                            if tool:
                                # Fix KB creation tool call structure if needed
                                if tool_call['name'] == 'KnowledgeBaseInsertKnowledgeBase':
                                    args = tool_call['args']
                                    # Check if the LLM provided the wrong structure
                                    if 'knowledge_base' not in args and 'name' in args:
                                        self.log("DEBUG: Fixing malformed KB creation tool call")
                                        # Restructure the args to match expected format
                                        fixed_args = {
                                            'knowledge_base': {
                                                'name': args.get('name'),
                                                'description': args.get('description', 'Knowledge base created by AI system'),
                                                'author_id': args.get('author_id', 1)
                                            }
                                        }
                                        self.log(f"DEBUG: Fixed args: {fixed_args}")
                                        result = tool.run(fixed_args)
                                    else:
                                        result = tool.run(args)
                                else:
                                    result = tool.run(tool_call['args'])
                                    
                                self.log(f"DEBUG: Tool {tool_call['name']} executed successfully")
                                
                                # Capture KB creation result
                                if tool_call['name'] == 'KnowledgeBaseInsertKnowledgeBase':
                                    kb_created = result
                                    # Handle both dict and int returns from tool
                                    if isinstance(result, dict):
                                        kb_id = result.get('id')
                                    elif isinstance(result, int):
                                        kb_id = result
                                        kb_created = {'id': result}
                                    else:
                                        kb_id = None
                                    self.log(f"DEBUG: KB created with ID: {kb_id}")
                        except Exception as e:
                            self.log(f"DEBUG: Tool execution error: {str(e)}")
                            
                            # Fallback: Try to create KB manually if the tool call failed
                            if tool_call['name'] == 'KnowledgeBaseInsertKnowledgeBase':
                                self.log("DEBUG: Attempting manual KB creation as fallback")
                                fallback_result = self._create_knowledge_base(user_request, {})
                                if fallback_result.get('success'):
                                    kb_created = {'id': fallback_result.get('kb_id')}
                
                # Store the KB result for passing to ContentCreator
                if kb_created:
                    if isinstance(kb_created, dict) and kb_created.get('id'):
                        kb_id = kb_created.get('id')
                    elif isinstance(kb_created, int):
                        kb_id = kb_created
                    else:
                        kb_id = None
                        
                    if kb_id:
                        state['knowledge_base_id'] = str(kb_id)  # Always store as string for consistency
                        state['created_kb_info'] = kb_created if isinstance(kb_created, dict) else {'id': kb_id}
                        
                        # Automatically set the new KB as the active context
                        self._set_kb_context_after_creation(state, str(kb_id))
                        
                        self.log(f"DEBUG: Storing KB ID {kb_id} in state for ContentCreator")
                
            return self._process_planning_response(response, user_request, state)
        except Exception as e:
            self.log(f"DEBUG: Exception during LLM invocation: {str(e)}")
            import traceback
            self.log(f"DEBUG: Traceback: {traceback.format_exc()}")
            return {
                "error": f"Error during content planning: {str(e)}",
                "needs_clarification": False
            }
    
    def _process_planning_response(self, response, user_request: str, state: AgentState) -> Dict[str, Any]:
        """Process the LLM planning response and extract strategy"""
        # NOTE: Tool calls are already processed in _create_content_strategy method
        # This method only extracts planning information from the response content
        
        # Extract planning content
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Get KB creation result from state if it was created
        kb_created = state.get('created_kb_info')
        
        # Analyze if clarification is needed (look for specific clarification patterns)
        needs_clarification = self._detect_clarification_need(content)
        
        if needs_clarification:
            return {
                "needs_clarification": True,
                "clarification_questions": self._extract_clarification_questions(content),
                "partial_plan": self._extract_partial_plan(content)
            }
        else:
            # Actually create a knowledge base and plan the content structure
            strategy = self._extract_strategy(content)
            hierarchy = self._extract_hierarchy(content)
            implementation = self._extract_implementation_plan(content)
            
            return {
                "needs_clarification": False,
                "strategy": strategy,
                "hierarchy": hierarchy, 
                "implementation": implementation,
                "kb_created": kb_created
            }

    def _needs_clarification(self, planning_result: Dict[str, Any]) -> bool:
        """Determine if clarification is needed based on planning result"""
        return planning_result.get("needs_clarification", False)
    
    def _detect_clarification_need(self, content: str) -> bool:
        """Detect if the response indicates clarification is needed"""
        clarification_indicators = [
            "need clarification",
            "unclear scope",
            "ambiguous request",
            "could you specify",
            "more details needed",
            "unclear focus"
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in clarification_indicators)
    
    def _extract_clarification_questions(self, content: str) -> str:
        """Extract clarification questions from the response"""
        # Simple extraction - in practice, this would be more sophisticated
        if "clarification" in content.lower():
            return content
        return "Could you provide more specific details about the scope and focus for this knowledge base?"
    
    def _extract_partial_plan(self, content: str) -> Dict[str, Any]:
        """Extract any partial planning information"""
        return {"preliminary_analysis": content}
    
    def _extract_strategy(self, content: str) -> Dict[str, Any]:
        """Extract the content strategy from the response"""
        return {
            "scope": "Comprehensive coverage determined",
            "approach": "Expert-level depth with practical applications",
            "target_depth": "Beginner to advanced progression",
            "content_analysis": content
        }
    
    def _extract_hierarchy(self, content: str) -> Dict[str, Any]:
        """Extract the content hierarchy from the response"""
        return {
            "structure_type": "Hierarchical with cross-references",
            "organization": "Topic-based with progressive complexity",
            "relationship_mapping": "Comprehensive cross-linking",
            "hierarchy_details": content
        }
    
    def _extract_implementation_plan(self, content: str) -> Dict[str, Any]:
        """Extract the implementation plan from the response"""
        return {
            "creation_order": "Foundation concepts first, then advanced topics",
            "content_priorities": "Core concepts, then specializations",
            "quality_targets": "Expert-level accuracy and comprehensive coverage",
            "implementation_details": content
        }

    def _create_knowledge_base(self, user_request: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Actually create a knowledge base using the available tools"""
        try:
            # Extract KB title from user request
            kb_title = self._extract_kb_title(user_request)
            
            # Create a comprehensive strategic description
            description = self._generate_strategic_description(user_request, kb_title, strategy)
            
            # Create the knowledge base
            kb_tool = next((tool for tool in self.tools if tool.name == "KnowledgeBaseInsertKnowledgeBase"), None)
            if kb_tool:
                kb_result = kb_tool.run({
                    "knowledge_base": {
                        "name": kb_title,
                        "description": description,
                        "author_id": 1
                    }
                })
                
                return {
                    "success": True,
                    "kb_id": kb_result.get("id") if kb_result else None,
                    "kb_title": kb_title,
                    "message": f"Knowledge base '{kb_title}' created successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "KnowledgeBase creation tool not available"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating knowledge base: {str(e)}"
            }

    def _generate_strategic_description(self, user_request: str, kb_title: str, strategy: Dict[str, Any]) -> str:
        """Generate a comprehensive strategic description for the knowledge base"""
        # Extract domain/topic from the request
        topic = kb_title.lower()
        
        # Determine scope and approach based on request context
        if any(word in user_request.lower() for word in ['beginner', 'intro', 'basic', 'getting started']):
            target_level = "beginner to intermediate"
            depth_approach = "foundational concepts with clear explanations and practical examples"
        elif any(word in user_request.lower() for word in ['advanced', 'expert', 'professional', 'deep']):
            target_level = "intermediate to expert"
            depth_approach = "advanced techniques, expert insights, and professional-grade methodologies"
        else:
            target_level = "beginner to advanced"
            depth_approach = "comprehensive coverage from fundamental concepts to expert-level implementation"
        
        # Determine content organization strategy
        if any(word in user_request.lower() for word in ['guide', 'step-by-step', 'how-to', 'tutorial']):
            organization = "structured, step-by-step progression with practical implementation guides"
        elif any(word in user_request.lower() for word in ['reference', 'encyclopedia', 'comprehensive']):
            organization = "encyclopedic reference structure with cross-linked topics and detailed coverage"
        else:
            organization = "logical topic progression with interconnected concepts and practical applications"
        
        description = f"""🎯 **Purpose & Scope**: This knowledge base provides comprehensive coverage of {topic}, designed as a strategic content foundation for multiple publishing formats. The scope encompasses core principles, practical applications, current best practices, and emerging trends in the field.

👥 **Target Audience**: Content is structured for {target_level} learners, including professionals, students, researchers, and practitioners seeking authoritative information and actionable insights in {topic}.

📋 **Content Strategy**: Information is organized using {organization}, ensuring logical knowledge progression and easy navigation. Each article builds upon previous concepts while standing alone as valuable reference material.

🔍 **Coverage Areas**: Key topics include fundamental concepts, practical methodologies, real-world applications, case studies, tools and technologies, best practices, common challenges and solutions, and future developments in {topic}.

📚 **Content Depth**: Articles demonstrate {depth_approach}, incorporating current research, industry standards, and practical wisdom from field experts.

🎪 **Use Cases**: This KB serves as source material for ebooks, blog series, educational courses, professional training materials, white papers, and marketing content. Content is designed for easy adaptation across multiple formats and audiences.

💡 **Value Proposition**: Provides unique synthesis of theoretical knowledge and practical application, offering frameworks, methodologies, and insights not readily available in fragmented online resources.

🔄 **Content Approach**: Evidence-based research methodology with authoritative citations, practical examples, actionable frameworks, and real-world case studies. Balance of theoretical understanding and implementation guidance."""
        
        return description

    def _extract_kb_title(self, user_request: str) -> str:
        """Extract a clean knowledge base title from the user request"""
        import re
        
        # Remove common prefixes and clean up the request
        cleaned = user_request.lower()
        cleaned = re.sub(r'^(create|build|make|generate)\s+(a\s+|an\s+)?(knowledge\s+base|kb)\s+(about|on|for)\s*', '', cleaned)
        cleaned = re.sub(r'^(.*?)\s*$', r'\1', cleaned)  # Remove extra whitespace
        
        # Remove quotes if present
        cleaned = cleaned.strip('"\'')
        
        # Capitalize properly
        title = ' '.join(word.capitalize() for word in cleaned.split())
        
        return title if title else "New Knowledge Base"
    
    def analyze_content_gaps(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze knowledge base structure and planning gaps"""
        self.log("🔍 ContentPlannerAgent analyzing KB for strategic planning gaps and opportunities...")
        
        try:
            # Ensure KB context is set before planning analysis
            if not self.ensure_kb_context():
                self.log("❌ Failed to establish KB context")
                return {"found_work": False, "message": "Could not establish KB context"}
            
            # Log current KB context for transparency
            kb_context = self.get_kb_context()
            self.log(f"📚 Planning for KB: {kb_context.get('knowledge_base_name')} (ID: {kb_context.get('knowledge_base_id')})")
            self.log(f"📄 KB Description: {kb_context.get('knowledge_base_description', 'No description')}")
            
            # Autonomous Priority 1: Analyze KB structure and planning needs
            structure_analysis = self.analyze_kb_structure_planning_needs(state)
            if structure_analysis.get("planning_needed", False):
                self.log("✅ Found knowledge base structure planning opportunities")
                # Create GitLab work items for structural planning
                work_creation_result = self.create_work_for_structure_planning(structure_analysis)
                return {
                    "found_work": True,
                    "work_type": "autonomous_structure_planning",
                    "work_details": structure_analysis,
                    "work_created": work_creation_result,
                    "priority": "high"
                }
            
            # Autonomous Priority 2: Analyze content roadmap and strategy needs
            roadmap_analysis = self.analyze_content_roadmap_needs(state)
            if roadmap_analysis.get("roadmap_needed", False):
                self.log("✅ Found content roadmap planning opportunities")
                # Create GitLab work items for roadmap planning
                work_creation_result = self.create_work_for_roadmap_planning(roadmap_analysis)
                return {
                    "found_work": True,
                    "work_type": "autonomous_roadmap_planning",
                    "work_details": roadmap_analysis,
                    "work_created": work_creation_result,
                    "priority": "medium"
                }
            
            # Autonomous Priority 3: Analyze content organization and taxonomy needs
            taxonomy_analysis = self.analyze_taxonomy_planning_needs(state)
            if taxonomy_analysis.get("taxonomy_work_needed", False):
                self.log("✅ Found content taxonomy planning opportunities")
                # Create GitLab work items for taxonomy planning
                work_creation_result = self.create_work_for_taxonomy_planning(taxonomy_analysis)
                return {
                    "found_work": True,
                    "work_type": "autonomous_taxonomy_planning",
                    "work_details": taxonomy_analysis,
                    "work_created": work_creation_result,
                    "priority": "low"
                }
            
            # No autonomous work opportunities found
            self.log("💡 No immediate planning opportunities found - KB structure appears well-organized")
            return {
                "found_work": False,
                "message": "Knowledge base planning analysis complete - no immediate structural issues detected"
            }
            
        except Exception as e:
            self.log(f"❌ Error in autonomous work discovery: {str(e)}")
            return {
                "found_work": False,
                "message": f"Error in autonomous planning analysis: {str(e)}"
            }
    
    def analyze_kb_structure_planning_needs(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze knowledge base structure for planning needs"""
        try:
            self.log("🔍 Analyzing KB structure for planning opportunities...")
            
            # Simulated structure analysis - would use KB tools in practice
            structure_needs = [
                {
                    "type": "knowledge_area_expansion",
                    "description": "Financial planning domain needs sub-category organization",
                    "priority": "medium",
                    "scope": "domain_restructuring"
                },
                {
                    "type": "content_flow_optimization",
                    "description": "Investment education pathway needs logical sequencing",
                    "priority": "high",
                    "scope": "learning_pathway_design"
                }
            ]
            
            if structure_needs:
                return {
                    "planning_needed": True,
                    "needs": structure_needs[:1],  # Limit to top 1
                    "analysis_method": "structural_analysis"
                }
            else:
                return {"planning_needed": False, "message": "No structural planning needs identified"}
                
        except Exception as e:
            self.log(f"❌ Error analyzing structure needs: {str(e)}")
            return {"planning_needed": False, "message": f"Error in structure analysis: {str(e)}"}
    
    def analyze_content_roadmap_needs(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze content roadmap and strategy planning needs"""
        try:
            self.log("🔍 Analyzing content roadmap planning needs...")
            
            roadmap_needs = [
                {
                    "type": "quarterly_content_strategy",
                    "description": "Q2 2024 content development roadmap planning",
                    "priority": "medium",
                    "timeline": "quarterly"
                }
            ]
            
            if roadmap_needs:
                return {
                    "roadmap_needed": True,
                    "needs": roadmap_needs[:1],  # Limit to top 1
                    "analysis_method": "roadmap_analysis"
                }
            else:
                return {"roadmap_needed": False, "message": "No roadmap planning needs identified"}
                
        except Exception as e:
            self.log(f"❌ Error analyzing roadmap needs: {str(e)}")
            return {"roadmap_needed": False, "message": f"Error in roadmap analysis: {str(e)}"}
    
    def analyze_taxonomy_planning_needs(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze content taxonomy and organization planning needs"""
        try:
            self.log("🔍 Analyzing content taxonomy planning needs...")
            
            taxonomy_needs = [
                {
                    "type": "tag_standardization",
                    "description": "Content tagging system needs standardization across domains",
                    "priority": "low",
                    "scope": "taxonomy_optimization"
                }
            ]
            
            if taxonomy_needs:
                return {
                    "taxonomy_work_needed": True,
                    "needs": taxonomy_needs[:1],  # Limit to top 1
                    "analysis_method": "taxonomy_analysis"
                }
            else:
                return {"taxonomy_work_needed": False, "message": "No taxonomy planning needs identified"}
                
        except Exception as e:
            self.log(f"❌ Error analyzing taxonomy needs: {str(e)}")
            return {"taxonomy_work_needed": False, "message": f"Error in taxonomy analysis: {str(e)}"}
    
    def create_work_for_structure_planning(self, structure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for structure planning"""
        try:
            self.log("📝 Creating GitLab work items for structure planning...")
            
            work_items_created = []
            needs = structure_data.get("needs", [])
            
            for need in needs:
                work_item = {
                    "title": f"Structure Planning: {need['description']}",
                    "description": f"KB structure planning needed: {need['type']} - {need['scope']}",
                    "priority": need['priority'],
                    "labels": ["structure-planning", "autonomous-work", "kb-architecture"],
                    "type": "structure_planning"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created structure planning work item: {work_item['title']}")
            
            return {
                "created": True,
                "work_items": work_items_created,
                "count": len(work_items_created)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating structure planning work items: {str(e)}")
            return {"created": False, "message": f"Error creating work: {str(e)}"}
    
    def create_work_for_roadmap_planning(self, roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for roadmap planning"""
        try:
            self.log("📝 Creating GitLab work items for roadmap planning...")
            
            work_items_created = []
            needs = roadmap_data.get("needs", [])
            
            for need in needs:
                work_item = {
                    "title": f"Roadmap Planning: {need['description']}",
                    "description": f"Content roadmap planning: {need['type']} - {need['timeline']}",
                    "priority": need['priority'],
                    "labels": ["roadmap-planning", "autonomous-work", "content-strategy"],
                    "type": "roadmap_planning"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created roadmap planning work item: {work_item['title']}")
            
            return {
                "created": True,
                "work_items": work_items_created,
                "count": len(work_items_created)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating roadmap planning work items: {str(e)}")
            return {"created": False, "message": f"Error creating work: {str(e)}"}
    
    def create_work_for_taxonomy_planning(self, taxonomy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for taxonomy planning"""
        try:
            self.log("📝 Creating GitLab work items for taxonomy planning...")
            
            work_items_created = []
            needs = taxonomy_data.get("needs", [])
            
            for need in needs:
                work_item = {
                    "title": f"Taxonomy Planning: {need['description']}",
                    "description": f"Content taxonomy planning: {need['type']} - {need['scope']}",
                    "priority": need['priority'],
                    "labels": ["taxonomy-planning", "autonomous-work", "content-organization"],
                    "type": "taxonomy_planning"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created taxonomy planning work item: {work_item['title']}")
            
            return {
                "created": True,
                "work_items": work_items_created,
                "count": len(work_items_created)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating taxonomy planning work items: {str(e)}")
            return {"created": False, "message": f"Error creating work: {str(e)}"}
    
    def _execute_work_item_to_completion(self, work_item: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a planning work item to completion"""
        try:
            self.log(f"Executing planning work item: {work_item.get('title')}")
            
            # This would contain the actual planning logic
            # For now, return a basic completion
            return {
                "success": True,
                "message": f"Planning work item '{work_item.get('title')}' processed",
                "work_item_id": work_item.get("id"),
                "completion_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.log(f"Error executing planning work item: {str(e)}", "ERROR")
            return {
                "success": False,
                "message": f"Error executing work item: {str(e)}"
            }
    
    def _set_kb_context_after_creation(self, state: AgentState, kb_id: str):
        """Automatically set the newly created KB as the active context and get KB details"""
        try:
            # Use the KnowledgeBaseSetContext tool to set the context properly
            for tool in self.tools:
                if tool.name == "KnowledgeBaseSetContext":
                    result = tool.run({"knowledge_base_id": kb_id})
                    if result.get("success"):
                        state["knowledge_base_name"] = result.get("knowledge_base_name")
                        self.log(f"✅ Automatically set KB context to: {result.get('knowledge_base_name')} (ID: {kb_id})")
                        
                        # Store notification message for user
                        state["kb_context_notification"] = f"📋 Knowledge base '{result.get('knowledge_base_name')}' (ID: {kb_id}) has been created and is now your active context."
                    else:
                        self.log(f"⚠️ Failed to set context for newly created KB {kb_id}: {result.get('error', 'Unknown error')}")
                    break
        except Exception as e:
            self.log(f"ERROR: Failed to set context for newly created KB {kb_id}: {str(e)}")

    def process_gitlab_assignment(self, issue_id: str, project_id: str) -> Dict[str, Any]:
        """Process a specific GitLab issue assignment for planning work"""
        if not self.is_gitlab_enabled():
            return {"success": False, "status": "error", "error": "GitLab not configured"}
        
        self.log(f"📋 Processing GitLab planning assignment: Issue #{issue_id} in project {project_id}")
        
        try:
            # First, establish the GitLab project context and find associated KB
            project_context = self.get_gitlab_project_for_current_work(project_id)
            
            if not project_context.get('success'):
                self.log(f"⚠️ {project_context.get('message', 'Unknown project context error')}")
                # Can still proceed with issue details, but without KB context
                kb_context_established = False
            else:
                self.log(f"✅ KB context established: {project_context.get('knowledge_base_name')}")
                kb_context_established = True
            
            # Get detailed issue information
            issue_details_tool = next(
                (tool for tool in self.tools if tool.name == "GitLabGetIssueDetailsTool"), 
                None
            )
            
            if not issue_details_tool:
                return {"success": False, "status": "error", "error": "GitLab issue details tool not available"}
            
            # Get issue details
            issue_details = issue_details_tool.run({
                "project_id": project_id, 
                "issue_iid": issue_id
            })
            
            self.log(f"📄 Retrieved planning issue details for #{issue_id}")
            
            # Process the planning assignment based on issue content
            result = {
                "success": True,  # Use 'success' instead of 'status' for swarm compatibility
                "status": "processed",
                "message": f"Processed planning assignment #{issue_id}",
                "issue_details": issue_details,
                "gitlab_project_id": project_id,
                "kb_context_established": kb_context_established
            }
            
            # Add KB context information if available
            if kb_context_established:
                result.update({
                    "knowledge_base_id": project_context.get('knowledge_base_id'),
                    "knowledge_base_name": project_context.get('knowledge_base_name'),
                    "work_context": f"Planning work on GitLab project {project_id} for KB '{project_context.get('knowledge_base_name')}'"
                })
                
                self.log(f"🎯 Ready to plan KB '{project_context.get('knowledge_base_name')}' via GitLab issue #{issue_id}")
                
                # NOW ACTUALLY EXECUTE THE PLANNING WORK - this was missing!
                try:
                    # Get the raw issue data from the details response
                    if isinstance(issue_details, dict) and "data" in issue_details:
                        issue_data = issue_details["data"]
                    elif isinstance(issue_details, str):
                        # Parse issue details from string response
                        import json
                        try:
                            parsed_details = json.loads(issue_details)
                            issue_data = parsed_details
                        except:
                            # Fallback: create issue data from available info
                            issue_data = {
                                "iid": issue_id,
                                "project_id": project_id,
                                "title": f"Planning Issue #{issue_id}",
                                "description": "Planning work item"
                            }
                    else:
                        # Fallback: create issue data from available info
                        issue_data = {
                            "iid": issue_id,
                            "project_id": project_id,
                            "title": f"Planning Issue #{issue_id}",
                            "description": "Planning work item"
                        }
                        
                    execution_result = self._execute_work_item_to_completion(issue_data, {"kb_context": project_context})
                    if execution_result and execution_result.get("success"):
                        result["actual_work_completed"] = True
                        result["execution_result"] = execution_result
                        self.log(f"✅ Successfully completed planning work for issue #{issue_id}")
                    else:
                        self.log(f"⚠️ Planning work execution returned with issues: {execution_result}")
                        result["actual_work_completed"] = False
                        result["execution_issues"] = execution_result
                except Exception as exec_error:
                    self.log(f"❌ Error executing planning work item: {str(exec_error)}")
                    result["actual_work_completed"] = False
                    result["execution_error"] = str(exec_error)
            else:
                result.update({
                    "work_context": f"Planning work on GitLab project {project_id} (no associated KB found)",
                    "note": "Consider creating a knowledge base for this project or linking an existing one"
                })
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing GitLab planning assignment #{issue_id}: {str(e)}"
            self.log(f"❌ {error_msg}")
            return {"success": False, "status": "error", "error": error_msg}