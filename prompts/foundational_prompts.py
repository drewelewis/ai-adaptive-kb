"""
Shared foundational prompts for the AI Adaptive Knowledge Base system.
All agents must reference these core principles to ensure consistency.
"""

from .core_prompts import CorePrompts

class FoundationalPrompts:
    """
    Core foundational approaches that ALL agents must understand and follow.
    These prompts ensure consistency across the entire multi-agent system.
    Now references consolidated CorePrompts to eliminate redundancy.
    """
    
    @staticmethod
    def knowledge_base_hierarchy_foundation():
        """
        THE FOUNDATIONAL KNOWLEDGE BASE HIERARCHY APPROACH
        
        This is the core structural principle that ALL agents must understand and implement.
        Every agent involved in content creation, planning, review, or supervision must 
        follow this exact three-tier hierarchy pattern.
        """
        return CorePrompts.foundational_hierarchy_requirements()

    @staticmethod
    def tagging_and_organization_foundation():
        """
        Universal tagging and content organization principles.
        All agents must implement consistent tagging strategies.
        """
        return CorePrompts.mandatory_tagging_standards()

    @staticmethod
    def content_quality_standards():
        """
        Universal content quality standards that all agents must enforce.
        """
        return CorePrompts.content_quality_standards()

    @staticmethod
    def agent_collaboration_principles():
        """
        Universal principles for how agents should collaborate and coordinate.
        """
        return CorePrompts.gitlab_integration_principles() + """

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
        return CorePrompts.get_complete_core_foundation() + f"""

{FoundationalPrompts.agent_collaboration_principles()}

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
    Now uses consolidated CorePrompts to eliminate redundancy.
    """
    
    @staticmethod
    def content_creation_foundation():
        """Foundation for agents that create content (ContentCreator, ContentManagement)"""
        return CorePrompts.get_complete_core_foundation() + """

**CONTENT CREATION SPECIFIC REQUIREMENTS:**
- ALWAYS use proper parent_id relationships when creating articles
- ALWAYS create and apply relevant tags to new content
- ALWAYS validate content depth matches hierarchical level
- ALWAYS ensure navigation flow from general to specific
"""
    
    @staticmethod
    def content_planning_foundation():
        """Foundation for agents that plan content strategy (ContentPlanner)"""
        return CorePrompts.get_complete_core_foundation() + """

**CONTENT PLANNING SPECIFIC REQUIREMENTS:**
- Design complete Category > Subcategory > Child Article taxonomies
- Plan balanced content distribution across hierarchy levels
- Establish domain-specific tagging strategies
- Ensure comprehensive topic coverage within planned structure
"""
    
    @staticmethod
    def content_review_foundation():
        """Foundation for agents that review content (ContentReviewer)"""
        return CorePrompts.get_complete_core_foundation() + """

**CONTENT REVIEW SPECIFIC REQUIREMENTS:**
- Validate hierarchy compliance in all content
- Verify appropriate content depth for hierarchical level
- Confirm tag application follows foundational standards
- Ensure content quality meets publication readiness standards
"""
    
    @staticmethod
    def content_management_foundation():
        """Foundation for agents that manage content operations (ContentManagement)"""
        return CorePrompts.get_complete_core_foundation() + """

**CONTENT MANAGEMENT SPECIFIC REQUIREMENTS:**
- Ensure all content operations maintain foundational hierarchy structure
- Coordinate cross-knowledge base operations with hierarchy awareness
- Manage content lifecycle while preserving Category > Subcategory > Child Article pattern
- Facilitate agent coordination with consistent foundational understanding
"""
    
    @staticmethod
    def supervision_foundation():
        """Foundation for supervisory agents (Supervisor, orchestration)"""
        return CorePrompts.get_complete_core_foundation() + """

**SUPERVISION SPECIFIC REQUIREMENTS:**
- Monitor system-wide compliance with foundational hierarchy approach
- Identify and correct deviations from Category > Subcategory > Child Article pattern
- Make judgment calls when content structure doesn't align with foundational principles
- Coordinate corrective actions through appropriate agent assignment
"""
    
    @staticmethod
    def content_retrieval_foundation():
        """Foundation for content retrieval agents (read-only operations)"""
        return CorePrompts.get_complete_core_foundation() + """

**CONTENT RETRIEVAL SPECIFIC REQUIREMENTS:**
- Understand and navigate the Category > Subcategory > Child Article hierarchy
- Provide accurate knowledge base content access with proper context awareness  
- Support GitLab integration for seamless content retrieval across platforms
- Maintain read-only operations while respecting foundational content structure
"""
