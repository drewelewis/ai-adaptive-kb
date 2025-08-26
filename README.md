# AI Adaptive Knowledge Base

A sophisticated autonomous knowledge base management system powered by Azure OpenAI and GitLab integration, featuring advanced multi-agent architectures with autonomous swarming capabilities for intelligent content management and self-directed workflow execution.

## 🏗️ System Architecture

This project provides multiple approaches to knowledge base management:

### Single-Agent System (Legacy)
A streamlined approach with one intelligent agent handling all operations.

### Multi-Agent Interactive System 
An advanced architecture with **seven specialized agents** working in coordination for enhanced user experience and robust content management.

### Autonomous Agent Swarm System (Current - Production Ready)
A cutting-edge **autonomous swarming architecture** where agents self-discover work through GitLab integration, execute tasks independently, and coordinate through standardized workflows for scalable, autonomous knowledge base operations.

## 🤖 Autonomous Agent Swarm Architecture (Production Ready)

### System Overview

The autonomous agent swarm represents the latest evolution in AI-driven knowledge base management, featuring:

1. **Autonomous Work Discovery**: Agents independently scan GitLab projects for available work items
2. **Self-Directed Execution**: Complete task execution from claim to completion without central coordination
3. **GitLab Workflow Integration**: Full integration with GitLab for work coordination, progress tracking, and quality assurance
4. **Standardized Agent Entry Points**: All agents use consistent `process()` methods with 3-step autonomous workflows
5. **Real-Time Content Creation**: Topic-specific content generation based on knowledge base context

### Autonomous Workflow Architecture

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                 AUTONOMOUS SWARMING SYSTEM                  │
                    └─────────────────────┬───────────────────────────────────────┘
                                          │
                              ┌───────────▼────────────┐
                              │   🌐 GitLab Integration │
                              │   (Work Coordination &  │
                              │    Progress Tracking)   │
                              └─────────┬───────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
          ┌─────────▼─────────┐ ┌───────▼───────┐ ┌─────────▼─────────┐
          │ 📋 ContentPlanner │ │ ✍️ ContentCreator │ │ 🔍 ContentReviewer │
          │     Agent         │ │     Agent         │ │     Agent         │
          │ (Strategic Plan)  │ │ (Content Writing) │ │ (Quality Review)  │
          └─────────┬─────────┘ └───────┬───────┘ └─────────┬─────────┘
                    │                   │                   │
                    │  ┌────────────────┼────────────────┐  │
                    │  │                │                │  │
          ┌─────────▼──▼──┐    ┌────────▼────────┐   ┌───▼──▼─────────┐
          │ 📚 ContentMgmt │    │ � ContentRetrieval │   │ 🎯 Supervisor  │
          │     Agent      │    │      Agent        │   │     Agent      │
          │ (KB Operations)│    │ (Research Support)│   │ (Quality Control)│
          └─────────┬──────┘    └─────────────────┘   └────────────────┘
                    │
          ┌─────────▼─────────┐
          │ 🗣️ UserProxy Agent │
          │   (User Interface │
          │   & Coordination) │
          └─────────┬─────────┘
                    │
    ┌───────────────▼──────────────────────────────────────────────┐
    │                 🗄️ PostgreSQL Database                        │
    │               (ACID Transactions & State)                    │
    │                                                              │
    │  📚 Knowledge Bases  📄 Articles      🏷️ Tags                │
    │  👥 Users           💬 Agent State    🔄 Work Coordination    │
    │  📊 Audit Logs     ⚡ Session Context 🎯 Autonomous Cycles   │
    └──────────────────────────────────────────────────────────────┘
```

### Autonomous Agent Workflow Pattern

Each agent follows a standardized 3-step autonomous workflow:

```
🔄 AUTONOMOUS AGENT CYCLE:

1️⃣ ASSIGNED WORK SCAN
   │
   ├─ Check GitLab for assigned issues
   ├─ Process high-priority assigned tasks
   └─ Execute assigned work items
   
2️⃣ AVAILABLE WORK SCAN  
   │
   ├─ Scan GitLab projects for claimable work
   ├─ Filter by agent specialization labels
   ├─ Claim and execute available work items
   └─ Update progress through GitLab
   
3️⃣ AUTONOMOUS ANALYSIS
   │
   ├─ Analyze KB for improvement opportunities
   ├─ Create new work items as needed
   ├─ Generate topic-specific content
   └─ Report completion and continue cycle
```

### Detailed Agent Interaction Flow

```
📊 AUTONOMOUS AGENT COORDINATION PATTERNS:

┌─ UserProxy ─┐    ┌─ GitLab Ops ─┐    ┌─ Agent Swarm ─┐    ┌─ Supervisor ─┐
│  • Interface│───▶│ • Project    │───▶│  • Autonomous │───▶│  • Quality    │
│  • Response │    │   Scanning   │    │    Discovery  │    │    Assurance  │
│  • Context  │◀───│ • Work Items │    │  • Self-Exec  │◀───│  • Validation │
│  • Coord.   │    │ • Progress   │    │  • Completion │    │  • Approval   │
└─────────────┘    └──────────────┘    └───────────────┘    └───────────────┘
                                                                      │
