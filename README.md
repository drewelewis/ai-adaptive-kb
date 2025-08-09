# AI Adaptive Knowledge Base

A sophisticated knowledge base management system powered by Azure OpenAI and LangGraph, featuring both single-agent and advanced multi-agent architectures for intelligent content management and user interaction.

## 🏗️ System Architecture

This project provides two distinct approaches to knowledge base management:

### Single-Agent System (Legacy)
A streamlined approach with one intelligent agent handling all operations.

### Multi-Agent System (Current)
An advanced architecture with **seven specialized agents** working in coordination for enhanced user experience, robust content management, and autonomous content creation.

## 🤖 Multi-Agent Architecture (Recommended)

### System Overview

The multi-agent system features two distinct workflows:

1. **Interactive Workflow**: User-driven operations for direct knowledge base management
2. **Autonomous Content Creation Workflow**: AI-driven content generation with minimal supervision

### Agent Flow Diagram

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    USER INTERACTION                        │
                    └─────────────────────┬───────────────────────────────────────┘
                                          │
                              ┌───────────▼────────────┐
                              │    🗣️ UserProxy Agent   │
                              │   (User Interface &    │
                              │   Response Formatting) │
                              └───────────┬────────────┘
                                          │
                              ┌───────────▼────────────┐
                              │    🧭 Router Agent      │
                              │  (Intent Classification │
                              │    & Route Decisions)   │
                              └─────┬─────────────┬─────┘
                                    │             │
                    ┌───────────────▼─────┐      │
                    │  INTERACTIVE FLOW   │      │
                    └─────────────────────┘      │
                              │                  │
                    ┌─────────▼─────────┐       │
                    │ ContentManagement │       │
                    │      Agent        │       │
                    │  (KB Operations)  │       │
                    └─────────┬─────────┘       │
                              │                  │
                    ┌─────────▼─────────┐       │
                    │   🎯 Supervisor    │       │
                    │      Agent        │       │
                    │ (Quality Control) │       │
                    └─────────┬─────────┘       │
                              │                  │
                              │                  │
                              │    ┌─────────────▼──────────────┐
                              │    │    AUTONOMOUS CONTENT      │
                              │    │     CREATION FLOW          │
                              │    └─────────────┬──────────────┘
                              │                  │
                              │        ┌─────────▼─────────┐
                              │        │ 📋 ContentPlanner │
                              │        │     Agent         │
                              │        │ (Strategy & Plan) │
                              │        └─────────┬─────────┘
                              │                  │
                              │        ┌─────────▼─────────┐
                              │        │ ✍️ ContentCreator  │
                              │        │     Agent         │
                              │        │ (Content Writing) │
                              │        └─────────┬─────────┘
                              │                  │
                              │        ┌─────────▼─────────┐
                              │        │ 🔍 ContentReviewer │
                              │        │     Agent         │
                              │        │ (Quality Review)  │
                              │        └─────────┬─────────┘
                              │                  │
                              └──────────────────┘
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │          🗄️ PostgreSQL Database           │
                    │         (All KB Artifacts & State)       │
                    │                                           │
                    │  📚 Knowledge Bases  📄 Articles         │
                    │  🏷️ Tags            📝 Versions          │
                    │  👥 Users           💬 Agent Messages    │
                    │  🔄 Session State   📊 Audit Logs        │
                    └───────────────────────────────────────────┘
```

### Detailed Agent Interaction Flow

```
📊 AGENT COMMUNICATION PATTERNS:

┌─ UserProxy ─┐    ┌─ Router ─┐    ┌─ ContentMgmt ─┐    ┌─ Supervisor ─┐
│  • Receive  │───▶│ • Analyze │───▶│  • Execute    │───▶│  • Validate   │
│    Input    │    │   Intent  │    │    Tools      │    │    Results    │
│  • Format   │◀───│ • Route   │    │  • Manage KB  │◀───│  • Approve/   │
│    Output   │    │   Request │    │  • Log Ops    │    │    Reject     │
└─────────────┘    └───────────┘    └───────────────┘    └───────────────┘
                                                                   │
