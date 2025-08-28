---
applyTo: '**'
description: 'AI Adaptive Knowledge Base - Autonomous Multi-Agent System for Knowledge Base Management'
---

# Project Context

This is an autonomous AI multi-agent system for knowledge base content creation and management. The system integrates with GitLab for work orchestration and uses PostgreSQL for state management, built on Azure OpenAI and LangChain.

## Core Components

- **Multi-Agent Architecture**: Specialized AI agents for content creation, planning, retrieval, review, and management
- **GitLab Integration**: Work item management, issue tracking, and agent collaboration
- **State Management**: PostgreSQL-backed persistent state for agent coordination
- **AI Framework**: LangChain with Azure OpenAI for natural language processing
- **Containerized Deployment**: Docker Compose for local development and testing

## Key Patterns

### Agent Development
- All agents inherit from `BaseAgent` class
- Use structured logging with `self.log()`
- Maintain knowledge base context via `self.kb_context`
- Implement GitLab integration through `GitLabAgentMapping`

### Configuration Management
- Environment-based configuration with `os.getenv()`
- Structured config classes in `config/` directory
- Never hardcode credentials or sensitive data

### Error Handling
- Use try/catch with structured logging
- Implement proper exception propagation
- Include contextual information in error messages

### Database Operations
- Use parameterized queries to prevent SQL injection
- Implement proper transaction handling
- Use connection pooling for performance

## File Organization

```
agents/         # Agent implementations inheriting from BaseAgent
config/         # Configuration classes and mappings
docs/          # Architecture and implementation documentation
models/        # Data models (Article, KnowledgeBase, Tags)
operations/    # External service operations (GitLab, GitHub, KB)
prompts/       # AI prompts organized by category and agent type
scripts/       # Setup and utility scripts
sql/          # Database schemas and migration scripts
tests/        # Unit and integration tests
tools/        # Utility tools and helpers
utils/        # Common utility functions
```

## Development Guidelines

1. **Follow established patterns** - Use existing architecture and code patterns
2. **Maintain GitLab integration** - Ensure all agent operations work with GitLab API
3. **Support autonomous operation** - Design for unattended, self-directed agent behavior
4. **Use consistent logging** - Follow established logging patterns with emoji indicators
5. **Implement proper error handling** - Include context and graceful degradation
6. **Update documentation** - Keep architecture docs synchronized with code changes
7. **Test agent interactions** - Verify multi-agent collaboration works correctly
8. **File naming conventions** - When creating temporary or test files, always prefix with `ghcp_` so they are ignored by git

## Technology Stack

- **Python 3.x** with type hints and async/await patterns
- **LangChain** for AI agent framework and prompt management
- **Azure OpenAI** for language model integration
- **PostgreSQL** for data persistence and state management
- **GitLab API** for work item management and collaboration
- **Docker & Docker Compose** for containerization and local development

## Security & Best Practices

- Store sensitive configuration in environment variables
- Use GitLab Personal Access Tokens for API authentication
- Implement input validation for all external data
- Follow principle of least privilege for database access
- Monitor and log all agent activities for audit trails
