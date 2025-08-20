# GitLab Work Item Naming Standards

## 🎯 Purpose

This document defines standardized naming conventions for GitLab work items created by the Supervisor Agent to ensure consistency, discoverability, and proper coordination across multiple knowledge bases.

## 📋 Standardized Work Item Naming Conventions

### **Primary Work Item Types**

| Work Type | Title Format | Purpose | Primary Agent | Content Gate |
|-----------|-------------|---------|---------------|--------------|
| **KB Definition (REQUIRED FIRST)** | `Define KB: [KB Name]` | KB definition and planning gate | All Agents (input) | **MUST BE CLOSED** before content creation |
| **Content Planning** | `KB-PLAN: [KB Name] - Content Planning & Strategy` | Strategic content planning and structure design | ContentPlannerAgent | Requires closed "Define KB" |
| **Content Creation** | `KB-CREATE: [KB Name] - Content Development` | Article creation and content development | ContentCreatorAgent | Requires closed "Define KB" |
| **Content Review** | `KB-REVIEW: [KB Name] - Quality Assurance & Review` | Quality review and optimization | ContentReviewerAgent | Requires closed "Define KB" |
| **Content Research** | `KB-RESEARCH: [KB Name] - Research & Analysis` | Domain research and competitive analysis | ContentRetrievalAgent | Requires closed "Define KB" |
| **KB Updates** | `KB-UPDATE: [KB Name] - Knowledge Base Updates` | Ongoing KB maintenance and updates | ContentManagementAgent | May proceed if KB exists |

### **Specialized Work Item Types**

| Work Type | Title Format | Purpose |
|-----------|-------------|---------|
| **Cross-KB Analysis** | `KB-ANALYSIS: Multi-KB - Cross-Knowledge Base Analysis` | Analysis across multiple KBs |
| **KB Migration** | `KB-MIGRATE: [KB Name] - Knowledge Base Migration` | KB structure or content migration |
| **KB Integration** | `KB-INTEGRATE: [KB Name] - System Integration` | Third-party integrations |
| **Human Feedback** | `KB-FEEDBACK: [KB Name] - Human Review Required` | Items requiring human input |

## 🚪 "Define KB" Gate Requirement

### **Critical Workflow Gate**
The "Define KB: [KB Name]" work item serves as a **mandatory gate** for all content creation:

- **MUST be created FIRST** for every new knowledge base
- **MUST be CLOSED** before any content creation can begin
- Content agents can contribute input and ask questions while it's open
- Content creation work items are blocked until this gate is closed

### **Gate Workflow**
1. Supervisor creates "Define KB: [KB Name]" (state: opened)
2. All content agents can contribute planning input via comments
3. Human stakeholders provide feedback and requirements
4. KB definition is finalized with clear scope and structure  
5. Supervisor closes "Define KB" work item (state: closed)
6. Content creation work items can now be processed

### **Agent Behavior During Gate**
- **Input Phase** (Define KB open): Agents contribute planning input, ask questions, provide suggestions
- **Creation Phase** (Define KB closed): Agents can process content creation work items
- **Gate Check**: All agents must verify "Define KB" status before content operations

## 🏷️ Label Standards

### **Required Labels for All Work Items**
- `supervisor-created` - Identifies supervisor-created work items
- `kb-[domain]` - Knowledge base domain (e.g., `kb-marketing`, `kb-technology`)
- Priority level: `high-priority`, `medium-priority`, `low-priority`
- Agent assignment: `content-management`, `content-planner`, `content-creator`, `content-reviewer`, `content-retrieval`

### **Special Labels for Define KB Work Items**
- `define-kb` - Marks the mandatory definition gate work item
- `planning-phase` - Indicates planning/input phase activity
- `content-gate` - Identifies work items that gate content creation

### **Optional Labels**
- `urgent` - Requires immediate attention
- `blocked` - Work item is blocked waiting for dependencies
- `human-input-required` - Needs human feedback or approval
- `cross-kb` - Work spans multiple knowledge bases
- `gate-closed` - Define KB has been completed (for reference)

## 📝 Work Item Description Template

