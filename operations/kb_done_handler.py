#!/usr/bin/env python3
"""
Knowledge Base Done Status Handler
Handles automated GitLab project creation when KB status changes to 'done'
"""

from typing import Optional, Dict, Any, List
from operations.knowledge_base_operations import KnowledgeBaseOperations
from operations.gitlab_operations import GitLabOperations

class KnowledgeBaseDoneHandler:
    """
    Handler for knowledge base completion workflow.
    Automatically creates GitLab projects when KB status is set to 'done'.
    """
    
    def __init__(self):
        self.kb_ops = KnowledgeBaseOperations()
        self.gitlab_ops = GitLabOperations()
    
    def handle_kb_done_status(self, kb_id: int, kb_name: str, kb_description: str) -> Dict[str, Any]:
        """
        Handle the workflow when a knowledge base is marked as 'done'.
        
        Args:
            kb_id: The knowledge base ID
            kb_name: The knowledge base name
            kb_description: The knowledge base description
            
        Returns:
            Dict containing the result of the GitLab project creation
        """
        try:
            print(f"🎉 Knowledge Base '{kb_name}' (ID: {kb_id}) marked as DONE")
            print(f"🚀 Initiating GitLab project creation workflow...")
            
            # Check if KB already has a GitLab project
            kb = self.kb_ops.get_knowledge_base_by_id(str(kb_id))
            if not kb:
                return {
                    "success": False,
                    "error": f"Knowledge Base {kb_id} not found"
                }
            
            if kb.gitlab_project_id:
                return {
                    "success": False,
                    "error": f"Knowledge Base already has GitLab project ID: {kb.gitlab_project_id}",
                    "project_id": kb.gitlab_project_id
                }
            
            # Generate GitLab project name (sanitized for GitLab)
            project_name = self._sanitize_project_name(kb_name)
            
            # Create description for GitLab project
            project_description = f"""# Knowledge Base Project: {kb_name}

**Status:** ✅ Knowledge Base Development Complete

## Description
{kb_description}

## Purpose
This GitLab project was automatically created when the knowledge base '{kb_name}' was marked as DONE. 

Use this project for:
- 📋 **Issue Tracking**: Manage ongoing maintenance, updates, and enhancements
- 🔄 **Change Management**: Track modifications and improvements to the knowledge base
- 👥 **Collaboration**: Coordinate team work on knowledge base evolution
- 📊 **Analytics**: Monitor usage, feedback, and performance metrics
- 🚀 **Deployment**: Manage knowledge base publication and distribution

## Knowledge Base Details
- **KB ID:** {kb_id}
- **Completion Date:** {self._get_current_timestamp()}
- **Content Status:** Ready for use and collaboration

## Next Steps
1. Review the completed knowledge base content
2. Set up maintenance schedules and update procedures  
3. Configure collaboration workflows for ongoing improvements
4. Establish feedback collection and analysis processes
"""

            # Create GitLab project for the completed knowledge base
            print(f"🏗️ Creating GitLab project: {project_name}")
            project = self.gitlab_ops.create_project_for_knowledge_base(
                kb_id=kb_id,
                name=project_name,
                description=project_description,
                visibility="public",  # Can be configurable
                initialize_with_readme=True
            )
            
            if project:
                project_id = project.get('id')
                project_url = project.get('web_url', f"Project ID: {project_id}")
                
                print(f"✅ GitLab project created successfully!")
                print(f"📋 Project ID: {project_id}")
                print(f"🔗 Project URL: {project_url}")
                
                # Create initial management issues for the completed KB
                try:
                    print(f"📝 Creating initial management issues...")
                    issues = self.gitlab_ops.create_kb_management_issues(str(project_id), kb_name)
                    print(f"✅ Created {len(issues)} management issues")
                except Exception as e:
                    print(f"⚠️ Warning: Failed to create management issues: {e}")
                
                return {
                    "success": True,
                    "project_id": project_id,
                    "project_url": project_url,
                    "project_name": project_name,
                    "knowledge_base_id": kb_id,
                    "knowledge_base_name": kb_name,
                    "message": f"GitLab project '{project_name}' created for completed knowledge base '{kb_name}'"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create GitLab project for knowledge base '{kb_name}'"
                }
                
        except Exception as e:
            print(f"❌ Error in KB done handler: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _sanitize_project_name(self, kb_name: str) -> str:
        """Sanitize knowledge base name for GitLab project naming requirements."""
        # GitLab project names should be lowercase, alphanumeric, with hyphens/underscores
        import re
        
        # Replace spaces and special chars with hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-_]', '', kb_name)
        sanitized = re.sub(r'\s+', '-', sanitized)
        sanitized = sanitized.lower().strip('-')
        
        # Ensure it starts with alphanumeric
        sanitized = re.sub(r'^[^a-zA-Z0-9]+', '', sanitized)
        
        # Add prefix to indicate it's a KB project
        if not sanitized.startswith('kb-'):
            sanitized = f"kb-{sanitized}"
        
        # Ensure maximum length (GitLab has limits)
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + "..."
        
        return sanitized or f"kb-project-{self._get_current_timestamp()}"
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d-%H%M%S")
    
    def check_and_handle_done_kbs(self) -> List[Dict[str, Any]]:
        """
        Check for knowledge bases marked as 'done' without GitLab projects
        and automatically create projects for them.
        
        Returns:
            List of results for each KB processed
        """
        try:
            print(f"🔍 Checking for completed knowledge bases without GitLab projects...")
            
            # Get all knowledge bases with 'done' status but no GitLab project
            # This would require a new query method - for now, get all KBs and filter
            all_kbs = self.kb_ops.get_knowledge_bases()
            done_kbs_without_gitlab = []
            
            for kb in all_kbs:
                if (hasattr(kb, 'status') and kb.status == 'done' and 
                    (not hasattr(kb, 'gitlab_project_id') or not kb.gitlab_project_id)):
                    done_kbs_without_gitlab.append(kb)
            
            if not done_kbs_without_gitlab:
                print(f"✅ No completed knowledge bases require GitLab project creation")
                return []
            
            print(f"📋 Found {len(done_kbs_without_gitlab)} completed KBs needing GitLab projects")
            
            results = []
            for kb in done_kbs_without_gitlab:
                print(f"\n🚀 Processing KB: {kb.name} (ID: {kb.id})")
                result = self.handle_kb_done_status(kb.id, kb.name, kb.description)
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ Error checking done KBs: {e}")
            return [{"success": False, "error": str(e)}]
