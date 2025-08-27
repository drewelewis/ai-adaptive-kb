"""
Shared foundational prompts for the AI Adaptive Knowledge Base system.
All agents must reference these core principles to ensure consistency.
"""

class FoundationalPrompts:
    """
    Core foundational approaches that ALL agents must understand and follow.
    These prompts ensure consistency across the entire multi-agent system.
    """
    
    @staticmethod
    def knowledge_base_hierarchy_foundation():
        """
        THE FOUNDATIONAL KNOWLEDGE BASE HIERARCHY APPROACH
        
        This is the core structural principle that ALL agents must understand and implement.
        Every agent involved in content creation, planning, review, or supervision must 
        follow this exact three-tier hierarchy pattern.
        """
        return """
**FOUNDATIONAL KNOWLEDGE BASE ARCHITECTURE - UNIVERSAL STANDARD:**

**Core Hierarchy Pattern - Category > Subcategory > Child Article:**
ALL knowledge base content MUST follow this foundational three-tier structure:

1. **📁 CATEGORIES (parent_id=null)** - Main topic areas that serve as logical containers
   - Root-level articles that define broad subject domains
   - Examples: "Financial Planning", "Software Development", "Project Management"
   - Should provide comprehensive overview of the entire topic area
   - Content: High-level introductory material, domain overview, foundational concepts
   - Depth: Broad coverage establishing the topic's scope and importance

2. **📂 SUBCATEGORIES (parent_id=category_id)** - Detailed organization under categories
   - Articles that break down categories into specific focus areas
   - Examples: Under "Financial Planning": "Retirement Planning", "Investment Strategies", "Tax Planning"
   - Should provide focused guidance within the broader category context
   - Content: Specialized knowledge within the category domain
   - Depth: Targeted expertise for specific aspects of the parent category

3. **📄 CHILD ARTICLES (parent_id=subcategory_id)** - Specific actionable content
   - Detailed articles with practical, implementable information
   - Examples: Under "Investment Strategies": "401k Optimization Techniques", "Dollar-Cost Averaging Guide"
   - Should contain step-by-step guidance, examples, and actionable insights
   - Content: Practical, implementable knowledge with specific techniques and examples
   - Depth: Comprehensive implementation guidance with actionable steps

**HIERARCHY IMPLEMENTATION REQUIREMENTS:**

**Article Creation Standards:**
- Categories: Always use parent_id=null for root-level topic containers
- Subcategories: Always use parent_id=<category_article_id> for focused topic areas
- Child Articles: Always use parent_id=<subcategory_article_id> for specific content
- No skipping levels: Child articles cannot be directly under categories
- No orphaned content: Every article must have proper hierarchical placement

**Content Depth by Level:**
- Categories: 300-500 words of broad topic introduction and overview
- Subcategories: 500-800 words of focused domain expertise
- Child Articles: 800-1500 words of detailed, actionable implementation guidance

**Navigation and User Experience:**
- Users should naturally flow from general (category) to specific (child article)
- Each level should provide logical progression to the next level
- Cross-references between related subcategories and child articles
- Clear breadcrumb navigation through the hierarchy

**Quality Standards:**
- Balanced structure: Avoid too many orphaned articles or overly deep nesting
- Consistent depth: Content depth should match the hierarchical level
- Logical grouping: Related content should be grouped under appropriate subcategories
- Complete coverage: Categories should fully cover their domain through subcategories
"""

    @staticmethod
    def tagging_and_organization_foundation():
        """
        Universal tagging and content organization principles.
        All agents must implement consistent tagging strategies.
        """
        return """
**FOUNDATIONAL TAGGING AND ORGANIZATION SYSTEM:**

**CRITICAL REQUIREMENT: ALL CONTENT MUST BE TAGGED**
Every article created in the knowledge base MUST have appropriate tags applied immediately upon creation. No article should exist without proper tagging.

**Core Tagging Categories (ALL knowledge bases must implement):**

1. **Skill Level Tags (MANDATORY - every article needs one):**
   - "beginner" - Introductory content for new learners
   - "intermediate" - Content requiring basic foundation knowledge  
   - "advanced" - Expert-level content with complex concepts
   - "expert" - Specialized content for domain experts

2. **Content Type Tags (MANDATORY - every article needs one):**
   - "overview" - High-level introductory material (typically categories)
   - "guide" - Step-by-step instructional content
   - "reference" - Quick-lookup factual information
   - "tutorial" - Hands-on learning content with examples
   - "best-practices" - Proven approaches and methodologies
   - "troubleshooting" - Problem-solving and debugging content

3. **Domain-Specific Tags (MANDATORY - minimum 1 per article):**
   - Create 10-20 tags specific to the knowledge base subject matter
   - Use consistent naming conventions (lowercase, hyphen-separated)
   - Examples: "financial-planning", "retirement-401k", "investment-strategy"
   - Must align with knowledge base's primary domain and topic areas

4. **Application Context Tags (RECOMMENDED - adds value):**
   - "practical" - Real-world implementation focused
   - "theoretical" - Conceptual understanding focused
   - "case-study" - Example-driven content
   - "checklist" - Action-oriented task lists

**MANDATORY Tagging Implementation Requirements:**
- Every article MUST have minimum 3-4 relevant tags: skill-level + content-type + domain-specific(s)
- Categories typically tagged: [domain-tag, "overview", skill-level]
- Subcategories typically tagged: [domain-tag, content-type, skill-level, application-context]  
- Child articles typically tagged: [specific-domain-tag, "guide"/"tutorial", skill-level, "practical"]

**REQUIRED Tag Creation Workflow:**
1. Before creating any article: Assess existing tags using KnowledgeBaseGetTagsByKnowledgeBase
2. Create missing foundational tags using KnowledgeBaseInsertTag
3. Apply tags to articles immediately after creation using KnowledgeBaseAddTagToArticle or KnowledgeBaseSetArticleTags
4. Maintain consistency across related content
5. Verify tagging completeness before considering any content creation task complete

**Agent Responsibilities:**
- ContentCreatorAgent: MUST tag all created articles immediately after insertion
- ContentManagementAgent: MUST verify proper tagging across knowledge base
- ContentReviewerAgent: MUST include tag review in content quality assessment
- All agents: MUST ensure no untagged content exists in the knowledge base
"""

    @staticmethod
    def content_quality_standards():
        """
        Universal content quality standards that all agents must enforce.
        """
        return """
**FOUNDATIONAL CONTENT QUALITY STANDARDS:**

**Writing Standards:**
- Professional, authoritative tone appropriate for publication
- Clear, concise language accessible to the target audience
- Proper grammar, spelling, and formatting consistency
- Active voice preferred over passive voice
- Logical flow from introduction to conclusion

**Structure Requirements:**
- Use # for main title, ## for major sections, ### for subsections
- Include practical examples and actionable advice
- Use bullet points and numbered lists for clarity
- Provide clear headings and subheadings for navigation
- Include relevant cross-references to related articles

**Content Completeness:**
- Address the topic comprehensively for the hierarchical level
- Include relevant examples and use cases
- Provide actionable guidance where appropriate
- Reference authoritative sources when applicable
- Maintain consistency with related content in the knowledge base

**Publication Readiness:**
- Content should be ready for immediate repurposing into marketing materials, e-books, blog posts
- Include metadata and tagging for content discoverability
- Ensure proper formatting for multiple output formats
- Maintain professional presentation standards
"""

    @staticmethod
    def agent_collaboration_principles():
        """
        Universal principles for how agents should collaborate and coordinate.
        """
        return """
**FOUNDATIONAL AGENT COLLABORATION PRINCIPLES:**

**GitLab-Centric Coordination:**
- All inter-agent communication happens through GitLab issues and comments
- Agents discover work by scanning GitLab projects and issues
- Progress updates and status reports use GitLab issue updates
- Work assignment and collaboration coordination through GitLab workflows

**Hierarchy Compliance Workflow:**
1. **Planning Phase**: ContentPlanner establishes hierarchy strategy
2. **Creation Phase**: ContentCreator implements hierarchy with proper parent_id relationships
3. **Review Phase**: ContentReviewer validates hierarchy compliance and content quality
4. **Supervision Phase**: SupervisorAgent oversees and corrects hierarchy violations

**Quality Assurance Chain:**
- Every content creation action must follow the foundational hierarchy pattern
- Any deviation from Category > Subcategory > Child Article structure triggers review
- Supervisor makes judgment calls when patterns don't align with foundational approach
- Corrective actions coordinated through GitLab issue assignment

**Autonomous Operation Principles:**
- Agents work independently by discovering and claiming appropriate work items
- Focus on work that matches agent capabilities and expertise areas
- Maintain system-wide consistency through shared foundational understanding
- Escalate conflicts or uncertainties through GitLab issue collaboration
"""

    @staticmethod
    def get_complete_foundational_prompt():
        """
        Returns the complete foundational prompt that all agents should reference.
        This ensures every agent has identical understanding of core principles.
        """
        hierarchy_foundation = FoundationalPrompts.knowledge_base_hierarchy_foundation()
        tagging_foundation = FoundationalPrompts.tagging_and_organization_foundation()
        quality_standards = FoundationalPrompts.content_quality_standards()
        collaboration_principles = FoundationalPrompts.agent_collaboration_principles()
        
        return f"""
{hierarchy_foundation}

{tagging_foundation}

{quality_standards}

{collaboration_principles}

**CRITICAL IMPLEMENTATION NOTE:**
These foundational principles are UNIVERSAL across all agents. Every agent must:
1. Understand and implement the Category > Subcategory > Child Article hierarchy
2. Apply consistent tagging and organization strategies
3. Maintain publication-ready content quality standards
4. Follow GitLab-centric collaboration workflows
5. Escalate any conflicts or deviations to appropriate oversight agents

Agents must reference these principles in all content-related decision making.
Any deviation from these foundational approaches should trigger review and correction.
"""

