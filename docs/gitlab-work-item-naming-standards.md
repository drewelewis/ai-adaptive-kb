# GitLab Work Item Naming Standards

## 🎯 Purpose

This document defines standardized naming conventions for GitLab work items created by the Supervisor Agent to ensure consistency, discoverability, and proper coordination across multiple knowledge bases.

## 📋 Standardized Work Item Naming Conventions

### **Primary Work Item Types**

| Work Type | Title Format | Purpose | Primary Agent | Content Gate |
|-----------|-------------|---------|---------------|--------------|
| **KB Setup** | `KB Setup: [KB Name]` | KB setup and planning coordination | All Agents | **Project coordination** |
| **Content Planning** | `KB-PLAN: [KB Name] - Content Planning & Strategy` | Strategic content planning and structure design | ContentPlannerAgent | Works alongside setup |
| **Content Creation** | `KB-CREATE: [KB Name] - Content Development` | Article creation and content development | ContentCreatorAgent | Can proceed when project available |
| **Content Review** | `KB-REVIEW: [KB Name] - Quality Assurance & Review` | Quality review and optimization | ContentReviewerAgent | Can proceed when project available |
| **Content Research** | `KB-RESEARCH: [KB Name] - Research & Analysis` | Domain research and competitive analysis | ContentRetrievalAgent | Can proceed when project available |
| **KB Updates** | `KB-UPDATE: [KB Name] - Knowledge Base Updates` | Ongoing KB maintenance and updates | ContentManagementAgent | May proceed if KB exists |

### **Specialized Work Item Types**

| Work Type | Title Format | Purpose |
|-----------|-------------|---------|
| **Cross-KB Analysis** | `KB-ANALYSIS: Multi-KB - Cross-Knowledge Base Analysis` | Analysis across multiple KBs |
| **KB Migration** | `KB-MIGRATE: [KB Name] - Knowledge Base Migration` | KB structure or content migration |
| **KB Integration** | `KB-INTEGRATE: [KB Name] - System Integration` | Third-party integrations |
| **Human Feedback** | `KB-FEEDBACK: [KB Name] - Human Review Required` | Items requiring human input |

## � GitLab Project Activation

### **Immediate Content Creation**
The "KB Setup: [KB Name]" work item serves as **project coordination** for all content creation:

- **Created for coordination** but does not block content creation
- **Content creation can proceed immediately** when GitLab projects are available  
- Content agents can work alongside setup coordination
- No blocking dependencies - all work proceeds in parallel

### **Project-Based Workflow**
1. Supervisor creates "KB Setup: [KB Name]" (state: opened)
2. All content agents can contribute planning input via comments
3. Human stakeholders provide feedback and requirements
4. KB definition is finalized with clear scope and structure  
5. Content creation begins immediately when GitLab project is available
6. All work items can be processed in parallel

### **Agent Behavior With Projects**
- **Setup Phase**: Agents contribute planning input, ask questions, provide suggestions
- **Creation Phase**: Agents can process content creation work items immediately when projects are available
- **Project Check**: All agents verify GitLab project availability before content operations

## 🏷️ Label Standards

### **Required Labels for All Work Items**
- `supervisor-created` - Identifies supervisor-created work items
- `kb-[domain]` - Knowledge base domain (e.g., `kb-marketing`, `kb-technology`)
- Priority level: `high-priority`, `medium-priority`, `low-priority`
- Agent assignment: `content-management`, `content-planner`, `content-creator`, `content-reviewer`, `content-retrieval`

### **Special Labels for KB Setup Work Items**
- `kb-setup` - Marks the project coordination work item
- `planning-phase` - Indicates planning/coordination phase activity
- `project-coordination` - Identifies work items for project management

### **Optional Labels**
- `urgent` - Requires immediate attention
- `blocked` - Work item is blocked waiting for dependencies
- `human-input-required` - Needs human feedback or approval
- `cross-kb` - Work spans multiple knowledge bases
- `setup-complete` - KB Setup coordination has been completed (for reference)

## 📝 Work Item Description Template

### **KB Setup Work Item Template**
```markdown
**Target KB:** [Knowledge Base Name]
**KB Domain:** [Topic area and scope]
**KB Context:** [Strategic purpose and background]

**Setup Requirements:**
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
- [ ] GitLab project is created and content creation can proceed immediately

**Project Status:** 
- 🚀 **ACTIVE**: Content creation can proceed immediately when GitLab project is available
- ✅ **COMPLETE**: Setup coordination is finished, content work continues
```

### **KB-CREATE Work Item Template** (works alongside setup)
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