┌─ ContentPlanner ─┐  ┌─ ContentCreator ─┐  ┌─ ContentReviewer ─┐    │
│  • GitLab Scan   │  │  • GitLab Scan   │  │  • GitLab Scan    │◀───┘
│  • Strategic     │─▶│  • Content Gen   │─▶│  • Quality Review │
│  • Work Items    │  │  • Topic-Specific│  │  • Optimization   │
└───────────────────┘  └──────────────────┘  └───────────────────┘
           ▲                        ▲                        │
           │                        │                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                🗄️ PostgreSQL + GitLab Integration              │
│              (ACID Transactions + Work Coordination)           │
└─────────────────────────────────────────────────────────────────┘
```

### Core Agent Architecture

#### 🗣️ UserProxy Agent
- **Role**: System interface and multi-agent coordination gateway
- **Responsibilities**:
  - Handle direct user interactions with natural language processing
  - Coordinate autonomous agent swarm initialization and monitoring
  - Format technical responses into user-friendly messages
  - Manage conversation flow and autonomous cycle reporting
  - Interface with autonomous swarming system for work coordination

#### 🎯 Supervisor Agent
- **Role**: Scrum Master and autonomous work quality assurance
- **Responsibilities**:
  - Monitor autonomous agent work completion through GitLab integration
  - Review and validate work completed by autonomous agents
  - Provide feedback and rework requests through GitLab workflows
  - Coordinate cross-agent communication and conflict resolution
  - Ensure autonomous operations meet quality standards and business requirements

#### 📚 ContentManagement Agent
- **Role**: Knowledge base operations and autonomous workflow orchestration
- **Responsibilities**:
  - Execute all knowledge base CRUD operations with exclusive tool access
  - Scan GitLab projects for content management work items
  - Create prescriptive workflow orchestration for other agents
  - Maintain knowledge base consistency and integrity through autonomous monitoring
  - Provide comprehensive audit trails and operation logging

### Autonomous Content Creation Agents

#### 📋 ContentPlanner Agent
- **Role**: Strategic planning and autonomous content architecture specialist
- **Responsibilities**:
  - Autonomously scan GitLab projects for planning work items
  - Analyze high-level knowledge base ideas and determine comprehensive scope
  - Create detailed content strategies and article hierarchies through GitLab workflows
  - Execute planning work items with progress tracking and completion documentation
  - Design publication-ready content structures for ContentCreator execution
  - Generate implementation plans and coordinate with other autonomous agents

#### ✍️ ContentCreator Agent
- **Role**: Autonomous content generation and topic-specific writing specialist
- **Responsibilities**:
  - Autonomously scan GitLab projects for content creation work items
  - Research and write comprehensive, topic-specific articles (e.g., "Emergency Fund Strategies During Inflationary Times")
  - Maintain expert-level quality across all domains through autonomous execution
  - Create content that demonstrates deep understanding of knowledge base context
  - Build comprehensive coverage following autonomous planning strategies
  - Generate cross-references and content relationships through automated workflows

#### 🔍 ContentReviewer Agent
- **Role**: Autonomous quality assurance and content optimization specialist
- **Responsibilities**:
  - Autonomously scan GitLab projects for review and quality assurance work items
  - Review content for expert-level quality and accuracy through standardized workflows
  - Create and execute quality improvement work items autonomously
  - Optimize content organization and structure through GitLab coordination
  - Validate publication readiness and coordinate revision cycles
  - Deliver publication-ready knowledge bases through autonomous quality processes

#### 📊 ContentRetrieval Agent
- **Role**: Autonomous research and analysis support specialist
- **Responsibilities**:
  - Autonomously scan for research gaps and data gathering opportunities
  - Provide specialized content retrieval and analysis support
  - Execute research work items through GitLab workflow integration
  - Support other agents with topic-specific research and data analysis
  - Maintain research quality standards through autonomous validation processes

### Advanced Autonomous Management Strategies

#### GitLab-Integrated Work Coordination
1. **Autonomous Work Discovery**
   - Real-time scanning of GitLab projects for available work items
   - Intelligent filtering by agent specialization labels (planning, content-creation, review, etc.)
   - Smart conflict avoidance to prevent multiple agents claiming the same work
   - Priority-based work selection using GitLab labels (urgent, high, medium, low)

2. **Standardized Agent Entry Points**
   - All agents use consistent `process()` methods with 3-step autonomous workflows
   - `_scan_assigned_gitlab_work()` - Check for specifically assigned work items
   - `_scan_available_gitlab_work()` - Discover and claim available work items
   - `_execute_gitlab_work()` - Execute work items with progress tracking and completion

3. **Self-Directed Work Execution**
   - Agents claim work items by commenting and adding labels in GitLab
   - Real-time progress updates through GitLab issue comments
   - Comprehensive completion documentation with before/after states
   - Automatic issue closure upon successful work completion

4. **Quality Assurance Integration**
   - Supervisor monitoring of completed work through GitLab labels
   - Automated rework detection and execution when quality issues identified
   - Cross-agent coordination through GitLab issue assignments and comments
   - Comprehensive audit trails for all autonomous operations

#### Intelligent Content Creation
1. **Topic-Specific Content Generation**
   - Context-aware article creation based on knowledge base themes
   - Examples: "Emergency Fund Strategies During Inflationary Times" for financial KBs
   - Expert-level content with 1000+ words per article
   - Comprehensive coverage from fundamentals to advanced topics

2. **Strategic Content Architecture**
   - Autonomous analysis of knowledge base scope and requirements
   - Hierarchical content structure design with logical depth
   - Knowledge gap identification and targeted content creation
   - Cross-referencing and relationship mapping between articles

3. **Quality Optimization Workflows**
   - Automated content quality analysis and improvement suggestions
   - Publication readiness assessment with validation checklists
   - Iterative improvement cycles through GitLab workflow coordination
   - Expert-level accuracy and completeness validation

#### Autonomous System Operations
1. **Multi-KB Environment Support**
   - Parallel operation across multiple knowledge bases simultaneously
   - Context switching and knowledge base-specific content creation
   - GitLab project correlation with knowledge base management
   - Scalable architecture supporting unlimited knowledge base expansion

2. **Error Recovery and Resilience**
   - Automatic error detection and recovery mechanisms
   - Transaction rollback capabilities for failed operations
   - Graceful degradation when external services are unavailable
   - Comprehensive error logging and reporting through GitLab integration

3. **Performance Optimization**
   - Efficient GitLab API usage with intelligent batching and caching
   - Parallel agent execution for maximum throughput
   - Resource optimization for large-scale content generation
   - Smart scheduling to avoid conflicts and maximize productivity

### PostgreSQL Persistence Layer

The system is built on a robust **PostgreSQL persistence layer** that serves as the central storage foundation for all knowledge base artifacts and system state management. This comprehensive database architecture ensures data integrity, performance, and scalability.

#### Knowledge Base Artifact Storage

All knowledge base content is persistently stored in PostgreSQL with the following core tables:

```sql
-- Core Knowledge Base Storage
knowledge_base          -- Knowledge base definitions and metadata
articles               -- Article content with hierarchical structure  
tags                   -- Tag definitions and categorization
article_tags          -- Many-to-many article-tag relationships
users                 -- Author and user management