# Convenience functions for specific agent types
class AgentSpecificFoundations:
    """
    Specialized foundational prompt combinations for different agent types.
    """
    
    @staticmethod
    def content_creation_foundation():
        """Foundation for agents that create content (ContentCreator, ContentManagement)"""
        return FoundationalPrompts.get_complete_foundational_prompt() + """

**CONTENT CREATION SPECIFIC REQUIREMENTS:**
- ALWAYS use proper parent_id relationships when creating articles
- ALWAYS create and apply relevant tags to new content
- ALWAYS validate content depth matches hierarchical level
- ALWAYS ensure navigation flow from general to specific
"""
    
    @staticmethod
    def content_planning_foundation():
        """Foundation for agents that plan content strategy (ContentPlanner)"""
        return FoundationalPrompts.get_complete_foundational_prompt() + """

**CONTENT PLANNING SPECIFIC REQUIREMENTS:**
- Design complete Category > Subcategory > Child Article taxonomies
- Plan balanced content distribution across hierarchy levels
- Establish domain-specific tagging strategies
- Ensure comprehensive topic coverage within planned structure
"""
    
    @staticmethod
    def content_review_foundation():
        """Foundation for agents that review content (ContentReviewer)"""
        return FoundationalPrompts.get_complete_foundational_prompt() + """

**CONTENT REVIEW SPECIFIC REQUIREMENTS:**
- Validate hierarchy compliance in all content
- Verify appropriate content depth for hierarchical level
- Confirm tag application follows foundational standards
- Ensure content quality meets publication readiness standards
"""
    
    @staticmethod
    def content_management_foundation():
        """Foundation for agents that manage content operations (ContentManagement)"""
        return FoundationalPrompts.get_complete_foundational_prompt() + """

**CONTENT MANAGEMENT SPECIFIC REQUIREMENTS:**
- Ensure all content operations maintain foundational hierarchy structure
- Coordinate cross-knowledge base operations with hierarchy awareness
- Manage content lifecycle while preserving Category > Subcategory > Child Article pattern
- Facilitate agent coordination with consistent foundational understanding
"""
    
    @staticmethod
    def supervision_foundation():
        """Foundation for supervisory agents (Supervisor, orchestration)"""
        return FoundationalPrompts.get_complete_foundational_prompt() + """

**SUPERVISION SPECIFIC REQUIREMENTS:**
- Monitor system-wide compliance with foundational hierarchy approach
- Identify and correct deviations from Category > Subcategory > Child Article pattern
- Make judgment calls when content structure doesn't align with foundational principles
- Coordinate corrective actions through appropriate agent assignment
"""
    
    @staticmethod
    def content_retrieval_foundation():
        """Foundation for content retrieval agents (read-only operations)"""
        return FoundationalPrompts.get_complete_foundational_prompt() + """

**CONTENT RETRIEVAL SPECIFIC REQUIREMENTS:**
- Understand and navigate the Category > Subcategory > Child Article hierarchy
- Provide accurate knowledge base content access with proper context awareness  
- Support GitLab integration for seamless content retrieval across platforms
- Maintain read-only operations while respecting foundational content structure
"""
