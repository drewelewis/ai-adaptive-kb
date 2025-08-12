from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from prompts.multi_agent_prompts import prompts


class UserProxyAgent(BaseAgent):
    """
    User Proxy Agent - Facilitates collaborative knowledge base design and creation.
    
    PRIMARY RESPONSIBILITIES:
    - Collaborate with users to design and define knowledge bases
    - Work directly with ContentManagement, ContentPlanner, and Supervisor agents
    - Develop detailed KB titles and descriptions that drive autonomous agent work
    - Guide users through KB creation, design, and implementation decisions
    - Facilitate iterative design refinement based on agent feedback
    
    COLLABORATIVE WORKFLOW:
    User ↔ UserProxy ↔ ContentPlanner (strategic planning)
                   ↔ ContentManagement (technical feasibility)  
                   ↔ Supervisor (coordination & validation)
                   ↓
    Detailed KB Design → Autonomous Agent Work Begins
    
    KEY CAPABILITIES:
    - Interactive KB design sessions with users
    - Multi-agent collaboration for comprehensive KB planning
    - Title and description development that guides all subsequent work
    - Design validation and iterative refinement
    - Seamless transition from design to autonomous implementation
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        system_prompt = prompts.user_proxy_prompt()
        super().__init__("UserProxy", llm, system_prompt)

    def process(self, state: AgentState) -> AgentState:
        """Process collaborative KB design and user interactions"""
        self.log("Processing collaborative KB design workflow")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Safety check for infinite loops
        recursions = state.get("recursions", 0)
        if recursions > 12:  # Increased limit for collaborative workflows
            self.log(f"Maximum recursions ({recursions}) reached, stopping workflow")
            state["current_agent"] = None
            error_message = AIMessage(content="I apologize, but our design session has become too complex. Let's start fresh with a clearer focus on your knowledge base goals.")
            state["messages"].append(error_message)
            return state
        
        messages = state.get("messages", [])
        if not messages:
            return state
            
        last_message = messages[-1]
        
        # Check for agent collaboration messages
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        # Check for collaborative design session state
        design_session = state.get("kb_design_session", {})
        session_active = design_session.get("active", False)
        
        # Process agent collaboration messages first
        if my_messages:
            latest_message = my_messages[-1]
            
            if latest_message.message_type == "design_collaboration":
                return self._handle_design_collaboration(latest_message, state)
            elif latest_message.message_type == "design_validation":
                return self._handle_design_validation(latest_message, state)
            elif latest_message.message_type == "design_complete":
                return self._handle_design_completion(latest_message, state)
            elif latest_message.message_type == "autonomous_work_ready":
                return self._handle_autonomous_work_initiation(latest_message, state)
            
        # Check if user is initiating KB design/creation
        if (hasattr(last_message, '__class__') and 
            last_message.__class__.__name__ == 'HumanMessage'):
            
            user_content = last_message.content.lower()
            
            # Detect KB design/creation intents
            kb_design_keywords = [
                "create kb", "new knowledge base", "design kb", "build knowledge base",
                "create knowledge base", "new kb", "design knowledge base", "plan kb",
                "knowledge base about", "kb for", "help me create", "help me design"
            ]
            
            is_kb_design_request = any(keyword in user_content for keyword in kb_design_keywords)
            
            if is_kb_design_request or session_active:
                return self._handle_kb_design_workflow(last_message, state)
            else:
                # Handle other user requests through existing workflow
                return self._handle_general_user_request(last_message, state)
        
        return state
    
    # =============================================
    # COLLABORATIVE KB DESIGN METHODS
    # =============================================
    
    def _handle_kb_design_workflow(self, user_message: BaseMessage, state: AgentState) -> AgentState:
        """Handle collaborative KB design workflow with user and agents"""
        self.log("Initiating collaborative KB design workflow")
        
        user_content = user_message.content
        design_session = state.get("kb_design_session", {})
        
        if not design_session.get("active", False):
            # Start new design session
            return self._start_design_session(user_content, state)
        else:
            # Continue existing design session
            return self._continue_design_session(user_content, design_session, state)
    
    def _handle_general_user_request(self, user_message: BaseMessage, state: AgentState) -> AgentState:
        """Handle general user requests through existing workflow (Router)"""
        self.log("Handling general user request through Router")
        
        user_message_content = user_message.content if hasattr(user_message, 'content') else str(user_message)
        
        # Send request to Router for intent classification and routing
        router_message = self.create_message(
            recipient="Router",
            message_type="routing_request",
            content=f"User request: {user_message_content}",
            metadata={"original_message": str(user_message)}
        )
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(router_message)
        
        # Set router as next agent
        state["current_agent"] = "Router"
        
        self.log("Sent user request to Router for classification and routing")
        return state
    
    def _start_design_session(self, user_content: str, state: AgentState) -> AgentState:
        """Start a new collaborative KB design session"""
        self.log("Starting new KB design session")
        
        # Initialize design session state
        design_session = {
            "active": True,
            "phase": "discovery",  # discovery -> planning -> validation -> completion
            "user_requirements": user_content,
            "design_elements": {
                "domain": None,
                "purpose": None,
                "target_audience": None,
                "scope": None,
                "structure_preferences": None
            },
            "collaborative_feedback": [],
            "iterations": 0
        }
        
        state["kb_design_session"] = design_session
        
        # Engage user in discovery conversation
        discovery_questions = self._generate_discovery_questions(user_content)
        
        response_content = f"""🎯 **Let's Design Your Knowledge Base Together!**