-- Version Control and Audit
article_versions      -- Complete version history for all articles
knowledge_base_versions -- Knowledge base version tracking
```

**Key Storage Features:**
- **Hierarchical Article Structure**: Native support for parent-child article relationships with unlimited depth
- **Version Control**: Automatic versioning for all content changes with complete history
- **Tagging System**: Flexible many-to-many relationship between articles and tags
- **Author Tracking**: Full user management with creation and modification tracking
- **Audit Trails**: Complete change history with timestamps and user attribution

#### Multi-Agent State Management

The PostgreSQL layer also manages all multi-agent system state and coordination:

```sql
-- Agent State Management  
session_states         -- Persistent conversation context and KB selection
conversation_messages  -- Complete message history between agents
state_audit_log       -- Comprehensive audit trail of all agent actions

-- Performance Optimization
-- GIN indexes for JSONB fields (session_context, agent_context)
-- B-tree indexes for common query patterns
-- Composite indexes for multi-column searches
```

**State Management Features:**
- **ACID Transaction Support**: Ensures data consistency across all operations
- **Session Persistence**: Maintains conversation context across restarts
- **Agent Coordination**: Tracks inter-agent message passing and state changes
- **Recovery Capabilities**: Robust error handling with transaction rollback
- **Concurrent Access**: Multi-user support with proper isolation levels
- **Knowledge Base Context**: Automatic KB selection and context maintenance

#### Database Schema Highlights

1. **Automatic Triggers and Functions**:
   - Auto-updating timestamps on all modifications
   - Automatic version creation when content changes
   - Recursive hierarchy queries for article organization

2. **Performance Optimization**:
   - Comprehensive indexing strategy for all common query patterns
   - GIN indexes for JSONB fields enabling fast metadata searches
   - Composite indexes for multi-column filtering and sorting

3. **Data Integrity**:
   - Foreign key constraints ensuring referential integrity
   - Cascade deletes for proper cleanup
   - Check constraints for data validation

4. **Advanced Features**:
   - Full-text search capabilities on article content
   - Recursive CTE functions for hierarchy traversal
   - JSONB storage for flexible metadata and configuration

The PostgreSQL persistence layer provides the foundation for both the interactive workflow (user-driven operations) and autonomous content creation workflow, ensuring all knowledge base artifacts, agent states, and system metadata are reliably stored and efficiently accessible.

## 🔧 Features

### Autonomous Agent Swarm Architecture
- **GitLab-Integrated Work Coordination**: Full integration with GitLab for autonomous work discovery, claiming, and execution
- **Standardized Agent Entry Points**: All agents use consistent `process()` methods with 3-step autonomous workflows
- **Self-Directed Task Execution**: Agents independently discover, claim, and complete work items without central coordination
- **Real-Time Progress Tracking**: Live updates through GitLab issue comments and label management
- **Quality Assurance Automation**: Supervisor-based review and rework cycles through GitLab workflows

### Advanced Content Creation
- **Topic-Specific Generation**: Context-aware content creation (e.g., "Emergency Fund Strategies During Inflationary Times")
- **Expert-Level Quality**: Comprehensive articles with 1000+ words demonstrating deep domain expertise
- **Strategic Planning**: Autonomous analysis of knowledge base scope with hierarchical content architecture
- **Cross-Agent Coordination**: Seamless collaboration between planning, creation, and review agents
- **Publication-Ready Output**: Complete knowledge bases ready for immediate deployment

### PostgreSQL-Based Knowledge Base Management
- **Complete Persistence**: All knowledge bases, articles, and metadata stored in PostgreSQL with ACID compliance
- **Hierarchical Organization**: Native parent-child article relationships with unlimited depth
- **Advanced Tagging**: PostgreSQL-backed tagging system with many-to-many relationships
- **Full-Text Search**: PostgreSQL full-text search capabilities across all content
- **Version Control**: Native PostgreSQL versioning for all content changes with complete audit trails

### GitLab Integration Features
- **Work Item Management**: Autonomous discovery and execution of GitLab issues across projects
- **Progress Coordination**: Real-time status updates and cross-agent communication through GitLab
- **Quality Workflows**: Supervisor review and rework cycles managed through GitLab issue workflows
- **Audit Trails**: Complete operation history tracked in GitLab with agent attribution
- **Multi-Project Support**: Parallel operations across multiple GitLab projects simultaneously

### Article Operations  
- **Rich Content Storage**: Articles with markdown formatting stored in PostgreSQL
- **Automatic Versioning**: PostgreSQL triggers create versions on every content change
- **Hierarchical Structure**: Parent-child relationships maintained in database schema
- **Bulk Operations**: Efficient PostgreSQL-based bulk content management
- **Context-Aware Creation**: Intelligent content generation based on knowledge base themes

### Tag Management
- **Database-Backed Tags**: All tags stored and managed in PostgreSQL
- **Usage Analytics**: PostgreSQL queries for tag usage optimization  
- **Advanced Search**: PostgreSQL-powered tag search with AND/OR logic
- **Relationship Mapping**: Database foreign keys ensure tag-article integrity

### Multi-Workflow Support
- **Interactive User Interface**: Natural language interaction through UserProxy agent for direct operations
- **Autonomous Content Creation**: Self-directed content generation with minimal human oversight
- **Hybrid Operations**: Seamless switching between user-driven and autonomous execution modes
- **Conversational Workflow**: Real-time operation feedback and status updates
- **Comprehensive Help**: Intelligent guidance system with multi-workflow support

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Azure OpenAI API access
- **PostgreSQL database** (primary data store for all knowledge base artifacts)
- **GitLab instance** (for autonomous work coordination and progress tracking)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/drewelewis/ai-adaptive-kb.git
   cd ai-adaptive-kb
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy env.sample .env
   # Edit .env with your Azure OpenAI, PostgreSQL database, and GitLab credentials
   ```

