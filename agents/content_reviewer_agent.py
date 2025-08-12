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


class ContentReviewerAgent(BaseAgent):
    """
    Content Reviewer Agent - Quality assurance and optimization specialist with GitLab integration.
    
    Responsibilities:
    - Review content for expert-level quality and accuracy
    - Ensure comprehensive coverage and depth
    - Optimize content organization and structure
    - Validate publication readiness
    - Coordinate revision cycles when needed
    - Access GitLab to find assigned review work
    - Communicate with other agents through GitLab issue comments and feedback
    - Deliver publication-ready knowledge bases through GitLab-coordinated workflows
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Combine base KB prompts with specialized review prompts
        base_prompt = kb_prompts.master_prompt()
        specialized_prompt = self._get_review_prompt()
        gitlab_integration_prompt = self._create_gitlab_integration_prompt()
        system_prompt = f"{base_prompt}\n\n{specialized_prompt}\n\n{gitlab_integration_prompt}"
        
        super().__init__("ContentReviewer", llm, system_prompt)
        
        # Initialize knowledge base tools - review and optimization focused
        kb_tools = KnowledgeBaseTools()
        all_kb_tools = kb_tools.tools()
        
        # Initialize GitLab tools
        self.gitlab_tools = GitLabTools()
        
        # Filter to review and optimization tools
        filtered_kb_tools = self._filter_review_tools(all_kb_tools)
        
        # Combine all tools
        self.tools = filtered_kb_tools + self.gitlab_tools.tools()
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
    def _filter_review_tools(self, all_tools):
        """Filter tools to include review and optimization operations"""
        review_tool_names = {
            "KnowledgeBaseUpdateKnowledgeBase",
            "KnowledgeBaseUpdateArticle",
            "KnowledgeBaseGetArticleHierarchy",
            "KnowledgeBaseAnalyzeContentGaps",
            "KnowledgeBaseGetArticleByArticleId",
            "KnowledgeBaseGetRootLevelArticles",
            "KnowledgeBaseGetChildArticlesByParentIds"
        }
        
        return [tool for tool in all_tools if tool.name in review_tool_names]
    
    def _create_gitlab_integration_prompt(self) -> str:
        """Create GitLab integration prompt for the content reviewer agent"""
        return """
**GITLAB INTEGRATION - QUALITY ASSURANCE & REVIEW COORDINATION:**

You have comprehensive GitLab integration capabilities for quality assurance and review coordination:

**REVIEW WORK DISCOVERY:**
- Check GitLab issues for assigned content review tasks
- Find review requests from ContentCreator and ContentPlanner agents
- Access detailed review criteria and quality standards from GitLab issue descriptions
- Monitor review backlogs and priority assignments across projects

**COLLABORATIVE QUALITY ASSURANCE:**
- Provide detailed review feedback through GitLab issue comments
- Coordinate with ContentCreator for content revision cycles
- Communicate with ContentPlanner about structural optimization needs
- Track quality metrics and improvement trends through GitLab reporting

**REVIEW WORKFLOW COORDINATION:**
- Update GitLab issues with review progress and quality assessments
- Create detailed revision requests as GitLab sub-issues when needed
- Document quality improvements and optimization recommendations
- Track review completion and approval status through GitLab workflows

**ITERATIVE IMPROVEMENT PROCESS:**
- Manage revision cycles through GitLab issue state transitions
- Coordinate multi-round reviews for complex content projects
- Document quality standards and best practices in GitLab project wikis
- Create improvement tracking issues for long-term quality enhancement

**PUBLICATION READINESS VALIDATION:**
- Final quality validation documented through GitLab approval processes
- Create publication-ready status updates for completed knowledge bases
- Coordinate with Supervisor for final publication approval workflows
- Maintain quality audit trails through comprehensive GitLab documentation

**REVIEW PROCESS:**
1. **Check Review Queue**: Look for assigned review work in GitLab issues
2. **Access Content**: Review content based on detailed GitLab specifications
3. **Quality Assessment**: Document comprehensive quality evaluation in GitLab
4. **Provide Feedback**: Create detailed revision requests through GitLab workflows
5. **Track Improvements**: Monitor revision implementation through GitLab updates
6. **Approve Completion**: Mark content as publication-ready when quality standards met

**GITLAB CAPABILITIES AVAILABLE:**
- Access review assignments with detailed quality criteria
- Create comprehensive review reports and feedback through issue comments
- Coordinate revision workflows with content creation agents
- Track quality metrics and improvement trends across projects
- Document best practices and quality standards for team reference