I'm excited to help you create a comprehensive knowledge base! To ensure we build exactly what you need, I'll work with you and our specialist agents to develop the perfect design.

**Initial Requirements Captured:**
{user_content}

**Let's start with some key questions to shape your KB:**

{discovery_questions}

**Our Collaborative Process:**
1. **Discovery** (current): Understanding your needs and vision
2. **Planning**: Working with ContentPlanner for strategic design
3. **Validation**: Technical review with ContentManagement 
4. **Implementation**: Supervisor coordinates autonomous agent work

Please answer the questions above, and feel free to share any additional thoughts about your knowledge base vision!
"""
        
        ai_message = AIMessage(content=response_content)
        state["messages"].append(ai_message)
        state["current_agent"] = None  # Wait for user response
        
        return state
    
    def _continue_design_session(self, user_content: str, design_session: Dict[str, Any], state: AgentState) -> AgentState:
        """Continue an active design session"""
        phase = design_session["phase"]
        
        if phase == "discovery":
            return self._handle_discovery_phase(user_content, design_session, state)
        elif phase == "planning":
            return self._handle_planning_phase(user_content, design_session, state)
        elif phase == "validation":
            return self._handle_validation_phase(user_content, design_session, state)
        elif phase == "completion":
            return self._handle_completion_phase(user_content, design_session, state)
        else:
            # Unknown phase, reset to discovery
            design_session["phase"] = "discovery"
            return self._continue_design_session(user_content, design_session, state)
    
    def _handle_discovery_phase(self, user_content: str, design_session: Dict[str, Any], state: AgentState) -> AgentState:
        """Handle the discovery phase of KB design"""
        self.log("Processing discovery phase input")
        
        # Update design elements with user input
        design_elements = design_session["design_elements"]
        design_elements = self._extract_design_elements(user_content, design_elements)
        design_session["design_elements"] = design_elements
        
        # Check if we have enough information to move to planning
        readiness_score = self._assess_design_readiness(design_elements)
        
        if readiness_score >= 0.7:  # 70% complete
            # Move to planning phase with ContentPlanner
            design_session["phase"] = "planning"
            return self._initiate_planning_collaboration(design_session, state)
        else:
            # Continue discovery with follow-up questions
            follow_up_questions = self._generate_follow_up_questions(design_elements, user_content)
            
            response_content = f"""📝 **Great insights! Let me capture what you've shared:**

{self._summarize_design_elements(design_elements)}

**To complete our discovery, I'd like to explore a bit more:**

{follow_up_questions}

**Progress:** {int(readiness_score * 100)}% ready for strategic planning phase.
"""
            
            ai_message = AIMessage(content=response_content)
            state["messages"].append(ai_message)
            state["current_agent"] = None
            
            return state
    
    def _initiate_planning_collaboration(self, design_session: Dict[str, Any], state: AgentState) -> AgentState:
        """Initiate collaboration with ContentPlanner for strategic design"""
        self.log("Initiating planning collaboration with ContentPlanner")
        
        design_elements = design_session["design_elements"]
        
        # Create planning request for ContentPlanner
        planning_request = self.create_message(
            recipient="ContentPlanner",
            message_type="strategic_design_request",
            content=f"Collaborative KB design planning needed for: {design_elements.get('domain', 'New Knowledge Base')}",
            metadata={
                "design_session": design_session,
                "design_elements": design_elements,
                "user_requirements": design_session["user_requirements"],
                "collaboration_type": "kb_design",
                "phase": "strategic_planning"
            }
        )
        
        state["agent_messages"].append(planning_request)
        state["current_agent"] = "ContentPlanner"
        
        # Update user about the collaboration
        response_content = f"""🎯 **Moving to Strategic Planning Phase!**