5. **Set up PostgreSQL database schema**
   ```bash
   # Run the comprehensive schema script to create all tables
   psql -h your_host -U your_user -d your_database -f sql/knowledgebase_schema.sql
   ```

   **Important**: The PostgreSQL schema creates all necessary tables for:
   - Knowledge base and article storage with hierarchical relationships
   - Version control and audit trails for all content changes
   - Tag management and many-to-many relationships
   - User management and attribution tracking
   - Agent state management and coordination
   - Performance optimization indexes for fast queries

6. **Set up GitLab integration**
   ```bash
   # Create GitLab agent users for autonomous coordination
   _setup_gitlab_agents.bat
   
   # Or manually:
   python scripts/gitlab_add_agent_users.py --dry-run  # Preview
   python scripts/gitlab_add_agent_users.py            # Create users
   ```

   **Important**: GitLab integration enables:
   - Autonomous work discovery and coordination across agents
   - Real-time progress tracking and status updates
   - Quality assurance workflows with supervisor review
   - Cross-agent communication and conflict resolution
   - Comprehensive audit trails for all autonomous operations

### Configuration

Update your `.env` file with:

```env
# Azure OpenAI Configuration
OPENAI_API_ENDPOINT=your_azure_openai_endpoint
OPENAI_API_MODEL_DEPLOYMENT_NAME=your_model_deployment
OPENAI_API_VERSION=2024-02-15-preview

# PostgreSQL Database Configuration (Primary Data Store)
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# GitLab Integration Configuration (Autonomous Work Coordination)
GITLAB_URL=http://localhost:8929
GITLAB_TOKEN=your_gitlab_access_token
GITLAB_PROJECTS_ROOT=your_gitlab_namespace
```

