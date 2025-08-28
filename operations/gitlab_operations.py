import os
import time
import signal
import gitlab
from typing import List, Optional, Dict, Any

# Don't load dotenv at module level - let the caller handle it

class GitLabOperations:
    """GitLab operations using the official python-gitlab library."""
    
    def __init__(self, agent_name=None):
        self.gitlab_url = os.getenv('GITLAB_URL', 'http://localhost:8929')
        self.agent_name = agent_name
        
        # Try to use agent-specific credentials if agent_name is provided
        if agent_name:
            self.gitlab_token = self._get_agent_credentials(agent_name)
            print(f"GitLab operations ready for {self.gitlab_url} (Agent: {agent_name})")
        else:
            # Use default PAT token - try both common environment variable names
            self.gitlab_token = os.getenv('GITLAB_PAT') or os.getenv('GITLAB_ADMIN_PAT')
            if not self.gitlab_token:
                raise ValueError("GITLAB_PAT or GITLAB_ADMIN_PAT environment variable is required when no agent_name is provided")
            print(f"GitLab operations ready for {self.gitlab_url} (Default credentials)")
        
        # Simple initialization - lazy load the client
        self.gl = None
    
    def _get_agent_credentials(self, agent_name):
        """Get GitLab credentials for a specific agent."""
        # Convert agent class name to environment variable format
        # e.g., "ContentCreatorAgent" -> "CONTENT_CREATOR_AGENT"
        
        # Remove 'Agent' suffix if present
        base_name = agent_name.replace('Agent', '') if agent_name.endswith('Agent') else agent_name
        
        # Convert CamelCase to snake_case
        import re
        # Insert underscore before uppercase letters (except the first one)
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', base_name)
        
        # Convert to uppercase and add AGENT suffix
        env_agent_name = f"{snake_case.upper()}_AGENT"
        
        # Try to get agent-specific PAT token
        username_key = f"GITLAB_AGENT_{env_agent_name}_USERNAME"
        pat_key = f"GITLAB_AGENT_{env_agent_name}_PAT"
        
        username = os.getenv(username_key)
        agent_pat = os.getenv(pat_key)
        
        print(f"🔍 Looking for credentials for {agent_name}:")
        print(f"   Username key: {username_key}")
        print(f"   PAT key: {pat_key}")
        print(f"   Username found: {username is not None}")
        print(f"   PAT found: {agent_pat is not None}")
        
        if not username:
            raise ValueError(f"Agent username not found. Missing environment variable: {username_key}")
        
        if not agent_pat:
            raise ValueError(f"Agent PAT token not found. Missing environment variable: {pat_key}")
        
        if agent_pat.startswith('glpat-placeholder'):
            raise ValueError(f"Agent PAT token is still a placeholder. Please set a real PAT token for {agent_name}")
        
        print(f"🔐 Using agent-specific credentials for {agent_name} (Username: {username})")
        return agent_pat
    
    def _ensure_client(self):
        """Lazy initialization of GitLab client."""
        if self.gl is None:
            print(f"🔄 Creating GitLab client...")
            import requests
            session = requests.Session()
            session.timeout = 5
            
            # Check if we should use agent-specific authentication
            if self.agent_name and not self.gitlab_token:
                # Get agent-specific username/password
                env_agent_name = self.agent_name.replace('Agent', '_AGENT').upper()
                if not env_agent_name.endswith('_AGENT'):
                    env_agent_name = f"{env_agent_name}_AGENT"
                
                import re
                env_agent_name = re.sub('([A-Z]+)', r'_\1', env_agent_name).upper().strip('_')
                
                username_key = f"GITLAB_AGENT_{env_agent_name}_USERNAME"
                password_key = f"GITLAB_AGENT_{env_agent_name}_PASSWORD"
                
                username = os.getenv(username_key)
                password = os.getenv(password_key)
                
                if username and password:
                    print(f"🔐 Authenticating as {username}")
                    # Use username/password authentication
                    self.gl = gitlab.Gitlab(
                        self.gitlab_url,
                        username=username,
                        password=password,
                        session=session
                    )
                else:
                    raise ValueError(f"Agent credentials not found for {self.agent_name}")
            else:
                # Use PAT token authentication
                self.gl = gitlab.Gitlab(
                    self.gitlab_url, 
                    private_token=self.gitlab_token, 
                    session=session
                )
            print(f"✅ GitLab client created")
    
    
    def _create_gitlab_client_with_timeout(self, timeout_seconds=10):
        """Create GitLab client with a timeout mechanism."""
        
        def timeout_handler(signum, frame):
            raise TimeoutError("GitLab client creation timed out")
        
        # Set up timeout signal (only works on Unix-like systems)
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            import requests
            session = requests.Session()
            session.timeout = 5
            
            gl = gitlab.Gitlab(
                self.gitlab_url, 
                private_token=self.gitlab_token, 
                session=session
            )
            
            signal.alarm(0)  # Cancel the alarm
            return gl
            
        except TimeoutError:
            raise Exception(f"GitLab client creation timed out after {timeout_seconds} seconds")
        finally:
            signal.signal(signal.SIGALRM, old_handler)  # Restore old handler
    
    def _initialize_gitlab_connection(self, max_retries=3, base_delay=1):
        """Initialize GitLab connection with retry logic and exponential backoff."""
        for attempt in range(max_retries):
            try:
                print(f"🔄 GitLab connection attempt {attempt + 1}/{max_retries}...")
                
                # Try to create client with timeout (if on Unix-like system)
                try:
                    print(f"   🔧 Creating GitLab client with timeout...")
                    self.gl = self._create_gitlab_client_with_timeout(10)
                    print(f"   ✅ GitLab client created")
                except:
                    # Fallback for Windows or if timeout doesn't work
                    print(f"   � Creating GitLab client (fallback method)...")
                    import requests
                    session = requests.Session()
                    session.timeout = 5
                    self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token, session=session)
                    print(f"   ✅ GitLab client created (fallback)")
                
                print(f"✅ GitLab connection established successfully!")
                return  # Success!
                    
            except Exception as e:
                print(f"❌ GitLab connection attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:  # Not the last attempt
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⏳ Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"💥 All GitLab connection attempts failed!")
                    print(f"⚠️ Continuing without GitLab verification...")
                    # Create a minimal client as last resort
                    import requests
                    session = requests.Session()
                    session.timeout = 5
                    self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token, session=session)
        print(f"🔑 Token configured: {'***' + self.gitlab_token[-4:] if self.gitlab_token else 'None'}")
        
        # We'll test the connection when we actually use it
    
    def get_projects_list(self) -> List[Dict[str, Any]]:
        """Get a list of all GitLab projects accessible with the current token.
        
        Excludes archived projects and projects pending deletion to improve performance
        and avoid unnecessary iteration over inactive projects.
        """
        try:
            self._ensure_client()  # Lazy load client
            # Filter out archived projects at the API level for better performance
            projects = self.gl.projects.list(all=True, archived=False)
            
            # Convert to dict format for consistency
            result = []
            for project in projects:
                # Additional filtering: skip projects with deletion indicators in name
                project_name_lower = project.name.lower()
                if any(deletion_keyword in project_name_lower for deletion_keyword in ['deleted', 'to-delete', 'pending-deletion', 'archived']):
                    continue
                    
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
                    'last_activity_at': project.last_activity_at,
                    'archived': getattr(project, 'archived', False)  # Include archived status for reference
                })
            
            return result
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_projects_list: {e}")
            return []
    
    def get_project_details(self, project_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific GitLab project."""
        try:
            self._ensure_client()
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
                'snippets_enabled': project.snippets_enabled,
                'archived': getattr(project, 'archived', False),  # Include archived status
                'open_issues_count': getattr(project, 'open_issues_count', 0)  # Include open issues count
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_project_details: {e}")
            return {}
    
    def get_project_files(self, project_id: str, path: str = "", ref: str = "main") -> List[Dict[str, Any]]:
        """Get a list of files in a GitLab project repository."""
        try:
            self._ensure_client()
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
            self._ensure_client()
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
            self._ensure_client()
            project = self.gl.projects.get(project_id)
            
            # Add agent attribution to description if agent_name is provided
            if self.agent_name:
                agent_attribution = f"\n\n---\nAgent: {self.agent_name}\nThis issue was created by the {self.agent_name} autonomous agent."
                description = description + agent_attribution
            
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
        """Get a list of issues from a GitLab project using direct HTTP API."""
        try:
            import requests
            
            # Use direct HTTP request instead of python-gitlab library for better reliability
            headers = {
                'PRIVATE-TOKEN': self.gitlab_token
            }
            
            url = f"{self.gitlab_url}/api/v4/projects/{project_id}/issues"
            params = {
                'state': state,
                'per_page': 100  # Get up to 100 issues
            }
            
            print(f"🔍 Fetching issues from {url}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                issues = response.json()
                print(f"✅ Found {len(issues)} issues")
                
                # Convert to our expected format
                result = []
                for issue in issues:
                    result.append({
                        'id': issue.get('id'),
                        'iid': issue.get('iid'),
                        'title': issue.get('title'),
                        'description': issue.get('description'),
                        'state': issue.get('state'),
                        'web_url': issue.get('web_url'),
                        'created_at': issue.get('created_at'),
                        'updated_at': issue.get('updated_at'),
                        'author': {'name': issue.get('author', {}).get('name', 'Unknown')},
                        'labels': issue.get('labels', []),
                        'assignees': issue.get('assignees', [])
                    })
                
                return result
            else:
                print(f"❌ GitLab API error: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_project_issues: {e}")
            return []
    
    def search_issues(self, project_id: str, search_text: str, state: str = "opened") -> List[Dict[str, Any]]:
        """Search for issues in a GitLab project using GitLab's native search functionality."""
        try:
            self._ensure_client()
            project = self.gl.projects.get(project_id)
            
            # Use GitLab's native search functionality
            issues = project.issues.list(search=search_text, state=state, all=True)
            
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
                    'labels': getattr(issue, 'labels', []),
                    'author': {'name': issue.author.get('name', 'Unknown')} if hasattr(issue, 'author') and issue.author else {'name': 'Unknown'}
                })
            
            return result
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.search_issues: {e}")
            return []
    
    def check_duplicate_issue(self, project_id: str, title: str) -> bool:
        """Check if an issue with the exact same title already exists."""
        try:
            self._ensure_client()
            
            # Search for issues with this title
            matching_issues = self.search_issues(project_id, title, state="opened")
            
            # Check for exact title matches
            exact_matches = [
                issue for issue in matching_issues 
                if issue['title'].strip() == title.strip()
            ]
            
            if exact_matches:
                print(f"🔄 Duplicate detected! Found {len(exact_matches)} exact matches for title: '{title}'")
                for match in exact_matches[:3]:  # Show first 3
                    print(f"   🔗 Existing issue #{match['iid']}: {match['web_url']}")
                return True
            else:
                print(f"✅ No duplicates found for title: '{title}'")
                return False
                
        except Exception as e:
            print(f"❌ Error checking for duplicates: {e}")
            # Return False to be safe - better to potentially create duplicate than miss required work
            return False
    
    def create_issue_with_duplicate_check(self, project_id: str, title: str, description: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create an issue with built-in duplicate detection."""
        try:
            # Check for duplicates first
            if self.check_duplicate_issue(project_id, title):
                print(f"🚫 Skipping issue creation due to duplicate: '{title}'")
                return {}
            
            # No duplicates found, create the issue
            return self.create_issue(project_id, title, description, labels)
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.create_issue_with_duplicate_check: {e}")
            return {}
    
    def get_user_assigned_issues(self, username: str, state: str = "opened", project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get a list of issues assigned to a specific user (by username)."""
        try:
            self._ensure_client()
            # First find the user by username
            users = self.gl.users.list(username=username)
            if not users:
                print(f"User with username '{username}' not found")
                return []
            
            user = users[0]
            user_id = user.id
            
            # Get issues assigned to this user
            if project_id:
                # Get issues from specific project
                project = self.gl.projects.get(project_id)
                issues = project.issues.list(assignee_id=user_id, state=state, all=True)
            else:
                # Get issues from all accessible projects
                issues = self.gl.issues.list(assignee_id=user_id, state=state, all=True)
            
            # Convert to dict format
            result = []
            for issue in issues:
                issue_dict = {
                    'id': issue.id,
                    'iid': issue.iid,
                    'title': issue.title,
                    'description': issue.description,
                    'state': issue.state,
                    'web_url': issue.web_url,
                    'created_at': issue.created_at,
                    'updated_at': issue.updated_at,
                    'project_id': issue.project_id,
                    'author': {'name': issue.author.get('name', 'Unknown')} if hasattr(issue, 'author') and issue.author else {'name': 'Unknown'},
                    'assignee': {'name': username, 'id': user_id}
                }
                
                # Add labels if available
                if hasattr(issue, 'labels'):
                    issue_dict['labels'] = issue.labels
                
                # Add milestone if available
                if hasattr(issue, 'milestone') and issue.milestone:
                    issue_dict['milestone'] = issue.milestone.get('title', 'Unknown')
                
                result.append(issue_dict)
            
            return result
                
        except Exception as e:
            print(f"An error occurred with GitLabOperations.get_user_assigned_issues: {e}")
            return []
    
    def get_issue_details(self, project_id: str, issue_iid: str) -> Dict[str, Any]:
        """Get detailed information about a specific issue, including tasks."""
        try:
            self._ensure_client()  # Ensure GitLab client is initialized
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
            self._ensure_client()
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
            self._ensure_client()
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
            self._ensure_client()
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
            self._ensure_client()
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
            self._ensure_client()  # Lazy load client
            
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
                    'title': '📋 Knowledge Base Planning',
                    'description': f'''# Knowledge Base Planning & Architecture

This issue defines the comprehensive planning and architectural foundation for the **{kb_name}** knowledge base.

## Specific Planning Deliverables:
- [ ] **Content Taxonomy Design**: Create hierarchical category structure with 3-5 main topics, each with 2-4 subtopics
- [ ] **Target Audience Analysis**: Define primary user personas and their specific information needs
- [ ] **Content Gap Assessment**: Identify 10-15 specific article topics needed for comprehensive coverage
- [ ] **Knowledge Map Creation**: Design interconnected topic relationships and dependency chains
- [ ] **Content Standards Document**: Define writing style, format templates, and quality criteria
- [ ] **Workflow Blueprint**: Establish content creation → review → publishing pipeline with clear handoffs

## Technical Requirements:
- [ ] Define metadata schema (tags, categories, difficulty levels, prerequisites)
- [ ] Establish content naming conventions and URL structures
- [ ] Plan search optimization strategy and keyword targeting
- [ ] Design content update and maintenance schedules

## Success Criteria:
- ✅ Complete content architecture with minimum 15 planned articles
- ✅ Documented workflow with defined agent responsibilities
- ✅ Quality standards that ensure 90%+ user satisfaction
- ✅ Scalable structure supporting future content expansion

## Agent Assignment:
**Primary**: ContentPlannerAgent  
**Support**: ContentManagementAgent (workflow design)  
**Review**: SupervisorAgent

## Timeline: 
**Estimated Completion**: 2-3 days  
**Dependencies**: None (foundational work)

/label ~planning ~knowledge-base ~{kb_name.lower().replace(' ', '-')} ~high-priority''',
                    'labels': ['planning', 'knowledge-base', kb_name.lower().replace(' ', '-'), 'high-priority']
                },
                {
                    'title': '✍️ Content Generation',
                    'description': f'''# Comprehensive Content Development

This issue manages the systematic creation of high-quality content for the **{kb_name}** knowledge base.

## Specific Content Deliverables:
- [ ] **Introduction Article**: Write comprehensive overview (1000+ words) introducing the knowledge base topic
- [ ] **Core Concept Articles**: Create 5-7 foundational articles (800-1200 words each) covering essential concepts
- [ ] **Tutorial Content**: Develop 3-5 step-by-step guides with practical examples and code samples
- [ ] **Reference Documentation**: Build detailed reference materials, glossaries, and quick-start guides
- [ ] **FAQ Section**: Compile 15-20 frequently asked questions with comprehensive answers
- [ ] **Case Studies**: Create 2-3 real-world application examples with detailed analysis

## Content Quality Standards:
- [ ] **Accuracy**: All technical information verified and tested
- [ ] **Completeness**: Each article covers topic comprehensively with examples
- [ ] **Readability**: Content structured with clear headings, bullet points, and visual aids
- [ ] **SEO Optimization**: Strategic keyword usage and search-friendly formatting
- [ ] **Cross-References**: Internal linking between related articles for navigation
- [ ] **Code Examples**: Working, tested code samples where applicable

## Technical Implementation:
- [ ] Format content using markdown with consistent styling
- [ ] Add appropriate metadata tags for categorization and search
- [ ] Include estimated reading times and difficulty levels
- [ ] Implement internal linking strategy for topic interconnection
- [ ] Optimize images and diagrams for web performance

## Progress Tracking:
- **Total Articles Planned**: 15-20
- **Articles Completed**: 0/{15-20}
- **Word Count Target**: 12,000-15,000 words total
- **Quality Score Target**: 95%+ (based on review criteria)

## Agent Assignment:
**Primary**: ContentCreatorAgent  
**Research Support**: ContentRetrievalAgent  
**Quality Control**: ContentReviewerAgent  
**Workflow Management**: ContentManagementAgent

## Timeline:
**Estimated Completion**: 5-7 days  
**Dependencies**: Planning phase completion

/label ~content-generation ~knowledge-base ~{kb_name.lower().replace(' ', '-')} ~medium-priority''',
                    'labels': ['content-generation', 'knowledge-base', kb_name.lower().replace(' ', '-'), 'medium-priority']
                },
                {
                    'title': '🔍 Quality Review',
                    'description': f'''# Comprehensive Quality Assurance & Content Validation

This issue ensures publication-ready quality and accuracy for all **{kb_name}** knowledge base content.

## Detailed Review Checklist:
### Content Accuracy Review
- [ ] **Technical Verification**: Validate all factual claims, statistics, and technical details
- [ ] **Code Testing**: Execute and verify all code examples, ensuring they work as documented
- [ ] **Link Validation**: Test all internal and external links for functionality
- [ ] **Reference Checking**: Verify all cited sources and ensure proper attribution
- [ ] **Currency Check**: Confirm information is up-to-date and reflects current best practices

### Editorial Review
- [ ] **Grammar & Style**: Comprehensive proofreading for language accuracy and consistency
- [ ] **Structure Analysis**: Ensure logical flow, appropriate headings, and clear organization
- [ ] **Readability Assessment**: Verify content is accessible to target audience skill level
- [ ] **Tone Consistency**: Maintain consistent voice and style across all articles
- [ ] **Format Compliance**: Check adherence to established content standards and templates

### User Experience Review
- [ ] **Navigation Testing**: Verify intuitive content flow and cross-referencing
- [ ] **Search Optimization**: Confirm SEO best practices and keyword optimization
- [ ] **Mobile Compatibility**: Test content display across different devices and screen sizes
- [ ] **Accessibility Compliance**: Ensure content meets accessibility standards (WCAG 2.1)
- [ ] **Performance Review**: Optimize page load times and media file sizes

## Quality Metrics & Scoring:
- **Accuracy Score**: Target 98%+ (technical correctness)
- **Readability Score**: Target 85%+ (Flesch-Kincaid grade level appropriate)
- **SEO Score**: Target 90%+ (search optimization metrics)
- **User Satisfaction**: Target 95%+ (based on review criteria)
- **Completeness Score**: Target 100% (all planned content delivered)

## Review Deliverables:
- [ ] **Quality Assessment Report**: Detailed analysis of each article with specific feedback
- [ ] **Improvement Recommendations**: Prioritized list of enhancements and corrections
- [ ] **Compliance Checklist**: Verification of adherence to quality standards
- [ ] **Final Approval Documentation**: Sign-off on publication readiness

## Agent Assignment:
**Primary**: ContentReviewerAgent  
**Technical Validation**: ContentRetrievalAgent  
**Process Management**: ContentManagementAgent  
**Final Approval**: SupervisorAgent

## Timeline:
**Estimated Completion**: 3-4 days  
**Dependencies**: Content generation phase completion

/label ~quality-review ~knowledge-base ~{kb_name.lower().replace(' ', '-')} ~high-priority''',
                    'labels': ['quality-review', 'knowledge-base', kb_name.lower().replace(' ', '-'), 'high-priority']
                },
                {
                    'title': '🚀 Deployment & Maintenance',
                    'description': f'''# Production Deployment & Ongoing Operations

This issue manages the deployment, launch, and ongoing maintenance operations for the **{kb_name}** knowledge base.

## Deployment Deliverables:
### Pre-Deployment Checklist
- [ ] **Content Finalization**: Ensure all articles are review-approved and publication-ready
- [ ] **Infrastructure Preparation**: Configure hosting environment, CDN, and backup systems
- [ ] **Search Integration**: Set up and test search functionality with content indexing
- [ ] **Analytics Setup**: Implement tracking for user engagement, popular content, and performance metrics
- [ ] **Security Configuration**: Enable SSL, configure access controls, and implement security headers
- [ ] **Performance Optimization**: Optimize images, enable compression, and configure caching

### Launch Execution
- [ ] **Production Deployment**: Deploy content to live environment with zero-downtime procedures
- [ ] **DNS Configuration**: Configure domain routing and ensure proper subdomain setup
- [ ] **SSL Certificate Installation**: Implement and verify HTTPS security
- [ ] **Search Engine Indexing**: Submit sitemap to search engines and verify crawlability
- [ ] **User Access Testing**: Verify all functionality works correctly in production environment
- [ ] **Monitoring Setup**: Activate uptime monitoring, error tracking, and performance alerts

## Ongoing Maintenance Plan:
### Content Maintenance (Weekly)
- [ ] **Content Freshness Review**: Check for outdated information and update as needed
- [ ] **Link Health Check**: Validate all external links and fix broken references
- [ ] **User Feedback Integration**: Review and respond to user comments and suggestions
- [ ] **Search Analytics**: Analyze search queries and identify content gaps
- [ ] **Performance Monitoring**: Review page load times and optimize slow-loading content

### Technical Maintenance (Monthly)
- [ ] **Security Updates**: Apply security patches and update dependencies
- [ ] **Backup Verification**: Test backup systems and restore procedures
- [ ] **Performance Audit**: Comprehensive analysis of site speed and optimization opportunities
- [ ] **SEO Analysis**: Review search rankings and optimize for better visibility
- [ ] **User Analytics Review**: Analyze traffic patterns and user behavior insights

### Strategic Maintenance (Quarterly)
- [ ] **Content Strategy Review**: Assess content performance and plan new additions
- [ ] **Technology Stack Evaluation**: Review and upgrade underlying technologies
- [ ] **User Satisfaction Survey**: Collect feedback and implement improvements
- [ ] **Competitive Analysis**: Review similar knowledge bases and identify enhancement opportunities

## Success Metrics:
- **Uptime Target**: 99.9% availability
- **Performance Target**: <2 second page load times
- **User Satisfaction**: 90%+ positive feedback
- **Search Visibility**: Top 3 rankings for target keywords
- **Content Freshness**: 95%+ of content updated within relevance timeframes

## Agent Assignment:
**Primary**: ContentManagementAgent  
**Technical Support**: All agents (specialized tasks)  
**Quality Oversight**: SupervisorAgent  
**User Feedback**: ContentReviewerAgent

## Timeline:
**Initial Deployment**: 1-2 days  
**Ongoing Maintenance**: Continuous operations  
**Dependencies**: Quality review phase completion

/label ~deployment ~maintenance ~knowledge-base ~{kb_name.lower().replace(' ', '-')} ~medium-priority''',
                    'labels': ['deployment', 'maintenance', 'knowledge-base', kb_name.lower().replace(' ', '-'), 'medium-priority']
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
            self._ensure_client()
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
            self._ensure_client()
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
    
    def add_issue_comment(self, project_id: str, issue_iid: str, comment: str, agent_name: str = None) -> Dict[str, Any]:
        """Add a comment to a GitLab issue with optional agent identification."""
        try:
            self._ensure_client()
            project = self.gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
            
            # Use instance agent_name if none provided
            effective_agent_name = agent_name or self.agent_name
            
            # Post comment without agent identification prefix
            formatted_comment = comment
            
            # Create a note (comment) on the issue
            note = issue.notes.create({'body': formatted_comment})
            
            return {
                'id': note.id,
                'body': note.body,
                'author': note.author.get('name', 'Unknown') if hasattr(note, 'author') and note.author else 'Unknown',
                'created_at': note.created_at,
                'updated_at': note.updated_at,
                'success': True
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.add_issue_comment: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_issue(self, project_id: str, issue_iid: str, title: str = None, 
                    description: str = None, state_event: str = None, 
                    labels: List[str] = None, assignee_ids: List[int] = None, 
                    agent_name: str = None) -> Dict[str, Any]:
        """Update a GitLab issue with new title, description, state, labels, or assignees with optional agent identification."""
        try:
            self._ensure_client()
            project = self.gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
            
            # Prepare update data
            update_data = {}
            if title is not None:
                update_data['title'] = title
            if description is not None:
                # Add agent identification to description if provided
                formatted_description = description
                if agent_name:
                    formatted_description = f"{description}\n\n---\n*Updated by Agent: {agent_name}*"
                update_data['description'] = formatted_description
            if state_event is not None:
                update_data['state_event'] = state_event  # 'close' or 'reopen'
            if labels is not None:
                update_data['labels'] = labels
            if assignee_ids is not None:
                update_data['assignee_ids'] = assignee_ids
            
            # Update the issue
            issue.save(**update_data)
            
            # Return updated issue details
            return {
                'id': issue.id,
                'iid': issue.iid,
                'title': issue.title,
                'description': issue.description,
                'state': issue.state,
                'labels': issue.labels,
                'web_url': issue.web_url,
                'updated_at': issue.updated_at,
                'success': True
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.update_issue: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_issue_labels(self, project_id: str, issue_iid: str, labels: List[str]) -> Dict[str, Any]:
        """Update the labels of a GitLab issue."""
        try:
            self._ensure_client()
            project = self.gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
            
            # Update labels
            issue.labels = labels
            issue.save()
            
            return {
                'id': issue.id,
                'iid': issue.iid,
                'labels': issue.labels,
                'success': True
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.update_issue_labels: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_issue(self, project_id: str, issue_iid: str, comment: str = None, agent_name: str = None) -> Dict[str, Any]:
        """Close a GitLab issue, optionally with a closing comment and agent identification."""
        try:
            self._ensure_client()
            project = self.gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
            
            # Use instance agent_name if none provided
            effective_agent_name = agent_name or self.agent_name
            
            # Add comment if provided
            if comment:
                formatted_comment = comment
                issue.notes.create({'body': formatted_comment})
            
            # Close the issue
            issue.state_event = 'close'
            issue.save()
            
            return {
                'id': issue.id,
                'iid': issue.iid,
                'state': issue.state,
                'success': True
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.close_issue: {e}")
            return {'success': False, 'error': str(e)}
    
    def reopen_issue(self, project_id: str, issue_iid: str, comment: str = None, agent_name: str = None) -> Dict[str, Any]:
        """Reopen a GitLab issue, optionally with a reopening comment and agent identification."""
        try:
            self._ensure_client()
            project = self.gl.projects.get(project_id)
            issue = project.issues.get(issue_iid)
            
            # Add comment if provided, with agent identification
            if comment:
                formatted_comment = comment
                issue.notes.create({'body': formatted_comment})
            
            # Reopen the issue
            issue.state_event = 'reopen'
            issue.save()
            
            return {
                'id': issue.id,
                'iid': issue.iid,
                'state': issue.state,
                'success': True
            }
            
        except Exception as e:
            print(f"An error occurred with GitLabOperations.reopen_issue: {e}")
            return {'success': False, 'error': str(e)}
