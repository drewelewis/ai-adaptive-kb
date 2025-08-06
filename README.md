# AI Adaptive Knowledge Base

A sophisticated knowledge base management system powered by Azure OpenAI and LangGraph, featuring both single-agent and advanced multi-agent architectures for intelligent content management and user interaction.

## 🏗️ System Architecture

This project provides two distinct approaches to knowledge base management:

### Single-Agent System (Legacy)
A streamlined approach with one intelligent agent handling all operations.

### Multi-Agent System (Current)
An advanced architecture with three specialized agents working in coordination for enhanced user experience and robust content management.

## 🤖 Multi-Agent Architecture (Recommended)

### Agent Overview

```
User Input → UserProxy Agent → Supervisor Agent → ContentManagement Agent
     ↑            ↓                   ↓                      ↓
User Response ← UserProxy ← Supervisor ← ContentManagement Results
```

#### 🗣️ UserProxy Agent
- **Role**: Primary user interface and communication
- **Responsibilities**:
  - Handle direct user interactions with natural language
  - Parse and interpret user intents
  - Translate technical responses to user-friendly language
  - Guide users through complex knowledge base operations
  - Route requests to appropriate system components

#### 🎯 Supervisor Agent
- **Role**: Workflow coordination and task management
- **Responsibilities**:
  - Analyze complex requests and create detailed workflow plans
  - Coordinate between UserProxy and ContentManagement agents
  - Ensure proper operation sequencing and validation
  - Handle error scenarios with recovery procedures
  - Aggregate results from multiple operations into coherent responses

#### 📚 ContentManagement Agent
- **Role**: Knowledge base operations and strategic content management
- **Responsibilities**:
  - Execute all knowledge base operations (exclusive tool access)
  - Implement advanced content management strategies
  - Maintain knowledge base consistency and integrity
  - Optimize content organization and discoverability
  - Provide comprehensive audit trails and operation logging

### Advanced Content Management Strategies

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

## 🔧 Features

### Knowledge Base Management
- Create, update, and manage multiple knowledge bases
- Hierarchical article organization with unlimited depth
- Advanced tagging system for content categorization
- Full-text search and discovery capabilities

### Article Operations
- Create articles with rich markdown formatting
- Update existing content with version tracking
- Organize articles in logical parent-child relationships
- Bulk operations for efficient content management

### Tag Management
- Strategic tag creation and assignment
- Tag usage analytics and optimization
- Advanced search by tags with AND/OR logic
- Tag relationship mapping

### User Interface
- Natural language interaction through UserProxy agent
- Conversational workflow for complex operations
- Real-time operation feedback and status updates
- Comprehensive help and guidance system

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Azure OpenAI API access
- PostgreSQL database
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
   # Edit .env with your Azure OpenAI and database credentials
   ```

5. **Set up database**
   ```bash
   # Run the schema script
   psql -h your_host -U your_user -d your_database -f sql/knowledgebase_schema.sql
   ```

### Configuration

Update your `.env` file with:

```env
# Azure OpenAI Configuration
OPENAI_API_ENDPOINT=your_azure_openai_endpoint
OPENAI_API_MODEL_DEPLOYMENT_NAME=your_model_deployment
OPENAI_API_VERSION=2024-02-15-preview

# Database Configuration
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

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
```
> Can you show me all available knowledge bases?
> I'd like to create a new article about Python programming
> Help me organize the content in my technical documentation KB
> Search for articles related to machine learning
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
├── agents/                     # Multi-agent system components
│   ├── __init__.py
│   ├── agent_types.py         # Data structures and types
│   ├── base_agent.py          # Base agent functionality
│   ├── user_proxy_agent.py    # User interface agent
│   ├── supervisor_agent.py    # Workflow coordination agent
│   └── content_management_agent.py  # Knowledge base operations agent
├── config/                    # Configuration management
├── models/                    # Data models
│   ├── article.py
│   ├── knowledge_base.py
│   └── tags.py
├── operations/                # Database operations
│   └── knowledge_base_operations.py
├── prompts/                   # System prompts
│   ├── knowledge_base_prompts.py
│   └── multi_agent_prompts.py
├── tools/                     # Knowledge base tools
│   └── knowledge_base_tools.py
├── utils/                     # Utility functions
├── sql/                       # Database schema
├── chat_multi_agent.py        # Multi-agent system entry point
├── chat_single_agent.py       # Single-agent system entry point
├── multi_agent_orchestrator.py  # Multi-agent coordination
└── requirements.txt
```

## 🔄 System Comparison

| Feature | Single-Agent | Multi-Agent |
|---------|--------------|-------------|
| **Architecture** | Monolithic agent | 3 specialized agents |
| **User Interface** | Direct LLM interaction | Dedicated UserProxy |
| **Task Coordination** | Built-in logic | Dedicated Supervisor |
| **Tool Execution** | Direct access | Specialized ContentManagement |
| **Error Handling** | Basic recursion limits | Multi-level validation |
| **User Experience** | Technical responses | Natural language interface |
| **Scalability** | Limited | Highly extensible |
| **Content Strategy** | Basic operations | Advanced management strategies |

## 🛠️ Development

### Adding New Agents
The multi-agent system is designed for extensibility. To add a new agent:

1. Create a new agent class inheriting from `BaseAgent`
2. Define specialized prompts in `multi_agent_prompts.py`
3. Update the orchestrator routing logic
4. Add agent to the workflow graph

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📚 Documentation

- **[Multi-Agent Architecture](MULTI_AGENT_ARCHITECTURE.md)** - Detailed system overview
- **[System Comparison](SYSTEM_COMPARISON.md)** - Single vs Multi-agent analysis
- **[Recursion Strategies](RECURSION_STRATEGIES.md)** - Error handling approaches

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and dependencies installed
2. **Database Connection**: Verify PostgreSQL credentials in `.env` file
3. **Azure OpenAI**: Check API endpoint and model deployment configuration
4. **Recursion Limits**: Use `/reset` command to clear conversation state

### Debug Mode
Set environment variables for detailed logging:
```bash
export LANGCHAIN_VERBOSE=true
export LANGCHAIN_DEBUG=true
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Powered by [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Database support via [PostgreSQL](https://www.postgresql.org/)

---

**Multi-Agent System**: Advanced architecture with specialized agents for optimal user experience and robust content management.

**Single-Agent System**: Streamlined approach for direct knowledge base operations.