**Note**: 
- **PostgreSQL** serves as the primary persistence layer storing all knowledge base artifacts including articles, hierarchical relationships, tags, versions, and multi-agent state management
- **GitLab** enables autonomous work coordination, progress tracking, and quality assurance workflows across all agents

## 💻 Usage

### Autonomous Agent Swarm System (Recommended - Production Ready)

#### Interactive Mode with Autonomous Background Operations
```bash
python chat_multi_agent.py
```

**Available Commands:**
- **Normal chat**: Ask questions or give commands naturally
- **`/agents`**: Show autonomous agent status and GitLab work coordination
- **`/reset` or `/r`**: Clear conversation state and restart autonomous cycles
- **`/q` or `/quit`**: Exit the system

**Example Interactions:**

*Interactive Operations with Autonomous Support:*
```
> Can you show me all available knowledge bases?
> I'd like to create a new article about Python programming
> Help me organize the content in my technical documentation KB
> Search for articles related to machine learning
```

*Autonomous Content Creation Requests:*
```
> Create a comprehensive knowledge base about "Inflation-Proof Family Finances"
> I need expert content covering machine learning fundamentals
> Generate a complete guide on web development best practices
> Build a knowledge base for database design principles
```

#### Direct Autonomous Swarm Execution
```bash
python content_agent_swarm.py
```

This runs the autonomous agent swarm directly, where agents:
- **Autonomously scan GitLab projects** for available work items
- **Claim and execute work** independently without central coordination
- **Create topic-specific content** based on knowledge base context
- **Provide real-time progress updates** through GitLab integration
- **Complete quality assurance cycles** with supervisor review

**Example Autonomous Cycle Output:**
```
🚀 Initializing Multi-Agent System (Session: 028dbea7...)
✅ PostgreSQL state management initialized
🎯 Auto-selecting preferred knowledge base: Inflation-Proof Family Finances (ID: 13)

[SYNC] Autonomous Cycle #1 - 19:46:11
------------------------------------------------------------
📋 ContentPlannerAgent: Found GitLab planning work - claiming and executing...
✍️ ContentCreatorAgent: Found content creation work - claiming and executing...
🔍 ContentReviewerAgent: Found quality review work - claiming and executing...

✅ ContentCreatorAgent created 4 topic-specific articles:
   • "Building a Resilient Emergency Fund During Inflationary Times" (ID: 145)
   • "Smart Grocery Shopping Tips to Manage Rising Food Costs" (ID: 146)
   • "Teaching Children About Money in an Inflationary Economy" (ID: 147)
   • "Budgeting Techniques and Cost-Cutting Ideas for Families" (ID: 148)

[STATS] Cycle Summary: 5/6 agents found work
```

### Multi-Agent Interactive System 

```bash
python chat_multi_agent.py --mode=interactive
```

Traditional interactive mode with user-driven operations and agent coordination.

### Single-Agent System (Legacy)

```bash
python chat_single_agent.py
```

**Available Commands:**
- **`/reset` or `/r`**: Clear conversation state
- **`/q` or `/quit`**: Exit the system

## 📁 Project Structure

