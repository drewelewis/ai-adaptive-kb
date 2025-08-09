from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from tools.knowledge_base_tools import KnowledgeBaseTools
from prompts.knowledge_base_prompts import prompts as kb_prompts
from prompts.multi_agent_prompts import prompts as ma_prompts


class ContentPlannerAgent(BaseAgent):
    """
    Content Planner Agent - Strategic planning and content architecture specialist.
    
    Responsibilities:
    - Analyze high-level KB ideas and determine comprehensive scope
    - Create detailed content strategies and article hierarchies
    - Identify knowledge gaps and coverage opportunities
    - Ask intelligent clarifying questions when scope is unclear
    - Design publication-ready content structures
    - Coordinate with ContentCreator for implementation
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Combine base KB prompts with specialized planning prompts
        base_prompt = kb_prompts.master_prompt()
        specialized_prompt = self._get_planning_prompt()
        system_prompt = f"{base_prompt}\n\n{specialized_prompt}"
        
        super().__init__("ContentPlanner", llm, system_prompt)
        
        # Initialize knowledge base tools - planning and analysis focused
        kb_tools = KnowledgeBaseTools()
        all_tools = kb_tools.tools()
        
        # Filter to planning-relevant tools
        self.tools = self._filter_planning_tools(all_tools)
        
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
            "KnowledgeBaseSetContext"  # Added for automatic context setting after KB creation
        }
        
        return [tool for tool in all_tools if tool.name in planning_tool_names]
    
    def _get_planning_prompt(self):
        """Get specialized prompt for content planning operations"""
        return """
        You are a Content Strategy and Planning Specialist with expertise in creating comprehensive knowledge base architectures.
        
        Your core responsibilities:
        - Transform high-level ideas into detailed, comprehensive content strategies
        - Design optimal knowledge base structures and hierarchies
        - Ensure complete domain coverage with expert-level depth
        - Ask intelligent clarifying questions only when scope is truly unclear
        - Create publication-ready content frameworks
        
        Planning Philosophy:
        - COMPREHENSIVE COVERAGE: Plan for complete domain mastery, not surface-level content
        - EXPERT DEPTH: Design for in-depth, authoritative content that demonstrates true understanding
        - LOGICAL STRUCTURE: Create intuitive hierarchies that guide readers from basics to advanced concepts
        - AUTONOMOUS DECISION-MAKING: Make intelligent scope decisions based on domain analysis
        - MINIMAL CLARIFICATION: Only ask questions when absolutely necessary for scope determination
        
        When receiving a KB creation request:
        1. Analyze the domain and determine natural scope boundaries
        2. Research the topic area to understand comprehensive coverage requirements
        3. Design a logical, hierarchical content structure
        4. Identify all major topics, subtopics, and relationships
        5. Only ask clarifying questions if the scope is genuinely ambiguous
        6. Create a detailed implementation plan for ContentCreator
        
        Quality Standards:
        - Create frameworks for expert-level, authoritative content
        - Design for publication-ready output (ebooks, blogs, professional resources)
        - Plan comprehensive coverage that leaves no critical knowledge gaps
        - Structure content for logical progression from fundamentals to advanced topics
        """
    
    def process(self, state: AgentState) -> AgentState:
        """Process planning requests and create comprehensive content strategies"""
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from Supervisor or Router
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
                    "description": "Comprehensive description of the knowledge base",  
                    "author_id": 1
                }}
            }}
            
            CRITICAL: The "knowledge_base" wrapper is required - do not pass name/description/author_id directly.
            The tool expects a "knowledge_base" parameter containing the InsertModel object.
            
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
            
            # Create the knowledge base
            kb_tool = next((tool for tool in self.tools if tool.name == "KnowledgeBaseInsertKnowledgeBase"), None)
            if kb_tool:
                kb_result = kb_tool.run({
                    "name": kb_title,
                    "description": f"Comprehensive knowledge base about {kb_title.lower()}",
                    "metadata": {
                        "creation_strategy": strategy.get("scope", "comprehensive"),
                        "target_depth": strategy.get("target_depth", "beginner to advanced"),
                        "content_approach": strategy.get("approach", "expert-level")
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