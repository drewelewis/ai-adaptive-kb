"""
GitLab Agent Configuration

This module contains configuration for AI agent GitLab users and related settings.
Used by the gitlab_add_agent_users.py script and other GitLab integration components.
"""

from typing import Dict, Any, List

# Environment configuration
GITLAB_CONFIG = {
    "default_url": "http://localhost:8929",
    "admin_token_env": "GITLAB_ADMIN_PAT",
    "fallback_token_env": "GITLAB_PAT",
    "user_domain": "ai-agents.local"
}

# Agent user configurations
AGENT_USERS = {
    "ContentManagementAgent": {
        "username": "content-management-agent",
        "email": "content-management@ai-agents.local",
        "name": "Content Management Agent",
        "bio": "🤖 AI Agent specializing in autonomous content management and GitLab workflow coordination. Part of the autonomous swarming system for knowledge base development.",
        "projects_limit": 100,
        "can_create_group": False,
        "external": True,
        "admin": False,
        "website_url": "",
        "location": "AI Autonomous Swarming System",
        "responsibilities": [
            "Autonomous work discovery",
            "GitLab issue management", 
            "Content workflow coordination",
            "Supervisor feedback handling"
        ],
        "gitlab_permissions": [
            "create_issues",
            "update_issues", 
            "add_comments",
            "assign_issues",
            "manage_labels"
        ]
    },
    "ContentPlannerAgent": {
        "username": "content-planner-agent", 
        "email": "content-planner@ai-agents.local",
        "name": "Content Planner Agent",
        "bio": "🤖 AI Agent specializing in strategic content planning and architecture design. Provides strategic guidance for knowledge base development through GitLab coordination.",
        "projects_limit": 100,
        "can_create_group": False,
        "external": True,
        "admin": False,
        "website_url": "",
        "location": "AI Autonomous Swarming System",
        "responsibilities": [
            "Strategic design collaboration",
            "Content architecture planning",
            "Requirements analysis",
            "Multi-agent coordination"
        ],
        "gitlab_permissions": [
            "create_issues",
            "update_issues",
            "add_comments", 
            "create_milestones",
            "manage_labels"
        ]
    },
    "ContentCreatorAgent": {
        "username": "content-creator-agent",
        "email": "content-creator@ai-agents.local", 
        "name": "Content Creator Agent",
        "bio": "🤖 AI Agent specializing in comprehensive content creation and research. Generates expert-level articles and documentation through autonomous GitLab workflows.",
        "projects_limit": 100,
        "can_create_group": False,
        "external": True,
        "admin": False,
        "website_url": "",
        "location": "AI Autonomous Swarming System",
        "responsibilities": [
            "Content creation and research",
            "Article writing and documentation",
            "Autonomous work execution",
            "Quality deliverable creation"
        ],
        "gitlab_permissions": [
            "create_issues",
            "update_issues",
            "add_comments",
            "upload_files",
            "manage_labels"
        ]
    },
    "ContentReviewerAgent": {
        "username": "content-reviewer-agent",
        "email": "content-reviewer@ai-agents.local",
        "name": "Content Reviewer Agent", 
        "bio": "🤖 AI Agent specializing in quality assurance and content optimization. Ensures publication-ready quality through systematic review workflows in GitLab.",
        "projects_limit": 100,
        "can_create_group": False,
        "external": True,
        "admin": False,
        "website_url": "",
        "location": "AI Autonomous Swarming System",
        "responsibilities": [
            "Quality assurance and review",
            "Content optimization",
            "Publication readiness validation",
            "Review workflow coordination"
        ],
        "gitlab_permissions": [
            "create_issues",
            "update_issues",
            "add_comments",
            "approve_merge_requests",
            "manage_labels"
        ]
    },
    "ContentRetrievalAgent": {
        "username": "content-retrieval-agent",
        "email": "content-retrieval@ai-agents.local",
        "name": "Content Retrieval Agent",
        "bio": "🤖 AI Agent specializing in content search, retrieval, and analysis. Provides research support and content gap analysis through GitLab coordination.",
        "projects_limit": 100,
        "can_create_group": False,
        "external": True,
        "admin": False,
        "website_url": "",
        "location": "AI Autonomous Swarming System",
        "responsibilities": [
            "Content search and retrieval",
            "Research and analysis",
            "Content gap identification",
            "Information gathering support"
        ],
        "gitlab_permissions": [
            "create_issues",
            "update_issues",
            "add_comments",
            "read_repository",
            "manage_labels"
        ]
    },
    "SupervisorAgent": {
        "username": "supervisor-agent",
        "email": "supervisor@ai-agents.local",
        "name": "Supervisor Agent",
        "bio": "🤖 AI Supervisor Agent acting as Scrum Master for autonomous agent coordination. Facilitates workflows, reviews completed work, and manages agent swarming through GitLab.",
        "projects_limit": 100,
        "can_create_group": True,
        "external": True,
        "admin": False,
        "website_url": "",
        "location": "AI Autonomous Swarming System",
        "responsibilities": [
            "Scrum Master coordination",
            "Work review and approval",
            "Agent workflow facilitation",
            "Quality gate management"
        ],
        "gitlab_permissions": [
            "create_issues",
            "update_issues",
            "add_comments",
            "assign_issues",
            "manage_labels",
            "create_milestones",
            "manage_project_access"
        ]
    },
    "UserProxyAgent": {
        "username": "user-proxy-agent",
        "email": "user-proxy@ai-agents.local", 
        "name": "User Proxy Agent",
        "bio": "🤖 AI Agent specializing in collaborative KB design and user interaction. Facilitates multi-agent design sessions and coordinates autonomous work initiation through GitLab.",
        "projects_limit": 100,
        "can_create_group": False,
        "external": True,
        "admin": False,
        "website_url": "",
        "location": "AI Autonomous Swarming System",
        "responsibilities": [
            "Collaborative design leadership",
            "User interaction facilitation", 
            "Multi-agent session coordination",
            "Autonomous work initiation"
        ],
        "gitlab_permissions": [
            "create_issues",
            "update_issues",
            "add_comments",
            "assign_issues",
            "manage_labels",
            "create_projects"
        ]
    }
}