```
ai-adaptive-kb/
├── agents/                          # Multi-agent system components
│   ├── __init__.py
│   ├── agent_types.py              # Data structures and types
│   ├── base_agent.py               # Base agent functionality
│   ├── orchestrator.py             # Multi-agent workflow orchestration
│   ├── postgresql_state_manager.py # PostgreSQL state management
│   │
│   ├── # USER INTERFACE & COORDINATION AGENTS
│   ├── user_proxy_agent.py         # User interface and autonomous system coordination
│   ├── supervisor_agent.py         # Quality assurance and autonomous work validation
│   ├── content_management_agent.py # Knowledge base operations and workflow orchestration
│   │
│   ├── # AUTONOMOUS CONTENT CREATION AGENTS  
│   ├── content_planner_agent.py    # Strategic content planning with GitLab integration
│   ├── content_creator_agent.py    # Expert content generation with autonomous workflows
│   ├── content_reviewer_agent.py   # Quality review and optimization with GitLab coordination
│   └── content_retrieval_agent.py  # Specialized content retrieval and research support
│
├── config/                         # Configuration management
│   ├── config_validator.py
│   ├── deployment_config.py
│   └── model_config.py
│
├── models/                         # Data models
│   ├── article.py
│   ├── knowledge_base.py
│   └── tags.py
│
├── operations/                     # Database and external service operations
│   ├── knowledge_base_operations.py # PostgreSQL KB operations
│   └── gitlab_operations.py        # GitLab integration and work coordination
│
├── prompts/                        # System prompts
│   ├── knowledge_base_prompts.py   # Core KB prompts
│   └── multi_agent_prompts.py      # Agent-specific prompts
│
├── tools/                          # Knowledge base and integration tools
│   ├── knowledge_base_tools.py     # Core KB toolset
│   └── gitlab_tools.py             # GitLab integration tools for autonomous coordination
│
├── utils/                          # Utility functions
│   ├── db_change_logger.py
│   ├── langgraph_utils.py
│   ├── llm_intent_classifier.py
│   └── robust_state_manager.py
│
├── scripts/                        # Automation and setup scripts
│   ├── gitlab_add_agent_users.py   # GitLab agent user creation for autonomous coordination
│   ├── gitlab_agent_config.py      # Agent user definitions and templates
│   └── README.md                   # Script documentation and setup guide
│
├── sql/                           # PostgreSQL Database Schema
│   └── knowledgebase_schema.sql  # Complete schema for all KB artifacts and agent state
│
├── content_agent_swarm.py         # Autonomous agent swarm system entry point
├── chat_multi_agent.py            # Multi-agent system with interactive and autonomous modes
├── chat_single_agent.py           # Single-agent system entry point (legacy)
├── _setup_gitlab_agents.bat       # Windows one-click GitLab agent setup
└── requirements.txt

**Key Architecture Components**:
- **Autonomous Agent Swarm**: Self-coordinating agents with GitLab integration
- **PostgreSQL Database**: Primary persistence layer for all knowledge base artifacts and agent state
- **GitLab Integration**: Work coordination, progress tracking, and quality assurance workflows
- **Standardized Agent Entry Points**: Consistent `process()` methods across all agents
- **Multi-Mode Operation**: Interactive user-driven and autonomous self-directed execution modes
```

## 🔄 System Comparison

| Feature | Single-Agent | Multi-Agent Interactive | Autonomous Agent Swarm |
|---------|--------------|-------------------------|------------------------|
| **Architecture** | Monolithic agent | 7 specialized agents | 6 autonomous swarming agents |
| **Work Coordination** | Built-in logic | Router-based orchestration | GitLab-integrated autonomous discovery |
| **Task Execution** | Direct access | Specialized ContentManagement | Self-directed with standardized entry points |
| **Content Creation** | Manual operations | Planned autonomous generation | Topic-specific autonomous creation |
| **Quality Control** | Basic validation | Supervisor validation | GitLab workflow-based QA with rework cycles |
| **Progress Tracking** | None | In-memory state | Real-time GitLab integration |
| **Error Handling** | Basic recursion limits | Multi-level validation + recovery | Autonomous error recovery with audit trails |
| **User Experience** | Technical responses | Natural language interface | Autonomous operation with user oversight |
| **Scalability** | Limited | Moderately extensible | Highly scalable with parallel execution |
| **Work Discovery** | User-directed | Router classification | Autonomous GitLab scanning |
| **State Management** | In-memory | PostgreSQL with ACID transactions | PostgreSQL + GitLab state coordination |
| **Agent Coordination** | N/A | Message-based coordination | GitLab issue-based coordination |
| **Content Quality** | Basic | Planned comprehensive coverage | Expert-level topic-specific content |

### Workflow Comparison

#### Interactive Workflow (User-Driven)
- **Entry**: UserProxy receives user input and coordinates with autonomous system
- **Processing**: Direct ContentManagement operations or coordination with autonomous agents
- **Validation**: Supervisor reviews complex operations through GitLab workflows
- **Response**: UserProxy formats and delivers results with autonomous operation status

#### Autonomous Workflow (Self-Directed)
- **Discovery**: Agents independently scan GitLab projects for available work items
- **Claiming**: Agents claim work by commenting and adding labels in GitLab
- **Execution**: Standardized `process()` methods with 3-step autonomous workflows
- **Coordination**: Cross-agent communication through GitLab issue assignments and comments
- **Quality Assurance**: Supervisor review and rework cycles through GitLab workflows
- **Completion**: Comprehensive documentation and automatic issue closure

#### Autonomous Swarming Benefits
- **Parallel Execution**: Multiple agents work simultaneously across different knowledge bases
- **Scalable Architecture**: Natural load balancing based on agent availability and work priority  
- **Self-Organization**: Agents discover and prioritize work without central coordination
- **Quality Assurance**: Built-in review cycles with comprehensive audit trails
- **Fault Tolerance**: Automatic error recovery and transaction rollback capabilities

## 🛠️ Development

### Adding New Autonomous Agents
The autonomous agent swarm system is designed for extensibility. To add a new agent:

