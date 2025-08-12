import os
import gitlab
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)

class GitLabOperations:
    """GitLab operations using the official python-gitlab library."""
    
    def __init__(self):
        self.gitlab_url = os.getenv('GITLAB_URL', 'http://localhost:8929')
        self.gitlab_token = os.getenv('GITLAB_PAT')
        
        if not self.gitlab_token:
            raise ValueError("GitLab Personal Access Token (GITLAB_PAT) is not set in environment variables.")
        
        # Initialize GitLab connection
        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token)
        
        # Authenticate to verify connection
        try:
            self.gl.auth()
            print(f"✅ Connected to GitLab at {self.gitlab_url}")
        except Exception as e:
            print(f"⚠️ GitLab connection warning: {e}")
    
    def get_projects_list(self) -> List[Dict[str, Any]]:
        """Get a list of all GitLab projects accessible with the current token."""
        try:
            projects = self.gl.projects.list(all=True)
            
            # Convert to dict format for consistency
            result = []
            for project in projects:
                result.append({
                    'id': project.id,
                    'name': project.name,
                    'path': project.path,
                    'path_with_namespace': project.path_with_namespace,
                    'description': project.description,
                    'visibility': project.visibility,
                    'web_url': project.web_url,
                    'default_branch': getattr(project, 'default_branch', 'main'),
                    'created_at': project.created_at,
                    'last_activity_at': project.last_activity_at
                })
            
            return result
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_projects_list: {e}")
            return []
    
    def get_project_details(self, project_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific GitLab project."""
        try:
            project = self.gl.projects.get(project_id)
            
            return {
                'id': project.id,
                'name': project.name,
                'path': project.path,
                'path_with_namespace': project.path_with_namespace,
                'description': project.description,
                'visibility': project.visibility,
                'web_url': project.web_url,
                'default_branch': getattr(project, 'default_branch', 'main'),
                'created_at': project.created_at,
                'last_activity_at': project.last_activity_at,
                'issues_enabled': project.issues_enabled,
                'merge_requests_enabled': project.merge_requests_enabled,
                'wiki_enabled': project.wiki_enabled,
                'snippets_enabled': project.snippets_enabled
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_project_details: {e}")
            return {}
    
    def get_project_files(self, project_id: str, path: str = "", ref: str = "main") -> List[Dict[str, Any]]:
        """Get a list of files in a GitLab project repository."""
        try:
            project = self.gl.projects.get(project_id)
            items = project.repository_tree(path=path, ref=ref, all=True)
            
            # Convert to dict format
            result = []
            for item in items:
                result.append({
                    'id': item['id'],
                    'name': item['name'],
                    'type': item['type'],
                    'path': item['path'],
                    'mode': item['mode']
                })
            
            return result
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_project_files: {e}")
            return []
    
    def get_file_content(self, project_id: str, file_path: str, ref: str = "main") -> str:
        """Get the content of a specific file from a GitLab project."""
        try:
            project = self.gl.projects.get(project_id)
            file_info = project.files.get(file_path=file_path, ref=ref)
            
            # Decode the content (it's base64 encoded)
            import base64
            content = base64.b64decode(file_info.content).decode('utf-8')
            return content
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_file_content: {e}")
            return ""
    
    def create_issue(self, project_id: str, title: str, description: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create a new issue in a GitLab project."""
        try:
            project = self.gl.projects.get(project_id)
            
            issue_data = {
                'title': title,
                'description': description
            }
            
            if labels:
                issue_data['labels'] = labels
            
            issue = project.issues.create(issue_data)
            
            return {
                'id': issue.id,
                'iid': issue.iid,
                'title': issue.title,
                'description': issue.description,
                'state': issue.state,
                'web_url': issue.web_url,
                'created_at': issue.created_at,
                'updated_at': issue.updated_at,
                'author': {'name': issue.author.get('name', 'Unknown')} if hasattr(issue, 'author') and issue.author else {'name': 'Unknown'}
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.create_issue: {e}")
            return {}
    
    def get_project_issues(self, project_id: str, state: str = "opened") -> List[Dict[str, Any]]:
        """Get a list of issues from a GitLab project."""
        try:
            project = self.gl.projects.get(project_id)
            issues = project.issues.list(state=state, all=True)
            
            # Convert to dict format
            result = []
            for issue in issues:
                result.append({
                    'id': issue.id,
                    'iid': issue.iid,
                    'title': issue.title,
                    'description': issue.description,
                    'state': issue.state,
                    'web_url': issue.web_url,
                    'created_at': issue.created_at,
                    'updated_at': issue.updated_at,
                    'author': {'name': issue.author.get('name', 'Unknown')} if hasattr(issue, 'author') and issue.author else {'name': 'Unknown'}
                })
            
            return result
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_project_issues: {e}")
            return []
    
    def get_issue_details(self, project_id: str, issue_iid: str) -> Dict[str, Any]:
        """Get detailed information about a specific issue, including tasks."""
        try:
            project = self.gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
            
            result = {
                'id': issue.id,
                'iid': issue.iid,
                'title': issue.title,
                'description': issue.description,
                'state': issue.state,
                'web_url': issue.web_url,
                'created_at': issue.created_at,
                'updated_at': issue.updated_at,
                'author': {'name': issue.author.get('name', 'Unknown')} if hasattr(issue, 'author') and issue.author else {'name': 'Unknown'}
            }
            
            # Add task completion status if available
            if hasattr(issue, 'task_completion_status'):
                result['task_completion_status'] = issue.task_completion_status
            
            return result
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_issue_details: {e}")
            return {}

    def update_project_details(self, project_id: str, name: str = None, description: str = None, 
                              visibility: str = None, topics: List[str] = None) -> Dict[str, Any]:
        """Update GitLab project details including name (now supported in newer GitLab versions)."""
        try:
            project = self.gl.projects.get(project_id)
            
            updates = {}
            if name is not None:
                updates['name'] = name
                # Also update the path to match the new name
                new_path = name.lower().replace(' ', '-').replace('_', '-')
                new_path = ''.join(c for c in new_path if c.isalnum() or c == '-')
                updates['path'] = new_path
            if description is not None:
                updates['description'] = description
            if visibility is not None:
                updates['visibility'] = visibility
            if topics is not None:
                updates['topics'] = topics
                
            if updates:
                # Update the project attributes
                if 'name' in updates:
                    project.name = updates['name']
                if 'path' in updates:
                    project.path = updates['path']
                if 'description' in updates:
                    project.description = updates['description']
                if 'visibility' in updates:
                    project.visibility = updates['visibility']
                if 'topics' in updates:
                    project.topics = updates['topics']
                project.save()
                
            return {
                'id': project.id,
                'name': project.name,
                'path': project.path,
                'path_with_namespace': project.path_with_namespace,
                'description': project.description,
                'visibility': project.visibility,
                'web_url': project.web_url,
                'topics': getattr(project, 'topics', []),
                'updated': True,
                'renamed': 'name' in updates
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.update_project_details: {e}")
            # Check if it's a rename-related error
            error_msg = str(e).lower()
            if 'name' in error_msg or 'path' in error_msg:
                return {
                    'error': f"Project renaming failed: {str(e)}. This GitLab instance may not support renaming or you may need admin permissions.",
                    'updated': False,
                    'rename_error': True
                }
            return {'error': str(e), 'updated': False}

    def rename_project(self, project_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a GitLab project (supported in newer GitLab versions)."""
        try:
            project = self.gl.projects.get(project_id)
            old_name = project.name
            
            # Update both name and path
            new_path = new_name.lower().replace(' ', '-').replace('_', '-')
            new_path = ''.join(c for c in new_path if c.isalnum() or c == '-')
            
            project.name = new_name
            project.path = new_path
            project.save()
            
            return {
                'id': project.id,
                'old_name': old_name,
                'new_name': project.name,
                'old_path': project.path_with_namespace.split('/')[-1] if '/' in project.path_with_namespace else project.path,
                'new_path': project.path,
                'path_with_namespace': project.path_with_namespace,
                'web_url': project.web_url,
                'renamed': True,
                'success': True
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"An error occurred with GitLabOperations.rename_project: {e}")
            
            # Provide specific error guidance
            if 'permission' in error_msg or 'forbidden' in error_msg:
                return {
                    'error': f"Permission denied: You need admin/maintainer permissions to rename this project. Error: {str(e)}",
                    'renamed': False,
                    'success': False,
                    'permission_error': True
                }
            elif 'exists' in error_msg or 'taken' in error_msg:
                return {
                    'error': f"Project name already exists: '{new_name}' is already taken in this namespace. Error: {str(e)}",
                    'renamed': False,
                    'success': False,
                    'name_conflict': True
                }
            elif 'not supported' in error_msg or 'not found' in error_msg:
                return {
                    'error': f"Renaming not supported: This GitLab instance may not support project renaming. Error: {str(e)}",
                    'renamed': False,
                    'success': False,
                    'unsupported': True
                }
            else:
                return {
                    'error': f"Rename failed: {str(e)}",
                    'renamed': False,
                    'success': False
                }

    def archive_project(self, project_id: str) -> Dict[str, Any]:
        """Archive a GitLab project (soft delete - can be restored)."""
        try:
            project = self.gl.projects.get(project_id)
            project.archive()
            
            return {
                'id': project.id,
                'name': project.name,
                'archived': True,
                'message': 'Project archived successfully'
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.archive_project: {e}")
            return {'error': str(e), 'archived': False}

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a GitLab project permanently (cannot be undone)."""
        try:
            project = self.gl.projects.get(project_id)
            project_name = project.name
            project.delete()
            
            return {
                'id': project_id,
                'name': project_name,
                'deleted': True,
                'message': 'Project deleted permanently'
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.delete_project: {e}")
            return {'error': str(e), 'deleted': False}
    
    def create_project(self, name: str, description: str = "", visibility: str = "public", 
                      initialize_with_readme: bool = False) -> Dict[str, Any]:
        """Create a new GitLab project for knowledge base management (without repository by default)."""
        try:
            project_data = {
                'name': name,
                'path': name.lower().replace(' ', '-').replace('_', '-'),
                'description': description or f"Knowledge Base project for {name}",
                'visibility': visibility,
                'initialize_with_readme': initialize_with_readme,
                'issues_enabled': True,
                'merge_requests_enabled': True,
                'wiki_enabled': True,
                'snippets_enabled': True
            }
            
            project = self.gl.projects.create(project_data)
            
            return {
                'id': project.id,
                'name': project.name,
                'path': project.path,
                'path_with_namespace': project.path_with_namespace,
                'description': project.description,
                'visibility': project.visibility,
                'web_url': project.web_url,
                'default_branch': getattr(project, 'default_branch', 'main'),
                'created_at': project.created_at,
                'issues_enabled': project.issues_enabled,
                'merge_requests_enabled': project.merge_requests_enabled
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.create_project: {e}")
            return {}
    
    def create_project_for_knowledge_base(self, kb_id: int, name: str, description: str = "", 
                                        visibility: str = "public", initialize_with_readme: bool = False) -> Optional[Dict[str, Any]]:
        """Create a GitLab project and link it to a knowledge base."""
        try:
            # Import here to avoid circular imports
            from operations.knowledge_base_operations import KnowledgeBaseOperations
            
            # Create the GitLab project
            project = self.create_project(name, description, visibility, initialize_with_readme)
            
            if project and project.get('id'):
                gitlab_project_id = project['id']
                
                # Update the knowledge base with the GitLab project ID
                kb_ops = KnowledgeBaseOperations()
                success = kb_ops.update_knowledge_base_gitlab_project_id(kb_id, gitlab_project_id)
                
                if success:
                    print(f"✅ Successfully linked Knowledge Base {kb_id} to GitLab project {gitlab_project_id}")
                    # Add the KB ID to the returned project info
                    project['linked_knowledge_base_id'] = kb_id
                    return project
                else:
                    print(f"⚠️ Created GitLab project {gitlab_project_id} but failed to link to Knowledge Base {kb_id}")
                    return project
            else:
                print(f"❌ Failed to create GitLab project for Knowledge Base {kb_id}")
                return None
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.create_project_for_knowledge_base: {e}")
            return None
    
    def create_kb_management_issues(self, project_id: str, kb_name: str) -> List[Dict[str, Any]]:
        """Create initial issues for knowledge base generation and management."""
        try:
            # Define standard KB management issues
            kb_issues = [
                {
                    'title': f'📋 Knowledge Base Planning - {kb_name}',
                    'description': f'''# Knowledge Base Planning

This issue tracks the overall planning and structure for the **{kb_name}** knowledge base.

## Planning Tasks:
- [ ] Define knowledge base scope and objectives
- [ ] Identify content sources and references
- [ ] Plan article structure and organization
- [ ] Set up content review process
- [ ] Define success criteria and metrics

## Status:
- **Phase**: Planning
- **KB Name**: {kb_name}
- **Created**: Auto-generated for KB management

/label ~planning ~knowledge-base ~{kb_name.lower().replace(' ', '-')}''',
                    'labels': ['planning', 'knowledge-base', kb_name.lower().replace(' ', '-')]
                },
                {
                    'title': f'✍️ Content Generation - {kb_name}',
                    'description': f'''# Content Generation

This issue tracks content creation and generation for the **{kb_name}** knowledge base.

## Content Tasks:
- [ ] Generate initial articles and documentation
- [ ] Create structured content outline
- [ ] Develop comprehensive article content
- [ ] Ensure content quality and accuracy
- [ ] Add relevant tags and metadata

## Progress Tracking:
- **Articles Created**: 0
- **Articles Reviewed**: 0
- **Content Coverage**: TBD

## Status:
- **Phase**: Content Generation
- **KB Name**: {kb_name}
- **Dependencies**: Planning phase completion

/label ~content-generation ~knowledge-base ~{kb_name.lower().replace(' ', '-')}''',
                    'labels': ['content-generation', 'knowledge-base', kb_name.lower().replace(' ', '-')]
                },
                {
                    'title': f'🔍 Quality Review - {kb_name}',
                    'description': f'''# Quality Review and Validation

This issue tracks quality assurance and review processes for the **{kb_name}** knowledge base.

## Review Tasks:
- [ ] Content accuracy verification
- [ ] Technical review of articles
- [ ] Format and style consistency check
- [ ] Cross-reference validation
- [ ] User acceptance testing

## Quality Metrics:
- **Accuracy Score**: TBD
- **Completeness**: TBD
- **User Feedback**: TBD

## Status:
- **Phase**: Quality Review
- **KB Name**: {kb_name}
- **Dependencies**: Content generation completion

/label ~quality-review ~knowledge-base ~{kb_name.lower().replace(' ', '-')}''',
                    'labels': ['quality-review', 'knowledge-base', kb_name.lower().replace(' ', '-')]
                },
                {
                    'title': f'🚀 Deployment & Maintenance - {kb_name}',
                    'description': f'''# Deployment and Ongoing Maintenance

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

## Status:
- **Phase**: Deployment & Maintenance
- **KB Name**: {kb_name}
- **Dependencies**: Quality review completion

/label ~deployment ~maintenance ~knowledge-base ~{kb_name.lower().replace(' ', '-')}''',
                    'labels': ['deployment', 'maintenance', 'knowledge-base', kb_name.lower().replace(' ', '-')]
                }
            ]
            
            created_issues = []
            for issue_data in kb_issues:
                issue = self.create_issue(
                    project_id=project_id,
                    title=issue_data['title'],
                    description=issue_data['description'],
                    labels=issue_data['labels']
                )
                if issue:
                    created_issues.append(issue)
            
            return created_issues
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.create_kb_management_issues: {e}")
            return []

    def get_work_items(self, project_id: str, work_item_type: str = "Task") -> List[Dict[str, Any]]:
        """Get work items from a project. In GitLab, work items might be issues or dedicated work items."""
        try:
            project = self.gl.projects.get(project_id)
            
            # Try to get work items if the API supports it
            try:
                # This might work in newer GitLab versions
                work_items = project.work_items.list(all=True)
                result = []
                for item in work_items:
                    if hasattr(item, 'work_item_type') and item.work_item_type.get('name', '').lower() == work_item_type.lower():
                        result.append({
                            'id': item.id,
                            'iid': item.iid,
                            'title': item.title,
                            'state': item.state,
                            'web_url': item.web_url,
                            'created_at': item.created_at,
                            'work_item_type': item.work_item_type,
                            'author': {'name': item.author.get('name', 'Unknown')} if hasattr(item, 'author') and item.author else {'name': 'Unknown'}
                        })
                return result
            except:
                # Fallback to issues for older GitLab versions
                print(f"Work items API not available, falling back to issues for {work_item_type}")
                return self.get_project_issues(project_id, "opened")
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_work_items: {e}")
            return []
    
    def get_work_item_details(self, project_id: str, work_item_iid: str) -> Dict[str, Any]:
        """Get detailed information about a specific work item/task."""
        try:
            project = self.gl.projects.get(project_id)
            
            # Try work items API first
            try:
                work_item = project.work_items.get(work_item_iid)
                return {
                    'id': work_item.id,
                    'iid': work_item.iid,
                    'title': work_item.title,
                    'description': getattr(work_item, 'description', ''),
                    'state': work_item.state,
                    'web_url': work_item.web_url,
                    'created_at': work_item.created_at,
                    'updated_at': work_item.updated_at,
                    'work_item_type': getattr(work_item, 'work_item_type', {'name': 'Work Item'}),
                    'author': {'name': work_item.author.get('name', 'Unknown')} if hasattr(work_item, 'author') and work_item.author else {'name': 'Unknown'}
                }
            except:
                # Fallback to issue API
                return self.get_issue_details(project_id, work_item_iid)
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_work_item_details: {e}")
            return {}