**BEST PRACTICES:**
- Always check GitLab for review context and quality standards before starting
- Provide detailed, actionable feedback through structured GitLab comments
- Use GitLab workflows to coordinate iterative improvement cycles
- Document quality decisions and rationale for future reference
- Maintain comprehensive audit trails of all quality assurance activities

When reviewing content, leverage GitLab's collaborative features to ensure consistent quality standards and effective coordination with the content creation team.
"""
    
    def _get_review_prompt(self):
        """Get specialized prompt for content review operations"""
        return """
        You are an Expert Content Quality Assurance and Optimization Specialist with authority across all domains.
        
        Your core responsibilities:
        - Review content for expert-level quality, accuracy, and comprehensiveness
        - Ensure publication-ready standards across all articles
        - Optimize content organization and knowledge base structure
        - Validate comprehensive domain coverage with no critical gaps
        - Coordinate revision cycles for continuous improvement
        - Deliver publication-ready knowledge bases that serve as definitive resources
        
        Quality Assurance Philosophy:
        - PUBLICATION EXCELLENCE: Content must meet professional publishing standards
        - EXPERT AUTHORITY: Validate that content demonstrates genuine expertise
        - COMPREHENSIVE COVERAGE: Ensure no critical knowledge gaps exist
        - OPTIMAL ORGANIZATION: Structure knowledge for maximum accessibility and value
        - AUTONOMOUS QUALITY: Make optimization decisions without requiring oversight
        - DEFINITIVE RESOURCE: Output serves as the authoritative source for the domain
        
        Review Standards:
        - Content accuracy and expert-level authority
        - Comprehensive coverage with appropriate depth
        - Clear, professional writing quality
        - Logical organization and structure
        - Effective cross-references and relationships
        - Publication readiness for target use cases
        
        Review Process:
        1. Analyze the complete knowledge base structure and content
        2. Evaluate coverage completeness against domain requirements
        3. Review individual articles for quality and depth
        4. Optimize organization and cross-references
        5. Identify and address any quality gaps
        6. Ensure publication readiness across all content
        7. Provide final optimization recommendations
        
        Quality Evaluation Criteria:
        - Expert Authority: Content demonstrates deep domain understanding
        - Comprehensive Scope: All critical topics covered with appropriate depth
        - Professional Quality: Writing meets publication standards
        - Logical Structure: Information organized for optimal learning/reference
        - Practical Value: Content includes applicable examples and use cases
        - Cross-Reference Quality: Related concepts properly linked
        
        Optimization Focus Areas:
        - Content depth and expertise demonstration
        - Knowledge base structure and navigation
        - Cross-references and content relationships
        - Publication formatting and presentation
        - Domain-specific quality standards
        - User experience for target publishing formats
        
        Revision Coordination:
        - Identify specific improvement areas
        - Coordinate with ContentCreator for revisions when needed
        - Ensure iterative improvement maintains quality momentum
        - Make autonomous optimization decisions when possible
        - Escalate only when external domain expertise required
        """
    
    def process(self, state: AgentState) -> AgentState:
        """Process content review requests"""
        self.log("Processing content review request")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from ContentCreator
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            self.log("No content review requests found")
            return state
        
        # Get the latest review request
        latest_request = my_messages[-1]
        content_strategy = latest_request.metadata.get("content_strategy", {})
        creation_result = latest_request.metadata.get("creation_result", {})
        original_request = latest_request.metadata.get("original_request", "")
        
        self.log(f"Reviewing content for: {original_request}")
        
        # Execute comprehensive content review
        review_result = self._execute_content_review(
            original_request,
            content_strategy,
            creation_result,
            state
        )
        
        # Determine next step based on review result
        if review_result.get("needs_revision", False):
            # Send revision request back to ContentCreator
            response_message = self.create_message(
                recipient="ContentCreator", 
                message_type="content_revision_request",
                content="Content review identified areas for improvement. Please address the specified revisions.",
                metadata={
                    "original_request": original_request,
                    "content_strategy": content_strategy,
                    "revision_requirements": review_result.get("revision_requirements", {}),
                    "review_feedback": review_result.get("feedback", "")
                }
            )
            
            # Route back to ContentCreator for revisions
            state["current_agent"] = "ContentCreator"
            
        else:
            # Content is publication-ready, send final result to UserProxy
            kb_notification = latest_request.metadata.get("kb_context_notification")
            message_content = "Knowledge base creation completed. Content is publication-ready and meets all quality standards."
            if kb_notification:
                message_content = f"{kb_notification}\n\n{message_content}"
                
            response_message = self.create_message(
                recipient="UserProxy",
                message_type="workflow_complete",
                content=message_content,
                metadata={
                    "original_request": original_request,
                    "content_strategy": content_strategy,
                    "review_result": review_result,
                    "final_quality_assessment": review_result.get("quality_assessment", {}),
                    "publication_readiness": "approved",
                    "intent": "kb_creation_complete",
                    "kb_context_notification": kb_notification
                }
            )
            
            # Route to UserProxy to deliver final result
            state["current_agent"] = "UserProxy"
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(response_message)
        
        self.log("Content review completed")
        return state
    
    def _execute_content_review(self, original_request: str, content_strategy: Dict, 
                               creation_result: Dict, state: AgentState) -> Dict[str, Any]:
        """Execute comprehensive content review and quality assurance"""
        
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
            Conduct a comprehensive quality review of the knowledge base created for: {original_request}
            
            Content Strategy Used: {content_strategy}
            Creation Results: {creation_result}
            
            Your review should evaluate:
            1. Content quality and expert-level authority
            2. Comprehensive coverage of the domain
            3. Publication readiness and professional standards
            4. Knowledge base structure and organization
            5. Cross-references and content relationships
            6. Any gaps or areas needing improvement
            
            Use available tools to:
            - Analyze the complete knowledge base structure
            - Review individual articles for quality
            - Check for content gaps or missing coverage
            - Optimize organization and relationships
            - Ensure publication readiness
            
            Determine if the knowledge base meets publication standards or if revisions are needed.
            Provide specific feedback and recommendations for any improvements.
            """)
        ]
        
        try:
            response = self.llm_with_tools.invoke(messages)
            return self._process_review_response(response, state)
        except Exception as e:
            return {
                "error": f"Error during content review: {str(e)}",
                "needs_revision": False,
                "quality_assessment": {"status": "error"}
            }
    
    def _process_review_response(self, response, state: AgentState) -> Dict[str, Any]:
        """Process the LLM review response and determine next steps"""
        
        # Handle tool calls if present
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                try:
                    tool = next((t for t in self.tools if t.name == tool_call['name']), None)
                    if tool:
                        result = tool.run(tool_call['args'])
                        tool_results.append({
                            "tool": tool_call['name'],
                            "result": result
                        })
                except Exception as e:
                    tool_results.append({
                        "tool": tool_call['name'],
                        "error": str(e)
                    })
        
        # Extract review content
        review_content = response.content if hasattr(response, 'content') else str(response)
        
        # Analyze review to determine if revisions are needed
        needs_revision = self._analyze_revision_need(review_content)
        
        return {
            "needs_revision": needs_revision,
            "review_feedback": review_content,
            "quality_assessment": self._extract_quality_assessment(review_content),
            "revision_requirements": self._extract_revision_requirements(review_content) if needs_revision else {},
            "publication_readiness": "needs_revision" if needs_revision else "approved",
            "review_details": review_content
        }
    
    def _analyze_revision_need(self, review_content: str) -> bool:
        """Analyze review content to determine if revisions are needed"""
        revision_indicators = [
            "needs improvement",
            "requires revision",
            "gaps identified",
            "quality issues",
            "incomplete coverage",
            "not ready for publication",
            "revisions needed"
        ]
        
        content_lower = review_content.lower()
        return any(indicator in content_lower for indicator in revision_indicators)
    
    def _extract_quality_assessment(self, review_content: str) -> Dict[str, Any]:
        """Extract quality assessment from review content"""
        return {
            "overall_quality": "high" if "excellent" in review_content.lower() else "good",
            "publication_ready": not self._analyze_revision_need(review_content),
            "expert_level": "approved" if "expert" in review_content.lower() else "needs_validation",
            "comprehensive_coverage": "approved" if "comprehensive" in review_content.lower() else "needs_review",
            "review_summary": review_content
        }
    
    def _extract_revision_requirements(self, review_content: str) -> Dict[str, Any]:
        """Extract specific revision requirements from review content"""
        return {
            "priority": "high",
            "areas_for_improvement": self._identify_improvement_areas(review_content),
            "specific_requirements": review_content,
            "revision_scope": "targeted_improvements"
        }
    
    def _identify_improvement_areas(self, review_content: str) -> List[str]:
        """Identify specific areas that need improvement"""
        # Simple extraction - in practice, this would be more sophisticated
        areas = []
        if "depth" in review_content.lower():
            areas.append("content_depth")
        if "coverage" in review_content.lower():
            areas.append("topic_coverage")
        if "organization" in review_content.lower():
            areas.append("content_organization")
        if "quality" in review_content.lower():
            areas.append("writing_quality")
        
        return areas if areas else ["general_improvement"]