1. **Create Agent Class**: Inherit from `BaseAgent` in the `agents/` directory
2. **Implement Standardized Methods**: Add `_scan_assigned_gitlab_work()`, `_scan_available_gitlab_work()`, and `_execute_gitlab_work()` methods
3. **Define Agent Prompts**: Add agent-specific prompts in `multi_agent_prompts.py` 
4. **Update Swarm Configuration**: Add agent configuration in `content_agent_swarm.py`
5. **Configure GitLab Integration**: Add agent user and labels for work discovery
6. **Test Autonomous Workflows**: Verify agent can discover, claim, and execute work items independently

### Autonomous Agent Communication Patterns

#### GitLab-Based Coordination
- Agents coordinate through GitLab issue assignments, comments, and labels
- Work items tracked through complete GitLab issue lifecycle management
- Cross-agent communication via GitLab mentions and issue references
- Progress tracking through real-time GitLab status updates

#### Standardized Entry Points
- **All agents use consistent `process()` methods** with 3-step autonomous workflows
- **Step 1**: `_scan_assigned_gitlab_work()` - Check for assigned work items
- **Step 2**: `_scan_available_gitlab_work()` - Discover and claim available work
- **Step 3**: `_execute_gitlab_work()` - Execute work with progress tracking and completion

#### Work Discovery Patterns
- **Autonomous Scanning**: Agents continuously scan GitLab projects for available work
- **Label-Based Filtering**: Work items filtered by agent specialization labels
- **Priority-Based Selection**: Work prioritized using GitLab labels (urgent, high, medium, low)
- **Conflict Avoidance**: Smart detection to prevent multiple agents claiming same work

#### Quality Assurance Integration
- **Supervisor Monitoring**: Automatic detection of completed work through GitLab labels
- **Review Workflows**: Structured review and feedback cycles through GitLab comments
- **Rework Processing**: Automatic detection and execution of rework requests
- **Audit Trails**: Complete operation history tracked in GitLab with agent attribution

### PostgreSQL + GitLab State Management

#### Dual-Layer State Architecture
The system uses a sophisticated dual-layer state management approach:

**PostgreSQL Layer (Persistent Data)**:
```sql
-- KNOWLEDGE BASE ARTIFACT STORAGE
knowledge_base           -- KB definitions, metadata, and versioning
articles                -- Hierarchical article content with parent-child relationships
article_versions        -- Complete version history for all content changes
tags                    -- Tag definitions scoped to knowledge bases  
article_tags           -- Many-to-many article-tag relationships
users                  -- Author and user management with audit tracking

-- MULTI-AGENT STATE MANAGEMENT
session_states         -- Persistent conversation context and KB selection
conversation_messages  -- Complete agent message history and coordination
state_audit_log       -- Comprehensive audit trail of all agent actions and decisions

-- PERFORMANCE AND INTEGRITY
-- Automatic triggers for versioning and timestamps
-- GIN indexes for JSONB metadata searches
-- Composite indexes for multi-column query optimization
-- Foreign key constraints ensuring referential integrity
```

**GitLab Layer (Work Coordination)**:
- **Issue Management**: All work items tracked as GitLab issues with labels and assignments
- **Progress Tracking**: Real-time status updates through issue comments and label changes
- **Agent Coordination**: Cross-agent communication via issue mentions and references
- **Quality Workflows**: Supervisor review and rework cycles managed through GitLab workflows
- **Audit Trails**: Complete operation history with timestamps and agent attribution

#### Key Integration Features
- **Synchronized State**: PostgreSQL and GitLab state automatically synchronized
- **ACID Transactions**: Ensures data consistency across both PostgreSQL and GitLab operations
- **Autonomous Recovery**: Automatic state recovery when external services are unavailable
- **Multi-Agent Support**: Concurrent access with proper isolation levels across all agents
- **Knowledge Base Context**: Automatic KB selection and context maintenance across both layers
- **Cross-Platform Audit**: Complete operation tracking across PostgreSQL and GitLab systems

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes with GitLab integration support
4. Add tests for autonomous agent functionality if applicable
5. Submit a pull request with documentation updates

## 📚 Documentation

- **[Getting Started Guide](docs/getting-started-guide.md)** - Comprehensive setup and usage guide
- **[Autonomous Swarming Architecture](docs/autonomous-swarming-architecture.md)** - Complete autonomous agent system documentation
- **[Autonomous Swarming Implementation](docs/autonomous-swarming-implementation.md)** - Implementation details and technical specifications
- **[GitLab Agent Integration](docs/gitlab-agent-integration-complete.md)** - GitLab integration setup and agent coordination
- **[Multi-Agent GitLab Implementation](docs/multi-agent-gitlab-implementation-summary.md)** - Complete GitLab workflow integration guide

### Architecture Deep Dive

#### Autonomous Agent Coordination
The system uses a sophisticated GitLab-based coordination mechanism where:
- **UserProxy** handles all user interaction, response formatting, and autonomous system oversight
- **Supervisor** provides quality assurance, validation oversight, and autonomous work review
- **ContentManagement** executes knowledge base operations and creates prescriptive workflows for other agents
- **All Content Agents** use standardized `process()` methods with 3-step autonomous workflows