### **Define KB Work Item Template**
```markdown
**Target KB:** [Knowledge Base Name]
**KB Domain:** [Topic area and scope]
**KB Context:** [Strategic purpose and background]

**Definition Requirements:**
- [ ] Finalize KB scope and boundaries
- [ ] Define target audience and use cases
- [ ] Establish content structure and hierarchy
- [ ] Clarify success criteria and objectives
- [ ] Identify required resources and timeline

**Planning Input Required:**
- [ ] ContentPlanner: Strategic structure recommendations
- [ ] ContentCreator: Content development feasibility assessment  
- [ ] ContentReviewer: Quality standards and review criteria
- [ ] ContentRetrieval: Research requirements and source identification
- [ ] ContentManagement: Technical implementation considerations

**Human Input Required:**
- [ ] Stakeholder approval of scope and objectives
- [ ] Budget and resource allocation confirmation
- [ ] Timeline and milestone approval
- [ ] Success criteria validation

**Completion Criteria:**
- [ ] All content agents have provided input
- [ ] Human stakeholders have approved the definition
- [ ] KB scope, structure, and objectives are clearly defined
- [ ] Success criteria and completion standards are established
- [ ] Ready to proceed with content creation work items

**Gate Status:** 
- ⚠️ **OPEN**: Content creation is BLOCKED - planning phase active
- ✅ **CLOSED**: Content creation is UNBLOCKED - definition complete
```

### **KB-CREATE Work Item Template** (requires closed Define KB)
```markdown
**Target KB:** [Knowledge Base Name]
**KB Domain:** [Topic area and scope]
**KB Context:** [Strategic purpose and background]

**Setup Requirements:**
- [ ] Create knowledge base in system
- [ ] Set KB context and metadata
- [ ] Initialize basic structure
- [ ] Configure access permissions

**Analysis Requirements:**
- [ ] Content gap analysis
- [ ] Structure assessment
- [ ] Research needs identification
- [ ] Resource requirements evaluation

**Team Coordination:**
- [ ] Create follow-up work items for ContentPlanner
- [ ] Assign research tasks to ContentRetrieval
- [ ] Schedule planning session with ContentCreator
- [ ] Set up review process with ContentReviewer

**Success Criteria:**
- [ ] KB successfully created and configured
- [ ] Initial analysis complete
- [ ] Work items created for all content agents
- [ ] Team coordination established

**Human Input Required:**
- [Any specific human requirements or feedback needed]

**Next Steps:**
- [Planned follow-up work items and assignments]
```

## 🔍 Filtering and Discovery

### **Agent Work Discovery Patterns**
Agents can use these filters to discover their assigned work:

- **ContentManagementAgent**: `labels:supervisor-created,content-management state:opened`
- **ContentPlannerAgent**: `labels:supervisor-created,content-planner state:opened`
- **ContentCreatorAgent**: `labels:supervisor-created,content-creator state:opened`
- **ContentReviewerAgent**: `labels:supervisor-created,content-reviewer state:opened`
- **ContentRetrievalAgent**: `labels:supervisor-created,content-retrieval state:opened`

### **KB-Specific Filtering**
To work on specific knowledge bases:
- `labels:kb-marketing state:opened` - All marketing KB work items
- `title:KB-INIT` - All KB initialization work items
- `title:"Digital Marketing"` - All work items for "Digital Marketing" KB

## ✅ Benefits of Standardized Naming

1. **Consistent Discovery**: Agents can reliably find their assigned work
2. **Clear Purpose**: Work type is immediately identifiable from title
3. **KB Context**: Knowledge base name is always visible
4. **Easy Filtering**: Standard prefixes enable automated filtering
5. **Multi-KB Management**: Clear separation between different knowledge bases
6. **Human Oversight**: Humans can easily understand work item purpose
7. **Audit Trail**: Clear tracking of work item types and purposes

## 🚨 Critical Requirements

1. **Supervisor MUST use these naming conventions** for all work items
2. **KB Name MUST be included** in every work item title
3. **Required labels MUST be applied** for proper discovery
4. **ContentManagementAgent gets initial KB-INIT work items** to set up the KB
5. **Follow-up work items** must be created for appropriate specialized agents

This standardization ensures smooth coordination across the multi-agent system while maintaining clear KB context awareness.