# GitLab project templates for agent coordination
PROJECT_TEMPLATES = {
    "knowledge_base_project": {
        "description_template": "Knowledge Base project for {kb_name} - managed by AI autonomous swarming system",
        "default_labels": [
            "knowledge-base",
            "ai-agents", 
            "autonomous-swarming",
            "content-management"
        ],
        "issue_templates": [
            {
                "title": "📋 KB Planning - {kb_name}",
                "template": "planning_issue_template",
                "assignee_role": "ContentPlannerAgent"
            },
            {
                "title": "✍️ Content Generation - {kb_name}", 
                "template": "content_creation_template",
                "assignee_role": "ContentCreatorAgent"
            },
            {
                "title": "🔍 Quality Review - {kb_name}",
                "template": "quality_review_template", 
                "assignee_role": "ContentReviewerAgent"
            },
            {
                "title": "🚀 Deployment & Maintenance - {kb_name}",
                "template": "deployment_template",
                "assignee_role": "ContentManagementAgent"
            }
        ]
    }
}

# Issue templates for different work types
ISSUE_TEMPLATES = {
    "planning_issue_template": """# Knowledge Base Planning

This issue tracks the overall planning and structure for the **{kb_name}** knowledge base.

## Planning Tasks:
- [ ] Define knowledge base scope and objectives
- [ ] Identify content sources and references
- [ ] Plan article structure and organization
- [ ] Set up content review process
- [ ] Define success criteria and metrics

## Agent Assignments:
- **Assigned To**: ContentPlannerAgent
- **Collaborators**: UserProxyAgent (design input), SupervisorAgent (coordination)
- **Dependencies**: User requirements gathering

## Status:
- **Phase**: Planning
- **KB Name**: {kb_name}
- **Created**: Auto-generated for KB management

/label ~planning ~knowledge-base ~{kb_slug}
""",

    "content_creation_template": """# Content Generation

This issue tracks content creation and generation for the **{kb_name}** knowledge base.

## Content Tasks:
- [ ] Generate initial articles and documentation
- [ ] Create structured content outline
- [ ] Develop comprehensive article content
- [ ] Ensure content quality and accuracy
- [ ] Add relevant tags and metadata

## Agent Assignments:
- **Assigned To**: ContentCreatorAgent
- **Reviewers**: ContentReviewerAgent, SupervisorAgent
- **Dependencies**: Planning phase completion

## Progress Tracking:
- **Articles Created**: 0
- **Articles Reviewed**: 0
- **Content Coverage**: TBD

## Status:
- **Phase**: Content Generation
- **KB Name**: {kb_name}

/label ~content-generation ~knowledge-base ~{kb_slug}
""",

    "quality_review_template": """# Quality Review and Validation

This issue tracks quality assurance and review processes for the **{kb_name}** knowledge base.

## Review Tasks:
- [ ] Content accuracy verification
- [ ] Technical review of articles
- [ ] Format and style consistency check
- [ ] Cross-reference validation
- [ ] User acceptance testing

## Agent Assignments:
- **Assigned To**: ContentReviewerAgent
- **Support**: ContentRetrievalAgent (research validation)
- **Approval**: SupervisorAgent
- **Dependencies**: Content generation completion

## Quality Metrics:
- **Accuracy Score**: TBD
- **Completeness**: TBD
- **User Feedback**: TBD

## Status:
- **Phase**: Quality Review
- **KB Name**: {kb_name}

/label ~quality-review ~knowledge-base ~{kb_slug}
""",

    "deployment_template": """# Deployment and Ongoing Maintenance

This issue tracks deployment and ongoing maintenance for the **{kb_name}** knowledge base.

## Deployment Tasks:
- [ ] Prepare knowledge base for production
- [ ] Deploy to target environment
- [ ] Configure access and permissions
- [ ] Set up monitoring and analytics
- [ ] Document deployment process

## Maintenance Tasks:
- [ ] Regular content updates
- [ ] Performance monitoring
- [ ] User feedback integration
- [ ] Continuous improvement
- [ ] Backup and recovery procedures

## Agent Assignments:
- **Assigned To**: ContentManagementAgent
- **Support**: All agents (maintenance coordination)
- **Oversight**: SupervisorAgent
- **Dependencies**: Quality review completion

## Status:
- **Phase**: Deployment & Maintenance
- **KB Name**: {kb_name}

/label ~deployment ~maintenance ~knowledge-base ~{kb_slug}
"""
}

