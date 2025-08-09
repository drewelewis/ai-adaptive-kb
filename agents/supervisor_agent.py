from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from prompts.multi_agent_prompts import prompts


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent - Reviews and validates work from other agents.
    This agent ensures quality control and provides oversight for operations.
    It does NOT handle routing decisions - that's the Router's job.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        system_prompt = self._create_supervisor_prompt()
        super().__init__("Supervisor", llm, system_prompt)
    
    def _create_supervisor_prompt(self) -> str:
        """Create the system prompt for the supervisor agent"""
        return """You are the Supervisor Agent for a multi-agent knowledge base system. Your primary responsibility is to review and validate work performed by other agents.

**Your Role:**
1. **Quality Assurance**: Review work completed by ContentManagement agent
2. **Validation**: Ensure operations meet quality standards and user requirements
3. **Error Detection**: Identify issues or problems in completed work
4. **Approval/Rejection**: Decide whether work should be accepted or requires revision
5. **Feedback**: Provide constructive feedback for improvements

**Review Criteria:**
- **Accuracy**: Is the work correct and error-free?
- **Completeness**: Does it fully address the user's request?
- **Quality**: Does it meet professional standards?
- **Consistency**: Is it consistent with existing content?
- **Usability**: Is it helpful and user-friendly?

**Decision Process:**
- **APPROVE**: Work meets all criteria - send to user
- **REVISE**: Work needs improvements - send back to ContentManagement with feedback
- **ESCALATE**: Complex issues requiring additional consideration

You should be thorough but efficient in your reviews, providing clear, actionable feedback."""

    def process(self, state: AgentState) -> AgentState:
        """Review and validate work from other agents"""
        self.log("Processing work review request")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from other agents
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            # No agent messages - this might be direct routing from Router
            self.log("No agent messages found - checking for direct routing from Router")
            return self._handle_direct_routing(state)
        
        # Get the latest message
        latest_message = my_messages[-1]
        
        if latest_message.message_type == "work_review":
            # Review work completed by ContentManagement
            self.log("Reviewing work from ContentManagement Agent")
            return self._review_work(state, latest_message)
        else:
            # Handle other types of supervision requests
            self.log(f"Processing supervision request: {latest_message.message_type}")
            return self._handle_supervision_request(state, latest_message)

    def _review_work(self, state: AgentState, work_message: AgentMessage) -> AgentState:
        """Review work completed by ContentManagement agent"""
        
        work_content = work_message.content
        metadata = work_message.metadata
        original_intent = metadata.get("intent", "unknown")
        
        # Perform comprehensive review using LLM
        review_prompt = f"""
Review this work completed by the ContentManagement agent:

**Original User Intent:** {original_intent}
**Work Completed:** {work_content}
**Metadata:** {metadata}

Evaluate the work based on:
1. Accuracy and correctness
2. Completeness relative to user request
3. Quality and professionalism
4. Consistency with knowledge base standards
5. User-friendliness and clarity

Provide your assessment:
- **Decision**: APPROVE, REVISE, or ESCALATE
- **Quality Score**: 1-10
- **Feedback**: Specific comments for improvement (if needed)
- **User Response**: How should this be presented to the user?
        """
        
        messages = [
            self.get_system_message(),
            HumanMessage(content=review_prompt)
        ]
        
        response = self.llm.invoke(messages)
        review_result = response.content
        
        # Parse review decision (simple keyword detection)
        if "APPROVE" in review_result.upper():
            decision = "approved"
        elif "REVISE" in review_result.upper():
            decision = "needs_revision"
        else:
            decision = "escalated"
        
        self.log(f"Work review decision: {decision}")
        
        if decision == "approved":
            # Send approved work to UserProxy for delivery to user
            user_message = self.create_message(
                recipient="UserProxy",
                message_type="workflow_complete",
                content=review_result,
                metadata={
                    "intent": original_intent,  # Make sure intent is passed for proper formatting
                    "review_status": "approved",
                    "original_work": work_content
                }
            )
            
            state["agent_messages"].append(user_message)
            state["current_agent"] = "UserProxy"
            
        elif decision == "needs_revision":
            # Send back to ContentManagement for revision
            revision_message = self.create_message(
                recipient="ContentManagement",
                message_type="revision_request",
                content=f"Work needs revision. Feedback: {review_result}",
                metadata={
                    "intent": original_intent,
                    "original_work": work_content,
                    "feedback": review_result
                }
            )
            
            state["agent_messages"].append(revision_message)
            state["current_agent"] = "ContentManagement"
            
        else:  # escalated
            # Handle escalation (for now, send to user with explanation)
            user_message = self.create_message(
                recipient="UserProxy",
                message_type="workflow_error",
                content=f"Work has been escalated for further review: {review_result}",
                metadata={
                    "intent": original_intent,  # Make sure intent is passed for proper formatting
                    "review_status": "escalated"
                }
            )
            
            state["agent_messages"].append(user_message)
            state["current_agent"] = "UserProxy"
        
        return state

    def _handle_supervision_request(self, state: AgentState, request_message: AgentMessage) -> AgentState:
        """Handle general supervision requests"""
        
        # Check if this is a workflow response from ContentManagement
        if request_message.message_type == "workflow_response":
            # This is a completed workflow - review it
            self.log("Received workflow response - reviewing work")
            return self._review_workflow_response(state, request_message)
        
        # For other requests, delegate to ContentManagement
        content_message = self.create_message(
            recipient="ContentManagement",
            message_type="supervised_work_request",
            content=request_message.content,
            metadata={
                **request_message.metadata,
                "requires_review": True,
                "supervisor_notes": "Work will be reviewed upon completion"
            }
        )
        
        state["agent_messages"].append(content_message)
        state["current_agent"] = "ContentManagement"
        
        self.log("Delegated work to ContentManagement with review requirement")
        
        return state
    
    def _handle_direct_routing(self, state: AgentState) -> AgentState:
        """Handle direct routing from Router agent"""
        
        # Get the user's intent and last message
        user_intent = state.get("user_intent", "unknown")
        messages = state.get("messages", [])
        
        if not messages:
            self.log("No messages to process in direct routing")
            return state
        
        last_message = messages[-1].content
        self.log(f"Handling direct routing for intent: {user_intent}")
        
        # Create a message for ContentManagement based on the user request
        content_message = self.create_message(
            recipient="ContentManagement",
            message_type="supervised_work_request",
            content=last_message,
            metadata={
                "intent": user_intent,
                "requires_review": True,
                "supervisor_notes": "Direct routing from Router - work will be reviewed upon completion",
                "original_request": last_message
            }
        )
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(content_message)
        state["current_agent"] = "ContentManagement"
        
        self.log("Delegated direct routing request to ContentManagement")
        
        return state

    def _review_workflow_response(self, state: AgentState, response_message: AgentMessage) -> AgentState:
        """Review workflow response from ContentManagement agent with actual supervision"""
        
        success = response_message.metadata.get("success", False)
        results = response_message.metadata.get("results", {})
        
        # Get the original intent - try multiple sources in order of preference
        original_intent = response_message.metadata.get("intent")  # First try response metadata
        if not original_intent or original_intent == "unknown":
            original_intent = state.get("user_intent", "unknown")  # Then try state
            if not original_intent or original_intent == "unknown":
                # Finally try results data
                if isinstance(results, dict):
                    original_intent = results.get("intent", "unknown")
        
        # PERFORM ACTUAL SUPERVISION - Don't just check success flag
        self.log(f"🔍 SUPERVISOR REVIEW: Analyzing work for intent '{original_intent}'")
        
        # Detailed review based on the type of work and results
        review_result = self._perform_detailed_review(
            original_intent, 
            response_message.content, 
            results, 
            success,
            state
        )
        
        if review_result["decision"] == "APPROVE":
            # Work meets standards - send to user
            self.log(f"✅ SUPERVISOR APPROVAL: Work approved with score {review_result['score']}/10")
            
            user_response = self.create_message(
                recipient="UserProxy",
                message_type="workflow_complete",
                content=review_result["user_message"],
                metadata={
                    "intent": original_intent,
                    "results": results,
                    "success": True,
                    "reviewed_by": "Supervisor",
                    "quality_score": review_result["score"],
                    "supervisor_feedback": review_result["feedback"]
                }
            )
            
            state["agent_messages"].append(user_response)
            state["current_agent"] = "UserProxy"
            
        elif review_result["decision"] == "REVISE":
            # Work needs improvement - send back for revision
            self.log(f"🔄 SUPERVISOR REVISION: Work needs improvement - score {review_result['score']}/10")
            
            revision_message = self.create_message(
                recipient="ContentManagement",
                message_type="revision_request",
                content=f"Work requires revision. Supervisor feedback: {review_result['feedback']}",
                metadata={
                    "intent": original_intent,
                    "original_work": response_message.content,
                    "supervisor_feedback": review_result["feedback"],
                    "quality_issues": review_result["issues"],
                    "revision_count": results.get("revision_count", 0) + 1
                }
            )
            
            state["agent_messages"].append(revision_message)
            state["current_agent"] = "ContentManagement"
            
        else:  # ESCALATE
            # Critical issues - inform user with detailed explanation
            self.log(f"⚠️ SUPERVISOR ESCALATION: Critical issues found - score {review_result['score']}/10")
            
            error_response = self.create_message(
                recipient="UserProxy",
                message_type="workflow_error",
                content=f"❌ **Work Quality Issues**\n\n{review_result['user_message']}\n\n**Supervisor Assessment:**\n{review_result['feedback']}",
                metadata={
                    "intent": original_intent,
                    "error": review_result["issues"],
                    "success": False,
                    "reviewed_by": "Supervisor",
                    "quality_score": review_result["score"],
                    "escalation_reason": review_result["feedback"]
                }
            )
            
            state["agent_messages"].append(error_response)
            state["current_agent"] = "UserProxy"
        
        return state
    
    def _perform_detailed_review(self, intent: str, work_content: str, results: Dict, 
                               reported_success: bool, state: AgentState) -> Dict[str, Any]:
        """Perform detailed quality review of completed work"""
        
        issues = []
        score = 10  # Start with perfect score and deduct points
        
        # Review based on intent type
        if intent == "set_knowledge_base_context":
            return self._review_kb_context_setting(work_content, results, reported_success, state)
        elif intent == "create_content":
            return self._review_content_creation(work_content, results, reported_success, state)
        elif intent in ["retrieve_content", "search_content"]:
            return self._review_content_retrieval(work_content, results, reported_success, state)
        else:
            return self._review_general_work(work_content, results, reported_success, state)
    
    def _review_kb_context_setting(self, work_content: str, results: Dict, 
                                 reported_success: bool, state: AgentState) -> Dict[str, Any]:
        """Review knowledge base context setting operations"""
        issues = []
        score = 10
        
        # Check if KB context was actually set
        kb_id = state.get("knowledge_base_id")
        kb_name = state.get("knowledge_base_name")
        
        if not kb_id:
            issues.append("Knowledge base context was not properly set in state")
            score -= 5
        
        if not results or not results.get("success"):
            issues.append("Tool execution failed or returned no success indicator")
            score -= 3
        
        if "error" in str(work_content).lower():
            issues.append("Work content contains error messages")
            score -= 2
        
        # Determine decision
        if score >= 8:
            decision = "APPROVE"
            feedback = f"Knowledge base context successfully set to {kb_name} (ID: {kb_id})" if kb_id else "Context operation completed"
            user_message = f"🔧 **Knowledge Base Context Set**\n\n{feedback}"
        elif score >= 6:
            decision = "REVISE"
            feedback = f"Context setting partially successful but has issues: {'; '.join(issues)}"
            user_message = work_content
        else:
            decision = "ESCALATE"
            feedback = f"Context setting failed with critical issues: {'; '.join(issues)}"
            user_message = f"Failed to set knowledge base context. Issues detected: {'; '.join(issues)}"
        
        return {
            "decision": decision,
            "score": score,
            "feedback": feedback,
            "user_message": user_message,
            "issues": issues
        }
    
    def _review_content_creation(self, work_content: str, results: Dict, 
                               reported_success: bool, state: AgentState) -> Dict[str, Any]:
        """Review content creation operations"""
        issues = []
        score = 10
        
        # Check if articles were actually created
        articles_created = results.get("articles_created", [])
        tool_results = results.get("tool_results", [])
        
        if not articles_created or len(articles_created) == 0:
            issues.append("No articles were successfully created")
            score -= 5
        
        # Check for tool execution errors
        error_count = 0
        for tool_result in tool_results:
            if isinstance(tool_result, dict) and not tool_result.get("success", True):
                error_count += 1
        
        if error_count > 0:
            issues.append(f"{error_count} tool execution errors occurred")
            score -= error_count * 2
        
        # Check for KB ID issues
        kb_id = state.get("knowledge_base_id")
        if not kb_id:
            issues.append("No knowledge base context available for content creation")
            score -= 3
        
        # Check work content for error indicators
        if "error" in str(work_content).lower() and "no error" not in str(work_content).lower():
            issues.append("Work content contains error messages")
            score -= 2
        
        # Determine decision
        if score >= 8:
            decision = "APPROVE"
            feedback = f"Content creation successful: {len(articles_created)} articles created"
            user_message = f"✅ **Content Creation Complete**\n\n{feedback}\n\n{work_content}"
        elif score >= 6:
            decision = "REVISE"
            feedback = f"Content creation partially successful but needs improvement: {'; '.join(issues)}"
            user_message = work_content
        else:
            decision = "ESCALATE"
            feedback = f"Content creation failed with critical issues: {'; '.join(issues)}"
            user_message = f"❌ Content creation encountered serious problems: {'; '.join(issues)}"
        
        return {
            "decision": decision,
            "score": score,
            "feedback": feedback,
            "user_message": user_message,
            "issues": issues
        }
    
    def _review_content_retrieval(self, work_content: str, results: Dict, 
                                reported_success: bool, state: AgentState) -> Dict[str, Any]:
        """Review content retrieval operations"""
        issues = []
        score = 10
        
        # Check if content was retrieved
        combined_results = results.get("combined_results", "")
        tool_results = results.get("tool_results", [])
        
        if not combined_results and not tool_results:
            issues.append("No content was retrieved")
            score -= 4
        
        if "error" in str(work_content).lower():
            issues.append("Retrieval operation contains errors")
            score -= 3
        
        # Determine decision
        if score >= 7:
            decision = "APPROVE"
            feedback = "Content retrieval completed successfully"
            user_message = f"📋 **Content Retrieved**\n\n{work_content}"
        elif score >= 5:
            decision = "REVISE"
            feedback = f"Retrieval partially successful: {'; '.join(issues)}"
            user_message = work_content
        else:
            decision = "ESCALATE"
            feedback = f"Retrieval failed: {'; '.join(issues)}"
            user_message = f"❌ Content retrieval failed: {'; '.join(issues)}"
        
        return {
            "decision": decision,
            "score": score,
            "feedback": feedback,
            "user_message": user_message,
            "issues": issues
        }
    
    def _review_general_work(self, work_content: str, results: Dict, 
                           reported_success: bool, state: AgentState) -> Dict[str, Any]:
        """Review general work operations"""
        issues = []
        score = 10
        
        if not reported_success:
            issues.append("Operation reported as unsuccessful")
            score -= 4
        
        if "error" in str(work_content).lower() and "no error" not in str(work_content).lower():
            issues.append("Work contains error messages")
            score -= 3
        
        if not work_content or work_content.strip() == "":
            issues.append("No meaningful work content provided")
            score -= 5
        
        # Determine decision
        if score >= 7:
            decision = "APPROVE"
            feedback = "Work completed satisfactorily"
            user_message = work_content
        elif score >= 5:
            decision = "REVISE"
            feedback = f"Work needs improvement: {'; '.join(issues)}"
            user_message = work_content
        else:
            decision = "ESCALATE"
            feedback = f"Work quality unacceptable: {'; '.join(issues)}"
            user_message = f"❌ Operation failed: {'; '.join(issues)}"
        
        return {
            "decision": decision,
            "score": score,
            "feedback": feedback,
            "user_message": user_message,
            "issues": issues
        }

        # Update task context
        state["task_context"] = {
            "workflow_plan": workflow_plan,
            "current_step": 0,
            "total_steps": len(workflow_plan["steps"]),
            "original_request": latest_message.content
        }
        
        # Execute the workflow
        state = self._execute_workflow(state, workflow_plan)
        
        return state
    
    def _analyze_and_plan(self, request_message: AgentMessage) -> Dict[str, Any]:
        """Analyze the request and create a workflow plan"""
        user_intent = request_message.metadata.get("intent", "general_inquiry")
        content = request_message.content
        
        self.log(f"Analyzing request with intent: {user_intent}")
        
        # Use LLM to analyze and create workflow plan
        analysis_prompt = f"""
Analyze this user request and create a detailed workflow plan:

User Intent: {user_intent}
User Request: {content}

Create a workflow plan that includes:
1. Required operations in logical sequence
2. Knowledge base validation steps
3. Error handling considerations
4. Expected outcomes

Respond with a clear plan for the Content Management Agent.
        """
        
        messages = [
            self.get_system_message(),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = self.llm.invoke(messages)
        plan_content = response.content
        
        # Create structured workflow plan
        workflow_plan = {
            "intent": user_intent,
            "description": plan_content,
            "steps": self._extract_workflow_steps(user_intent, content),
            "validation_required": self._requires_validation(user_intent),
            "risk_level": self._assess_risk_level(user_intent),
            "original_request": content  # Include original user request for content extraction
        }
        
        return workflow_plan
    
    def _extract_workflow_steps(self, intent: str, content: str) -> List[Dict[str, Any]]:
        """Extract specific workflow steps based on intent"""
        steps = []
        
        if intent == "set_knowledge_base_context":
            steps = [
                {"action": "extract_kb_id", "description": "Extract knowledge base ID from user request"},
                {"action": "validate_kb_exists", "description": "Validate knowledge base exists"},
                {"action": "set_context", "description": "Set knowledge base context"},
                {"action": "confirm_context", "description": "Confirm context change to user"}
            ]
        elif intent == "set_article_context":
            steps = [
                {"action": "extract_article_id", "description": "Extract article ID from user request"},
                {"action": "validate_article_exists", "description": "Validate article exists in current KB"},
                {"action": "set_article_context", "description": "Set article working context"},
                {"action": "confirm_article_context", "description": "Confirm article context to user"}
            ]
        elif intent == "create_knowledge_base":
            steps = [
                {"action": "validate_kb_creation", "description": "Validate knowledge base creation request"},
                {"action": "create_kb", "description": "Create new knowledge base"},
                {"action": "confirm_creation", "description": "Confirm successful creation"}
            ]
        elif intent == "create_article":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "get_kb_structure", "description": "Retrieve current knowledge base structure"},
                {"action": "validate_article_placement", "description": "Determine appropriate article placement"},
                {"action": "create_article", "description": "Create the new article"},
                {"action": "update_hierarchy", "description": "Display updated hierarchy"}
            ]
        elif intent == "update_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "locate_content", "description": "Find the content to update"},
                {"action": "update_content", "description": "Perform the update operation"},
                {"action": "validate_update", "description": "Confirm update was successful"}
            ]
        elif intent == "retrieve_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "retrieve_content", "description": "Retrieve requested content"},
                {"action": "format_response", "description": "Format response for user"}
            ]
        elif intent == "retrieve_filtered_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "identify_section", "description": "Identify the specific section to filter by"},
                {"action": "retrieve_hierarchy", "description": "Retrieve full article hierarchy"},
                {"action": "filter_section_content", "description": "Filter to show only the requested section and its children"},
                {"action": "format_filtered_response", "description": "Format filtered response showing only the requested section"}
            ]
        elif intent == "search_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "search_content", "description": "Perform search operation"},
                {"action": "format_results", "description": "Format search results"}
            ]
        elif intent == "create_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "analyze_content_request", "description": "Analyze the content creation request"},
                {"action": "determine_content_type", "description": "Determine if creating categories, articles, or both"},
                {"action": "create_categories_if_needed", "description": "Create any missing categories first"},
                {"action": "create_articles", "description": "Create the requested articles with appropriate content"},
                {"action": "validate_content_structure", "description": "Ensure content is properly structured and linked"},
                {"action": "confirm_content_creation", "description": "Confirm successful content creation to user"}
            ]
        elif intent == "analyze_content_gaps":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "retrieve_full_hierarchy", "description": "Get complete knowledge base structure"},
                {"action": "analyze_content_coverage", "description": "Analyze existing content for gaps and opportunities"},
                {"action": "identify_missing_topics", "description": "Identify potential topics that could enhance the knowledge base"},
                {"action": "generate_content_recommendations", "description": "Generate specific article recommendations with rationale"}
            ]
        else:
            steps = [
                {"action": "analyze_request", "description": "Analyze the request"},
                {"action": "execute_operation", "description": "Execute appropriate operation"},
                {"action": "format_response", "description": "Format response"}
            ]
        
        return steps
    
    def _requires_validation(self, intent: str) -> bool:
        """Determine if the operation requires user validation"""
        high_risk_operations = ["create_knowledge_base", "delete_content", "update_content"]
        return intent in high_risk_operations
    
    def _assess_risk_level(self, intent: str) -> str:
        """Assess the risk level of the operation"""
        if intent in ["delete_content"]:
            return "high"
        elif intent in ["create_knowledge_base", "update_content"]:
            return "medium"
        else:
            return "low"
    
    def _execute_workflow(self, state: AgentState, workflow_plan: Dict[str, Any]) -> AgentState:
        """Execute the planned workflow"""
        self.log(f"Executing workflow: {workflow_plan['intent']}")
        
        # Create message for Content Management Agent
        cm_message = self.create_message(
            recipient="ContentManagement",
            message_type="workflow_request",
            content=f"Execute workflow for: {workflow_plan['intent']}",
            metadata={
                "workflow_plan": workflow_plan,
                "original_request": state.get("task_context", {}).get("original_request", "")
            }
        )
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(cm_message)
        
        # Set Content Management Agent as next active agent
        state["current_agent"] = "ContentManagement"
        
        self.log("Workflow delegated to Content Management Agent")
        
        return state
    
    def process_cm_response(self, state: AgentState, cm_response: AgentMessage) -> AgentState:
        """Process response from Content Management Agent"""
        self.log("Processing response from Content Management Agent")
        
        # Extract results from CM response
        results = cm_response.metadata.get("results", {})
        success = cm_response.metadata.get("success", False)
        
        # Create response for User Proxy Agent
        if success:
            user_response = self.create_message(
                recipient="UserProxy",
                message_type="workflow_complete",
                content=f"Operation completed successfully: {cm_response.content}",
                metadata={"results": results, "success": True}
            )
        else:
            user_response = self.create_message(
                recipient="UserProxy", 
                message_type="workflow_error",
                content=f"Operation encountered an issue: {cm_response.content}",
                metadata={"error": results, "success": False}
            )
        
        # Add to agent messages
        state["agent_messages"].append(user_response)
        
        # Set User Proxy as next agent to respond to user
        state["current_agent"] = "UserProxy"
        
        self.log("Response prepared for User Proxy Agent")
        
        return state
