from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from tools.gitlab_tools import GitLabTools
from tools.knowledge_base_tools import KnowledgeBaseTools
from prompts.multi_agent_prompts import prompts


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent - Reviews and validates work from other agents with GitLab integration.
    This agent ensures quality control and provides oversight for operations.
    Handles coordination and work assignment in the GitLab-centric architecture.
    Uses GitLab for work validation tracking and status reporting.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        system_prompt = self._create_supervisor_prompt()
        super().__init__("SupervisorAgent", llm, system_prompt)
        
        # Initialize GitLab tools for work validation tracking
        self.gitlab_tools = GitLabTools()
        
        # Initialize read-only KB tools for oversight and coordination
        self.kb_tools = KnowledgeBaseTools()
        
        # Combine GitLab tools with read-only KB tools
        gitlab_tools_list = self.gitlab_tools.tools()
        readonly_kb_tools = self._get_readonly_kb_tools()
        self.tools = gitlab_tools_list + readonly_kb_tools
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
    def _get_readonly_kb_tools(self) -> List:
        """Get read-only knowledge base tools for supervisor oversight.
        
        The Supervisor needs visibility into KB content for coordination purposes
        but should not create, modify, or delete any content. All content 
        operations are handled by the content_agent_swarm.
        """
        all_kb_tools = self.kb_tools.get_tools()
        
        # Only include read-only tools for oversight and coordination
        readonly_tool_names = [
            "KnowledgeBaseGetKnowledgeBases",           # List all KBs
            "KnowledgeBaseGetRootLevelArticles",        # View KB content structure
            "KnowledgeBaseGetArticleHierarchy",         # View content organization
            "KnowledgeBaseGetArticleByArticleId",       # Read specific articles
            "KnowledgeBaseGetChildArticlesByParentIds", # Navigate content structure
            "KnowledgeBaseGetTagsByKnowledgeBase",      # View KB tagging
            "KnowledgeBaseGetTagById",                  # Read tag details
            "KnowledgeBaseGetTagsForArticle",           # View article tags
            "KnowledgeBaseGetArticlesForTag",           # Search by tags
            "KnowledgeBaseGetTagsWithUsageCount",       # Content analytics
        ]
        
        # Filter to only include read-only tools
        readonly_tools = [
            tool for tool in all_kb_tools 
            if tool.name in readonly_tool_names
        ]
        
        return readonly_tools
    
    def _create_supervisor_prompt(self) -> str:
        """Create the system prompt for the supervisor agent"""
        return """You are the Supervisor Agent functioning as a SCRUM MASTER for a multi-agent knowledge base system with comprehensive GitLab integration. Your primary responsibility is to facilitate and coordinate work across all content agents, evaluate work streams, and provide status updates to stakeholders.

**DIRECT COMMUNICATION ARCHITECTURE:**
- **UserProxy Agent**: Direct bidirectional communication for user collaboration and status updates
- **ContentManagement Agent**: Direct bidirectional communication for operational coordination and work delegation
- **Other Agents**: NO direct communication - coordinate only through GitLab issues, projects, and workflows

**SCRUM MASTER ROLE - GITLAB-CENTRIC FACILITATION:**
You function as the team's Scrum Master, facilitating agile workflows through GitLab:
- ContentPlanner, ContentCreator, ContentReviewer, and ContentRetrieval agents work autonomously through GitLab
- These agents discover their work by checking GitLab for assigned issues
- You coordinate them by creating GitLab issues, milestones, and project structures
- You facilitate sprint planning, daily standups, and retrospectives through GitLab workflows
- You remove blockers and impediments for the content agent team through GitLab
- You evaluate work streams and team velocity through GitLab metrics

**Your Scrum Master Responsibilities:**
1. **Sprint Planning**: Create GitLab milestones and issues for sprint planning
2. **Daily Standups**: Monitor GitLab activity to track agent progress and identify blockers
3. **Work Stream Evaluation**: Continuously assess team velocity, work quality, and delivery patterns through GitLab metrics
4. **Impediment Removal**: Identify and resolve blockers through GitLab issue management
5. **Sprint Reviews**: Evaluate completed work through GitLab issue completion analysis
6. **Retrospectives**: Analyze team performance using GitLab metrics and feedback
7. **Stakeholder Communication**: Provide regular status updates to UserProxy and ContentManagement

**SCRUM WORKFLOWS THROUGH GITLAB:**

**Sprint Planning Process:**
1. **User Story Analysis**: Break down user requests into clear, actionable user stories
2. **Story Estimation**: Work with ContentPlanner to estimate effort and complexity
3. **Sprint Creation**: Create GitLab milestones to represent sprints with clear goals
4. **Issue Assignment**: Create and assign GitLab issues to content agents based on capacity
5. **Definition of Done**: Establish clear acceptance criteria for all work items

**Daily Standup Coordination:**
- **Monitor GitLab Activity**: Review overnight GitLab updates from all content agents
- **Track Progress**: Assess what was completed, what's in progress, and what's planned
- **Identify Blockers**: Spot impediments preventing agents from completing work
- **Facilitate Communication**: Ensure agents communicate dependencies through GitLab
- **Update Stakeholders**: Provide daily progress summaries to UserProxy when requested

**Work Stream Evaluation:**
- **Velocity Tracking**: Monitor team velocity through completed GitLab issues and story points
- **Quality Metrics**: Track defect rates, rework frequency, and review feedback patterns
- **Burndown Analysis**: Monitor sprint progress and identify risks to delivery commitments
- **Resource Utilization**: Assess agent workload balance and capacity planning
- **Delivery Predictability**: Evaluate team's ability to meet commitments and improve estimation

**Impediment Management:**
- **Blocker Identification**: Proactively identify obstacles preventing agent progress
- **Resolution Coordination**: Work with appropriate stakeholders to remove impediments
- **Escalation Management**: Escalate systemic issues that require organizational intervention
- **Process Improvement**: Identify and implement process improvements to prevent recurring issues

**Stakeholder Communication:**
- **Status Reporting**: Provide regular status updates to UserProxy with clear, actionable information
- **Transparency**: Maintain visibility into team performance, challenges, and achievements
- **Expectation Management**: Set realistic expectations based on team velocity and capacity
- **Feedback Integration**: Incorporate stakeholder feedback into team processes and priorities

**GITLAB-BASED AGILE WORKFLOWS:**

**Sprint Management:**
- Create GitLab milestones for each sprint with clear objectives and timelines
- Track sprint progress through GitLab burndown charts and velocity metrics
- Conduct sprint reviews through GitLab issue completion analysis
- Facilitate sprint retrospectives using GitLab issue labels and comments

**Issue Lifecycle Management:**
- **Backlog Refinement**: Create well-groomed GitLab issues and backlogs for autonomous agent discovery
- **Story Assignment**: Assign GitLab issues to agents based on skills, capacity, and priorities
- **Progress Tracking**: Monitor issue state transitions and time-in-state metrics
- **Quality Gates**: Ensure all work meets Definition of Done before marking complete

**Team Coordination:**
- **Dependencies**: Track and manage cross-agent dependencies through GitLab issue relationships
- **Capacity Planning**: Balance workload across agents based on historical velocity
- **Skills Development**: Identify opportunities for agent capability improvement through GitLab analytics
- **Knowledge Sharing**: Facilitate knowledge transfer through GitLab documentation and wikis

**GITLAB CAPABILITIES AVAILABLE:**
- Create and manage GitLab projects, milestones, and issue hierarchies
- Track team velocity and performance metrics through GitLab analytics
- Coordinate cross-agent collaboration through GitLab workflows and notifications
- Maintain comprehensive audit trails through GitLab activity tracking
- Generate status reports and dashboards through GitLab project management features

**KNOWLEDGE BASE READ-ONLY ACCESS:**
For coordination and oversight purposes, you have read-only access to KB data:
- **View KB Structure**: List all knowledge bases and their hierarchical content
- **Read Content**: Access articles, tags, and metadata for coordination context
- **Analyze Content**: Review content organization for sprint planning and work estimation
- **Monitor Progress**: Track content creation progress without making changes

**CRITICAL BOUNDARY: NO CONTENT MODIFICATION**
- **NO Creation**: You cannot create articles, tags, or KB entries
- **NO Modification**: You cannot edit, update, or modify any content
- **NO Deletion**: You cannot delete any KB content or structures
- **Delegation Only**: All content operations must be delegated to content_agent_swarm

**BEST PRACTICES:**
- Focus on facilitating team success rather than directing individual work
- Use data-driven insights from GitLab metrics to guide process improvements
- Maintain servant leadership approach - remove obstacles for the team
- Promote agent self-organization while providing necessary structure through GitLab
- Ensure transparency and visibility for all stakeholders through GitLab

**COMMUNICATION PATTERNS:**
- **To UserProxy**: Direct communication for clear, concise status updates with actionable insights
- **To ContentManagement**: Direct communication for operational coordination and work delegation
- **For Content Operations**: ALWAYS delegate to content_agent_swarm via ContentManagement - never perform content operations directly
- **To Other Agents**: NO direct communication - coordinate only through GitLab issues, projects, and assignments
- **Cross-functional**: Coordinate with other systems and stakeholders through GitLab workflows

**DELEGATION WORKFLOW FOR CONTENT OPERATIONS:**
When users request content creation, modification, or management:
1. **Acknowledge Request**: Confirm understanding of the content operation needed
2. **Coordinate via ContentManagement**: Route all content work through ContentManagement agent
3. **Create GitLab Issues**: Set up appropriate GitLab tracking for the content work
4. **Monitor Progress**: Use read-only KB tools to track progress without interfering
5. **Report Status**: Provide updates to UserProxy on content operation progress

You are the team's servant leader, focused on maximizing team effectiveness and delivering value to users through excellent facilitation, GitLab coordination, and continuous improvement."""

    def process(self, state: AgentState) -> AgentState:
        """Review and validate work from other agents"""
        self.log("Processing work review request")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for excessive recursions and reset if needed
        recursions = state.get("recursions", 0)
        if recursions > 12 or state.get("loop_detected", False):
            self.log(f"Loop or excessive recursions detected, resetting session")
            
            # Reset the session state completely
            state["current_agent"] = None
            state["recursions"] = 0
            state["agent_messages"] = []
            state["kb_design_session"] = {"active": False}
            state["loop_detected"] = False
            
            # Send a reset message to UserProxy
            reset_message = self.create_message(
                recipient="UserProxy",
                message_type="workflow_complete",
                content="🔄 **Session Reset** - Please start your request again with clear instructions.",
                metadata={"success": True, "reset": True}
            )
            
            state["agent_messages"].append(reset_message)
            state["current_agent"] = "UserProxy"
            return state
        
        # Check for messages from other agents
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient in [self.name, "Supervisor"]]
        
        if not my_messages:
            # No agent messages - this might be direct routing from UserProxy
            self.log("No agent messages found - checking for direct routing from UserProxy")
            return self._handle_direct_routing(state)
        
        # Get the latest message
        latest_message = my_messages[-1]
        
        if latest_message.message_type in ["work_review", "workflow_response"]:
            # Review work completed by ContentManagement
            self.log("Reviewing work from ContentManagement Agent")
            return self._review_workflow_response(state, latest_message)
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
        
        # Check if this is a GitLab coordination request from UserProxy
        if request_message.message_type == "gitlab_coordination_request":
            self.log("Received GitLab coordination request")
            return self._handle_gitlab_coordination_request(state, request_message)
        
        # Check if this is a workflow response from ContentManagement
        if request_message.message_type == "workflow_response":
            # This is a completed workflow - review it
            self.log("Received workflow response - reviewing work")
            return self._review_workflow_response(state, request_message)
        
        # Check if this is a status update from ContentManagement indicating no work available
        if (request_message.message_type == "status_update" and 
            request_message.sender == "ContentManagement" and
            request_message.metadata.get("work_available") == False):
            
            self.log("ContentManagement reports no work available - routing back to UserProxy")
            
            # Send informative response to UserProxy
            no_work_response = self.create_message(
                recipient="UserProxy",
                message_type="info_response", 
                content="No GitLab work items are currently available. For basic operations like listing knowledge bases, please try your request again or be more specific about what you need.",
                metadata={
                    "agent_status": "no_work_available",
                    "suggestion": "Try asking: 'get all knowledge bases' or 'list kbs'"
                }
            )
            
            state["agent_messages"].append(no_work_response)
            state["current_agent"] = None  # End the workflow
            return state
        
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
        """Handle direct routing from UserProxy agent"""
        
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
                "intent": "llm_driven",  # Always use LLM-driven approach
                "requires_review": True,
                "supervisor_notes": "Direct routing from UserProxy - LLM will determine appropriate actions",
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
        
        # Check if tool execution was successful regardless of score
        tool_executed_successfully = False
        if isinstance(results, dict):
            tool_executed_successfully = results.get("tool_executed", False) or \
                                       "executed successfully" in str(results).lower() or \
                                       reported_success
        
        # Determine decision - be more lenient for successful tool executions
        if score >= 7:
            decision = "APPROVE"
            feedback = "Work completed satisfactorily"
            user_message = work_content
        elif score >= 5 and tool_executed_successfully:
            # If tools executed successfully, approve even with medium score
            decision = "APPROVE"
            feedback = "Work completed with tool execution success"
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
    
    # =============================================
    # GITLAB INTEGRATION METHODS
    # =============================================
    
    def track_review_in_gitlab(self, project_id: str, issue_id: str, 
                             review_status: str, quality_score: int, 
                             feedback: str = "") -> bool:
        """Track work review progress and decisions in GitLab"""
        try:
            self.log(f"Tracking review in GitLab issue #{issue_id}: {review_status}")
            
            # Create detailed review comment
            comment_content = f"**🔍 SUPERVISOR REVIEW UPDATE**\n\n"
            comment_content += f"**Review Status:** {review_status}\n"
            comment_content += f"**Quality Score:** {quality_score}/10\n\n"
            
            if feedback:
                comment_content += f"**Review Feedback:**\n{feedback}\n\n"
            
            comment_content += f"**Review Decision:**\n"
            if review_status.upper() == "APPROVED":
                comment_content += "✅ **APPROVED** - Work meets all quality criteria and requirements\n"
            elif review_status.upper() == "NEEDS_REVISION":
                comment_content += "🔄 **NEEDS REVISION** - Work requires improvements before approval\n"
            elif review_status.upper() == "ESCALATED":
                comment_content += "⚠️ **ESCALATED** - Complex issues require additional consideration\n"
            else:
                comment_content += f"📋 **STATUS:** {review_status}\n"
            
            comment_content += f"\n**Reviewed by:** SupervisorAgent\n"
            comment_content += f"**Review Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Update GitLab issue with review comment
            success = self._add_gitlab_comment(project_id, issue_id, comment_content)
            
            # Update issue labels based on review status
            if success:
                self._update_issue_labels(project_id, issue_id, review_status)
            
            return success
            
        except Exception as e:
            self.log(f"Error tracking review in GitLab: {str(e)}", "ERROR")
            return False
    
    def create_revision_gitlab_issue(self, original_project_id: str, original_issue_id: str,
                                   revision_title: str, revision_description: str,
                                   required_changes: List[str]) -> Optional[Dict[str, Any]]:
        """Create a new GitLab issue for work that needs revision"""
        try:
            self.log(f"Creating revision issue for original issue #{original_issue_id}")
            
            # Build comprehensive revision issue description
            description = f"**🔄 REVISION REQUIRED**\n\n"
            description += f"**Original Issue:** #{original_issue_id}\n"
            description += f"**Revision Reason:** {revision_description}\n\n"
            
            description += f"**Required Changes:**\n"
            for i, change in enumerate(required_changes, 1):
                description += f"{i}. {change}\n"
            
            description += f"\n**Review Process:**\n"
            description += f"- [ ] Address all required changes listed above\n"
            description += f"- [ ] Verify work meets quality standards\n"
            description += f"- [ ] Request supervisor re-review\n"
            description += f"- [ ] Update original issue #{original_issue_id} with completion\n"
            
            description += f"\n**Quality Standards:**\n"
            description += f"- Accuracy and correctness\n"
            description += f"- Completeness relative to requirements\n"
            description += f"- Professional quality and consistency\n"
            description += f"- User-friendliness and clarity\n"
            
            description += f"\n**Created by:** SupervisorAgent\n"
            description += f"**Creation Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Create the revision issue
            revision_issue = self._create_gitlab_issue(
                project_id=original_project_id,
                title=revision_title,
                description=description,
                labels=["revision-required", "supervisor-feedback", "content-management"]
            )
            
            if revision_issue:
                self.log(f"Created revision issue #{revision_issue.get('iid', 'unknown')}")
                
                # Add reference to original issue
                self._add_gitlab_comment(
                    original_project_id, 
                    original_issue_id,
                    f"**🔄 Revision Required:** Created revision issue #{revision_issue.get('iid', 'unknown')} to address required changes."
                )
                
                return revision_issue
            
            return None
            
        except Exception as e:
            self.log(f"Error creating revision GitLab issue: {str(e)}", "ERROR")
            return None
    
    def create_escalation_gitlab_issue(self, original_project_id: str, original_issue_id: str,
                                     escalation_reason: str, complexity_details: str) -> Optional[Dict[str, Any]]:
        """Create an escalation GitLab issue for complex problems"""
        try:
            self.log(f"Creating escalation issue for original issue #{original_issue_id}")
            
            escalation_title = f"🚨 ESCALATION: Complex Issue #{original_issue_id}"
            
            description = f"**🚨 ESCALATION REQUIRED**\n\n"
            description += f"**Original Issue:** #{original_issue_id}\n"
            description += f"**Escalation Reason:** {escalation_reason}\n\n"
            
            description += f"**Complexity Details:**\n{complexity_details}\n\n"
            
            description += f"**Escalation Process:**\n"
            description += f"- [ ] Senior review of complexity and requirements\n"
            description += f"- [ ] Determine appropriate resolution approach\n"
            description += f"- [ ] Assign additional resources if needed\n"
            description += f"- [ ] Create detailed action plan\n"
            description += f"- [ ] Execute resolution with oversight\n"
            description += f"- [ ] Document lessons learned and process improvements\n"
            
            description += f"\n**Priority:** High\n"
            description += f"**Impact:** Blocking normal workflow progression\n"
            
            description += f"\n**Escalated by:** SupervisorAgent\n"
            description += f"**Escalation Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Create escalation issue
            escalation_issue = self._create_gitlab_issue(
                project_id=original_project_id,
                title=escalation_title,
                description=description,
                labels=["escalation", "high-priority", "supervisor-review", "complex-issue"]
            )
            
            if escalation_issue:
                self.log(f"Created escalation issue #{escalation_issue.get('iid', 'unknown')}")
                
                # Add reference to original issue
                self._add_gitlab_comment(
                    original_project_id,
                    original_issue_id,
                    f"**🚨 Escalated:** Created escalation issue #{escalation_issue.get('iid', 'unknown')} due to complexity requiring additional oversight."
                )
                
                return escalation_issue
            
            return None
            
        except Exception as e:
            self.log(f"Error creating escalation GitLab issue: {str(e)}", "ERROR")
            return None
    
    def approve_work_in_gitlab(self, project_id: str, issue_id: str, 
                             approval_summary: str, quality_metrics: Dict[str, Any] = None) -> bool:
        """Mark work as approved in GitLab with quality metrics"""
        try:
            self.log(f"Approving work in GitLab issue #{issue_id}")
            
            # Create approval comment
            comment_content = f"**✅ WORK APPROVED**\n\n"
            comment_content += f"**Approval Summary:** {approval_summary}\n\n"
            
            if quality_metrics:
                comment_content += f"**Quality Metrics:**\n"
                for metric, value in quality_metrics.items():
                    comment_content += f"- **{metric}:** {value}\n"
                comment_content += "\n"
            
            comment_content += f"**Quality Standards Met:**\n"
            comment_content += f"✅ Accuracy and correctness\n"
            comment_content += f"✅ Completeness relative to requirements\n"
            comment_content += f"✅ Professional quality and consistency\n"
            comment_content += f"✅ User-friendliness and clarity\n\n"
            
            comment_content += f"**Approved by:** SupervisorAgent\n"
            comment_content += f"**Approval Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            comment_content += "This work is now ready for user delivery and can be considered completed."
            
            # Add approval comment
            success = self._add_gitlab_comment(project_id, issue_id, comment_content)
            
            # Update issue labels to reflect approval
            if success:
                self._update_issue_labels(project_id, issue_id, "APPROVED")
            
            return success
            
        except Exception as e:
            self.log(f"Error approving work in GitLab: {str(e)}", "ERROR")
            return False
    
    # =============================================
    # GITLAB HELPER METHODS
    # =============================================
    
    def _add_gitlab_comment(self, project_id: str, issue_id: str, comment: str) -> bool:
        """Add a comment to a GitLab issue"""
        try:
            # GitLab issue commenting would typically be done through issue updates
            # This is a placeholder for the actual GitLab API integration
            self.log(f"Adding comment to GitLab issue #{issue_id}")
            return True
            
        except Exception as e:
            self.log(f"Error adding GitLab comment: {str(e)}", "ERROR")
            return False
    
    def _update_issue_labels(self, project_id: str, issue_id: str, status: str) -> bool:
        """Update GitLab issue labels based on review status"""
        try:
            # Map review status to appropriate labels
            status_labels = {
                "APPROVED": ["approved", "supervisor-approved", "ready-for-delivery"],
                "NEEDS_REVISION": ["needs-revision", "supervisor-feedback", "in-progress"],
                "ESCALATED": ["escalated", "high-priority", "complex-issue"],
                "UNDER_REVIEW": ["under-review", "supervisor-reviewing"]
            }
            
            labels = status_labels.get(status.upper(), ["supervisor-processed"])
            self.log(f"Updating GitLab issue #{issue_id} labels: {labels}")
            
            # This would use GitLab tools to update issue labels
            return True
            
        except Exception as e:
            self.log(f"Error updating issue labels: {str(e)}", "ERROR")
            return False
    
    def _create_gitlab_issue(self, project_id: str, title: str, description: str, labels: List[str]) -> Optional[Dict[str, Any]]:
        """Create a GitLab issue using available tools"""
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
            self.log(f"Error creating GitLab issue: {str(e)}", "ERROR")
            return None
    
    def _parse_issue_from_result(self, result: str) -> Dict[str, Any]:
        """Parse issue data from GitLab tool result"""
        # This would parse the string result from GitLab tools
        # and extract structured issue data
        return {}
    
    def _handle_gitlab_coordination_request(self, state: AgentState, request_message: AgentMessage) -> AgentState:
        """Handle GitLab coordination requests from UserProxy"""
        self.log("Processing GitLab coordination request")
        
        metadata = request_message.metadata
        gitlab_coordination = metadata.get("gitlab_coordination", {})
        target_agent = gitlab_coordination.get("target_agent")
        work_type = gitlab_coordination.get("work_type")
        design_session = metadata.get("design_session", {})
        
        # For ContentPlanner coordination, create GitLab issue for autonomous discovery
        if target_agent == "ContentPlanner" and work_type == "strategic_design":
            
            # In the simplified chat system, delegate the complete KB creation to ContentManagement
            # instead of waiting for autonomous GitLab discovery
            self.log("Delegating KB creation to ContentManagement for immediate execution")
            
            # Create KB creation request for ContentManagement
            kb_creation_request = self.create_message(
                recipient="ContentManagementAgent",
                message_type="supervised_work_request",
                content=f"Create knowledge base with strategic design for: {design_session.get('design_elements', {}).get('domain', 'Financial Freedom')}",
                metadata={
                    "design_session": design_session,
                    "requires_review": True,
                    "supervisor_notes": "Complete KB creation with strategic planning integration",
                    "intent": "create_knowledge_base",
                    "kb_creation": True
                }
            )
            
            state["agent_messages"].append(kb_creation_request)
            state["current_agent"] = "ContentManagementAgent"
            
            self.log(f"Delegated KB creation to ContentManagement for immediate execution")
            
        else:
            # Handle other coordination requests
            error_response = self.create_message(
                recipient="UserProxy",
                message_type="coordination_error",
                content=f"Unknown GitLab coordination request: {target_agent} - {work_type}",
                metadata={"error": "unsupported_coordination_type"}
            )
            
            state["agent_messages"].append(error_response)
            state["current_agent"] = "UserProxy"
        
        return state