┌─ ContentPlanner ─┐  ┌─ ContentCreator ─┐  ┌─ ContentReviewer ─┐ │
│  • Analyze Scope │  │  • Generate      │  │  • Review Quality │◀┘
│  • Create Plan   │─▶│    Content       │─▶│  • Optimize       │
│  • Define Hier.  │  │  • Research      │  │  • Validate       │
└───────────────────┘  └──────────────────┘  └───────────────────┘
                                ▲                        │
                                │                        ▼
                       ┌─────────────────────────────────────┐
                       │     🗄️ PostgreSQL Persistence       │
                       │     (ACID Transactions)            │
                       └─────────────────────────────────────┘
```

### Core Agent Architecture

#### 🗣️ UserProxy Agent
- **Role**: Primary user interface and communication gateway
- **Responsibilities**:
  - Handle direct user interactions with natural language processing
  - Format technical responses into user-friendly messages
  - Manage conversation flow and context
  - Provide error handling and recovery guidance
  - Interface with Router for intent classification

#### 🧭 Router Agent  
- **Role**: Intelligent request routing and intent classification
- **Responsibilities**:
  - Analyze user requests to determine appropriate handling agent
  - Classify intent between simple responses and complex operations
  - Route simple queries directly back to UserProxy
  - Route complex operations to ContentManagement or content creation workflow
  - Maintain conversation context for better routing decisions

#### 🎯 Supervisor Agent
- **Role**: Quality assurance and work validation
- **Responsibilities**:
  - Review and validate work completed by ContentManagement agent
  - Ensure operations meet quality standards and user requirements
  - Identify issues or problems in completed work
  - Provide approval/rejection decisions with constructive feedback
  - Coordinate revision cycles when improvements are needed

#### 📚 ContentManagement Agent
- **Role**: Knowledge base operations and strategic content management
- **Responsibilities**:
  - Execute all knowledge base CRUD operations (exclusive tool access)
  - Implement advanced content management strategies
  - Maintain knowledge base consistency and integrity
  - Optimize content organization and discoverability
  - Provide comprehensive audit trails and operation logging

### Autonomous Content Creation Agents

#### 📋 ContentPlanner Agent
- **Role**: Strategic planning and content architecture specialist
- **Responsibilities**:
  - Analyze high-level knowledge base ideas and determine comprehensive scope
  - Create detailed content strategies and article hierarchies
  - Identify knowledge gaps and coverage opportunities
  - Ask intelligent clarifying questions when scope is unclear
  - Design publication-ready content structures
  - Generate implementation plans for ContentCreator

#### ✍️ ContentCreator Agent
- **Role**: Expert content generation and research specialist
- **Responsibilities**:
  - Research and write comprehensive, in-depth articles
  - Maintain expert-level quality across all domains
  - Create content that demonstrates deep understanding
  - Build comprehensive coverage following ContentPlanner strategy
  - Generate cross-references and content relationships
  - Work autonomously with minimal supervision

#### 🔍 ContentReviewer Agent
- **Role**: Quality assurance and optimization specialist
- **Responsibilities**:
  - Review content for expert-level quality and accuracy
  - Ensure comprehensive coverage and depth
  - Optimize content organization and structure
  - Validate publication readiness
  - Coordinate revision cycles when needed
  - Deliver publication-ready knowledge bases

### Advanced Content Management Strategies

#### Interactive Operations
1. **Intelligent Content Organization**
   - Hierarchical content structures with logical depth
   - Optimal parent-child relationships
   - Balanced content distribution across categories

2. **Strategic Content Placement**
   - Analysis of existing structure before additions
   - Content relationship mapping
   - Semantic coherence maintenance

3. **Comprehensive Tagging Strategy**
   - Semantic tag taxonomies for discoverability
   - Strategic cross-referencing capabilities
   - Advanced search and filtering optimization

4. **Content Lifecycle Management**
   - Quality validation before creation/updates
   - Version control and change tracking
   - Content relevance monitoring

5. **Operational Excellence**
   - Multi-stage validation processes
   - Comprehensive error handling and recovery
   - Detailed operation logging and audit trails

#### Autonomous Content Creation
1. **Strategic Content Planning**
   - Comprehensive domain analysis and scope determination
   - Hierarchical content architecture design
   - Knowledge gap identification and coverage optimization
   - Publication-ready content structure planning

2. **Expert Content Generation**
   - Research-driven, authoritative content creation
   - Domain expertise demonstration across all subjects
   - Comprehensive coverage from fundamentals to advanced topics
   - Cross-referencing and relationship building

3. **Quality Assurance and Optimization**
   - Expert-level accuracy and completeness validation
   - Content structure and organization optimization
   - Publication readiness assessment
   - Iterative improvement coordination

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

### PostgreSQL-Based Knowledge Base Management
- **Complete Persistence**: All knowledge bases, articles, and metadata stored in PostgreSQL
- **Hierarchical Organization**: Native parent-child article relationships with unlimited depth
- **Advanced Tagging**: PostgreSQL-backed tagging system with many-to-many relationships
- **Full-Text Search**: PostgreSQL full-text search capabilities across all content
- **Version Control**: Native PostgreSQL versioning for all content changes

### Article Operations  
- **Rich Content Storage**: Articles with markdown formatting stored in PostgreSQL
- **Automatic Versioning**: PostgreSQL triggers create versions on every content change
- **Hierarchical Structure**: Parent-child relationships maintained in database schema
- **Bulk Operations**: Efficient PostgreSQL-based bulk content management
- **Audit Trails**: Complete change tracking with PostgreSQL audit tables

### Tag Management
- **Database-Backed Tags**: All tags stored and managed in PostgreSQL
- **Usage Analytics**: PostgreSQL queries for tag usage optimization  
- **Advanced Search**: PostgreSQL-powered tag search with AND/OR logic
- **Relationship Mapping**: Database foreign keys ensure tag-article integrity

### Autonomous Content Creation
- **Intelligent Planning**: AI-driven content strategy development
- **Expert Generation**: Research-based, authoritative content creation
- **Quality Assurance**: Automated review and optimization cycles
- **Publication Ready**: Complete knowledge bases with minimal human oversight

### Interactive User Interface
- Natural language interaction through UserProxy agent
- Conversational workflow for complex operations
- Real-time operation feedback and status updates
- Comprehensive help and guidance system
- Multi-workflow support (interactive vs. autonomous)

### Advanced Agent Coordination
- **Router-based Intent Classification**: Intelligent request routing
- **Supervisor Quality Control**: Multi-stage validation and approval
- **Specialized Tool Access**: Dedicated agents for specific operations
- **Autonomous Workflows**: Self-directed content creation cycles
- **Error Recovery**: Robust handling with rollback capabilities

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Azure OpenAI API access
- **PostgreSQL database** (primary data store for all knowledge base artifacts)
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
   # Edit .env with your Azure OpenAI and PostgreSQL database credentials
   ```