# Agent role mappings for automatic assignment
AGENT_ROLE_MAPPINGS = {
    "planning": "ContentPlannerAgent",
    "content-creation": "ContentCreatorAgent", 
    "content-generation": "ContentCreatorAgent",
    "quality-review": "ContentReviewerAgent",
    "review": "ContentReviewerAgent",
    "deployment": "ContentManagementAgent",
    "maintenance": "ContentManagementAgent",
    "research": "ContentRetrievalAgent",
    "retrieval": "ContentRetrievalAgent",
    "supervision": "SupervisorAgent",
    "coordination": "SupervisorAgent",
    "user-design": "UserProxyAgent",
    "collaboration": "UserProxyAgent"
}

# Label taxonomy for agent work classification
GITLAB_LABELS = {
    # Work type labels
    "planning": {"color": "#1f77b4", "description": "Strategic planning and architecture tasks"},
    "content-generation": {"color": "#ff7f0e", "description": "Content creation and writing tasks"},
    "quality-review": {"color": "#2ca02c", "description": "Quality assurance and review tasks"},
    "deployment": {"color": "#d62728", "description": "Deployment and maintenance tasks"},
    "research": {"color": "#9467bd", "description": "Research and information gathering tasks"},
    
    # Priority labels
    "priority-high": {"color": "#ff0000", "description": "High priority work items"},
    "priority-medium": {"color": "#ffaa00", "description": "Medium priority work items"},
    "priority-low": {"color": "#00aa00", "description": "Low priority work items"},
    
    # Status labels
    "autonomous-work": {"color": "#17a2b8", "description": "Autonomous agent work"},
    "agent-claimed": {"color": "#6f42c1", "description": "Work claimed by an agent"},
    "supervisor-review": {"color": "#fd7e14", "description": "Pending supervisor review"},
    "rework-needed": {"color": "#dc3545", "description": "Requires rework based on feedback"},
    "collaboration-required": {"color": "#20c997", "description": "Multi-agent collaboration needed"},
    
    # System labels
    "knowledge-base": {"color": "#007bff", "description": "Knowledge base related work"},
    "ai-agents": {"color": "#6610f2", "description": "AI agent system work"},
    "autonomous-swarming": {"color": "#e83e8c", "description": "Autonomous swarming system"}
}


def get_agent_by_username(username: str) -> Dict[str, Any]:
    """Get agent configuration by username"""
    for agent_name, config in AGENT_USERS.items():
        if config['username'] == username:
            return {'name': agent_name, **config}
    return None


def get_agent_usernames() -> List[str]:
    """Get list of all agent usernames"""
    return [config['username'] for config in AGENT_USERS.values()]


def get_agent_emails() -> List[str]:
    """Get list of all agent emails"""
    return [config['email'] for config in AGENT_USERS.values()]


def validate_agent_config() -> Dict[str, List[str]]:
    """Validate agent configuration for conflicts"""
    issues = {
        'duplicate_usernames': [],
        'duplicate_emails': [],
        'invalid_emails': []
    }
    
    usernames = []
    emails = []
    
    for agent_name, config in AGENT_USERS.items():
        username = config['username']
        email = config['email']
        
        # Check for duplicate usernames
        if username in usernames:
            issues['duplicate_usernames'].append(username)
        usernames.append(username)
        
        # Check for duplicate emails
        if email in emails:
            issues['duplicate_emails'].append(email)
        emails.append(email)
        
        # Check email format
        if '@' not in email or not email.endswith('@ai-agents.local'):
            issues['invalid_emails'].append(email)
    
    return issues