Excellent! I have enough information to begin strategic planning. I'm now collaborating with our ContentPlanner specialist to develop a comprehensive structural design for your knowledge base.

**Design Summary So Far:**
{self._summarize_design_elements(design_elements)}

**ContentPlanner is now analyzing:**
- Optimal content organization strategies
- Taxonomic structure recommendations  
- Content categorization approaches
- Strategic content planning roadmap

You'll see the strategic recommendations shortly, and we can refine them together before moving to technical validation.
"""
        
        ai_message = AIMessage(content=response_content)
        state["messages"].append(ai_message)
        
        return state
    
    # =============================================
    # AGENT COLLABORATION HANDLERS
    # =============================================
    
    def _handle_design_collaboration(self, message: AgentMessage, state: AgentState) -> AgentState:
        """Handle design collaboration messages from ContentPlanner"""
        self.log("Processing design collaboration from ContentPlanner")
        
        metadata = message.metadata
        strategic_plan = metadata.get("strategic_plan", {})
        design_session = state.get("kb_design_session", {})
        
        # Store strategic feedback
        design_session["strategic_plan"] = strategic_plan
        design_session["collaborative_feedback"].append({
            "agent": "ContentPlanner",
            "phase": "strategic_planning",
            "feedback": message.content,
            "recommendations": strategic_plan
        })
        
        # Present strategic plan to user for feedback
        response_content = f"""🎯 **Strategic Design Plan Complete!**

Our ContentPlanner has developed a comprehensive strategic plan for your knowledge base. Here's what they recommend:

**Strategic Analysis:**
{message.content}

**Recommended Structure:**
{self._format_strategic_plan(strategic_plan)}

**What do you think about this strategic approach?**
- Are there areas you'd like to modify or expand?
- Do the categories and organization make sense for your needs?
- Any additional topics or sections you'd like to include?

Your feedback will help us refine the design before moving to technical validation with ContentManagement.
"""
        
        ai_message = AIMessage(content=response_content)
        state["messages"].append(ai_message)
        state["current_agent"] = None  # Wait for user feedback
        
        return state
    
    def _handle_design_validation(self, message: AgentMessage, state: AgentState) -> AgentState:
        """Handle design validation messages from ContentManagement"""
        self.log("Processing design validation from ContentManagement")
        
        metadata = message.metadata
        technical_analysis = metadata.get("technical_analysis", {})
        design_session = state.get("kb_design_session", {})
        
        # Store technical feedback
        design_session["technical_analysis"] = technical_analysis
        design_session["collaborative_feedback"].append({
            "agent": "ContentManagement",
            "phase": "technical_validation",
            "feedback": message.content,
            "analysis": technical_analysis
        })
        
        # Present validation results to user
        response_content = f"""🔧 **Technical Validation Complete!**

Our ContentManagement specialist has reviewed the design for technical feasibility and implementation details:

**Technical Analysis:**
{message.content}

**Implementation Readiness:**
{self._format_technical_analysis(technical_analysis)}

The design is ready for implementation! Would you like to:
1. **Proceed with implementation** - Have the Supervisor coordinate the autonomous agents to build your KB
2. **Make final adjustments** - Refine any aspects of the design before implementation
3. **Review the complete design** - See a comprehensive summary of the final KB plan

What would you prefer?
"""
        
        ai_message = AIMessage(content=response_content)
        state["messages"].append(ai_message)
        state["current_agent"] = None
        
        return state
    
    def _handle_design_completion(self, message: AgentMessage, state: AgentState) -> AgentState:
        """Handle design completion and prepare for autonomous work"""
        self.log("Processing design completion")
        
        design_session = state.get("kb_design_session", {})
        
        # Mark design session as complete
        design_session["active"] = False
        design_session["phase"] = "completed"
        design_session["final_design"] = message.metadata.get("final_design", {})
        
        response_content = f"""✅ **Knowledge Base Design Complete!**

Excellent! Your knowledge base design is finalized and ready for implementation.

**Final Design Summary:**
{message.content}

**Next Steps:**
The Supervisor will now coordinate our autonomous agents to build your knowledge base:
- **ContentCreator** will generate comprehensive content
- **ContentReviewer** will ensure quality and consistency  
- **ContentPlanner** will maintain strategic organization
- **ContentManagement** will handle technical implementation