5. **Set up PostgreSQL database schema**
   ```bash
   # Run the comprehensive schema script to create all tables
   psql -h your_host -U your_user -d your_database -f sql/knowledgebase_schema.sql
   ```

   **Important**: The PostgreSQL schema creates all necessary tables for:
   - Knowledge base and article storage
   - Hierarchical article relationships  
   - Version control and audit trails
   - Tag management and relationships
   - User management and attribution
   - Performance optimization indexes

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
```

**Note**: PostgreSQL serves as the primary persistence layer storing all knowledge base artifacts including articles, hierarchical relationships, tags, versions, and multi-agent state management.

## 💻 Usage

### Multi-Agent System (Recommended)

```bash
python chat_multi_agent.py
```

**Available Commands:**
- **Normal chat**: Ask questions or give commands naturally
- **`/agents`**: Show agent status and tool availability
- **`/reset` or `/r`**: Clear conversation state and restart
- **`/q` or `/quit`**: Exit the system

**Example Interactions:**

*Interactive Operations:*
```
> Can you show me all available knowledge bases?
> I'd like to create a new article about Python programming
> Help me organize the content in my technical documentation KB
> Search for articles related to machine learning
```

*Autonomous Content Creation:*
```
> Create a comprehensive knowledge base about Python data structures
> I need a complete guide on machine learning fundamentals
> Generate expert content covering web development best practices
> Build a knowledge base for database design principles
```

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
│   ├── orchestrator.py             # Main workflow orchestration
│   ├── postgresql_state_manager.py # PostgreSQL state management
│   │
│   ├── # INTERACTIVE WORKFLOW AGENTS
│   ├── user_proxy_agent.py         # User interface agent
│   ├── router_agent.py             # Intent classification and routing
│   ├── supervisor_agent.py         # Quality assurance and validation
│   ├── content_management_agent.py # Knowledge base operations
│   │
│   ├── # AUTONOMOUS CONTENT CREATION AGENTS  
│   ├── content_planner_agent.py    # Strategic content planning
│   ├── content_creator_agent.py    # Expert content generation
│   ├── content_reviewer_agent.py   # Quality review and optimization
│   └── content_retrieval_agent.py  # Specialized content retrieval
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
├── operations/                     # Database operations
│   ├── knowledge_base_operations.py
│   └── github_operations.py
│
├── prompts/                        # System prompts
│   ├── knowledge_base_prompts.py   # Core KB prompts
│   └── multi_agent_prompts.py      # Agent-specific prompts
│
├── tools/                          # Knowledge base tools
│   ├── knowledge_base_tools.py     # Core KB toolset
│   └── github_tools.py
│
├── utils/                          # Utility functions
│   ├── db_change_logger.py
│   ├── langgraph_utils.py
│   ├── llm_intent_classifier.py
│   └── robust_state_manager.py
│
├── sql/                           # PostgreSQL Database Schema
│   └── knowledgebase_schema.sql  # Complete schema for all KB artifacts
│
├── chat_multi_agent.py            # Multi-agent system entry point
├── chat_single_agent.py           # Single-agent system entry point
└── requirements.txt

**Key Storage Architecture**:
- **PostgreSQL Database**: Primary persistence layer for all knowledge base artifacts
- **Complete Schema**: Tables for KB content, articles, tags, versions, and agent state
- **ACID Compliance**: All operations use PostgreSQL transactions for data integrity
```