#### Autonomous Content Creation Workflow
The autonomous workflow provides AI-driven content generation with GitLab coordination:
- **ContentPlanner** analyzes requirements and creates comprehensive strategies through GitLab issues
- **ContentCreator** generates expert-level, topic-specific content following planned architecture
- **ContentReviewer** ensures publication quality and optimization through autonomous quality processes

#### GitLab-Integrated State Management Architecture
- **PostgreSQL Backend**: Robust, ACID-compliant persistence layer for all KB artifacts and agent state
- **GitLab Integration**: Work coordination, progress tracking, and quality assurance workflows
- **Dual-Layer State**: Synchronized state management across PostgreSQL and GitLab systems
- **Complete Data Storage**: All knowledge bases, articles, tags, and versions stored in PostgreSQL
- **Work Coordination**: All agent work items, progress, and coordination managed through GitLab
- **Session Context**: Persistent conversation and knowledge base context across restarts
- **Message Logging**: Complete audit trail of all agent interactions and GitLab operations
- **Recovery Mechanisms**: Automatic error handling with transaction rollback and GitLab state recovery
- **Version Control**: Native PostgreSQL storage for all content versions and changes
- **Hierarchical Data**: Native support for article parent-child relationships with unlimited depth
- **Agent State Synchronization**: Real-time coordination between PostgreSQL state and GitLab work items

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and dependencies installed
2. **Database Connection**: Verify PostgreSQL credentials in `.env` file
3. **GitLab Connection**: Check GitLab URL and access token configuration
4. **Azure OpenAI**: Check API endpoint and model deployment configuration
5. **Agent Coordination**: Use `/agents` command to check autonomous agent status
6. **Work Discovery**: Verify GitLab agent users are created and have project access
7. **Autonomous Cycles**: Use `/reset` command to restart autonomous cycles if agents appear stuck

### Debug Mode
Set environment variables for detailed logging:
```bash
export LANGCHAIN_VERBOSE=true
export LANGCHAIN_DEBUG=true
export GITLAB_DEBUG=true
```

### Agent-Specific Debugging

#### UserProxy Issues
- Check autonomous system coordination and GitLab integration status
- Verify conversation context maintenance and autonomous cycle reporting
- Ensure proper error message display and autonomous operation oversight

#### Autonomous Agent Issues
- Check GitLab project access and agent user permissions
- Verify work discovery scanning and claiming functionality
- Review standardized `process()` method execution and error handling
- Monitor GitLab issue lifecycle and progress tracking

#### Content Creation Issues
- Check ContentPlanner strategic analysis and GitLab issue creation
- Verify ContentCreator topic-specific content generation and KB context usage
- Ensure ContentReviewer quality validation and autonomous improvement processes
- Review cross-agent coordination through GitLab issue assignments and comments

#### Database + GitLab State Issues
- Check PostgreSQL connection and schema integrity
- Verify GitLab API connectivity and authentication
- Review session initialization and dual-layer state synchronization
- Examine audit logs for error patterns across both PostgreSQL and GitLab systems

### Performance Optimization

#### Autonomous Agent Coordination
- Monitor GitLab API usage efficiency and implement rate limiting
- Optimize work discovery scanning frequency and project filtering
- Reduce unnecessary GitLab API calls through intelligent caching
- Balance autonomous cycle frequency with system resource usage

#### Database + GitLab Performance
- Index optimization for frequent PostgreSQL queries
- GitLab API response caching and intelligent batching
- Connection pooling configuration for both PostgreSQL and GitLab
- Transaction optimization across dual-layer state management

#### Content Generation Optimization
- Optimize LLM calls for autonomous content creation workflows
- Implement intelligent content caching for similar knowledge base topics
- Batch GitLab operations where possible to reduce API overhead
- Smart scheduling of autonomous cycles to maximize agent productivity

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- Built with [LangChain](https://langchain.com/) for multi-agent orchestration and LLM integration
- Powered by [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) for intelligent content generation
- Database support via [PostgreSQL](https://www.postgresql.org/) for comprehensive persistence and ACID transactions
- Work coordination through [GitLab](https://gitlab.com/) for autonomous agent collaboration and progress tracking

---

**🚀 Autonomous Agent Swarm System**: Cutting-edge architecture with 6 autonomous agents featuring GitLab-integrated work coordination, standardized entry points, and self-directed workflow execution for scalable, autonomous knowledge base operations.

**🎯 Key Differentiators**: 
- GitLab-integrated autonomous work discovery and coordination
- Standardized agent entry points with 3-step autonomous workflows  
- Topic-specific content creation (e.g., "Emergency Fund Strategies During Inflationary Times")
- Real-time progress tracking and quality assurance through GitLab workflows
- Dual-layer state management with PostgreSQL + GitLab integration
- Self-directed agent execution with comprehensive audit trails