You'll receive updates as the work progresses, and I'll let you know when your knowledge base is ready!

**Implementation begins now...**
"""
        
        ai_message = AIMessage(content=response_content)
        state["messages"].append(ai_message)
        
        # Initiate autonomous work through Supervisor
        return self._initiate_autonomous_implementation(design_session, state)
    
    def _handle_autonomous_work_initiation(self, message: AgentMessage, state: AgentState) -> AgentState:
        """Handle autonomous work initiation confirmation"""
        self.log("Processing autonomous work initiation")
        
        response_content = f"""🚀 **Autonomous Implementation Started!**

{message.content}

Your knowledge base is being built by our autonomous agent team. I'll provide updates as major milestones are completed.

You can continue using the system normally while the implementation proceeds in the background.
"""
        
        ai_message = AIMessage(content=response_content)
        state["messages"].append(ai_message)
        state["current_agent"] = None
        
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
    
    # =============================================
    # DESIGN SESSION HELPER METHODS
    # =============================================
    
    def _generate_discovery_questions(self, user_content: str) -> str:
        """Generate targeted discovery questions based on initial user input"""
        
        # Analyze user content to customize questions
        content_lower = user_content.lower()
        
        base_questions = [
            "🎯 **What is the main subject/domain** of your knowledge base? (e.g., technology, finance, healthcare, education)",
            "👥 **Who will be using** this knowledge base? (e.g., team members, customers, students, general public)",
            "📋 **What specific topics or areas** should be covered?",
            "🎪 **What's the primary purpose**? (e.g., training, reference, documentation, customer support)"
        ]
        
        # Add contextual questions based on user input
        contextual_questions = []
        
        if any(word in content_lower for word in ["business", "company", "organization"]):
            contextual_questions.append("🏢 **What type of business/organizational content** should be included?")
        
        if any(word in content_lower for word in ["team", "internal", "employee"]):
            contextual_questions.append("👥 **What departments or roles** will be contributing to and using this content?")
        
        if any(word in content_lower for word in ["customer", "client", "external"]):
            contextual_questions.append("🌐 **What level of detail** should be provided for external users?")
        
        if any(word in content_lower for word in ["training", "education", "learning"]):
            contextual_questions.append("📚 **What skill levels or experience** should the content accommodate?")
        
        all_questions = base_questions + contextual_questions
        return "\n".join(all_questions)
    
    def _extract_design_elements(self, user_input: str, current_elements: Dict[str, Any]) -> Dict[str, Any]:
        """Extract design elements from user input using LLM analysis"""
        
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""Analyze this user input for knowledge base design elements:

User Input: "{user_input}"

Current Design Elements: {current_elements}

Extract and update the following design elements based on the user input:
- domain: The main subject area or field
- purpose: The primary goal or use case
- target_audience: Who will use this KB
- scope: What topics/areas to cover
- structure_preferences: Any organizational preferences mentioned

Return ONLY a JSON object with these fields. Set fields to null if not mentioned or unclear.

Example:
{{"domain": "Personal Finance", "purpose": "Educational reference", "target_audience": "General public", "scope": "Budgeting, investments, planning", "structure_preferences": "Beginner to advanced progression"}}""")
        ]
        
        try:
            response = self.llm.invoke(messages)
            import json
            
            # Extract JSON from response
            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            extracted_elements = json.loads(response_text)
            
            # Update current elements with non-null extracted values
            for key, value in extracted_elements.items():
                if value is not None and value.strip():
                    current_elements[key] = value
                    
        except Exception as e:
            self.log(f"Error extracting design elements: {str(e)}", "WARNING")
            # Fallback: simple keyword extraction
            user_lower = user_input.lower()
            
            # Simple keyword-based extraction as fallback
            if not current_elements.get("domain"):
                for domain_keyword in ["finance", "technology", "healthcare", "education", "business"]:
                    if domain_keyword in user_lower:
                        current_elements["domain"] = domain_keyword.title()
                        break
        
        return current_elements
    
    def _assess_design_readiness(self, design_elements: Dict[str, Any]) -> float:
        """Assess how ready the design is for planning phase (0.0 to 1.0)"""
        
        required_elements = ["domain", "purpose", "target_audience", "scope"]
        completed_count = sum(1 for key in required_elements if design_elements.get(key))
        
        base_score = completed_count / len(required_elements)
        
        # Bonus for structure preferences
        if design_elements.get("structure_preferences"):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _generate_follow_up_questions(self, design_elements: Dict[str, Any], recent_input: str) -> str:
        """Generate follow-up questions based on missing design elements"""
        
        questions = []
        
        if not design_elements.get("domain"):
            questions.append("🎯 **What is the main subject area** for your knowledge base?")
        
        if not design_elements.get("purpose"):
            questions.append("📋 **What is the primary purpose** - training, reference, support documentation, or something else?")
        
        if not design_elements.get("target_audience"):
            questions.append("👥 **Who will be the main users** of this knowledge base?")
        
        if not design_elements.get("scope"):
            questions.append("📚 **What specific topics or areas** should be covered in detail?")
        
        if not design_elements.get("structure_preferences"):
            questions.append("🏗️ **Do you have any preferences** for how the content should be organized? (e.g., by difficulty level, by topic, by user role)")
        
        return "\n".join(questions) if questions else "Just let me know if there's anything else you'd like to add or clarify about your vision!"
    
    def _summarize_design_elements(self, design_elements: Dict[str, Any]) -> str:
        """Create a user-friendly summary of current design elements"""
        
        summary_parts = []
        
        if design_elements.get("domain"):
            summary_parts.append(f"**Domain:** {design_elements['domain']}")
        
        if design_elements.get("purpose"):
            summary_parts.append(f"**Purpose:** {design_elements['purpose']}")
        
        if design_elements.get("target_audience"):
            summary_parts.append(f"**Target Audience:** {design_elements['target_audience']}")
        
        if design_elements.get("scope"):
            summary_parts.append(f"**Scope:** {design_elements['scope']}")
        
        if design_elements.get("structure_preferences"):
            summary_parts.append(f"**Organization:** {design_elements['structure_preferences']}")
        
        return "\n".join(summary_parts) if summary_parts else "Still gathering design requirements..."
    
    def _format_strategic_plan(self, strategic_plan: Dict[str, Any]) -> str:
        """Format strategic plan for user presentation"""
        
        if not strategic_plan:
            return "Strategic plan details are being finalized..."
        
        formatted_sections = []
        
        if strategic_plan.get("structure"):
            formatted_sections.append(f"**Recommended Structure:**\n{strategic_plan['structure']}")
        
        if strategic_plan.get("categories"):
            categories = strategic_plan["categories"]
            if isinstance(categories, list):
                category_list = "\n".join(f"• {cat}" for cat in categories)
                formatted_sections.append(f"**Main Categories:**\n{category_list}")
        
        if strategic_plan.get("organization_strategy"):
            formatted_sections.append(f"**Organization Strategy:**\n{strategic_plan['organization_strategy']}")
        
        return "\n\n".join(formatted_sections) if formatted_sections else str(strategic_plan)
    
    def _format_technical_analysis(self, technical_analysis: Dict[str, Any]) -> str:
        """Format technical analysis for user presentation"""
        
        if not technical_analysis:
            return "Technical analysis details are being finalized..."
        
        formatted_sections = []
        
        if technical_analysis.get("feasibility"):
            formatted_sections.append(f"**Feasibility:** {technical_analysis['feasibility']}")
        
        if technical_analysis.get("implementation_plan"):
            formatted_sections.append(f"**Implementation Plan:**\n{technical_analysis['implementation_plan']}")
        
        if technical_analysis.get("estimated_timeline"):
            formatted_sections.append(f"**Estimated Timeline:** {technical_analysis['estimated_timeline']}")
        
        if technical_analysis.get("recommendations"):
            recommendations = technical_analysis["recommendations"]
            if isinstance(recommendations, list):
                rec_list = "\n".join(f"• {rec}" for rec in recommendations)
                formatted_sections.append(f"**Recommendations:**\n{rec_list}")
        
        return "\n\n".join(formatted_sections) if formatted_sections else str(technical_analysis)
    
    def _initiate_autonomous_implementation(self, design_session: Dict[str, Any], state: AgentState) -> AgentState:
        """Initiate autonomous implementation through Supervisor"""
        self.log("Initiating autonomous implementation through Supervisor")
        
        final_design = design_session.get("final_design", {})
        
        # Create implementation request for Supervisor
        implementation_request = self.create_message(
            recipient="Supervisor",
            message_type="autonomous_implementation_request",
            content="Ready to begin autonomous KB implementation based on collaborative design",
            metadata={
                "design_session": design_session,
                "final_design": final_design,
                "implementation_type": "autonomous_kb_creation",
                "priority": "high",
                "requires_coordination": True
            }
        )
        
        state["agent_messages"].append(implementation_request)
        state["current_agent"] = "Supervisor"
        
        return state