## 🔄 System Comparison

| Feature | Single-Agent | Multi-Agent |
|---------|--------------|-------------|
| **Architecture** | Monolithic agent | 7 specialized agents |
| **User Interface** | Direct LLM interaction | Dedicated UserProxy with Router |
| **Task Coordination** | Built-in logic | Dedicated Supervisor + Router |
| **Tool Execution** | Direct access | Specialized ContentManagement |
| **Content Creation** | Manual operations | Autonomous content generation |
| **Quality Control** | Basic validation | Multi-stage review process |
| **Error Handling** | Basic recursion limits | Multi-level validation + recovery |
| **User Experience** | Technical responses | Natural language interface |
| **Scalability** | Limited | Highly extensible |
| **Content Strategy** | Basic operations | Advanced planning + implementation |
| **State Management** | In-memory | PostgreSQL with ACID transactions |
| **Workflows** | Single workflow | Dual workflows (interactive + autonomous) |

### Workflow Comparison

#### Interactive Workflow (User-Driven)
- **Entry**: UserProxy receives user input
- **Routing**: Router classifies intent and determines handling
- **Processing**: ContentManagement or direct UserProxy response
- **Validation**: Supervisor reviews complex operations
- **Response**: UserProxy formats and delivers final response

#### Autonomous Workflow (AI-Driven)
- **Planning**: ContentPlanner analyzes request and creates strategy
- **Creation**: ContentCreator generates comprehensive content
- **Review**: ContentReviewer validates quality and optimization
- **Delivery**: UserProxy presents final publication-ready content

## 🛠️ Development

### Adding New Agents
The multi-agent system is designed for extensibility. To add a new agent:

1. **Create Agent Class**: Inherit from `BaseAgent` in the `agents/` directory
2. **Define Specialized Prompts**: Add agent-specific prompts in `multi_agent_prompts.py`
3. **Update Orchestrator**: Add agent node and routing logic in `orchestrator.py`
4. **Configure Tools**: Assign appropriate tools if needed
5. **Update Workflow**: Add conditional edges for agent communication

### Agent Communication Patterns

#### Message-Based Communication
- Agents communicate through `AgentMessage` objects
- Messages include content, metadata, and routing information
- State is managed through `AgentState` dictionary

#### Tool Access Patterns
- **Exclusive Access**: Only ContentManagement has direct tool access
- **Specialized Tools**: Each agent has tools relevant to their role
- **Shared State**: All agents can read from shared state

