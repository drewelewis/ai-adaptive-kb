# AI Adaptive Knowledge Base - GitHub Copilot Instructions

## Project Overview

This is an autonomous AI multi-agent system for knowledge base content creation and management, integrated with GitLab for work orchestration and PostgreSQL for state management. The system uses Azure OpenAI and LangChain for AI capabilities.

## Core Architecture

### Multi-Agent System
- **Base Agent Pattern**: All agents inherit from `BaseAgent` class in `agents/base_agent.py`
- **Specialized Agents**: Content Creator, Content Planner, Content Retrieval, Content Reviewer, Content Management
- **Orchestration**: Supervisor agent coordinates work distribution and agent collaboration
- **State Management**: PostgreSQL-backed state management for agent coordination

### Technology Stack
- **AI Framework**: LangChain with Azure OpenAI integration
- **Database**: PostgreSQL for state management and knowledge base storage
- **Integration**: GitLab API for work item management and collaboration
- **Deployment**: Docker Compose for local development
- **Authentication**: GitLab Personal Access Tokens (PAT) for agent authentication

## Coding Guidelines

### Python Code Standards

#### Import Organization
```python
# Standard library imports first
import os
import sys
import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

# Third-party imports
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

# Local imports last
from .agent_types import AgentState, AgentMessage
from config.gitlab_agent_mapping import GitLabAgentMapping
```

#### Agent Development Patterns

**Base Agent Inheritance**
- All agents MUST inherit from `BaseAgent`
- Implement required abstract methods
- Use `self.log()` for consistent logging
- Initialize GitLab integration via `GitLabAgentMapping`

**Knowledge Base Context**
- Always maintain KB context: `self.kb_context`
- Include knowledge_base_id, name, description, gitlab_project_id
- Use `set_kb_context()` method for updates

**Error Handling**
```python
try:
    # Agent operations
    result = await self.perform_action()
    self.log(f"✅ Action completed: {result}")
    return result
except Exception as e:
    self.log(f"❌ Error in {self.name}: {str(e)}")
    raise
```

#### Configuration Management

**Environment Variables**
- Use `os.getenv()` with defaults
- Store sensitive data (API keys, tokens) in environment variables
- Never hardcode credentials

**Config Classes**
- Use structured config classes in `config/` directory
- Implement validation in config classes
- Support both environment variables and config files

#### Database Operations

**State Management**
- Use `postgresql_state_manager.py` for agent state persistence
- Implement atomic operations for state updates
- Handle connection pooling appropriately

**Knowledge Base Operations**
- Use `operations/knowledge_base_operations.py` for KB CRUD
- Implement proper transaction handling
- Use parameterized queries to prevent SQL injection

#### GitLab Integration

**Agent Authentication**
- Use centralized PAT token authentication
- All agents access GitLab via `operations/gitlab_operations.py`
- Implement proper error handling for API calls

**Work Item Management**
- Follow GitLab naming standards in `docs/gitlab-work-item-naming-standards.md`
- Use consistent work item creation patterns
- Implement proper issue assignment and tracking

### File Organization

#### Directory Structure
```
agents/           # Agent implementations
config/          # Configuration classes and mappings
docs/           # Documentation and architecture guides
models/         # Data models (Article, KnowledgeBase, Tags)
operations/     # External service operations (GitLab, GitHub, KB)
prompts/        # AI prompts organized by category
scripts/        # Utility and setup scripts
sql/           # Database schemas and migrations
tests/         # Unit and integration tests
tools/         # Utility tools and helpers
utils/         # Common utility functions
```

#### File Naming
- Use snake_case for Python files
- Agent files: `{purpose}_agent.py` (e.g., `content_creator_agent.py`)
- Operation files: `{service}_operations.py` (e.g., `gitlab_operations.py`)
- Config files: `{purpose}_config.py` (e.g., `model_config.py`)
- Temporary/test files: Prefix with `ghcp_` to ensure git ignores them

### Documentation Standards

#### Code Documentation
- Use docstrings for all classes and methods
- Include type hints for all function parameters and returns
- Document complex algorithms and business logic

#### Architectural Documentation
- Keep architecture docs in `docs/` directory updated
- Document agent interactions and workflows
- Maintain GitLab integration guides

