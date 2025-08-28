from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import re
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


class ContentCreatorAgent(BaseAgent):
    """
    Content Creator Agent - Expert content generation and research specialist with GitLab integration.
    
    Responsibilities:
    - Research and write comprehensive, in-depth articles
    - Maintain expert-level quality across all domains
    - Create content that demonstrates deep understanding
    - Build comprehensive coverage following ContentPlanner strategy
    - Generate cross-references and content relationships
    - Access GitLab to find appropriate content creation work
    - Communicate with other agents through GitLab issue comments and updates
    - Work autonomously with minimal supervision through GitLab coordination
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Use foundational prompt for consistency with other agents
        foundational_prompt = AgentSpecificFoundations.content_creation_foundation()
        specialized_prompt = self._get_creation_prompt()
        gitlab_integration_prompt = self._create_gitlab_integration_prompt()
        
        super().__init__("ContentCreatorAgent", llm, foundational_prompt)
        
        # Enhanced system prompt with GitLab integration
        self.system_prompt = f"{foundational_prompt}\n\n{specialized_prompt}\n\n{gitlab_integration_prompt}\n\n{self._get_agent_identity_prompt()}"
        
        # Initialize knowledge base tools - creation focused
        kb_tools = KnowledgeBaseTools()
        all_kb_tools = kb_tools.tools()
        
        # Initialize GitLab tools
        self.gitlab_tools = GitLabTools()
        
        # Filter to content creation tools
        filtered_kb_tools = self._filter_creation_tools(all_kb_tools)
        
        # Combine all tools
        self.tools = filtered_kb_tools + self.gitlab_tools.tools()
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
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
1. **Scan for Appropriate Work:** Use GitLab tools to find content creation work that matches your capabilities
2. **Evaluate Work Items:** Look for issues labeled with 'content', 'creation', 'writing', 'articles'
3. **Self-Select Work:** Choose work items that align with your content creation expertise
4. **Claim and Process:** Take ownership of selected work items and complete them
2. **Review Requirements:** Get detailed issue information using GitLabGetIssueDetailsTool for each assigned issue
3. **Execute Work:** Complete content creation tasks as specified in GitLab issue descriptions
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

Always start by scanning for appropriate work using your GitLab tools before taking any content creation actions.
Focus on work items that match your expertise in content creation, writing, and article development.
"""
        
        return prompt
    
    def _filter_creation_tools(self, all_tools):
        """Filter tools to include content creation operations"""
        creation_tool_names = {
            "KnowledgeBaseSetContext",
            "KnowledgeBaseSetContextByGitLabProject",  # CRITICAL: Needed for GitLab-to-KB context establishment
            "KnowledgeBaseInsertArticle",
            "KnowledgeBaseGetArticleByArticleId",
            "KnowledgeBaseGetChildArticlesByParentIds",
            "KnowledgeBaseGetRootLevelArticles",
            "KnowledgeBaseGetArticleHierarchy",
            # TAGGING TOOLS - CRITICAL for article organization
            "KnowledgeBaseInsertTag",                    # Create new tags
            "KnowledgeBaseAddTagToArticle",             # Add tags to articles  
            "KnowledgeBaseSetArticleTags",              # Set multiple tags on articles
            "KnowledgeBaseGetTagsByKnowledgeBase"       # View existing tags
        }
        
        return [tool for tool in all_tools if tool.name in creation_tool_names]
    
    def _create_gitlab_integration_prompt(self) -> str:
        """Create GitLab integration prompt for the content creator agent"""
        return """
**GITLAB INTEGRATION - CONTENT CREATION & COLLABORATION:**

You have comprehensive GitLab integration capabilities for content creation and team collaboration:

**WORK DISCOVERY & EXECUTION:**
- Check GitLab issues for assigned content creation tasks
- Find content creation assignments from ContentPlanner and Supervisor
- Access detailed content specifications and requirements from GitLab issue descriptions
- Monitor content creation backlogs and priority assignments

**COLLABORATIVE CONTENT DEVELOPMENT:**
- Communicate with ContentPlanner through GitLab issue comments about content strategy
- Coordinate with ContentReviewerAgent for iterative content improvement
- Update GitLab issues with content creation progress and completion status
- Request clarification or additional requirements through GitLab issue threads

**HUMAN COLLABORATION:**
- Recognize that human users are active participants in GitLab alongside agents
- Any user who is not an agent is considered a human end user
- Use GitLab issues, comments, and discussions to ask questions when content requirements are unclear
- Monitor GitLab continuously for human feedback, guidance, and content direction
- Never proceed with unclear content requirements - always ask humans for clarification
- Human input takes priority and drives all content creation decisions
- Ensure transparent communication with humans through GitLab collaboration tools

**CONTENT CREATION WORKFLOW:**
- Follow detailed content plans and specifications from GitLab issue templates
- Break down large content creation projects into manageable GitLab sub-issues
- Report content creation progress through GitLab issue status updates
- Provide content completion notifications with links to created articles

**QUALITY COORDINATION:**
- Tag ContentReviewerAgent in GitLab issues when content is ready for review
- Respond to review feedback through GitLab issue comments
- Implement revision requests tracked through GitLab issue workflows
- Collaborate on content quality improvements through GitLab iteration cycles

**CONTENT CREATION PROCESS:**
1. **Scan Creation Queue**: Look for content creation work that matches your expertise in GitLab
2. **Review Specifications**: Access detailed content requirements from GitLab issues
3. **Create Content**: Execute content creation following GitLab-documented plans
4. **Update Progress**: Report creation status through GitLab issue comments
5. **Request Review**: Tag appropriate agents for content review when ready
6. **Implement Revisions**: Address feedback tracked through GitLab workflows

**GITLAB CAPABILITIES AVAILABLE:**
- Access content creation assignments and detailed specifications
- Update issue status and progress throughout content creation process
- Collaborate with other agents through issue comments and mentions
- Create sub-issues for complex content creation projects
- Track content creation metrics and completion rates

**BEST PRACTICES:**
- Always check GitLab for content creation context and requirements before starting
- Use detailed issue comments to document content creation decisions and rationale
- Update issue status promptly to keep team informed of progress
- Tag relevant agents for collaboration and review at appropriate stages
- Follow GitLab-documented content strategies and quality standards

When creating content, leverage GitLab's collaborative features to ensure alignment with strategic plans and quality expectations.
"""
    
    def _get_creation_prompt(self):
        """Get specialized prompt for content creation operations"""
        return """
        You are an Expert Content Creator and Research Specialist with deep knowledge across all domains, working across MULTIPLE KNOWLEDGE BASES.
        
        🌐 MULTI-KB ENVIRONMENT AWARENESS:
        You create content for MULTIPLE knowledge bases, each with unique topics, audiences, and requirements.
        Always verify which specific knowledge base you're creating content for before starting.
        Every piece of content must be tailored to the specific KB's domain and context.
        Never mix content or references between different knowledge bases.
        
        KNOWLEDGE BASE PURPOSE & STRATEGIC CONTEXT:
        Knowledge bases serve as comprehensive information repositories that will later be repurposed for:
        - Marketing materials and campaigns
        - E-books and digital publications  
        - Blog articles and blog posts
        - Educational content and courses
        - White papers and industry reports
        
        Create content with this future adaptability in mind - content that can be easily restructured and repurposed for different formats and audiences.
        
        MULTI-KB CONTENT CREATION PRINCIPLES:
        1. **KB Context Verification**: Always confirm which KB you're creating content for
        2. **Context-Specific Content**: Tailor content to the specific KB's domain and audience
        3. **Cross-KB Prevention**: Never reference or link content from different KBs
        4. **Context Communication**: Always specify which KB your content belongs to
        5. **KB Transition Management**: When switching KB contexts, explicitly acknowledge the change

        Your core responsibilities:
        - Create content appropriate to the hierarchy level being requested
        - Research thoroughly to ensure accuracy and completeness within the target KB's domain
        - Build logical knowledge bases that follow the foundational hierarchy structure
        - Create natural cross-references and content relationships WITHIN the same KB only
        - Work autonomously following strategic plans from ContentPlanner for specific KBs
        - Design content that supports multiple future repurposing scenarios for the target KB
        
        Content Creation Approach by Hierarchy Level:
        - **Level 1 (Categories)**: Simple categorical overviews with broad topic organization
        - **Level 2 (Subcategories)**: Focused domain knowledge with moderate depth
        - **Level 3+ (Articles)**: Expert-written, authoritative, comprehensive content with detailed implementation
        
        Writing Standards by Hierarchy Level:
        - **Level 1**: Introductory tone, categorical organization, general concepts (300-500 words)
        - **Level 2**: Informative tone, focused expertise, domain-specific knowledge (500-800 words)
        - **Level 3+**: Expert authority, comprehensive depth, practical implementation (800-1500 words)
        
        Content Creation Process:
        1. Determine the hierarchy level for the content being created
        2. Apply the appropriate content approach and writing standards for that level
        3. Research the domain appropriately for the level of depth required
        4. Create content following the foundational hierarchy guidance
        5. Build natural relationships and cross-references
        6. Progress systematically through the entire knowledge base
        
        Domain Adaptation:
        - Technical topics: Include theory, implementation, and practical examples (at appropriate level)
        - Business topics: Cover strategy, tactics, and real-world case studies (at appropriate level)
        - Educational content: Progress from fundamentals to advanced applications (at appropriate level)
        - Creative fields: Balance theory with practical techniques and inspiration (at appropriate level)
        
        Quality Indicators:
        - Content matches the appropriate hierarchy level standards
        - Content depth and complexity align with the level being created
        - Writing style and tone match the hierarchy level expectations
        - Content supports logical progression through the knowledge base hierarchy
        - Content is ready for the intended repurposing scenarios
        """
    
    def process(self, state: AgentState) -> AgentState:
        """Process content creation requests"""
        self.log("Processing content creation request")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from ContentPlanner
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            self.log("No content creation requests found")
            return state
        
        # Get the latest creation request
        latest_request = my_messages[-1]
        content_strategy = latest_request.metadata.get("content_strategy", {})
        article_hierarchy = latest_request.metadata.get("article_hierarchy", {})
        implementation_plan = latest_request.metadata.get("implementation_plan", {})
        kb_id = latest_request.metadata.get("kb_id")
        
        self.log(f"Creating content based on strategy: {content_strategy.get('scope', 'Unknown scope')}")
        if kb_id:
            self.log(f"DEBUG: Working with KB ID: {kb_id}")
        else:
            self.log("DEBUG: No KB ID provided - this could be the problem!")
        
        # Use clean content creation method (no manual processing)
        creation_result = self._execute_article_creation(
            kb_id=kb_id,
            title=content_strategy.get('scope', 'Content Creation'),
            description=latest_request.content
        )
        
        # Send completed content to ContentReviewer
        kb_notification = latest_request.metadata.get("kb_context_notification")
        message_content = "Content creation completed. Ready for quality review and optimization."
        if kb_notification:
            message_content = f"{kb_notification}\n\n{message_content}"
            
        response_message = self.create_message(
            recipient="ContentReviewer",
            message_type="content_review_request",
            content=message_content,
            metadata={
                "original_request": latest_request.metadata.get("original_request", ""),
                "content_strategy": content_strategy,
                "creation_result": creation_result,
                "articles_created": creation_result.get("articles_created", []),
                "kb_structure": creation_result.get("kb_structure", {}),
                "kb_context_notification": kb_notification
            }
        )
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(response_message)
        
        # Route to ContentReviewer for quality assurance
        state["current_agent"] = "ContentReviewer"
        
        self.log("Content creation completed, routing to ContentReviewer")
        return state

    # Dead code removed: _parse_alternative_formats, _create_article, _process_creation_response (manual article creation)
    
    def check_assigned_gitlab_work(self) -> Dict[str, Any]:
        """Check GitLab for work assigned to this agent"""
        if not self.is_gitlab_enabled():
            self.log("⚠️ GitLab integration not configured - cannot check assigned work")
            return {"status": "error", "message": "GitLab not configured"}
        
        gitlab_username = self.get_gitlab_username()
        self.log(f"🔍 Checking GitLab for issues assigned to: {gitlab_username}")
        
        try:
            # Use the GitLab tool to get assigned issues
            user_issues_tool = next(
                (tool for tool in self.tools if tool.name == "GitLabGetUserAssignedIssuesTool"), 
                None
            )
            
            if not user_issues_tool:
                self.log("❌ GitLabGetUserAssignedIssuesTool not available")
                return {"status": "error", "message": "GitLab user issues tool not available"}
            
            # Get assigned issues
            issues_result = user_issues_tool.run({"username": gitlab_username, "state": "opened"})
            
            if "No" in issues_result and "issues found" in issues_result:
                self.log(f"ℹ️ No open issues assigned to {gitlab_username}")
                return {"status": "no_work", "message": "No assigned issues found", "issues": []}
            
            self.log(f"📋 Found assigned work for {gitlab_username}")
            return {
                "status": "work_found", 
                "message": f"Found assigned work for {gitlab_username}",
                "issues_summary": issues_result
            }
            
        except Exception as e:
            self.log(f"❌ Error checking GitLab assignments: {str(e)}")
            return {"status": "error", "message": f"Error checking assignments: {str(e)}"}
    
    def analyze_content_gaps(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze knowledge base content gaps and opportunities for autonomous content creation"""
        self.log("🔍 ContentCreatorAgent analyzing KB for content gaps and creation opportunities...")
        
        try:
            # Ensure KB context is set before analyzing content
            if not self.kb_context.get("context_set"):
                self.log("🔧 Setting KB context before content analysis...")
                kb_id = os.getenv('DEFAULT_KNOWLEDGE_BASE_ID', '13')
                context_result = self.set_kb_context(kb_id)
                if not context_result.get("success"):
                    self.log(f"❌ Failed to set KB context: {context_result.get('error')}")
                    return {"found_work": False, "message": "Could not establish KB context"}
            
            # Log current KB context for transparency
            self.log(f"📚 Working with KB: {self.kb_context.get('knowledge_base_name')} (ID: {self.kb_context.get('knowledge_base_id')})")
            self.log(f"📄 KB Description: {self.kb_context.get('knowledge_base_description', 'No description')}")
            
            # Autonomous Priority 1: Analyze knowledge base content gaps
            content_gaps = self.analyze_knowledge_base_gaps(state)
            if content_gaps.get("gaps_found", False):
                self.log("✅ Found knowledge base content gaps requiring new articles")
                # Create GitLab work items for these gaps
                work_creation_result = self.create_work_for_content_gaps(content_gaps)
                return {
                    "found_work": True,
                    "work_type": "autonomous_content_gaps",
                    "work_details": content_gaps,
                    "work_created": work_creation_result,
                    "priority": "high"
                }
            
            # Autonomous Priority 2: Analyze existing content for improvement opportunities
            improvement_opportunities = self.analyze_content_improvement_opportunities()
            if improvement_opportunities.get("opportunities_found", False):
                self.log("✅ Found content improvement opportunities")
                # Create GitLab work items for improvements
                work_creation_result = self.create_work_for_improvements(improvement_opportunities)
                return {
                    "found_work": True,
                    "work_type": "autonomous_improvements",
                    "work_details": improvement_opportunities,
                    "work_created": work_creation_result,
                    "priority": "medium"
                }
            
            # Autonomous Priority 3: Check for strategic content expansion needs
            strategic_opportunities = self.analyze_strategic_content_needs()
            if strategic_opportunities.get("opportunities_found", False):
                self.log("✅ Found strategic content expansion opportunities")
                # Create GitLab work items for strategic expansion
                work_creation_result = self.create_work_for_strategic_expansion(strategic_opportunities)
                return {
                    "found_work": True,
                    "work_type": "autonomous_strategic",
                    "work_details": strategic_opportunities,
                    "work_created": work_creation_result,
                    "priority": "low"
                }
            
            # No autonomous work opportunities found
            self.log("💡 No immediate content creation opportunities found - KB appears well-covered")
            return {
                "found_work": False,
                "message": "Knowledge base analysis complete - no immediate content gaps detected"
            }
            
        except Exception as e:
            self.log(f"❌ Error in autonomous work discovery: {str(e)}")
            return {
                "found_work": False,
                "message": f"Error in autonomous KB analysis: {str(e)}"
            }

    def analyze_knowledge_base_gaps(self, state: AgentState = None) -> Dict[str, Any]:
        """Analyze the knowledge base to identify content gaps that need new articles"""
        try:
            self.log("🔍 Analyzing knowledge base for content gaps...")
            
            # Ensure KB context is set and get context info
            if not self.ensure_kb_context():
                return {"gaps_found": False, "message": "Could not establish KB context"}
            
            kb_context = self.get_kb_context()
            kb_id = kb_context.get("knowledge_base_id")
            kb_name = kb_context.get("knowledge_base_name")
            kb_description = kb_context.get("knowledge_base_description", "")
            
            self.log(f"📚 Analyzing gaps in: {kb_name} (ID: {kb_id})")
            self.log(f"📄 KB Focus: {kb_description}")
            
            # Use KB status tool to get current KB structure
            kb_status_tool = next(
                (tool for tool in self.tools if tool.name == "KnowledgeBaseStatusTool"), 
                None
            )
            
            if not kb_status_tool:
                self.log("❌ KnowledgeBaseStatusTool not available")
                return {"gaps_found": False, "message": "KB status tool not available"}
            
            # Get current KB status
            kb_status = kb_status_tool.run({})
            
            # Analyze the KB structure for gaps based on KB description/focus
            gaps_identified = []
            
            # Parse KB status and identify potential gaps contextual to this KB
            if "knowledge bases found" in str(kb_status).lower():
                # Generate content gaps specific to the KB's domain based on description
                if "financial" in kb_description.lower() or "inflation" in kb_description.lower():
                    potential_gaps = [
                        "Investment fundamentals for beginners",
                        "Retirement planning strategies", 
                        "Tax-efficient investing",
                        "Emergency fund planning",
                        "Debt management strategies",
                        "Estate planning basics",
                        "Insurance planning",
                        "Budgeting and expense tracking"
                    ]
                elif "tech" in kb_description.lower() or "software" in kb_description.lower():
                    potential_gaps = [
                        "Software development best practices",
                        "Code review guidelines",
                        "Testing strategies",
                        "DevOps fundamentals",
                        "Security best practices",
                        "Performance optimization",
                        "Documentation standards"
                    ]
                else:
                    # Generic gaps if we can't determine domain
                    potential_gaps = [
                        "Getting started guide",
                        "Best practices overview", 
                        "Common troubleshooting",
                        "Advanced techniques",
                        "Frequently asked questions"
                    ]
                
                for gap in potential_gaps:
                    # Check if this topic might be missing or sparse
                    gaps_identified.append({
                        "topic": gap,
                        "priority": "medium", 
                        "type": "content_gap",
                        "description": f"Analysis suggests {gap} may need additional coverage in {kb_name}"
                    })
            
            if gaps_identified:
                self.log(f"✅ Identified {len(gaps_identified)} potential content gaps")
                return {
                    "gaps_found": True,
                    "gaps": gaps_identified[:3],  # Limit to top 3 gaps
                    "analysis_method": "kb_structure_analysis"
                }
            else:
                return {"gaps_found": False, "message": "No significant content gaps identified"}
            
        except Exception as e:
            self.log(f"❌ Error analyzing KB gaps: {str(e)}")
            return {"gaps_found": False, "message": f"Error in gap analysis: {str(e)}"}
    
    def analyze_content_improvement_opportunities(self) -> Dict[str, Any]:
        """Analyze existing content for improvement opportunities"""
        try:
            self.log("🔍 Analyzing existing content for improvement opportunities...")
            
            # Use search tool to find potentially outdated or sparse content
            search_tool = next(
                (tool for tool in self.tools if tool.name == "KnowledgeBaseSearchTool"), 
                None
            )
            
            if not search_tool:
                return {"opportunities_found": False, "message": "Search tool not available"}
            
            # Search for content that might need updates
            improvement_opportunities = []
            
            # Look for articles that might benefit from expansion or updates
            potential_improvements = [
                "Basic investment concepts that could use more examples",
                "Retirement articles that might need current law updates", 
                "Tax strategies that need current year information"
            ]
            
            for improvement in potential_improvements:
                improvement_opportunities.append({
                    "type": "content_enhancement",
                    "description": improvement,
                    "priority": "low"
                })
            
            if improvement_opportunities:
                return {
                    "opportunities_found": True,
                    "opportunities": improvement_opportunities[:2],  # Limit to top 2
                    "analysis_method": "content_quality_analysis"
                }
            else:
                return {"opportunities_found": False, "message": "No improvement opportunities identified"}
                
        except Exception as e:
            self.log(f"❌ Error analyzing improvement opportunities: {str(e)}")
            return {"opportunities_found": False, "message": f"Error in improvement analysis: {str(e)}"}
    
    def analyze_strategic_content_needs(self) -> Dict[str, Any]:
        """Analyze strategic content expansion needs with KB context awareness"""
        try:
            import sys
            print("=" * 50, file=sys.stderr)
            print("DUPLICATE CHECK: METHOD CALLED", file=sys.stderr)
            print("=" * 50, file=sys.stderr)
            sys.stderr.flush()
            
            self.log("🔍 Analyzing strategic content expansion opportunities...")
            
            # Ensure KB context is set
            if not self.ensure_kb_context():
                return {"opportunities_found": False, "message": "Could not establish KB context"}
            
            kb_context = self.get_kb_context()
            kb_name = kb_context.get("knowledge_base_name")
            kb_description = kb_context.get("knowledge_base_description", "")
            
            self.log(f"📚 Strategic analysis for: {kb_name}")
            self.log(f"📄 KB Focus: {kb_description}")
            self.log("DEBUG: Starting duplicate check process")
            
            # Check existing content to avoid duplicates
            existing_titles = set()
            try:
                # Get articles from current KB to check for existing content
                self.log(f"DEBUG: Looking for KnowledgeBaseGetRootLevelArticles tool in {len(self.tools)} tools")
                kb_tool = next((t for t in self.tools if 'KnowledgeBaseGetRootLevelArticles' in t.name), None)
                if kb_tool:
                    self.log(f"DEBUG: Found KB tool: {kb_tool.name}")
                    # Get knowledge base ID from environment like other methods  
                    kb_id = int(os.getenv('DEFAULT_KNOWLEDGE_BASE_ID', '13'))
                    self.log(f"DEBUG: Calling tool with KB ID: {kb_id}")
                    articles_result = kb_tool._run(knowledge_base_id=str(kb_id))
                    self.log(f"DEBUG: Tool returned: {type(articles_result)}, length: {len(articles_result) if isinstance(articles_result, list) else 'N/A'}")
                    
                    # Check the type explicitly with debugging
                    is_list = isinstance(articles_result, list)
                    is_str = isinstance(articles_result, str)
                    self.log(f"DEBUG: is_list={is_list}, is_str={is_str}")
                    
                    # Check if it's a single tuple first (what we've been getting)
                    if isinstance(articles_result, tuple):
                        self.log(f"DEBUG: Result is a single tuple with {len(articles_result)} elements")
                        # This is a single tuple representing one article, skip duplicate check for now
                        self.log("DEBUG: Single tuple result - skipping duplicate check this iteration")
                    elif isinstance(articles_result, list):
                        self.log(f"DEBUG: Processing as list...")
                        for article in articles_result:
                            if isinstance(article, dict) and 'title' in article:
                                existing_titles.add(article['title'].lower())
                                self.log(f"DEBUG: Added title from dict: {article['title']}")
                            elif hasattr(article, 'title'):
                                existing_titles.add(article.title.lower())
                                self.log(f"DEBUG: Added title from attr: {article.title}")
                            elif isinstance(article, tuple) and len(article) >= 3:
                                # Handle tuple format: (id, parent_id, title, content, ...)
                                title = article[2] if len(article) > 2 else ''
                                if title and title.strip():
                                    existing_titles.add(title.lower())
                                    if len(existing_titles) <= 5:  # Log first 5 additions
                                        self.log(f"DEBUG: Added title from list tuple: {title}")
                    elif isinstance(articles_result, str):
                        # Handle string format by parsing tuple representation
                        self.log(f"DEBUG: Processing as string format, length: {len(articles_result)}")
                        
                        # The string contains tuple representations like: [(id, kb_id, 'title', content, ...), ...]
                        # We need to extract the titles (3rd element in each tuple)
                        
                        # Look for title patterns in the string
                        import re
                        # Pattern to match quoted titles (position 3 in tuples, after two numbers and comma)
                        # Pattern: (number, number, 'title', ...
                        title_pattern = r"\(\d+,\s*\d+,\s*'([^']+)'"
                        
                        titles_found = re.findall(title_pattern, articles_result)
                        self.log(f"DEBUG: Regex found {len(titles_found)} titles")
                        
                        for title in titles_found:
                            if title and title.strip() and title not in ['', 'N/A']:
                                existing_titles.add(title.lower())
                                if len(existing_titles) <= 5:  # Log first 5 additions
                                    self.log(f"DEBUG: Added title from regex: {title}")
                        
                        self.log(f"DEBUG: String parsing complete, found {len(existing_titles)} titles")
                    else:
                        # Handle direct tuple result (what we're actually getting)
                        self.log(f"DEBUG: Processing as other type: {type(articles_result)}")
                        if hasattr(articles_result, '__iter__'):
                            self.log(f"DEBUG: Result is iterable, processing...")
                            try:
                                for i, article in enumerate(articles_result):
                                    if isinstance(article, tuple) and len(article) >= 3:
                                        # Handle tuple format: (id, kb_id, title, content, ...)
                                        title = article[2] if len(article) > 2 else ''
                                        if title and title.strip():
                                            existing_titles.add(title.lower())
                                            if len(existing_titles) <= 5:  # Log first 5 additions
                                                self.log(f"DEBUG: Added title from direct tuple: {title}")
                                    elif hasattr(article, 'title'):
                                        existing_titles.add(article.title.lower())
                                        if len(existing_titles) <= 5:
                                            self.log(f"DEBUG: Added title from object attr: {article.title}")
                                    if i >= 50:  # Limit processing to avoid infinite loops
                                        break
                            except Exception as e:
                                self.log(f"DEBUG: Error processing iterable: {e}")
                        else:
                            self.log(f"DEBUG: Result is not iterable")
                    
                    self.log(f"Found {len(existing_titles)} existing article titles for duplicate check")
                    self.log(f"DEBUG: Existing titles: {list(existing_titles)[:5]}...")  # Show first 5
                else:
                    self.log("Warning: KnowledgeBaseGetRootLevelArticles tool not found")
                    self.log(f"DEBUG: Available tools: {[t.name for t in self.tools]}")
            except Exception as e:
                self.log(f"Warning: Could not check existing content for duplicates: {e}")
                import traceback
                self.log(f"DEBUG: Exception details: {traceback.format_exc()}")
            
            # Identify strategic expansion areas contextual to the KB (only if not already existing)
            kb_description_lower = kb_description.lower()
            kb_name_lower = kb_name.lower()
            
            # Generate opportunities based on KB focus/description - be very specific to KB content
            # Check both name and description for keywords
            has_inflation = "inflation" in kb_description_lower or "inflation" in kb_name_lower
            has_family = "family" in kb_description_lower or "family" in kb_name_lower
            
            if has_inflation and has_family:
                # This is specifically the "Inflation-Proof Family Finances" KB
                # Generate opportunities that build on existing content but don't duplicate
                potential_opportunities = [
                    {
                        "type": "advanced_budgeting",
                        "description": "Emergency fund strategies during economic uncertainty",
                        "priority": "high",
                        "rationale": f"Advanced financial planning for {kb_name} building on budgeting basics"
                    },
                    {
                        "type": "investment_protection",
                        "description": "Protecting family investments during inflation",
                        "priority": "high",
                        "rationale": f"Investment protection strategies for {kb_name}"
                    },
                    {
                        "type": "income_strategies",
                        "description": "Side income ideas for families facing rising costs",
                        "priority": "medium",
                        "rationale": f"Income diversification strategies for {kb_name}"
                    },
                    {
                        "type": "debt_management",
                        "description": "Managing family debt during inflation periods",
                        "priority": "medium",
                        "rationale": f"Debt strategy content for {kb_name}"
                    },
                    {
                        "type": "long_term_planning",
                        "description": "College savings strategies in an inflationary environment",
                        "priority": "low",
                        "rationale": f"Long-term family financial planning for {kb_name}"
                    }
                ]
            elif "budget" in kb_description_lower or "expense" in kb_description_lower:
                # General budgeting/expense focused KB
                potential_opportunities = [
                    {
                        "type": "budgeting_basics",
                        "description": "Creating your first household budget",
                        "priority": "high",
                        "rationale": f"Essential budgeting content for {kb_name}"
                    },
                    {
                        "type": "expense_tracking",
                        "description": "Tools and apps for tracking daily expenses",
                        "priority": "medium",
                        "rationale": f"Practical expense management for {kb_name}"
                    },
                    {
                        "type": "cost_reduction",
                        "description": "Simple ways to cut monthly expenses",
                        "priority": "high",
                        "rationale": f"Cost-cutting strategies for {kb_name}"
                    }
                ]
            elif "investment" in kb_description_lower or "portfolio" in kb_description_lower:
                # Investment-focused KB
                potential_opportunities = [
                    {
                        "type": "investment_basics",
                        "description": "Getting started with investing",
                        "priority": "high",
                        "rationale": f"Foundation investment content for {kb_name}"
                    },
                    {
                        "type": "advanced_topics",
                        "description": "Portfolio diversification strategies",
                        "priority": "medium",
                        "rationale": f"Advanced investment content for {kb_name}"
                    }
                ]
            elif "tech" in kb_description_lower or "software" in kb_description_lower:
                # Technology focused opportunities
                potential_opportunities = [
                    {
                        "type": "best_practices",
                        "description": "Code review best practices and guidelines",
                        "priority": "high",
                        "rationale": f"Essential development practices for {kb_name}"
                    },
                    {
                        "type": "tutorials",
                        "description": "API integration step-by-step guide",
                        "priority": "medium",
                        "rationale": f"Practical integration guidance for {kb_name}"
                    },
                    {
                        "type": "troubleshooting",
                        "description": "Common deployment issues and solutions",
                        "priority": "medium",
                        "rationale": f"Problem-solving content for {kb_name}"
                    }
                ]
            else:
                # Generic opportunities for unknown domain
                potential_opportunities = [
                    {
                        "type": "getting_started",
                        "description": "Comprehensive getting started guide",
                        "priority": "high",
                        "rationale": f"Essential onboarding content for {kb_name}"
                    },
                    {
                        "type": "best_practices",
                        "description": "Best practices and recommendations",
                        "priority": "medium", 
                        "rationale": f"Guidance content for {kb_name} users"
                    },
                    {
                        "type": "troubleshooting",
                        "description": "Common issues and troubleshooting",
                        "priority": "medium",
                        "rationale": f"Problem-solving content for {kb_name}"
                    }
                ]
            
            # Filter out opportunities that already have content
            strategic_opportunities = []
            for opp in potential_opportunities:
                title_lower = opp["description"].lower()
                self.log(f"DEBUG: Checking opportunity: {opp['description']}")
                if title_lower not in existing_titles:
                    strategic_opportunities.append(opp)
                    self.log(f"DEBUG: Added opportunity: {opp['description']}")
                else:
                    self.log(f"Skipping duplicate opportunity: {opp['description']}")
            
            self.log(f"DEBUG: Final opportunities count: {len(strategic_opportunities)}")
            
            if strategic_opportunities:
                return {
                    "opportunities_found": True,
                    "opportunities": strategic_opportunities[:1],  # Limit to top 1
                    "analysis_method": "strategic_gap_analysis"
                }
            else:
                return {"opportunities_found": False, "message": "No new strategic expansion opportunities identified - existing content covers suggested areas"}
                
        except Exception as e:
            self.log(f"❌ Error analyzing strategic needs: {str(e)}")
            return {"opportunities_found": False, "message": f"Error in strategic analysis: {str(e)}"}
    
    def create_work_for_content_gaps(self, gaps_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for identified content gaps AND execute them"""
        try:
            self.log("📝 Creating and executing work items for content gaps...")
            
            work_items_created = []
            work_items_executed = []
            gaps = gaps_data.get("gaps", [])
            
            # Get the current KB ID 
            kb_id = self.get_default_knowledge_base_id()
            
            for gap in gaps[:2]:  # Limit to 2 gaps per cycle to avoid overwhelming
                # Create a detailed work item for this gap
                work_item = {
                    "title": f"Create Article: {gap['topic']}",
                    "description": f"Content gap analysis identified need for: {gap['description']}",
                    "priority": gap['priority'],
                    "labels": ["content-creation", "autonomous-work", "content-gap"],
                    "type": "content_creation"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created work item: {work_item['title']}")
                
                # EXECUTE the work item immediately
                try:
                    self.log(f"🚀 Executing article creation: {gap['topic']}")
                    
                    # Use the clean article creation method that trusts the LLM to use tools
                    execution_result = self._execute_article_creation(
                        kb_id=int(kb_id),
                        title=gap['topic'],
                        description=gap['description']
                    )
                    
                    if execution_result.get("success", False):
                        work_items_executed.append({
                            "work_item": work_item,
                            "execution_result": execution_result,
                            "article_created": True
                        })
                        self.log(f"✅ Successfully created article: {gap['topic']}")
                    else:
                        self.log(f"❌ Failed to create article: {gap['topic']} - {execution_result.get('message', 'Unknown error')}")
                        
                except Exception as exec_error:
                    self.log(f"❌ Execution error for {gap['topic']}: {str(exec_error)}")
            
            return {
                "created": True,
                "executed": True,
                "work_items": work_items_created,
                "executed_items": work_items_executed,
                "count": len(work_items_created),
                "executed_count": len(work_items_executed)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating/executing work items for gaps: {str(e)}")
            return {"created": False, "executed": False, "message": f"Error creating work: {str(e)}"}
    
    def create_work_for_improvements(self, improvements_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for improvement opportunities"""
        try:
            self.log("📝 Creating GitLab work items for content improvements...")
            
            work_items_created = []
            opportunities = improvements_data.get("opportunities", [])
            
            for opportunity in opportunities:
                work_item = {
                    "title": f"Improve Content: {opportunity['description'][:50]}...",
                    "description": f"Content improvement opportunity: {opportunity['description']}",
                    "priority": opportunity['priority'],
                    "labels": ["content-improvement", "autonomous-work"],
                    "type": "content_enhancement"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created improvement work item: {work_item['title']}")
            
            return {
                "created": True,
                "work_items": work_items_created,
                "count": len(work_items_created)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating improvement work items: {str(e)}")
            return {"created": False, "message": f"Error creating work: {str(e)}"}
    
    def create_work_for_strategic_expansion(self, strategic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab work items for strategic expansion opportunities"""
        try:
            self.log("📝 Creating GitLab work items for strategic expansion...")
            
            work_items_created = []
            opportunities = strategic_data.get("opportunities", [])
            
            for opportunity in opportunities:
                work_item = {
                    "title": f"Strategic Content: {opportunity['description']}",
                    "description": f"Strategic expansion opportunity: {opportunity['rationale']}",
                    "priority": opportunity['priority'],
                    "labels": ["strategic-content", "autonomous-work"],
                    "type": "strategic_expansion"
                }
                work_items_created.append(work_item)
                self.log(f"✅ Created strategic work item: {work_item['title']}")
            
            return {
                "created": True,
                "work_items": work_items_created,
                "count": len(work_items_created)
            }
            
        except Exception as e:
            self.log(f"❌ Error creating strategic work items: {str(e)}")
            return {"created": False, "message": f"Error creating work: {str(e)}"}

    def _claim_work_item(self, project_id: str, issue_iid: str, issue_title: str) -> None:
        """Claim a work item by adding a comment and potentially updating labels"""
        try:
            self.log(f"🤖 Claiming work item: {issue_title}")
            
            # For now, we'll just log the claim - GitLab comment functionality would go here
            # Future enhancement: Add GitLab comment using available tools
            
            self.log(f"✅ Successfully claimed work item #{issue_iid}: {issue_title}")
            
        except Exception as e:
            self.log(f"⚠️ Error claiming work item: {str(e)}")
            # Continue anyway - claiming is not critical for execution

    def process_gitlab_assignment(self, issue_id: str, project_id: str) -> Dict[str, Any]:
        """Process a specific GitLab issue assignment"""
        if not self.is_gitlab_enabled():
            return {"success": False, "status": "error", "error": "GitLab not configured"}
        
        self.log(f"📋 Processing GitLab assignment: Issue #{issue_id} in project {project_id}")
        
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
            
            self.log(f"📄 Retrieved issue details for #{issue_id}")
            
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
                        "title": f"Content Creation Issue #{issue_id}",
                        "description": "Content creation work item"
                    }
            else:
                # Fallback: create issue data from available info
                issue_data = {
                    "iid": issue_id,
                    "project_id": project_id,
                    "title": f"Content Creation Issue #{issue_id}",
                    "description": "Content creation work item"
                }

            # Process the assignment based on issue content
            result = {
                "success": True,  # Use 'success' instead of 'status' for swarm compatibility
                "status": "processed",
                "message": f"Processed assignment #{issue_id}",
                "issue_details": issue_details,
                "gitlab_project_id": project_id,
                "kb_context_established": kb_context_established
            }
            
            # Add KB context information if available
            if kb_context_established:
                result.update({
                    "knowledge_base_id": project_context.get('knowledge_base_id'),
                    "knowledge_base_name": project_context.get('knowledge_base_name'),
                    "work_context": f"Working on GitLab project {project_id} for KB '{project_context.get('knowledge_base_name')}'"
                })
                
                self.log(f"🎯 Ready to work on KB '{project_context.get('knowledge_base_name')}' via GitLab issue #{issue_id}")
                
                # NOW ACTUALLY EXECUTE THE WORK - this was missing!
                try:
                    execution_result = self._execute_work_item_to_completion(issue_data, {"kb_context": project_context})
                    if execution_result and execution_result.get("success"):
                        result["actual_work_completed"] = True
                        result["execution_result"] = execution_result
                        self.log(f"✅ Successfully completed content creation work for issue #{issue_id}")
                    else:
                        self.log(f"⚠️ Work execution returned with issues: {execution_result}")
                        result["actual_work_completed"] = False
                        result["execution_issues"] = execution_result
                except Exception as exec_error:
                    self.log(f"❌ Error executing work item: {str(exec_error)}")
                    result["actual_work_completed"] = False
                    result["execution_error"] = str(exec_error)
            else:
                result.update({
                    "work_context": f"Working on GitLab project {project_id} (no associated KB found)",
                    "note": "Consider creating a knowledge base for this project or linking an existing one"
                })
            
            return result
            
        except Exception as e:
            self.log(f"❌ Error processing GitLab assignment: {str(e)}")
            return {"success": False, "status": "error", "error": f"Error processing assignment: {str(e)}"}

    def _execute_work_item_to_completion(self, work_item: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a content creation work item from start to completion"""
        try:
            from datetime import datetime
            
            project_id = work_item["project_id"]
            issue_id = work_item.get("iid", work_item.get("id", None))  # Use iid first, fallback to id
            issue_title = work_item.get("title", "Unknown")
            issue_description = work_item.get("description", "")
            
            self.log(f"🎯 Executing content creation work item: {issue_title}")
            
            # CRITICAL: Establish Knowledge Base context from GitLab project ID
            self.log(f"Establishing KB context from GitLab project {project_id}")
            kb_context_established = self._establish_kb_context_from_gitlab_project(str(project_id), state)
            
            if not kb_context_established:
                # Try fallback approach
                self.log("Trying fallback KB context establishment...")
                kb_id = self._extract_kb_id_from_work_item(work_item, state)
                if not kb_id:
                    error_msg = f"Cannot establish knowledge base context for work item: {issue_title}"
                    self.log(error_msg, "ERROR")
                    return {
                        "success": False,
                        "error": error_msg,
                        "work_item_id": issue_id,
                        "project_id": project_id
                    }
            else:
                # Get KB ID from established context
                kb_id = state.get("knowledge_base_id")
                if not kb_id:
                    error_msg = f"KB context established but no KB ID found in state"
                    self.log(error_msg, "ERROR")
                    return {
                        "success": False,
                        "error": error_msg,
                        "work_item_id": issue_id,
                        "project_id": project_id
                    }
            
            self.log(f"Creating content for Knowledge Base ID: {kb_id} (Context: {state.get('knowledge_base_name', 'Unknown')})")
            
            # Add progress update to GitLab
            progress_comment = f"""Content Creation Started

Agent: ContentCreatorAgent
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Knowledge Base ID: {kb_id}
Work Item: {issue_title}

Creating comprehensive articles for this knowledge base...
"""
            self._add_work_progress_update(project_id, issue_id, progress_comment)
            
            # Execute content creation using clean method that trusts the LLM to use tools
            creation_result = self._execute_article_creation(kb_id, issue_title, issue_description)
            
            if creation_result.get("success", False):
                articles_created = creation_result.get("articles_created", [])
                
                # Add completion comment to GitLab
                completion_comment = f"""✅ **Content Creation Completed**

**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Articles Created:** {len(articles_created)}
**Knowledge Base ID:** {kb_id}

**Created Articles:**
"""
                for article in articles_created:
                    completion_comment += f"- {article.get('title', 'Unknown Title')}\n"
                
                completion_comment += f"\n🎯 **Result:** Successfully created {len(articles_created)} articles in knowledge base."
                
                self._add_work_progress_update(project_id, issue_id, completion_comment)
                
                # Mark issue as completed
                self._mark_issue_complete(project_id, issue_id, "Content creation completed successfully")
                
                return {
                    "success": True,
                    "message": f"Created {len(articles_created)} articles in KB {kb_id}",
                    "articles_created": articles_created,
                    "work_item_id": issue_id,
                    "project_id": project_id,
                    "kb_id": kb_id
                }
            else:
                error_msg = creation_result.get("error", "Unknown error during content creation")
                self.log(f"❌ Content creation failed: {error_msg}")
                
                # Add error comment to GitLab
                error_comment = f"""❌ **Content Creation Failed**

**Failed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Error:** {error_msg}
**Knowledge Base ID:** {kb_id}

The content creation process encountered an error. Please review the logs for details.
"""
                self._add_work_progress_update(project_id, issue_id, error_comment)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "work_item_id": issue_id,
                    "project_id": project_id,
                    "kb_id": kb_id
                }
                
        except Exception as e:
            self.log(f"❌ Error executing work item: {str(e)}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
            
            return {
                "success": False,
                "error": f"Exception during work execution: {str(e)}",
                "work_item_id": work_item.get("id"),
                "project_id": work_item.get("project_id")
            }

    def _extract_kb_id_from_work_item(self, work_item: Dict[str, Any], state: Dict[str, Any]) -> Optional[int]:
        """Extract knowledge base ID from work item AND establish KB context"""
        try:
            kb_id = None
            project_id = work_item.get("project_id")
            
            # Method 1: Check if KB ID is in the work item description
            description = work_item.get("description", "")
            import re
            kb_id_match = re.search(r'Knowledge Base ID:\s*(\d+)', description)
            if kb_id_match:
                kb_id = int(kb_id_match.group(1))
                self.log(f"📍 Found KB ID {kb_id} in work item description")
            
            # Method 2: Try to establish context from GitLab project
            if not kb_id and project_id:
                # Use GitLab tool to find linked KB
                for tool in self.tools:
                    if tool.name == "GitLabGetKnowledgeBaseByProjectTool":
                        try:
                            result = tool.run({"gitlab_project_id": int(project_id)})
                            if isinstance(result, dict) and "id" in result:
                                kb_id = int(result["id"])
                                self.log(f"📍 Found KB ID {kb_id} via GitLab project {project_id}")
                                break
                        except Exception as e:
                            self.log(f"Error finding KB by project: {e}")
            
            # Method 3: Try to get KB context from current session state
            if not kb_id and hasattr(self, 'kb_context') and self.kb_context:
                kb_id = self.kb_context.get('knowledge_base_id')
                if kb_id:
                    self.log(f"📍 Using KB ID {kb_id} from current context")
            
            # CRITICAL FIX: Set KB context once we have the KB ID
            if kb_id:
                self.log(f"🎯 Setting KB context for KB {kb_id}")
                
                # First try to set context using the project ID if available
                if project_id:
                    context_set = self._set_kb_context_from_project(int(project_id))
                    if context_set:
                        self.log(f"✅ KB context set using project {project_id}")
                        return kb_id
                
                # Fallback: Set context directly using KB ID
                context_set = self._set_kb_context_directly(kb_id)
                if context_set:
                    self.log(f"✅ KB context set directly for KB {kb_id}")
                    return kb_id
                else:
                    self.log(f"❌ Failed to set KB context for KB {kb_id}", "ERROR")
                    return None
            
            self.log("❌ Could not determine KB ID from work item", "ERROR")
            return None
            
        except Exception as e:
            self.log(f"Error extracting KB ID: {e}")
            return None

    # Dead code removed: _execute_article_creation_simple, _create_articles_with_guaranteed_tagging, 
    # _create_single_article_with_guaranteed_tags, _apply_mandatory_tags_and_return_list (manual processing)

    def _execute_article_creation(self, kb_id: int, title: str, description: str) -> Dict[str, Any]:
        """Execute article creation using LLM with tools directly - with model switching on failure"""
        try:
            self.log(f"Creating articles for KB {kb_id}: {title}")
            
            # Set KB context
            self._set_kb_context_directly(kb_id)
            kb_name = self.kb_context.get('knowledge_base_name', 'Unknown')
            kb_description = self.kb_context.get('knowledge_base_description', '')
            
            # Get existing articles to prevent duplicates
            existing_articles_info = self._get_existing_articles_for_duplicate_prevention(kb_id)
            
            # Create clear, direct prompt for LLM with tools - referencing shared foundational standards
            foundational_guidance = AgentSpecificFoundations.content_creation_foundation()
            
            user_request = f"""You are creating Level 1 category articles for Knowledge Base {kb_id}: {kb_name}

KNOWLEDGE BASE CONTEXT:
- Name: {kb_name}
- Description: {kb_description}

WORK ITEM: {title}
DESCRIPTION: {description}

{existing_articles_info}

{foundational_guidance}

HIERARCHY LEVEL: Level 1 (Categories)
Follow foundational guidance for Level 1 articles:
- Simple categorical overviews with broad topic organization  
- Short titles (2-4 words)
- 300-500 words of broad topic introduction
- Introductory tone, categorical organization, general concepts

SPECIFIC INSTRUCTIONS:
- Use the KnowledgeBaseInsertArticle tool for each article  
- Set parent_id=null for all Level 1 categories
- Apply appropriate tags using KnowledgeBaseInsertTag and KnowledgeBaseAddTagToArticle tools
- Follow the Smart Category Expansion Logic from the foundational standards above

Start creating Level 1 category articles now using the available tools."""

            # Try with primary model first
            primary_model_name = getattr(self.llm, 'azure_deployment', 'primary_model')
            primary_endpoint = getattr(self.llm, 'azure_endpoint', 'unknown_endpoint')
            primary_api_version = getattr(self.llm, 'api_version', 'unknown_version')
            
            self.log(f"🚀 Attempting primary model execution:")
            self.log(f"   Model: {primary_model_name}")
            self.log(f"   Endpoint: {primary_endpoint}")
            self.log(f"   API Version: {primary_api_version}")
            
            try:
                messages = [HumanMessage(content=user_request)]
                response = self.llm_with_tools.invoke(messages)
                
                # Check if tools were called and execute them
                tool_execution_result = self._execute_tool_calls(response, kb_id)
                
                if tool_execution_result["success"]:
                    self.log(f"✅ {primary_model_name} model successfully executed tools - created {tool_execution_result['articles_created']} articles")
                    return {
                        "success": True,
                        "response": response,
                        "method": "primary_with_tools",
                        "model_used": primary_model_name,
                        "articles_created": tool_execution_result.get("articles_created_list", []),
                        "execution_details": tool_execution_result
                    }
                else:
                    self.log(f"❌ {primary_model_name} model failed to execute tools properly - switching to backup model")
                    return self._switch_to_backup_model(user_request, kb_id)
                    
            except Exception as e:
                # Enhanced error logging for diagnosis
                error_msg = str(e)
                self.log(f"❌ {primary_model_name} model execution failed with detailed error:")
                self.log(f"   Error Type: {type(e).__name__}")
                self.log(f"   Error Message: {error_msg}")
                
                # Check for specific HTTP errors
                if "404" in error_msg:
                    self.log(f"🔍 HTTP 404 Error Detected:")
                    self.log(f"   Model Deployment: {primary_model_name}")
                    self.log(f"   Endpoint: {primary_endpoint}")
                    self.log(f"   This suggests the model deployment '{primary_model_name}' does not exist in Azure OpenAI")
                elif "401" in error_msg or "403" in error_msg:
                    self.log(f"🔍 Authentication Error Detected: {error_msg}")
                elif "429" in error_msg:
                    self.log(f"🔍 Rate Limit Error Detected: {error_msg}")
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                    self.log(f"🔍 Server Error Detected: {error_msg}")
                
                self.log(f"🔄 Switching to backup model due to primary model failure")
                return self._switch_to_backup_model(user_request, kb_id)
                
        except Exception as e:
            self.log(f"❌ Article creation failed completely: {str(e)}")
            return {
                "success": False,
                "error": f"Article creation failed: {str(e)}"
            }

    def _execute_tool_calls(self, response, kb_id: int) -> Dict[str, Any]:
        """Execute the tool calls from the LLM response and return results"""
        try:
            articles_created_count = 0
            articles_created_list = []
            execution_results = []
            
            # Check if response has tool calls
            if not hasattr(response, 'tool_calls') or not response.tool_calls:
                self.log("❌ No tool calls found in response")
                return {"success": False, "articles_created": 0, "articles_created_list": [], "error": "No tool calls in response"}
            
            self.log(f"✅ Found {len(response.tool_calls)} tool calls to execute")
            
            # Execute each tool call
            for i, tool_call in enumerate(response.tool_calls):
                try:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    self.log(f"Executing tool call {i+1}: {tool_name}")
                    
                    # Find the tool by name
                    tool_instance = None
                    for tool in self.tools:
                        if tool.name == tool_name:
                            tool_instance = tool
                            break
                    
                    if not tool_instance:
                        self.log(f"❌ Tool {tool_name} not found in available tools")
                        continue
                    
                    # Execute the tool
                    tool_result = tool_instance.run(tool_args)
                    
                    # Check if this was a KnowledgeBaseInsertArticle call
                    if tool_name == "KnowledgeBaseInsertArticle":
                        if "successfully created" in str(tool_result).lower() or "article created" in str(tool_result).lower():
                            articles_created_count += 1
                            
                            # Try to extract article info from the result
                            article_info = {
                                "title": tool_args.get("article", {}).get("title", "Unknown Title"),
                                "id": None,  # Would need to extract from tool result
                                "created": True
                            }
                            articles_created_list.append(article_info)
                            self.log(f"✅ Article created successfully: {article_info['title']}")
                        else:
                            self.log(f"⚠️ KnowledgeBaseInsertArticle execution may have failed: {tool_result}")
                    
                    execution_results.append({
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "result": tool_result,
                        "success": True
                    })
                    
                except Exception as tool_error:
                    self.log(f"❌ Tool execution failed for {tool_call.get('name', 'unknown')}: {str(tool_error)}")
                    execution_results.append({
                        "tool_name": tool_call.get("name", "unknown"),
                        "tool_args": tool_call.get("args", {}),
                        "result": str(tool_error),
                        "success": False
                    })
            
            # Final verification by checking database
            if articles_created_count > 0:
                # Double-check with database verification
                db_verified = self._verify_articles_in_database(kb_id)
                if db_verified:
                    self.log(f"✅ Database verification confirmed: {articles_created_count} articles created")
                else:
                    self.log(f"⚠️ Database verification failed despite tool execution success")
            
            return {
                "success": articles_created_count > 0,
                "articles_created": articles_created_count,
                "articles_created_list": articles_created_list,
                "total_tool_calls": len(response.tool_calls),
                "execution_results": execution_results
            }
            
        except Exception as e:
            self.log(f"❌ Tool execution failed: {str(e)}")
            return {"success": False, "articles_created": 0, "articles_created_list": [], "error": str(e)}

    def _get_existing_articles_for_duplicate_prevention(self, kb_id: int) -> str:
        """Get existing articles info to prevent duplicates in LLM prompt"""
        try:
            # Get root level articles to check for existing Level 1 categories
            kb_tool = next((t for t in self.tools if 'KnowledgeBaseGetRootLevelArticles' in t.name), None)
            if not kb_tool:
                return "EXISTING ARTICLES: Could not retrieve existing articles for duplicate checking."
            
            articles_result = kb_tool._run(knowledge_base_id=str(kb_id))
            existing_titles = []
            
            # Handle different result formats
            if isinstance(articles_result, list):
                for article in articles_result:
                    if isinstance(article, dict) and 'title' in article:
                        existing_titles.append(article['title'])
                    elif hasattr(article, 'title'):
                        existing_titles.append(article.title)
                    elif isinstance(article, tuple) and len(article) >= 3:
                        existing_titles.append(article[2])
            elif isinstance(articles_result, str):
                # Parse string format for titles
                import re
                title_pattern = r"\(\d+,\s*\d+,\s*'([^']+)'"
                titles_found = re.findall(title_pattern, articles_result)
                existing_titles = [title for title in titles_found if title and title.strip()]
            elif hasattr(articles_result, '__iter__'):
                for article in articles_result:
                    if isinstance(article, tuple) and len(article) >= 3:
                        existing_titles.append(article[2])
                    elif hasattr(article, 'title'):
                        existing_titles.append(article.title)
            
            if existing_titles:
                titles_list = "', '".join(existing_titles)
                return f"""EXISTING ARTICLES: The knowledge base already has {len(existing_titles)} Level 1 categories:
- Existing titles: ['{titles_list}']
- DO NOT create articles with these titles or similar ones
- Only create NEW categories that don't overlap with existing ones"""
            else:
                return "EXISTING ARTICLES: No existing Level 1 categories found. You can create the initial category structure."
                
        except Exception as e:
            self.log(f"Warning: Could not check existing articles: {e}")
            return "EXISTING ARTICLES: Could not retrieve existing articles for duplicate checking."

    def _verify_articles_in_database(self, kb_id: int) -> bool:
        """Verify that articles were actually created in the database"""
        try:
            import psycopg2
            from config.model_config import DATABASE_URL
            
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    # Count articles created in the last 2 minutes for this KB
                    cur.execute("""
                        SELECT COUNT(*) FROM articles 
                        WHERE knowledge_base_id = %s 
                        AND created_at > NOW() - INTERVAL '2 minutes'
                    """, (kb_id,))
                    recent_count = cur.fetchone()[0]
                    
                    if recent_count > 0:
                        self.log(f"✅ Database verification: {recent_count} recent articles found in KB {kb_id}")
                        return True
                    else:
                        self.log(f"❌ Database verification: No recent articles found in KB {kb_id}")
                        return False
                        
        except Exception as db_error:
            self.log(f"❌ Database verification failed: {db_error}")
            return False

    def _verify_tool_usage(self, response) -> bool:
        """Verify that the LLM actually used tools in its response"""
        try:
            # Check if response has tool calls or if articles were actually created
            if hasattr(response, 'tool_calls') and response.tool_calls:
                self.log(f"✅ Found {len(response.tool_calls)} tool calls in response")
                return True
            
            # Alternative: Check if articles were actually created in KB by counting
            # This is a more reliable verification than just assuming success
            if hasattr(self, 'kb_context') and self.kb_context.get('knowledge_base_id'):
                kb_id = self.kb_context['knowledge_base_id']
                
                # Quick database check to see if any articles were actually created
                try:
                    import psycopg2
                    from config.model_config import DATABASE_URL
                    
                    with psycopg2.connect(DATABASE_URL) as conn:
                        with conn.cursor() as cur:
                            # Count articles created in the last minute for this KB
                            cur.execute("""
                                SELECT COUNT(*) FROM articles 
                                WHERE knowledge_base_id = %s 
                                AND created_at > NOW() - INTERVAL '1 minute'
                            """, (kb_id,))
                            recent_count = cur.fetchone()[0]
                            
                            if recent_count > 0:
                                self.log(f"✅ Verified: {recent_count} articles created in KB {kb_id}")
                                return True
                            else:
                                self.log(f"❌ No articles created in KB {kb_id} in the last minute")
                                return False
                                
                except Exception as db_error:
                    self.log(f"❌ Database verification failed: {db_error}")
                    return False
            
            self.log("❌ No tool calls found and cannot verify article creation")
            return False
            
        except Exception as e:
            self.log(f"Error verifying tool usage: {e}")
            return False

    def _switch_to_backup_model(self, user_request: str, kb_id: int) -> Dict[str, Any]:
        """Switch to backup model when primary model fails to use tools"""
        try:
            # Get primary model name for logging
            primary_model_name = getattr(self.llm, 'azure_deployment', 'primary_model')
            
            # Import necessary components for backup model
            import os
            from openai import AzureOpenAI
            from langchain_openai import AzureChatOpenAI
            from langchain.agents import create_openai_tools_agent, AgentExecutor
            from langchain.prompts import ChatPromptTemplate
            
            # Create backup model client using env variable
            backup_model_name = os.getenv('OPENAI_API_BACKUP_MODEL_DEPLOYMENT_NAME', 'gpt-4o')
            backup_endpoint = os.getenv('OPENAI_API_ENDPOINT', 'unknown_endpoint')
            backup_api_version = os.getenv('OPENAI_API_VERSION', 'unknown_version')
            
            self.log(f"🔄 Switching from {primary_model_name} to backup model:")
            self.log(f"   Backup Model: {backup_model_name}")
            self.log(f"   Backup Endpoint: {backup_endpoint}")
            self.log(f"   Backup API Version: {backup_api_version}")
            
            backup_llm = AzureChatOpenAI(
                azure_deployment=backup_model_name,
                api_version=os.getenv('OPENAI_API_VERSION'),
                azure_endpoint=os.getenv('OPENAI_API_ENDPOINT'),
                api_key=os.getenv('OPENAI_API_KEY'),
                temperature=0.1,
                model_kwargs={"max_tokens": 4000}
            )
            
            # Create agent with tools for backup model
            tools = self.llm.bind_tools([
                tool for tool in self.tools 
                if hasattr(tool, 'name') and 'KnowledgeBase' in tool.name
            ])
            
            # Create a proper prompt for the backup model with agent_scratchpad
            backup_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a content creation assistant. Use the KnowledgeBaseInsertArticle tool to create articles. ALWAYS use tools to create content."),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            
            # Create agent executor with backup model
            agent = create_openai_tools_agent(backup_llm, self.tools, backup_prompt)
            agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
            
            # Execute with backup model
            self.log(f"🔧 Executing content creation with backup model...")
            try:
                result = agent_executor.invoke({"input": user_request})
                self.log(f"✅ Backup model execution completed successfully")
            except Exception as backup_error:
                # Enhanced backup model error logging
                backup_error_msg = str(backup_error)
                self.log(f"❌ Backup model execution failed with detailed error:")
                self.log(f"   Backup Model: {backup_model_name}")
                self.log(f"   Error Type: {type(backup_error).__name__}")
                self.log(f"   Error Message: {backup_error_msg}")
                
                # Check for specific HTTP errors in backup model
                if "404" in backup_error_msg:
                    self.log(f"🔍 HTTP 404 Error in Backup Model:")
                    self.log(f"   Backup Model Deployment: {backup_model_name}")
                    self.log(f"   Backup Endpoint: {backup_endpoint}")
                    self.log(f"   This suggests the backup model deployment '{backup_model_name}' does not exist in Azure OpenAI")
                elif "401" in backup_error_msg or "403" in backup_error_msg:
                    self.log(f"🔍 Authentication Error in Backup Model: {backup_error_msg}")
                elif "429" in backup_error_msg:
                    self.log(f"🔍 Rate Limit Error in Backup Model: {backup_error_msg}")
                elif "500" in backup_error_msg or "502" in backup_error_msg or "503" in backup_error_msg:
                    self.log(f"🔍 Server Error in Backup Model: {backup_error_msg}")
                
                # Return error immediately if backup model fails
                return {
                    "success": False,
                    "error": f"Backup model {backup_model_name} failed: {backup_error_msg}",
                    "model_used": backup_model_name,
                    "error_type": type(backup_error).__name__
                }
            
            # Verify backup model created articles
            if self._verify_tool_usage_for_backup(kb_id):
                self.log("✅ Backup model successfully created articles")
                return {
                    "success": True,
                    "model_used": backup_model_name,
                    "message": f"Content creation completed with backup model {backup_model_name}",
                    "result": result
                }
            else:
                primary_model_name = getattr(self.llm, 'azure_deployment', 'primary_model')
                self.log("❌ Backup model also failed to create articles")
                return {
                    "success": False,
                    "error": f"Both {primary_model_name} and {backup_model_name} failed to create articles",
                    "model_used": backup_model_name
                }
            
        except Exception as e:
            # Enhanced overall backup model error logging
            error_msg = str(e)
            self.log(f"❌ Backup model execution failed with system error:")
            self.log(f"   Error Type: {type(e).__name__}")
            self.log(f"   Error Message: {error_msg}")
            self.log(f"   Backup Model: {backup_model_name}")
            
            # Check for specific errors in system-level backup failures
            if "404" in error_msg:
                self.log(f"🔍 System-level 404 Error in Backup Model Setup:")
                self.log(f"   This could indicate deployment '{backup_model_name}' doesn't exist")
            elif "import" in error_msg.lower():
                self.log(f"🔍 Import Error in Backup Model Setup: {error_msg}")
            elif "connection" in error_msg.lower():
                self.log(f"🔍 Connection Error in Backup Model Setup: {error_msg}")
            
            return {
                "success": False,
                "error": f"Backup model system failure: {str(e)}",
                "error_type": type(e).__name__,
                "backup_model": backup_model_name
            }

    def _verify_tool_usage_for_backup(self, kb_id: int) -> bool:
        """Verify that the backup model actually created articles"""
        try:
            import psycopg2
            from config.model_config import DATABASE_URL
            
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    # Count articles created in the last 2 minutes for this KB
                    cur.execute("""
                        SELECT COUNT(*) FROM articles 
                        WHERE knowledge_base_id = %s 
                        AND created_at > NOW() - INTERVAL '2 minutes'
                    """, (kb_id,))
                    recent_count = cur.fetchone()[0]
                    
                    if recent_count > 0:
                        self.log(f"✅ Backup model verification: {recent_count} articles created in KB {kb_id}")
                        return True
                    else:
                        self.log(f"❌ Backup model verification: No articles created in KB {kb_id}")
                        return False
                        
        except Exception as e:
            self.log(f"❌ Backup model verification failed: {e}")
            return False

    # Technical debt fallback methods removed - trusting the LLM to use tools properly

    def _get_project_id_from_kb(self, kb_id: int) -> Optional[int]:
        """Get GitLab project ID associated with this KB"""
        try:
            # For KB 40, we know it's project 22
            if kb_id == 40:
                return 22
            # Add more mappings as needed
            return None
        except Exception as e:
            self.log(f"Error getting project ID for KB {kb_id}: {e}")
            return None

    def _set_kb_context_from_project(self, project_id: int):
        """Set KB context using GitLab project ID"""
        try:
            for tool in self.tools:
                if tool.name == 'KnowledgeBaseSetContextByGitLabProject':
                    result = tool.run({"gitlab_project_id": str(project_id)})
                    self.log(f"✅ KB context set from project {project_id}: {result}")
                    return True
        except Exception as e:
            self.log(f"Error setting KB context from project {project_id}: {e}")
        return False

    def _set_kb_context_directly(self, kb_id: int):
        """Set KB context directly using KB ID"""
        try:
            for tool in self.tools:
                if tool.name == 'KnowledgeBaseSetContext':
                    result = tool.run({"knowledge_base_id": str(kb_id)})
                    self.log(f"✅ KB context set directly for KB {kb_id}: {result}")
                    return True
        except Exception as e:
            self.log(f"Error setting KB context for KB {kb_id}: {e}")
        return False

    def _establish_kb_context_from_gitlab_project(self, project_id: str, state: Dict[str, Any]) -> bool:
        """Establish Knowledge Base context from GitLab project ID using the appropriate tool"""
        try:
            self.log(f"Attempting to establish KB context from GitLab project {project_id}")
            
            # Find the KnowledgeBaseSetContextByGitLabProject tool
            context_tool = None
            for tool in self.tools:
                if tool.name == "KnowledgeBaseSetContextByGitLabProject":
                    context_tool = tool
                    break
            
            if not context_tool:
                self.log("KnowledgeBaseSetContextByGitLabProject tool not found", "ERROR")
                return False
            
            # Call the tool to establish context
            self.log(f"Calling KnowledgeBaseSetContextByGitLabProject with project_id={project_id}")
            result = context_tool._run(gitlab_project_id=project_id)
            
            if result.get("success"):
                # Update state with the established context
                state["knowledge_base_id"] = result.get("knowledge_base_id")
                state["knowledge_base_name"] = result.get("knowledge_base_name")
                state["gitlab_project_id"] = result.get("gitlab_project_id")
                
                self.log(f"✅ KB context established: {result.get('knowledge_base_name')} (ID: {result.get('knowledge_base_id')})")
                return True
            else:
                error_msg = result.get("error", "Unknown error")
                self.log(f"Failed to establish KB context: {error_msg}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error establishing KB context from GitLab project {project_id}: {str(e)}", "ERROR")
            return False

    def _add_work_progress_update(self, project_id: int, issue_id: int, comment: str):
        """Add a progress update comment to GitLab issue"""
        try:
            # Find the GitLab comment tool
            for tool in self.tools:
                if hasattr(tool, 'name') and tool.name == 'GitLabAddCommentTool':
                    # Pass the agent class name as the agent identifier
                    agent_name = self.__class__.__name__
                    result = tool._run(str(project_id), str(issue_id), comment, agent_name)
                    self.log(f"GitLab comment result: {result}")
                    return True
            
            # Fallback - log locally if tool not found
            self.log(f"Progress update (GitLabAddCommentTool not found): {comment[:100]}...")
            return False
            
        except Exception as e:
            self.log(f"Error adding progress update: {e}")
            return False

    def _mark_issue_complete(self, project_id: int, issue_id: int, message: str):
        """Mark GitLab issue as complete"""
        try:
            # First add a completion comment
            self._add_work_progress_update(project_id, issue_id, f"✅ COMPLETED: {message}")
            
            # Then close the issue
            for tool in self.tools:
                if hasattr(tool, 'name') and tool.name == 'GitLabCloseIssueTool':
                    # Pass the agent class name as the agent identifier
                    agent_name = self.__class__.__name__
                    result = tool._run(str(project_id), str(issue_id), f"Issue completed: {message}", agent_name)
                    self.log(f"GitLab close issue result: {result}")
                    return True
            
            self.log(f"Marking issue #{issue_id} as complete: {message} (GitLabCloseIssueTool not found)")
            return False
            
        except Exception as e:
            self.log(f"Error marking issue complete: {e}")
            return False

    def _determine_hierarchical_parent_id(self, kb_id: int, title: str, content: str) -> Optional[int]:
        """
        Determine the appropriate parent_id for hierarchical article placement.
        
        Implements the hierarchical structure:
        - Level 1 (Root Categories): parent_id=None - broad topic containers
        - Level 2 (Subcategories): parent_id=category_id - focused topic areas  
        - Level 3+ (Content Articles): parent_id=subcategory_id - detailed content
        
        Args:
            kb_id: Knowledge base ID
            title: Article title for context analysis
            content: Article content for context analysis
            
        Returns:
            Optional[int]: parent_id (None for root categories, article_id for children)
        """
        try:
            self.log(f"🏗️ HIERARCHY: Determining parent_id for '{title}' in KB {kb_id}")
            
            # Get current hierarchy using the tool
            hierarchy_tool = None
            for tool in self.tools:
                if tool.name == 'KnowledgeBaseGetArticleHierarchy':
                    hierarchy_tool = tool
                    break
            
            if not hierarchy_tool:
                self.log("⚠️ HIERARCHY: KnowledgeBaseGetArticleHierarchy tool not found, defaulting to root level")
                return None
            
            # Get existing hierarchy
            hierarchy_result = hierarchy_tool._run(knowledge_base_id=str(kb_id))
            
            if not hierarchy_result or "No articles found" in str(hierarchy_result):
                self.log("🏗️ HIERARCHY: No existing articles - creating first root category")
                return None
            
            # Parse hierarchy to understand current structure
            articles = self._parse_hierarchy_result(hierarchy_result)
            
            # Analyze what type of article this should be based on content and existing structure
            article_type = self._classify_article_type(title, content, articles)
            
            if article_type == "root_category":
                self.log(f"🏗️ HIERARCHY: Article '{title}' classified as ROOT CATEGORY (parent_id=None)")
                return None
            elif article_type == "subcategory":
                # Find best matching root category as parent
                parent_id = self._find_best_category_parent(title, content, articles)
                self.log(f"🏗️ HIERARCHY: Article '{title}' classified as SUBCATEGORY (parent_id={parent_id})")
                return parent_id
            else:  # content_article
                # Find best matching subcategory as parent
                parent_id = self._find_best_subcategory_parent(title, content, articles)
                self.log(f"🏗️ HIERARCHY: Article '{title}' classified as CONTENT ARTICLE (parent_id={parent_id})")
                return parent_id
                
        except Exception as e:
            self.log(f"❌ HIERARCHY: Error determining parent_id: {str(e)} - defaulting to None")
            import traceback
            self.log(f"HIERARCHY ERROR: {traceback.format_exc()}")
            return None

    def _parse_hierarchy_result(self, hierarchy_result) -> List[Dict]:
        """Parse the hierarchy tool result into a structured format"""
        articles = []
        try:
            # Handle different result formats
            if isinstance(hierarchy_result, str):
                # Parse text format that typically includes article info
                lines = hierarchy_result.split('\n')
                for line in lines:
                    if 'ID:' in line and 'Title:' in line:
                        # Extract article info from formatted strings
                        parts = line.split('|')
                        if len(parts) >= 3:
                            id_part = parts[0].strip()
                            title_part = parts[1].strip() 
                            parent_part = parts[2].strip() if len(parts) > 2 else "None"
                            
                            article_id = None
                            if 'ID:' in id_part:
                                id_match = re.search(r'ID:\s*(\d+)', id_part)
                                if id_match:
                                    article_id = int(id_match.group(1))
                                    
                            parent_id = None
                            if 'Parent:' in parent_part and 'None' not in parent_part:
                                parent_match = re.search(r'Parent:\s*(\d+)', parent_part)
                                if parent_match:
                                    parent_id = int(parent_match.group(1))
                                    
                            if article_id:
                                articles.append({
                                    'id': article_id,
                                    'title': title_part.replace('Title:', '').strip(),
                                    'parent_id': parent_id
                                })
                                
            self.log(f"🏗️ HIERARCHY: Parsed {len(articles)} articles from hierarchy")
            return articles
            
        except Exception as e:
            self.log(f"❌ HIERARCHY: Error parsing hierarchy result: {str(e)}")
            return []

    def _classify_article_type(self, title: str, content: str, existing_articles: List[Dict]) -> str:
        """
        Classify what type of article this should be in the hierarchy.
        
        Returns: "root_category", "subcategory", or "content_article"
        """
        try:
            # Count existing structure levels
            root_categories = [a for a in existing_articles if a.get('parent_id') is None]
            subcategories = [a for a in existing_articles if a.get('parent_id') is not None and 
                           any(root.get('id') == a.get('parent_id') for root in root_categories)]
            
            self.log(f"🏗️ HIERARCHY: Current structure - {len(root_categories)} root categories, {len(subcategories)} subcategories")
            
            # Rule 1: If we have < 3 root categories, prefer creating root categories for broad topics
            if len(root_categories) < 3:
                # Check if this looks like a broad, categorical topic
                broad_indicators = [
                    len(title.split()) <= 4,  # Short, categorical titles
                    any(word in title.lower() for word in [
                        'budgeting', 'saving', 'investing', 'planning', 'strategies', 
                        'basics', 'fundamentals', 'introduction', 'overview', 'guide'
                    ]),
                    len(content) < 800  # Shorter content suggests overview/category
                ]
                
                if sum(broad_indicators) >= 2:
                    return "root_category"
            
            # Rule 2: If we have good root structure (3-8 categories), prefer subcategories
            if 3 <= len(root_categories) <= 8:
                # Check if this looks like a focused subtopic
                focused_indicators = [
                    len(title.split()) > 4,  # More specific titles
                    any(word in title.lower() for word in [
                        'techniques', 'methods', 'tips', 'advanced', 'specific', 
                        'how to', 'step by', 'detailed', 'comprehensive'
                    ]),
                    500 <= len(content) <= 1200  # Medium content suggests subcategory
                ]
                
                if sum(focused_indicators) >= 2:
                    return "subcategory"
            
            # Rule 3: Default to content article for detailed, specific content
            content_indicators = [
                len(content) > 800,  # Longer content suggests detailed article
                any(word in title.lower() for word in [
                    'tutorial', 'walkthrough', 'example', 'case study', 'implementation',
                    'practical', 'actionable', 'tools', 'resources', 'checklist'
                ])
            ]
            
            if sum(content_indicators) >= 1:
                return "content_article"
            
            # Fallback logic based on structure balance
            if len(root_categories) < 3:
                return "root_category"
            elif len(subcategories) < len(root_categories) * 2:
                return "subcategory" 
            else:
                return "content_article"
                
        except Exception as e:
            self.log(f"❌ HIERARCHY: Error classifying article type: {str(e)}")
            return "content_article"  # Safe default

    def _find_best_category_parent(self, title: str, content: str, existing_articles: List[Dict]) -> Optional[int]:
        """Find the best root category to use as parent for a subcategory"""
        try:
            root_categories = [a for a in existing_articles if a.get('parent_id') is None]
            
            if not root_categories:
                self.log("🏗️ HIERARCHY: No root categories found for subcategory parent")
                return None
            
            # Simple keyword matching to find most relevant parent
            best_match = None
            best_score = 0
            
            for category in root_categories:
                score = 0
                category_title = category.get('title', '').lower()
                search_text = (title + ' ' + content).lower()
                
                # Score based on keyword overlap
                category_words = set(category_title.split())
                content_words = set(search_text.split())
                overlap = len(category_words.intersection(content_words))
                
                score += overlap * 2
                
                # Boost score for thematic matching
                financial_themes = {
                    'budget': ['budget', 'expense', 'income', 'money', 'cost', 'financial'],
                    'saving': ['save', 'saving', 'frugal', 'cut', 'reduce', 'tips'],
                    'invest': ['invest', 'portfolio', 'stock', 'return', 'growth', 'wealth'],
                    'plan': ['plan', 'strategy', 'goal', 'future', 'retirement', 'long-term']
                }
                
                for theme, keywords in financial_themes.items():
                    if theme in category_title:
                        theme_matches = sum(1 for keyword in keywords if keyword in search_text)
                        score += theme_matches
                
                if score > best_score:
                    best_score = score
                    best_match = category.get('id')
            
            self.log(f"🏗️ HIERARCHY: Best category parent ID: {best_match} (score: {best_score})")
            return best_match
            
        except Exception as e:
            self.log(f"❌ HIERARCHY: Error finding category parent: {str(e)}")
            return None

    def _find_best_subcategory_parent(self, title: str, content: str, existing_articles: List[Dict]) -> Optional[int]:
        """Find the best subcategory to use as parent for a content article"""
        try:
            # Get subcategories (articles that have root categories as parents)
            root_categories = [a for a in existing_articles if a.get('parent_id') is None]
            root_ids = {a.get('id') for a in root_categories}
            
            subcategories = [a for a in existing_articles if a.get('parent_id') in root_ids]
            
            if not subcategories:
                # If no subcategories exist, find best root category as parent
                self.log("🏗️ HIERARCHY: No subcategories found, using best root category as parent")
                return self._find_best_category_parent(title, content, existing_articles)
            
            # Find best matching subcategory
            best_match = None
            best_score = 0
            
            for subcategory in subcategories:
                score = 0
                subcategory_title = subcategory.get('title', '').lower()
                search_text = (title + ' ' + content).lower()
                
                # Score based on keyword overlap
                subcat_words = set(subcategory_title.split())
                content_words = set(search_text.split())
                overlap = len(subcat_words.intersection(content_words))
                
                score += overlap * 3  # Higher weight for subcategory matching
                
                # Boost for semantic similarity
                if any(word in subcategory_title for word in search_text.split()[:5]):
                    score += 2
                
                if score > best_score:
                    best_score = score
                    best_match = subcategory.get('id')
            
            self.log(f"🏗️ HIERARCHY: Best subcategory parent ID: {best_match} (score: {best_score})")
            return best_match
            
        except Exception as e:
            self.log(f"❌ HIERARCHY: Error finding subcategory parent: {str(e)}")
            return None