#### Workflow Integration
- **Router Decisions**: Based on intent classification
- **Conditional Routing**: State-based agent selection
- **Error Handling**: Automatic recovery and rerouting

### PostgreSQL State Management

#### Database Schema
The system uses a comprehensive PostgreSQL schema for complete persistence:

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

#### Key Persistence Features
- **Complete Artifact Storage**: All knowledge base content persisted in PostgreSQL
- **ACID Transactions**: Ensures data consistency across all agent operations
- **Version Control**: Automatic versioning for all content with complete history
- **Audit Trails**: Complete operation logging with agent attribution
- **Recovery Capabilities**: Transaction rollback and error recovery
- **Concurrent Access**: Multi-user session support with proper isolation
- **Hierarchical Support**: Native parent-child article relationships

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📚 Documentation

- **[Getting Started Guide](docs/getting-started-guide.md)** - Comprehensive setup and usage guide
- **[Content Retrieval Agent Implementation](docs/content-retrieval-agent-implementation.md)** - Specialized agent documentation

### Architecture Deep Dive

#### Multi-Agent Coordination
The system uses a sophisticated routing mechanism where:
- **UserProxy** handles all user interaction and response formatting
- **Router** performs intelligent intent classification and routing decisions
- **Supervisor** provides quality assurance and validation oversight
- **ContentManagement** executes all knowledge base operations with exclusive tool access

#### Autonomous Content Creation
The autonomous workflow provides AI-driven content generation:
- **ContentPlanner** analyzes requirements and creates comprehensive strategies
- **ContentCreator** generates expert-level content following planned architecture
- **ContentReviewer** ensures publication quality and optimization

#### State Management Architecture
- **PostgreSQL Backend**: Robust, ACID-compliant persistence layer for all KB artifacts
- **Complete Data Storage**: All knowledge bases, articles, tags, and versions stored in PostgreSQL
- **Session Context**: Persistent conversation and knowledge base context across restarts
- **Message Logging**: Complete audit trail of all agent interactions and decisions
- **Recovery Mechanisms**: Automatic error handling with transaction rollback capabilities
- **Version Control**: Native PostgreSQL storage for all content versions and changes
- **Hierarchical Data**: Native support for article parent-child relationships with unlimited depth

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and dependencies installed
2. **Database Connection**: Verify PostgreSQL credentials in `.env` file
3. **Azure OpenAI**: Check API endpoint and model deployment configuration
4. **Agent Recursion**: Use `/reset` command to clear conversation state
5. **Tool Access Errors**: Ensure ContentManagement agent is properly routing operations

### Debug Mode
Set environment variables for detailed logging:
```bash
export LANGCHAIN_VERBOSE=true
export LANGCHAIN_DEBUG=true
```

### Agent-Specific Debugging

#### UserProxy Issues
- Check message formatting and routing to Router
- Verify conversation context maintenance
- Ensure proper error message display

#### Router Problems  
- Verify intent classification accuracy
- Check routing decision logic
- Ensure proper agent selection

#### Content Creation Issues
- Check ContentPlanner strategy generation
- Verify ContentCreator article generation
- Ensure ContentReviewer quality validation

#### Database State Issues
- Check PostgreSQL connection and schema
- Verify session initialization
- Review audit logs for error patterns

### Performance Optimization

#### Agent Communication
- Monitor message passing efficiency
- Optimize routing decision speed
- Reduce unnecessary agent calls

#### Database Performance
- Index optimization for frequent queries
- Connection pooling configuration
- Transaction optimization

#### Content Generation
- Optimize LLM calls for content creation
- Batch operations where possible
- Cache frequently accessed content

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Powered by [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Database support via [PostgreSQL](https://www.postgresql.org/)

---

**🚀 Multi-Agent System**: Advanced architecture with 7 specialized agents featuring dual workflows for optimal user experience, autonomous content creation, and robust state management.

**📚 Single-Agent System**: Streamlined approach for direct knowledge base operations with simplified architecture.

**🎯 Key Differentiators**: 
- Router-based intelligent routing
- Autonomous content creation workflow  
- PostgreSQL state management with ACID transactions
- Supervisor-based quality assurance
- Specialized agent coordination