### Testing Guidelines

#### Test Structure
- Unit tests for individual agent methods
- Integration tests for agent collaboration
- Mock external services (GitLab, Azure OpenAI)

#### Test Data
- Use fixtures for consistent test data
- Mock database operations where appropriate
- Test error conditions and edge cases

### Security Considerations

#### Credential Management
- Never commit credentials to version control
- Use environment variables for sensitive configuration
- Implement proper token rotation for GitLab PATs

#### Input Validation
- Validate all external inputs (GitLab webhooks, API responses)
- Sanitize user-provided content before processing
- Implement rate limiting for API calls

### Performance Guidelines

#### Agent Efficiency
- Implement caching for frequently accessed data
- Use async/await for I/O operations where possible
- Monitor and log agent performance metrics

#### Database Optimization
- Use connection pooling for database access
- Implement proper indexing for frequent queries
- Monitor query performance and optimize as needed

## AI-Specific Guidelines

### Prompt Engineering
- Store prompts in `prompts/` directory organized by category
- Use consistent prompt templates across agents
- Implement prompt versioning for testing and optimization

### Model Configuration
- Use `config/model_config.py` for Azure OpenAI settings
- Implement proper model selection based on task complexity
- Monitor token usage and costs

### Agent Collaboration
- Use structured message passing between agents
- Implement proper state synchronization
- Design for autonomous operation with minimal human intervention

## Development Workflow

### Local Development
1. Use Docker Compose for local PostgreSQL and GitLab
2. Set up environment variables via `env.bat` or `.env`
3. Run setup scripts: `_env_create.bat`, `_install.bat`, `_seed_database.bat`

### GitLab Integration
1. Set up agent users via `_setup_gitlab_agents.bat`
2. Configure PAT tokens for API access
3. Test agent operations in isolated GitLab projects

### Deployment
- Follow containerization patterns in `docker-compose.yaml`
- Implement proper health checks for services
- Use environment-specific configuration management

## Common Patterns to Follow

### Agent Implementation Template
```python
class SpecificAgent(BaseAgent):
    def __init__(self, llm: AzureChatOpenAI):
        super().__init__(
            name="specific_agent",
            llm=llm,
            system_prompt=SPECIFIC_AGENT_PROMPT
        )
        self.specific_tools = []  # Agent-specific tools
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method for agent requests"""
        try:
            self.log(f"Processing request: {request.get('type', 'unknown')}")
            
            # Set KB context if provided
            if 'kb_context' in request:
                self.set_kb_context(request['kb_context'])
            
            # Process the request
            result = await self._handle_request(request)
            
            self.log(f"✅ Request processed successfully")
            return result
            
        except Exception as e:
            self.log(f"❌ Error processing request: {str(e)}")
            raise
    
    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation-specific request handling"""
        # Implement agent-specific logic here
        pass
```

### Configuration Class Template
```python
class ServiceConfig:
    def __init__(self):
        self.setting1 = os.getenv('SETTING1', 'default_value')
        self.setting2 = os.getenv('SETTING2', 'default_value')
        
    def validate(self) -> bool:
        """Validate configuration settings"""
        # Implement validation logic
        return True
    
    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        """Create config from environment variables"""
        config = cls()
        if not config.validate():
            raise ValueError("Invalid configuration")
        return config
```

## When Making Changes

1. **Always preserve existing patterns** - Follow the established architecture
2. **Update documentation** - Keep docs in sync with code changes
3. **Test agent interactions** - Ensure changes don't break agent collaboration
4. **Maintain GitLab integration** - Test work item creation and assignment
5. **Consider autonomous operation** - Ensure changes support unattended operation
6. **Update configuration** - Add new settings to appropriate config classes
7. **Log appropriately** - Use consistent logging patterns for debugging

## Key Files to Reference

- `agents/base_agent.py` - Base agent implementation patterns
- `config/gitlab_agent_mapping.py` - Agent-to-GitLab user mapping
- `operations/gitlab_operations.py` - GitLab API interaction patterns
- `docs/gitlab-centric-architecture.md` - System architecture overview
- `prompts/` - Prompt templates and organization
