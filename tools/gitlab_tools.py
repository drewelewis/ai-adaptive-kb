import os
from typing import List, Optional, Type
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv(override=True)

from operations.gitlab_operations import GitLabOperations

# Use direct GitLab API - simpler and more reliable
gitlab_operations = GitLabOperations()

class GitLabTools:
    """Tools for interacting with GitLab through the MCP server."""
    
    class GitLabGetProjectsListTool(BaseTool):
        name: str = "GitLabGetProjectsListTool"
        description: str = """
            A tool to get a list of all GitLab projects accessible with the current token.
            This tool is useful when you need to see what GitLab projects are available.
            It returns a list of projects with their names, IDs, and basic information.
            Use this tool first before trying to access specific project files or create issues.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetProjectsListToolInputModel(BaseModel):
            # No parameters needed for listing all projects
            pass
            
        args_schema: Optional[ArgsSchema] = GitLabGetProjectsListToolInputModel
     
        def _run(self) -> str:
            projects = gitlab_operations.get_projects_list()
            if not projects:
                return "No projects found or error occurred while fetching projects."
            
            # Format the output nicely
            result = "GitLab Projects:\n"
            for project in projects:
                project_id = project.get('id', 'N/A')
                name = project.get('name', 'Unknown')
                path = project.get('path_with_namespace', project.get('path', 'N/A'))
                description = project.get('description', 'No description')
                visibility = project.get('visibility', 'unknown')
                
                result += f"\n📁 {name} (ID: {project_id})\n"
                result += f"   Path: {path}\n"
                result += f"   Visibility: {visibility}\n"
                if description and description != 'No description':
                    result += f"   Description: {description}\n"
                result += "   " + "-" * 40 + "\n"
            
            return result

    class GitLabGetProjectDetailsTool(BaseTool):
        name: str = "GitLabGetProjectDetailsTool"
        description: str = """
            A tool to get detailed information about a specific GitLab project.
            Requires the project ID which you can get from GitLabGetProjectsListTool.
            Returns comprehensive project information including repository details.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetProjectDetailsToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabGetProjectDetailsTool error: project_id parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabGetProjectDetailsToolInputModel
     
        def _run(self, project_id: str) -> str:
            project = gitlab_operations.get_project_details(project_id)
            if not project:
                return f"No project details found for project ID: {project_id}"
            
            # Format the project details nicely
            result = f"GitLab Project Details (ID: {project_id}):\n\n"
            
            if 'name' in project:
                result += f"📁 Name: {project['name']}\n"
            if 'path_with_namespace' in project:
                result += f"🔗 Path: {project['path_with_namespace']}\n"
            if 'description' in project:
                result += f"📝 Description: {project['description']}\n"
            if 'visibility' in project:
                result += f"👁️ Visibility: {project['visibility']}\n"
            if 'default_branch' in project:
                result += f"🌿 Default Branch: {project['default_branch']}\n"
            if 'web_url' in project:
                result += f"🌐 Web URL: {project['web_url']}\n"
            if 'created_at' in project:
                result += f"📅 Created: {project['created_at']}\n"
            if 'last_activity_at' in project:
                result += f"⏰ Last Activity: {project['last_activity_at']}\n"
            
            return result

    class GitLabGetProjectFilesTool(BaseTool):
        name: str = "GitLabGetProjectFilesTool"
        description: str = """
            A tool to get a list of files in a GitLab project repository.
            Requires the project ID. Optionally specify a path to browse subdirectories
            and a branch/ref (defaults to 'main'). Returns file and directory listings.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetProjectFilesToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")
            path: str = Field(default="", description="Path within the repository (empty for root)")
            ref: str = Field(default="main", description="Branch or commit reference (default: main)")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabGetProjectFilesTool error: project_id parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabGetProjectFilesToolInputModel
     
        def _run(self, project_id: str, path: str = "", ref: str = "main") -> str:
            files = gitlab_operations.get_project_files(project_id, path, ref)
            if not files:
                return f"No files found in project {project_id} at path '{path}' on ref '{ref}'"
            
            # Format the file listing nicely
            result = f"Files in GitLab Project {project_id}"
            if path:
                result += f" at path '{path}'"
            result += f" (ref: {ref}):\n\n"
            
            directories = []
            files_list = []
            
            for item in files:
                name = item.get('name', 'Unknown')
                item_type = item.get('type', 'blob')
                
                if item_type == 'tree':
                    directories.append(f"📁 {name}/")
                else:
                    size = item.get('size', 'Unknown size')
                    files_list.append(f"📄 {name} ({size} bytes)")
            
            # Show directories first, then files
            for directory in sorted(directories):
                result += directory + "\n"
            for file in sorted(files_list):
                result += file + "\n"
            
            return result

    class GitLabGetFileContentTool(BaseTool):
        name: str = "GitLabGetFileContentTool"
        description: str = """
            A tool to get the content of a specific file from a GitLab project repository.
            Requires the project ID and file path. Optionally specify branch/ref (defaults to 'main').
            Returns the actual file content which you can analyze, document, or process.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetFileContentToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")
            file_path: str = Field(description="Path to the file within the repository")
            ref: str = Field(default="main", description="Branch or commit reference (default: main)")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabGetFileContentTool error: project_id parameter is empty")
                return v
            
            @field_validator("file_path")
            @classmethod
            def validate_file_path(cls, v):
                if not v:
                    raise ValueError("GitLabGetFileContentTool error: file_path parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabGetFileContentToolInputModel
     
        def _run(self, project_id: str, file_path: str, ref: str = "main") -> str:
            content = gitlab_operations.get_file_content(project_id, file_path, ref)
            if not content:
                return f"No content found for file '{file_path}' in project {project_id} on ref '{ref}'"
            
            result = f"Content of '{file_path}' from GitLab project {project_id} (ref: {ref}):\n\n"
            result += "=" * 60 + "\n"
            result += content
            result += "\n" + "=" * 60
            
            return result

    class GitLabCreateIssueTool(BaseTool):
        name: str = "GitLabCreateIssueTool"
        description: str = """
            A tool to create a new issue in a GitLab project.
            Requires the project ID, issue title, and description.
            Optionally specify labels as a comma-separated list.
            Returns information about the created issue.
        """.strip()
        return_direct: bool = False
    
        class GitLabCreateIssueToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")
            title: str = Field(description="Issue title")
            description: str = Field(description="Issue description")
            labels: Optional[str] = Field(default=None, description="Comma-separated list of labels (optional)")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabCreateIssueTool error: project_id parameter is empty")
                return v
            
            @field_validator("title")
            @classmethod
            def validate_title(cls, v):
                if not v:
                    raise ValueError("GitLabCreateIssueTool error: title parameter is empty")
                return v
                
            @field_validator("description")
            @classmethod
            def validate_description(cls, v):
                if not v:
                    raise ValueError("GitLabCreateIssueTool error: description parameter is empty")
                return v
                
        args_schema: Optional[ArgsSchema] = GitLabCreateIssueToolInputModel

        def _run(self, project_id: str, title: str, description: str, labels: Optional[str] = None) -> str:
            labels_list = []
            if labels:
                labels_list = [label.strip() for label in labels.split(',') if label.strip()]
            
            issue = gitlab_operations.create_issue(project_id, title, description, labels_list)
            if not issue:
                return f"Failed to create issue in project {project_id}"
            
            result = f"✅ Successfully created GitLab issue:\n\n"
            if 'iid' in issue:
                result += f"🆔 Issue #: {issue['iid']}\n"
            if 'title' in issue:
                result += f"📝 Title: {issue['title']}\n"
            if 'web_url' in issue:
                result += f"🔗 URL: {issue['web_url']}\n"
            if 'state' in issue:
                result += f"📊 State: {issue['state']}\n"
            if 'created_at' in issue:
                result += f"📅 Created: {issue['created_at']}\n"
            
            return result

    class GitLabGetProjectIssuesTool(BaseTool):
        name: str = "GitLabGetProjectIssuesTool"
        description: str = """
            A tool to get a list of issues from a GitLab project.
            Requires the project ID. Optionally specify state (opened, closed, all).
            Returns a list of issues with their details.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetProjectIssuesToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")
            state: str = Field(default="opened", description="Issue state: opened, closed, or all")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabGetProjectIssuesTool error: project_id parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabGetProjectIssuesToolInputModel
     
        def _run(self, project_id: str, state: str = "opened") -> str:
            issues = gitlab_operations.get_project_issues(project_id, state)
            if not issues:
                return f"No {state} issues found in project {project_id}"
            
            result = f"GitLab Issues in Project {project_id} (state: {state}):\n\n"
            
            for issue in issues:
                iid = issue.get('iid', 'N/A')
                title = issue.get('title', 'No title')
                state_val = issue.get('state', 'unknown')
                created_at = issue.get('created_at', 'Unknown')
                author = issue.get('author', {}).get('name', 'Unknown')
                
                result += f"🐛 Issue #{iid}: {title}\n"
                result += f"   📊 State: {state_val}\n"
                result += f"   👤 Author: {author}\n"
                result += f"   📅 Created: {created_at}\n"
                
                if 'web_url' in issue:
                    result += f"   🔗 URL: {issue['web_url']}\n"
                
                result += "   " + "-" * 40 + "\n"
            
            return result

    class GitLabGetIssueDetailsTool(BaseTool):
        name: str = "GitLabGetIssueDetailsTool"
        description: str = """
            A tool to get detailed information about a specific GitLab issue, including its description and any task lists.
            Requires the project ID and issue IID (issue number).
            Returns comprehensive issue information including task lists if present.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetIssueDetailsToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")
            issue_iid: str = Field(description="The issue IID (issue number)")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabGetIssueDetailsTool error: project_id parameter is empty")
                return v
            
            @field_validator("issue_iid")
            @classmethod
            def validate_issue_iid(cls, v):
                if not v:
                    raise ValueError("GitLabGetIssueDetailsTool error: issue_iid parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabGetIssueDetailsToolInputModel
     
        def _run(self, project_id: str, issue_iid: str) -> str:
            issue = gitlab_operations.get_issue_details(project_id, issue_iid)
            if not issue:
                return f"No issue found with IID {issue_iid} in project {project_id}"
            
            result = f"GitLab Issue Details (Project {project_id}, Issue #{issue_iid}):\n\n"
            
            # Basic issue info
            if 'title' in issue:
                result += f"📝 Title: {issue['title']}\n"
            if 'state' in issue:
                result += f"📊 State: {issue['state']}\n"
            if 'author' in issue:
                result += f"👤 Author: {issue['author'].get('name', 'Unknown')}\n"
            if 'created_at' in issue:
                result += f"📅 Created: {issue['created_at']}\n"
            if 'updated_at' in issue:
                result += f"🔄 Updated: {issue['updated_at']}\n"
            if 'web_url' in issue:
                result += f"🔗 URL: {issue['web_url']}\n"
            
            # Description
            description = issue.get('description', '')
            if description:
                result += f"\n📋 Description:\n"
                result += "=" * 50 + "\n"
                result += description + "\n"
                result += "=" * 50 + "\n"
                
                # Parse task lists from description
                task_patterns = [
                    ('- [ ]', '❌ Uncompleted'),
                    ('- [x]', '✅ Completed'),
                    ('- [X]', '✅ Completed'),
                    ('* [ ]', '❌ Uncompleted'),
                    ('* [x]', '✅ Completed'),
                    ('* [X]', '✅ Completed')
                ]
                
                found_tasks = []
                for line in description.split('\n'):
                    for pattern, status in task_patterns:
                        if pattern in line:
                            task_text = line.replace(pattern, '').strip()
                            found_tasks.append(f"{status}: {task_text}")
                
                if found_tasks:
                    result += f"\n📋 Task List ({len(found_tasks)} items):\n"
                    for task in found_tasks:
                        result += f"  {task}\n"
                else:
                    result += f"\n❌ No task list items found in description\n"
            else:
                result += f"\n❌ No description available\n"
            
            # Task completion status (if available)
            task_status = issue.get('task_completion_status', {})
            if task_status and isinstance(task_status, dict):
                total = task_status.get('count', 0)
                completed = task_status.get('completed_count', 0)
                if total > 0:
                    result += f"\n📊 Task Progress: {completed}/{total} completed ({(completed/total)*100:.1f}%)\n"
            
            return result

    class GitLabGetWorkItemsTool(BaseTool):
        name: str = "GitLabGetWorkItemsTool"
        description: str = """
            A tool to get a list of work items (tasks) from a GitLab project.
            Work items are used for tasks, epics, and other work tracking in GitLab.
            Requires the project ID. Optionally specify work item type (default: Task).
            Returns a list of work items with their details.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetWorkItemsToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")
            work_item_type: str = Field(default="Task", description="Type of work item (Task, Epic, etc.)")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabGetWorkItemsTool error: project_id parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabGetWorkItemsToolInputModel
     
        def _run(self, project_id: str, work_item_type: str = "Task") -> str:
            work_items = gitlab_operations.get_work_items(project_id, work_item_type)
            if not work_items:
                return f"No {work_item_type} work items found in project {project_id}"
            
            result = f"GitLab Work Items ({work_item_type}) in Project {project_id}:\n\n"
            
            for item in work_items:
                iid = item.get('iid', 'N/A')
                title = item.get('title', 'No title')
                state = item.get('state', 'unknown')
                created_at = item.get('created_at', 'Unknown')
                author = item.get('author', {}).get('name', 'Unknown')
                
                result += f"📋 Work Item #{iid}: {title}\n"
                result += f"   📊 State: {state}\n"
                result += f"   👤 Author: {author}\n"
                result += f"   📅 Created: {created_at}\n"
                
                if 'web_url' in item:
                    result += f"   🔗 URL: {item['web_url']}\n"
                
                result += "   " + "-" * 40 + "\n"
            
            return result

    class GitLabGetWorkItemDetailsTool(BaseTool):
        name: str = "GitLabGetWorkItemDetailsTool"
        description: str = """
            A tool to get detailed information about a specific GitLab work item/task.
            Requires the project ID and work item IID (internal ID).
            Returns comprehensive work item information including description and metadata.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetWorkItemDetailsToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")
            work_item_iid: str = Field(description="The work item IID (internal ID)")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabGetWorkItemDetailsTool error: project_id parameter is empty")
                return v
            
            @field_validator("work_item_iid")
            @classmethod
            def validate_work_item_iid(cls, v):
                if not v:
                    raise ValueError("GitLabGetWorkItemDetailsTool error: work_item_iid parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabGetWorkItemDetailsToolInputModel
     
        def _run(self, project_id: str, work_item_iid: str) -> str:
            work_item = gitlab_operations.get_work_item_details(project_id, work_item_iid)
            if not work_item:
                return f"No work item details found for IID: {work_item_iid} in project {project_id}"
            
            # Format the work item details nicely
            result = f"GitLab Work Item Details (Project: {project_id}, IID: {work_item_iid}):\n\n"
            
            if 'title' in work_item:
                result += f"📋 Title: {work_item['title']}\n"
            if 'work_item_type' in work_item:
                result += f"🏷️ Type: {work_item['work_item_type'].get('name', 'Unknown')}\n"
            if 'state' in work_item:
                result += f"📊 State: {work_item['state']}\n"
            if 'description' in work_item:
                result += f"📝 Description: {work_item['description']}\n"
            if 'author' in work_item:
                result += f"👤 Author: {work_item['author'].get('name', 'Unknown')}\n"
            if 'created_at' in work_item:
                result += f"📅 Created: {work_item['created_at']}\n"
            if 'updated_at' in work_item:
                result += f"⏰ Updated: {work_item['updated_at']}\n"
            if 'web_url' in work_item:
                result += f"🔗 URL: {work_item['web_url']}\n"
            
            return result

    class GitLabCreateProjectTool(BaseTool):
        name: str = "GitLabCreateProjectTool"
        description: str = """
            A tool to create a new GitLab project for knowledge base management.
            Requires a project name. Optionally specify description and visibility.
            Creates a project with issues, merge requests, wiki, and snippets enabled.
            Projects are created as PUBLIC by default for knowledge base sharing.
            Creates project without repository by default (no README or git repo initialization).
            Perfect for creating dedicated projects to manage KB generation and tracking.
        """.strip()
        return_direct: bool = False
        
        class GitLabCreateProjectToolInputModel(BaseModel):
            name: str = Field(description="Project name")
            description: str = Field(default="", description="Project description (optional)")
            visibility: str = Field(default="public", description="Project visibility: private, internal, or public")

            @field_validator("name")
            @classmethod
            def validate_name(cls, v):
                if not v:
                    raise ValueError("GitLabCreateProjectTool error: name parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabCreateProjectToolInputModel
     
        def _run(self, name: str, description: str = "", visibility: str = "public") -> str:
            project = gitlab_operations.create_project(name, description, visibility)
            if not project:
                return f"Failed to create GitLab project '{name}'"
            
            result = f"✅ Successfully created GitLab project:\n\n"
            if 'name' in project:
                result += f"📁 Name: {project['name']}\n"
            if 'id' in project:
                result += f"🆔 Project ID: {project['id']}\n"
            if 'path_with_namespace' in project:
                result += f"🔗 Path: {project['path_with_namespace']}\n"
            if 'description' in project:
                result += f"📝 Description: {project['description']}\n"
            if 'visibility' in project:
                result += f"👁️ Visibility: {project['visibility']}\n"
            if 'web_url' in project:
                result += f"🌐 Web URL: {project['web_url']}\n"
            if 'issues_enabled' in project:
                result += f"🐛 Issues Enabled: {project['issues_enabled']}\n"
            if 'merge_requests_enabled' in project:
                result += f"🔀 Merge Requests Enabled: {project['merge_requests_enabled']}\n"
            
            result += f"\n💡 This project is ready for knowledge base management and issue tracking!"
            
            return result

    class GitLabCreateProjectForKBTool(BaseTool):
        name: str = "GitLabCreateProjectForKBTool"
        description: str = """
            A tool to create a GitLab project and automatically link it to an existing knowledge base.
            Requires a knowledge base ID and project name. Optionally specify description and visibility.
            Creates a project with issues, merge requests, wiki, and snippets enabled.
            Projects are created as PUBLIC by default for knowledge base sharing.
            Creates project without repository by default (no README or git repo initialization).
            Automatically updates the knowledge base record with the GitLab project ID for seamless integration.
        """.strip()
        return_direct: bool = False
        
        class GitLabCreateProjectForKBToolInputModel(BaseModel):
            knowledge_base_id: int = Field(description="Knowledge base ID to link to the GitLab project")
            name: str = Field(description="Project name")
            description: str = Field(default="", description="Project description (optional)")
            visibility: str = Field(default="public", description="Project visibility: private, internal, or public")

            @field_validator("knowledge_base_id")
            @classmethod
            def validate_kb_id(cls, v):
                if not v or v <= 0:
                    raise ValueError("GitLabCreateProjectForKBTool error: knowledge_base_id must be a positive integer")
                return v
                
            @field_validator("name")
            @classmethod
            def validate_name(cls, v):
                if not v:
                    raise ValueError("GitLabCreateProjectForKBTool error: name parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabCreateProjectForKBToolInputModel
     
        def _run(self, knowledge_base_id: int, name: str, description: str = "", visibility: str = "public") -> str:
            project = gitlab_operations.create_project_for_knowledge_base(
                knowledge_base_id, name, description, visibility
            )
            if not project:
                return f"Failed to create GitLab project '{name}' for Knowledge Base {knowledge_base_id}"
            
            result = f"✅ Successfully created GitLab project and linked to Knowledge Base {knowledge_base_id}:\n\n"
            if 'name' in project:
                result += f"📁 Name: {project['name']}\n"
            if 'id' in project:
                result += f"🆔 Project ID: {project['id']}\n"
            if 'linked_knowledge_base_id' in project:
                result += f"📚 Linked Knowledge Base ID: {project['linked_knowledge_base_id']}\n"
            if 'path_with_namespace' in project:
                result += f"🔗 Path: {project['path_with_namespace']}\n"
            if 'description' in project:
                result += f"📝 Description: {project['description']}\n"
            if 'visibility' in project:
                result += f"👁️ Visibility: {project['visibility']}\n"
            if 'web_url' in project:
                result += f"🌐 Web URL: {project['web_url']}\n"
            if 'issues_enabled' in project:
                result += f"🐛 Issues Enabled: {project['issues_enabled']}\n"
            if 'merge_requests_enabled' in project:
                result += f"🔀 Merge Requests Enabled: {project['merge_requests_enabled']}\n"
            
            result += f"\n💡 This project is now linked to your knowledge base for integrated management!"
            
            return result

    class GitLabGetKnowledgeBaseByProjectTool(BaseTool):
        name: str = "GitLabGetKnowledgeBaseByProjectTool"
        description: str = """
            A tool to find a knowledge base that is linked to a specific GitLab project.
            Requires a GitLab project ID. Returns the knowledge base information if a link exists.
            Useful for finding which knowledge base is associated with a GitLab project.
        """.strip()
        return_direct: bool = False
        
        class GitLabGetKnowledgeBaseByProjectToolInputModel(BaseModel):
            gitlab_project_id: int = Field(description="GitLab project ID to find linked knowledge base for")

            @field_validator("gitlab_project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v or v <= 0:
                    raise ValueError("GitLabGetKnowledgeBaseByProjectTool error: gitlab_project_id must be a positive integer")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabGetKnowledgeBaseByProjectToolInputModel
     
        def _run(self, gitlab_project_id: int) -> str:
            try:
                # Import here to avoid circular imports
                from operations.knowledge_base_operations import KnowledgeBaseOperations
                
                kb_ops = KnowledgeBaseOperations()
                kb = kb_ops.get_knowledge_base_by_gitlab_project_id(gitlab_project_id)
                
                if not kb:
                    return f"No knowledge base found linked to GitLab project {gitlab_project_id}"
                
                result = f"📚 Knowledge Base linked to GitLab Project {gitlab_project_id}:\n\n"
                result += f"🆔 KB ID: {kb.id}\n"
                result += f"📁 Name: {kb.name}\n"
                result += f"📝 Description: {kb.description}\n"
                result += f"👤 Author ID: {kb.author_id}\n"
                result += f"✅ Is Active: {kb.is_active}\n"
                result += f"🔗 GitLab Project ID: {kb.gitlab_project_id}\n"
                
                return result
                
            except Exception as e:
                return f"Error finding knowledge base for GitLab project {gitlab_project_id}: {str(e)}"

    class GitLabCreateKBManagementIssuesTool(BaseTool):
        name: str = "GitLabCreateKBManagementIssuesTool"
        description: str = """
            A tool to create standard knowledge base management issues in a GitLab project.
            Requires project ID and KB name. Creates a complete set of issues for:
            - Planning and structure
            - Content generation
            - Quality review
            - Deployment and maintenance
            Perfect for setting up structured KB management workflow.
        """.strip()
        return_direct: bool = False
        
        class GitLabCreateKBManagementIssuesToolInputModel(BaseModel):
            project_id: str = Field(description="The GitLab project ID")
            kb_name: str = Field(description="Knowledge base name for issue labeling and organization")

            @field_validator("project_id")
            @classmethod
            def validate_project_id(cls, v):
                if not v:
                    raise ValueError("GitLabCreateKBManagementIssuesTool error: project_id parameter is empty")
                return v
            
            @field_validator("kb_name")
            @classmethod
            def validate_kb_name(cls, v):
                if not v:
                    raise ValueError("GitLabCreateKBManagementIssuesTool error: kb_name parameter is empty")
                return v
            
        args_schema: Optional[ArgsSchema] = GitLabCreateKBManagementIssuesToolInputModel
     
        def _run(self, project_id: str, kb_name: str) -> str:
            issues = gitlab_operations.create_kb_management_issues(project_id, kb_name)
            if not issues:
                return f"Failed to create KB management issues for '{kb_name}' in project {project_id}"
            
            result = f"✅ Successfully created {len(issues)} KB management issues for '{kb_name}':\n\n"
            
            for issue in issues:
                iid = issue.get('iid', 'N/A')
                title = issue.get('title', 'No title')
                web_url = issue.get('web_url', '')
                
                result += f"📋 Issue #{iid}: {title}\n"
                if web_url:
                    result += f"   🔗 {web_url}\n"
                result += "   " + "-" * 40 + "\n"
            
            result += f"\n🎯 Knowledge base '{kb_name}' is now set up with a complete management workflow!"
            result += f"\n💡 Use these issues to track planning, content generation, quality review, and deployment."
            
            return result

    def _create_update_project_tool(self):
        """Create a tool for updating GitLab project details including name (now supported)."""
        class GitLabUpdateProjectTool(BaseTool):
            name: str = "GitLabUpdateProjectTool"
            description: str = """
                Update GitLab project details including name, description, visibility, and topics.
                
                IMPROVED: Modern GitLab versions now support project renaming!
                This tool can update:
                - Name (project renaming - requires admin/maintainer permissions)
                - Description
                - Visibility (private, internal, public)
                - Topics/tags
                
                Note: Project renaming may not be available on all GitLab instances or may require special permissions.
                If renaming fails, the tool will provide specific guidance based on the error.
            """.strip()
            return_direct: bool = False

            class UpdateProjectInputModel(BaseModel):
                project_id: str = Field(description="GitLab project ID (required)")
                name: Optional[str] = Field(default=None, description="New project name (renaming supported in modern GitLab)")
                description: Optional[str] = Field(default=None, description="New project description")
                visibility: Optional[str] = Field(default=None, description="Project visibility: private, internal, or public")
                topics: Optional[List[str]] = Field(default=None, description="List of topic tags for the project")

                @field_validator("project_id")
                def validate_project_id(cls, project_id):
                    if not project_id or not project_id.strip():
                        raise ValueError("Project ID is required")
                    return project_id.strip()

                @field_validator("visibility")
                def validate_visibility(cls, visibility):
                    if visibility and visibility.lower() not in ['private', 'internal', 'public']:
                        raise ValueError("Visibility must be 'private', 'internal', or 'public'")
                    return visibility.lower() if visibility else None

                @field_validator("name")
                def validate_name(cls, name):
                    if name and not name.strip():
                        raise ValueError("Project name cannot be empty")
                    return name.strip() if name else None

            args_schema: Optional[ArgsSchema] = UpdateProjectInputModel

            def _run(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None, 
                    visibility: Optional[str] = None, topics: Optional[List[str]] = None) -> str:
                try:
                    gitlab_ops = GitLabOperations()
                    result = gitlab_ops.update_project_details(
                        project_id=project_id,
                        name=name,
                        description=description,
                        visibility=visibility,
                        topics=topics
                    )
                    
                    if result.get('error'):
                        error = result['error']
                        if result.get('rename_error'):
                            return f"❌ **Project Renaming Failed:** {error}\n\n**Troubleshooting:**\n- Check if you have admin/maintainer permissions\n- Verify this GitLab instance supports renaming\n- Try using GitLabRenameProjectGuidanceTool for migration alternatives"
                        else:
                            return f"❌ **Error updating project:** {error}\n\n**Troubleshooting:**\n- Verify project ID {project_id} exists\n- Check GitLab permissions\n- Ensure visibility value is valid"
                    
                    if result.get('updated'):
                        output = f"✅ **Project Updated Successfully!**\n"
                        output += f"🆔 **Project ID:** {result['id']}\n"
                        output += f"📁 **Project Name:** {result['name']}"
                        
                        if result.get('renamed'):
                            output += " ✨ **RENAMED!** ✨\n"
                        else:
                            output += "\n"
                            
                        output += f"📝 **Description:** {result.get('description', 'Not set')}\n"
                        output += f"👁️ **Visibility:** {result.get('visibility', 'Unknown')}\n"
                        output += f"🔗 **URL:** {result.get('web_url', 'Not available')}\n"
                        
                        if result.get('topics'):
                            output += f"🏷️ **Topics:** {', '.join(result['topics'])}\n"
                        
                        if result.get('renamed'):
                            output += f"\n🎉 **Project successfully renamed!** The new URL and path have been updated."
                        
                        return output
                    else:
                        return f"⚠️ **No changes made** - all values were already current or no updates specified."
                        
                except Exception as e:
                    return f"❌ **Error:** {str(e)}\n\n**Common Solutions:**\n- Verify project exists\n- Check GitLab connection\n- Ensure proper permissions (admin/maintainer for renaming)"

        return GitLabUpdateProjectTool()

    def _create_rename_project_tool(self):
        """Create a dedicated tool for renaming GitLab projects."""
        class GitLabRenameProjectTool(BaseTool):
            name: str = "GitLabRenameProjectTool"
            description: str = """
                Rename a GitLab project directly (now supported in modern GitLab versions).
                
                This tool attempts to rename a GitLab project by updating both the name and path.
                Requires admin or maintainer permissions on the project.
                
                If renaming fails, it provides specific error guidance and suggests alternatives.
                Use this when you specifically want to rename a project without changing other attributes.
            """.strip()
            return_direct: bool = False

            class RenameProjectInputModel(BaseModel):
                project_id: str = Field(description="GitLab project ID to rename")
                new_name: str = Field(description="The new project name")

                @field_validator("project_id")
                def validate_project_id(cls, project_id):
                    if not project_id or not project_id.strip():
                        raise ValueError("Project ID is required")
                    return project_id.strip()

                @field_validator("new_name")
                def validate_new_name(cls, new_name):
                    if not new_name or not new_name.strip():
                        raise ValueError("New name is required")
                    return new_name.strip()

            args_schema: Optional[ArgsSchema] = RenameProjectInputModel

            def _run(self, project_id: str, new_name: str) -> str:
                try:
                    gitlab_ops = GitLabOperations()
                    result = gitlab_ops.rename_project(project_id, new_name)
                    
                    if result.get('success'):
                        output = f"✅ **Project Renamed Successfully!**\n\n"
                        output += f"🆔 **Project ID:** {result['id']}\n"
                        output += f"📁 **Old Name:** {result['old_name']}\n"
                        output += f"🎉 **New Name:** {result['new_name']}\n"
                        output += f"🔗 **New Path:** {result['new_path']}\n"
                        output += f"🌐 **Updated URL:** {result.get('web_url', 'Not available')}\n"
                        output += f"\n💡 **Note:** The project URL and all references have been updated automatically!"
                        return output
                    else:
                        error = result.get('error', 'Unknown error')
                        
                        if result.get('permission_error'):
                            return f"❌ **Permission Error:** {error}\n\n**Solutions:**\n- Request admin/maintainer access to this project\n- Ask a project admin to perform the rename\n- Use GitLabRenameProjectGuidanceTool for migration alternatives"
                        elif result.get('name_conflict'):
                            return f"❌ **Name Conflict:** {error}\n\n**Solutions:**\n- Try a different project name\n- Check if there's an archived project with this name\n- Consider adding a suffix like '-v2' or '-new'"
                        elif result.get('unsupported'):
                            return f"❌ **Feature Not Supported:** {error}\n\n**Solutions:**\n- This GitLab instance may be older and not support renaming\n- Use GitLabRenameProjectGuidanceTool for migration alternatives\n- Contact your GitLab administrator about upgrading"
                        else:
                            return f"❌ **Rename Failed:** {error}\n\n**Troubleshooting:**\n- Verify project ID exists\n- Check GitLab connection\n- Try using GitLabUpdateProjectTool with name parameter"
                        
                except Exception as e:
                    return f"❌ **Error:** {str(e)}\n\n**Common Solutions:**\n- Verify project exists\n- Check GitLab connection\n- Ensure proper permissions\n- Try GitLabRenameProjectGuidanceTool for alternatives"

        return GitLabRenameProjectTool()

    def _create_rename_project_guidance_tool(self):
        """Create a tool that provides comprehensive guidance for GitLab project renaming."""
        class GitLabRenameProjectGuidanceTool(BaseTool):
            name: str = "GitLabRenameProjectGuidanceTool"
            description: str = """
                Provides comprehensive guidance for GitLab project renaming with modern GitLab support.
                
                NEW: Modern GitLab versions now support direct project renaming!
                This tool provides guidance on:
                - Direct renaming (if supported and you have permissions)
                - Migration alternatives (if direct renaming fails)
                - Troubleshooting common renaming issues
            """.strip()
            return_direct: bool = False

            class RenameGuidanceInputModel(BaseModel):
                project_id: str = Field(description="Current GitLab project ID")
                desired_name: str = Field(description="The desired new project name")
                knowledge_base_id: Optional[str] = Field(default=None, description="Associated knowledge base ID (if any)")

                @field_validator("project_id")
                def validate_project_id(cls, project_id):
                    if not project_id or not project_id.strip():
                        raise ValueError("Project ID is required")
                    return project_id.strip()

                @field_validator("desired_name")
                def validate_desired_name(cls, desired_name):
                    if not desired_name or not desired_name.strip():
                        raise ValueError("Desired name is required")
                    return desired_name.strip()

            args_schema: Optional[ArgsSchema] = RenameGuidanceInputModel

            def _run(self, project_id: str, desired_name: str, knowledge_base_id: Optional[str] = None) -> str:
                try:
                    gitlab_ops = GitLabOperations()
                    
                    # Get current project details
                    project_details = gitlab_ops.get_project_details(project_id)
                    if not project_details:
                        return f"❌ **Error:** Project ID {project_id} not found."
                    
                    current_name = project_details.get('name', 'Unknown')
                    project_url = project_details.get('web_url', 'Not available')
                    
                    # Generate safe project path from desired name
                    safe_path = desired_name.lower().replace(' ', '-').replace('_', '-')
                    safe_path = ''.join(c for c in safe_path if c.isalnum() or c == '-')
                    
                    output = f"🎯 **GitLab Project Renaming Guide**\n\n"
                    output += f"Current project: **{current_name}** (ID: {project_id})\n"
                    output += f"Desired name: **{desired_name}**\n\n"
                    
                    output += f"## ✨ **Option 1: Direct Renaming (RECOMMENDED - Now Supported!)**\n\n"
                    output += f"Modern GitLab versions support direct project renaming!\n\n"
                    output += f"**Using GitLabRenameProjectTool:**\n"
                    output += f"```\n{{\n"
                    output += f"  \"project_id\": \"{project_id}\",\n"
                    output += f"  \"new_name\": \"{desired_name}\"\n"
                    output += f"}}\n```\n\n"
                    output += f"**Or using GitLabUpdateProjectTool:**\n"
                    output += f"```\n{{\n"
                    output += f"  \"project_id\": \"{project_id}\",\n"
                    output += f"  \"name\": \"{desired_name}\"\n"
                    output += f"}}\n```\n\n"
                    output += f"**Requirements:**\n"
                    output += f"- ✅ Admin or Maintainer permissions on the project\n"
                    output += f"- ✅ Modern GitLab instance (most recent versions)\n"
                    output += f"- ✅ Unique name within the namespace\n\n"
                    
                    output += f"## 🔄 **Option 2: Migration (If Direct Renaming Fails)**\n\n"
                    output += f"If direct renaming fails (older GitLab, permission issues, etc.):\n\n"
                    output += f"### Step-by-Step Migration:\n"
                    output += f"1. **Create new project** with name '{desired_name}' and path '{safe_path}'\n"
                    output += f"2. **Copy issues/content** from old project to new project\n"
                    if knowledge_base_id:
                        output += f"3. **Update knowledge base link:** Link KB {knowledge_base_id} to new project\n"
                    output += f"4. **Archive old project:** Keep it as backup or delete if not needed\n\n"
                    
                    output += f"## 🤖 **Automated Assistance**\n\n"
                    output += f"I can help you with:\n"
                    output += f"1. **Try direct renaming first** using GitLabRenameProjectTool\n"
                    output += f"2. **Fallback to migration** if renaming fails\n"
                    output += f"3. **Create new project** with the desired name\n"
                    output += f"4. **Set up same KB management issues**\n"
                    if knowledge_base_id:
                        output += f"5. **Update knowledge base link** to new project\n"
                        output += f"6. **Archive old project** safely\n\n"
                        output += f"**Would you like me to try the direct rename first, or proceed with migration?**\n"
                    else:
                        output += f"5. **Archive old project** safely\n\n"
                        output += f"**Would you like me to try the direct rename first?**\n"
                    
                    output += f"## 🛠️ **Troubleshooting Common Issues**\n\n"
                    output += f"**Permission Denied:**\n"
                    output += f"- Request admin/maintainer access\n"
                    output += f"- Ask project owner to perform rename\n"
                    output += f"- Use migration approach instead\n\n"
                    
                    output += f"**Name Already Exists:**\n"
                    output += f"- Try '{desired_name}-v2' or '{desired_name}-new'\n"
                    output += f"- Check for archived projects with same name\n"
                    output += f"- Consider different naming convention\n\n"
                    
                    output += f"**Feature Not Supported:**\n"
                    output += f"- GitLab instance may be older\n"
                    output += f"- Contact admin about upgrading\n"
                    output += f"- Use migration approach\n\n"
                    
                    output += f"## 📋 **Migration Checklist** (if needed)\n\n"
                    output += f"- [ ] Try direct rename first with GitLabRenameProjectTool\n"
                    output += f"- [ ] If failed: Create new project '{desired_name}'\n"
                    output += f"- [ ] Copy important issues from old project\n"
                    output += f"- [ ] Update any external links/bookmarks\n"
                    if knowledge_base_id:
                        output += f"- [ ] Update knowledge base {knowledge_base_id} link\n"
                    output += f"- [ ] Archive/delete old project '{current_name}'\n"
                    output += f"- [ ] Notify team members of project changes\n"
                    
                    return output
                    
                except Exception as e:
                    return f"❌ **Error:** {str(e)}\n\n**Please verify the project ID and try again.**"

        return GitLabRenameProjectGuidanceTool()

    def _create_archive_project_tool(self):
        """Create a tool for archiving GitLab projects."""
        class GitLabArchiveProjectTool(BaseTool):
            name: str = "GitLabArchiveProjectTool"
            description: str = """
                Archive a GitLab project (soft delete - can be restored later).
                Use this when you want to remove a project temporarily or as part of renaming workflow.
                Archived projects remain accessible but are hidden from normal views.
            """.strip()
            return_direct: bool = False

            class ArchiveProjectInputModel(BaseModel):
                project_id: str = Field(description="GitLab project ID to archive")
                confirm: bool = Field(default=False, description="Confirmation that you want to archive the project")

                @field_validator("project_id")
                def validate_project_id(cls, project_id):
                    if not project_id or not project_id.strip():
                        raise ValueError("Project ID is required")
                    return project_id.strip()

            args_schema: Optional[ArgsSchema] = ArchiveProjectInputModel

            def _run(self, project_id: str, confirm: bool = False) -> str:
                if not confirm:
                    return f"⚠️ **Confirmation Required:** To archive project {project_id}, you must set confirm=True. **This action can be reversed but will hide the project from normal views.**"
                
                try:
                    gitlab_ops = GitLabOperations()
                    result = gitlab_ops.archive_project(project_id)
                    
                    if result.get('error'):
                        return f"❌ **Error archiving project:** {result['error']}\n\n**Troubleshooting:**\n- Verify project ID exists\n- Check GitLab permissions\n- Ensure you have admin access to the project"
                    
                    if result.get('archived'):
                        return f"✅ **Project Archived Successfully!**\n\n🆔 **Project ID:** {result['id']}\n📁 **Project Name:** {result['name']}\n📦 **Status:** Archived\n\n⚠️ **Note:** Archived projects can be restored later through GitLab web interface."
                    else:
                        return f"⚠️ **Archive operation failed** - project may already be archived or inaccessible."
                        
                except Exception as e:
                    return f"❌ **Error:** {str(e)}\n\n**Common Solutions:**\n- Verify project exists\n- Check GitLab connection\n- Ensure proper admin permissions"

        return GitLabArchiveProjectTool()

    # Initialize tools and make them available
    def __init__(self) -> None:
        self._tools = [
            self.GitLabGetProjectsListTool(),
            self.GitLabGetProjectDetailsTool(),
            self.GitLabGetProjectFilesTool(),
            self.GitLabGetFileContentTool(),
            self.GitLabCreateIssueTool(),
            self.GitLabGetProjectIssuesTool(),
            self.GitLabGetIssueDetailsTool(),
            self.GitLabGetWorkItemsTool(),
            self.GitLabGetWorkItemDetailsTool(),
            self.GitLabCreateProjectTool(),
            self.GitLabCreateProjectForKBTool(),
            self.GitLabGetKnowledgeBaseByProjectTool(),
            self.GitLabCreateKBManagementIssuesTool(),
            self._create_update_project_tool(),
            self._create_rename_project_tool(),
            self._create_rename_project_guidance_tool(),
            self._create_archive_project_tool()
        ]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self._tools
    
    def get_tools(self) -> List[BaseTool]:
        return self._tools
