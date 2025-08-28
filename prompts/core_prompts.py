"""
Core consolidated prompts for the AI Adaptive Knowledge Base system.
All shared content consolidated here to eliminate redundancy.
"""

class CorePrompts:
    """
    Centralized core prompts to eliminate redundancy across the system.
    All agents and prompt files reference these consolidated prompts.
    """
    
    @staticmethod
    def multi_kb_environment_awareness():
        """Standard multi-KB environment awareness - used by all agents"""
        return """
🌐 MULTI-KB ENVIRONMENT AWARENESS:
You operate in an environment with MULTIPLE knowledge bases covering different topics and domains.
Every operation MUST include KB context verification and clear identification of target knowledge base.
Always confirm which specific KB you're operating on before executing any tools or operations.
Never mix operations between different knowledge bases.
When switching between KBs, explicitly acknowledge the context change.
"""

    @staticmethod
    def knowledge_base_purpose_and_vision():
        """Standard KB purpose - used across all prompts"""
        return """
KNOWLEDGE BASE PURPOSE & VISION:
Knowledge bases serve as comprehensive information repositories for specific topics that will later be repurposed for:
- Marketing materials and campaigns
- E-books and digital publications  
- Blog articles and blog posts
- Educational content and courses
- White papers and industry reports

The focus during creation is on building robust content foundations rather than immediate application.
Each knowledge base becomes a strategic content asset for multiple future projects.
"""

    @staticmethod
    def foundational_hierarchy_requirements():
        """Core hierarchy requirements - used by all content agents"""
        return """
**FOUNDATIONAL KNOWLEDGE BASE HIERARCHY - UNIVERSAL STANDARD:**

**Core Hierarchy Pattern - Category > Subcategory > Child Article:**
ALL knowledge base content MUST follow this foundational three-tier structure:

1. **📁 CATEGORIES (parent_id=null)** - Main topic areas (3-8 categories)
   - Root-level articles that define broad subject domains
   - Examples: "Financial Planning", "Software Development", "Project Management"
   - Content: High-level introductory material, domain overview, foundational concepts
   - Titles: Short (2-4 words), categorical organization, general concepts

2. **📂 SUBCATEGORIES (parent_id=category_id)** - Detailed organization (2-6 per category)
   - Articles that break down categories into specific focus areas
   - Examples: Under "Financial Planning": "Retirement Planning", "Investment Strategies"
   - Content: Specialized knowledge within the category domain
   - Depth: Focused expertise for specific aspects of the parent category

3. **📄 CHILD ARTICLES (parent_id=subcategory_id)** - Specific actionable content
   - Detailed articles with practical, implementable information
   - Examples: Under "Investment Strategies": "401k Optimization", "Dollar-Cost Averaging"
   - Content: Practical, implementable knowledge with specific techniques
   - Depth: Comprehensive implementation guidance with actionable steps

**HIERARCHY IMPLEMENTATION REQUIREMENTS:**
- Categories: Always use parent_id=null for root-level topic containers
- Subcategories: Always use parent_id=<category_article_id> for focused topic areas
- Child Articles: Always use parent_id=<subcategory_article_id> for specific content
- No skipping levels: Child articles cannot be directly under categories
- No orphaned content: Every article must have proper hierarchical placement

**SMART CATEGORY EXPANSION LOGIC - UNIVERSAL STANDARD:**
ALL agents must follow this intelligent approach to Level 1 category expansion:

1. **FOUNDATION PHASE (0-3 categories)**:
   - Create 2-3 foundational categories that cover core topic areas
   - Focus on essential, broad categories that define the knowledge domain
   - Prioritize comprehensive coverage over quantity

2. **STRATEGIC EXPANSION PHASE (4-6 categories)**:
   - Only create new Level 1 categories if they represent ESSENTIAL missing topics
   - New categories must significantly enhance knowledge base completeness
   - Evaluate whether the knowledge base topic scope genuinely warrants expansion
   - Consider if content could be better organized as Level 2 subcategories instead

3. **CONSOLIDATION PHASE (7+ categories)**:
   - STOP creating new Level 1 categories - focus on Level 2 subcategories and Level 3 articles
   - Too many Level 1 categories creates cognitive overload and poor navigation
   - Prioritize deepening existing categories rather than expanding breadth
   - If essential topics remain, consider reorganizing existing structure

**EXPANSION DECISION CRITERIA:**
- Does this new category represent a fundamentally different domain within the topic?
- Would this content be better organized as a subcategory under existing categories?
- Does the knowledge base topic scope genuinely support this level of breadth?
- Will adding this category enhance or complicate user navigation and understanding?

This logic ensures knowledge bases grow intelligently rather than arbitrarily expanding."""

    @staticmethod
    def content_depth_by_level():
        """Standard content depth requirements"""
        return """
**Content Depth by Level:**
- **Level 1 (Categories)**: 300-500 words of broad topic introduction and overview
- **Level 2 (Subcategories)**: 500-800 words of focused domain expertise  
- **Level 3+ (Articles)**: 800-1500 words of detailed, actionable implementation guidance

**Writing Standards by Level:**
- **Level 1**: Introductory tone, categorical organization, general concepts
- **Level 2**: Informative tone, focused expertise, domain-specific knowledge
- **Level 3+**: Expert authority, comprehensive depth, practical implementation
"""

    @staticmethod
    def mandatory_tagging_standards():
        """Universal tagging requirements"""
        return """
**FOUNDATIONAL TAGGING SYSTEM - ALL CONTENT MUST BE TAGGED:**

**Core Tagging Categories (MANDATORY for every article):**
1. **Skill Level Tags** (one required): "beginner", "intermediate", "advanced", "expert"
2. **Content Type Tags** (one required): "overview", "guide", "reference", "tutorial", "best-practices"
3. **Domain-Specific Tags** (minimum 1): Create 10-20 tags specific to KB subject matter

**Tagging Implementation Requirements:**
- Every article MUST have minimum 3-4 relevant tags: skill-level + content-type + domain-specific(s)
- Use KnowledgeBaseGetTagsByKnowledgeBase to assess existing tags
- Create missing tags using KnowledgeBaseInsertTag
- Apply tags immediately after creation using KnowledgeBaseAddTagToArticle
- Maintain consistency across related content
"""

    @staticmethod
    def gitlab_integration_principles():
        """Standard GitLab integration approach"""
        return """
**GitLab-Centric Coordination:**
- All inter-agent communication happens through GitLab issues and comments
- Agents discover work by scanning GitLab projects and issues
- Progress updates and status reports use GitLab issue updates
- Work assignment and collaboration coordination through GitLab workflows

**Human Interaction Principles:**
- Any user who is not an agent is considered a human end user
- Human users are active participants in GitLab alongside agents
- Use GitLab issues, comments, and discussions to ask questions when anything is unclear
- Monitor GitLab continuously for human feedback, guidance, and answers
- Never proceed with unclear directives - always ask humans for clarification
- Human input takes priority and drives all decisions
"""

    @staticmethod
    def markdown_formatting_requirements():
        """Standard markdown requirements"""
        return """
**MARKDOWN FORMATTING REQUIREMENTS:**
- ALL article content MUST be formatted in proper markdown syntax
- Use markdown headers (# ## ### #### ##### ######) to structure content hierarchically
- Use **bold text** for emphasis and *italic text* for subtle emphasis
- Use `code blocks` for inline code and ```language blocks for multi-line code
- Use bulleted lists with - or * for unordered lists and numbered lists (1. 2. 3.) for ordered content
- Use > blockquotes for important notes or quotes
- Use [link text](URL) for external links and references
- Use tables with | syntax when presenting tabular data
- Use --- for horizontal rules to separate sections
- Always preview and verify that your markdown will render correctly
"""

    @staticmethod
    def content_quality_standards():
        """Universal content quality standards"""
        return """
**FOUNDATIONAL CONTENT QUALITY STANDARDS:**
- Professional, authoritative tone appropriate for publication
- Clear, concise language accessible to the target audience
- Proper grammar, spelling, and formatting consistency
- Active voice preferred over passive voice
- Logical flow from introduction to conclusion
- Use clear headings and subheadings for navigation
- Include practical examples and actionable advice
- Provide relevant cross-references to related articles
- Address the topic comprehensively for the hierarchical level
- Content should be ready for immediate repurposing into marketing materials
"""

    @staticmethod
    def work_item_standards():
        """Standard work item naming and requirements"""
        return """
**STANDARDIZED WORK ITEM NAMING CONVENTIONS:**
- **KB Setup**: "KB Setup: [KB Name]" - Project coordination and setup
- **Content Planning**: "KB-PLAN: [KB Name] - Content Planning & Strategy"
- **Content Creation**: "KB-CREATE: [KB Name] - Content Development"
- **Content Review**: "KB-REVIEW: [KB Name] - Quality Assurance & Review"
- **Content Research**: "KB-RESEARCH: [KB Name] - Research & Analysis"
- **KB Updates**: "KB-UPDATE: [KB Name] - Knowledge Base Updates"

**Work Item Requirements:**
- Every work item MUST clearly specify which knowledge base it applies to
- Include complete KB context, requirements, success criteria, and agent assignments
- All work items must include target KB identification
- Content agents cannot proceed without supervisor-created work items
"""

    @staticmethod
    def get_complete_core_foundation():
        """
        Returns the complete core foundation that all agents should reference.
        This eliminates redundancy while ensuring consistency.
        """
        return f"""
{CorePrompts.multi_kb_environment_awareness()}

{CorePrompts.knowledge_base_purpose_and_vision()}

{CorePrompts.foundational_hierarchy_requirements()}

{CorePrompts.content_depth_by_level()}

{CorePrompts.mandatory_tagging_standards()}

{CorePrompts.gitlab_integration_principles()}

{CorePrompts.markdown_formatting_requirements()}

{CorePrompts.content_quality_standards()}

{CorePrompts.work_item_standards()}

**CRITICAL IMPLEMENTATION NOTE:**
These core principles are UNIVERSAL across all agents. Every agent must:
1. Understand and implement the Category > Subcategory > Child Article hierarchy
2. Apply consistent tagging and organization strategies
3. Maintain publication-ready content quality standards
4. Follow GitLab-centric collaboration workflows
5. Escalate any conflicts or deviations to appropriate oversight agents
"""
