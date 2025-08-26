import os
from typing import List, Optional, Type, Dict, Any
from langchain_core.callbacks import  CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator
from models.article import Article
from models.knowledge_base import KnowledgeBase
from models.tags import Tags

from dotenv import load_dotenv
load_dotenv(override=True)

from operations.knowledge_base_operations import KnowledgeBaseOperations

kb_Operations=KnowledgeBaseOperations()

# Input schemas for tools
class KnowledgeBaseAnalyzeContentGapsInput(BaseModel):
    knowledge_base_id: str = Field(description="The knowledge base ID to analyze for content gaps")

class KnowledgeBaseTools():
    
    class KnowledgeBaseGetKnowledgeBases(BaseTool):
        name: str = "KnowledgeBaseGetKnowledgeBases"
        description: str = """
            useful for when you need to get all Knowledge Bases.
        """.strip()
        return_direct: bool = False

        def _run(self) -> str:
            print(f"🔧 TOOL: KnowledgeBaseGetKnowledgeBases CALLED")
            print(f"🔍 Retrieving all knowledge bases...")
            
            try:
                # Get knowledge bases with IDs and names
                knowledge_bases = kb_Operations.get_knowledge_bases_with_ids()
                
                print(f"📊 Found {len(knowledge_bases)} knowledge bases")
                
                if not knowledge_bases:
                    print(f"⚠️ No knowledge bases found")
                    return "No knowledge bases found."
                
                # Format the knowledge bases nicely
                lines = ["Available Knowledge Bases:", ""]
                for kb in knowledge_bases:
                    lines.append(f"• {kb['name']} (ID: {kb['id']})")
                    if kb['description']:
                        lines.append(f"  Description: {kb['description']}")
                    lines.append("")
                    print(f"📚 KB: {kb['name']} (ID: {kb['id']})")
                
                print(f"✅ SUCCESS: Retrieved {len(knowledge_bases)} knowledge bases")
                return "\n".join(lines).strip()
                    
            except Exception as e:
                print(f"💥 ERROR in KnowledgeBaseGetKnowledgeBases: {str(e)}")
                import traceback
                print(f"🔍 Traceback: {traceback.format_exc()}")
                return f"Error retrieving knowledge bases: {e}"

    class KnowledgeBaseSetContext(BaseTool):
        name: str = "KnowledgeBaseSetContext"
        description: str = """
            useful for when you need to set the current knowledge base context.
            This establishes which knowledge base should be used for subsequent operations.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSetContextInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id to set as current context")

            @field_validator("knowledge_base_id")
            def validate_knowledge_base_id(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseSetContext error: knowledge_base_id parameter is empty")
                return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSetContextInputModel
    
        def _run(self, knowledge_base_id: str) -> Dict[str, Any]:
            print(f"🔧 TOOL: KnowledgeBaseSetContext CALLED")
            print(f"📊 KB ID: {knowledge_base_id}")
            print(f"🔍 Validating knowledge base exists...")
            
            # Validate that the knowledge base exists
            kb = kb_Operations.get_knowledge_base_by_id(knowledge_base_id)
            if not kb:
                print(f"❌ FAILED: Knowledge base with ID {knowledge_base_id} not found")
                return {
                    "success": False,
                    "error": f"Knowledge base with ID {knowledge_base_id} not found"
                }
            
            print(f"✅ KB Found: {kb.name}")
            print(f"📄 Description: {kb.description}")
            print(f"🔗 GitLab Project: {kb.gitlab_project_id}")
            
            # Prepare context information including GitLab project
            context_info = {
                "success": True,
                "knowledge_base_id": knowledge_base_id,
                "knowledge_base_name": kb.name,
                "knowledge_base_description": kb.description,
                "gitlab_project_id": kb.gitlab_project_id,
                "message": f"Knowledge base context set to: {kb.name} (ID: {knowledge_base_id})"
            }
            
            # Add GitLab project information if available
            if kb.gitlab_project_id:
                context_info["gitlab_project_context"] = {
                    "project_id": kb.gitlab_project_id,
                    "message": f"GitLab project context: Project ID {kb.gitlab_project_id}",
                    "workflow_note": f"Agents should check for issues in GitLab project {kb.gitlab_project_id} for work related to this knowledge base."
                }
                context_info["message"] += f" | GitLab Project: {kb.gitlab_project_id}"
            else:
                context_info["gitlab_project_context"] = {
                    "project_id": None,
                    "message": "No GitLab project associated with this knowledge base",
                    "workflow_note": "Consider creating a GitLab project for this knowledge base to enable agent collaboration."
                }
            
            return context_info

    class KnowledgeBaseSetContextByGitLabProject(BaseTool):
        name: str = "KnowledgeBaseSetContextByGitLabProject"
        description: str = """
            useful for when you need to set the knowledge base context based on a GitLab project ID.
            This allows agents to establish KB context when they know the GitLab project they're working in.
            Perfect for agents discovering work in GitLab and needing to set the corresponding KB context.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSetContextByGitLabProjectInputModel(BaseModel):
            gitlab_project_id: str = Field(description="GitLab project ID to find associated knowledge base")

            @field_validator("gitlab_project_id")
            def validate_gitlab_project_id(cls, gitlab_project_id):
                if not gitlab_project_id:
                    raise ValueError("KnowledgeBaseSetContextByGitLabProject error: gitlab_project_id parameter is empty")
                return gitlab_project_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSetContextByGitLabProjectInputModel
    
        def _run(self, gitlab_project_id: str) -> Dict[str, Any]:
            try:
                print(f"🔧 TOOL: KnowledgeBaseSetContextByGitLabProject CALLED")
                print(f"📝 Parameters:")
                print(f"   - GitLab Project ID: {gitlab_project_id}")
                
                print(f"🔄 Converting project ID to integer...")
                # Convert to int since DB expects integer
                project_id_int = int(gitlab_project_id)
                
                print(f"🔍 Finding knowledge base for GitLab project {project_id_int}...")
            except ValueError:
                error_result = {
                    "success": False,
                    "error": f"Invalid GitLab project ID: {gitlab_project_id}. Must be a valid integer."
                }
                print(f"❌ KnowledgeBaseSetContextByGitLabProject failed: Invalid project ID format")
                return error_result
            
            try:
                # Find knowledge base by GitLab project ID
                kb = kb_Operations.get_knowledge_base_by_gitlab_project_id(project_id_int)
                if not kb:
                    error_result = {
                        "success": False,
                        "error": f"No knowledge base found for GitLab project ID {gitlab_project_id}",
                        "suggestion": "Consider creating a knowledge base for this GitLab project or linking an existing one."
                    }
                    print(f"❌ KnowledgeBaseSetContextByGitLabProject failed: No KB found for project {gitlab_project_id}")
                    return error_result
                
                print(f"✅ Found KB: {kb.name} (ID: {kb.id})")
                
                # Prepare context information
                context_info = {
                    "success": True,
                    "knowledge_base_id": str(kb.id),
                    "knowledge_base_name": kb.name,
                    "knowledge_base_description": kb.description,
                    "gitlab_project_id": kb.gitlab_project_id,
                    "message": f"Knowledge base context set via GitLab project: {kb.name} (KB ID: {kb.id}, GitLab Project: {gitlab_project_id})",
                    "gitlab_project_context": {
                        "project_id": kb.gitlab_project_id,
                        "message": f"Working in GitLab project {gitlab_project_id} for knowledge base '{kb.name}'",
                        "workflow_note": f"Agents should focus on GitLab project {gitlab_project_id} issues for this knowledge base."
                    }
                }
                
                print(f"✅ KnowledgeBaseSetContextByGitLabProject completed successfully")
                return context_info
                
            except Exception as e:
                error_msg = f"❌ KnowledgeBaseSetContextByGitLabProject failed: {str(e)}"
                print(error_msg)
                print(f"🔍 Full error traceback:")
                import traceback
                traceback.print_exc()
                return {
                    "success": False,
                    "error": error_msg
                }

    class KnowledgeBaseGetCurrentContext(BaseTool):
        name: str = "KnowledgeBaseGetCurrentContext"
        description: str = """
            useful for when you need to get the current knowledge base context and details.
            This returns information about which knowledge base is currently active, including its name, 
            description, GitLab project association, and other relevant context details.
            Use this when you're unsure which KB you're working with or need complete KB details.
        """.strip()
        return_direct: bool = False

        def _run(self) -> Dict[str, Any]:
            print(f"🔧 TOOL: KnowledgeBaseGetCurrentContext CALLED")
            print(f"🔍 Checking current knowledge base context...")
            
            try:
                # Try to get current session context
                try:
                    from agents.postgresql_state_manager import PostgreSQLStateManager
                    state_manager = PostgreSQLStateManager()
                    session_context = state_manager.get_session_context()
                    
                    if session_context and session_context.knowledge_base_id:
                        current_kb_id = session_context.knowledge_base_id
                        print(f"📊 Found current KB ID from session: {current_kb_id}")
                    else:
                        print(f"⚠️ No KB context in session, checking environment default")
                        current_kb_id = os.getenv('DEFAULT_KNOWLEDGE_BASE_ID')
                        if current_kb_id:
                            print(f"📊 Using default KB ID from environment: {current_kb_id}")
                        else:
                            print(f"❌ No current KB context found")
                            return {
                                "success": False,
                                "error": "No current knowledge base context found. Use KnowledgeBaseSetContext to establish context.",
                                "suggestion": "Call KnowledgeBaseGetKnowledgeBases to see available options, then use KnowledgeBaseSetContext with a knowledge_base_id."
                            }
                            
                except Exception as session_error:
                    print(f"⚠️ Could not access session context: {session_error}")
                    print(f"🔄 Falling back to environment default")
                    current_kb_id = os.getenv('DEFAULT_KNOWLEDGE_BASE_ID')
                    if not current_kb_id:
                        return {
                            "success": False,
                            "error": "No current knowledge base context available and no default configured.",
                            "suggestion": "Set DEFAULT_KNOWLEDGE_BASE_ID in environment or use KnowledgeBaseSetContext to establish context."
                        }
                
                # Get the knowledge base details
                kb = kb_Operations.get_knowledge_base_by_id(current_kb_id)
                if not kb:
                    print(f"❌ KB ID {current_kb_id} not found in database")
                    return {
                        "success": False,
                        "error": f"Knowledge base with ID {current_kb_id} not found",
                        "current_kb_id": current_kb_id,
                        "suggestion": "Use KnowledgeBaseGetKnowledgeBases to see available options."
                    }
                
                print(f"✅ Found current KB: {kb.name}")
                
                # Get additional statistics
                try:
                    # Get article count
                    articles = kb_Operations.get_articles_by_knowledge_base_id(current_kb_id)
                    article_count = len(articles) if articles else 0
                    
                    # Get tag count
                    tags = kb_Operations.get_tags_by_knowledge_base_id(current_kb_id)
                    tag_count = len(tags) if tags else 0
                    
                    print(f"📊 KB Stats: {article_count} articles, {tag_count} tags")
                    
                except Exception as stats_error:
                    print(f"⚠️ Could not get KB statistics: {stats_error}")
                    article_count = "Unknown"
                    tag_count = "Unknown"
                
                # Prepare comprehensive context information
                context_info = {
                    "success": True,
                    "knowledge_base_id": current_kb_id,
                    "knowledge_base_name": kb.name,
                    "description": kb.description,
                    "author_id": str(kb.author_id) if hasattr(kb, 'author_id') and kb.author_id else "Unknown",
                    "is_active": getattr(kb, 'is_active', True),
                    "status": getattr(kb, 'status', 'active'),
                    "gitlab_project_id": kb.gitlab_project_id,
                    "article_count": article_count,
                    "tag_count": tag_count,
                    "created_at": getattr(kb, 'created_at', 'Unknown'),
                    "message": f"Currently working with: {kb.name} (ID: {current_kb_id})"
                }
                
                # Add GitLab project information if available
                if kb.gitlab_project_id:
                    context_info["gitlab_project_context"] = {
                        "project_id": kb.gitlab_project_id,
                        "message": f"Associated with GitLab project {kb.gitlab_project_id}",
                        "workflow_note": f"This KB is linked to GitLab project {kb.gitlab_project_id}. Check that project for related issues and work items."
                    }
                else:
                    context_info["gitlab_project_context"] = {
                        "project_id": None,
                        "message": "No GitLab project associated",
                        "workflow_note": "Consider creating a GitLab project for this KB using KnowledgeBaseCreateGitLabProject tool."
                    }
                
                print(f"✅ SUCCESS: Retrieved complete context for KB {current_kb_id}")
                return context_info
                
            except Exception as e:
                error_msg = f"❌ KnowledgeBaseGetCurrentContext failed: {str(e)}"
                print(error_msg)
                print(f"🔍 Full error traceback:")
                import traceback
                traceback.print_exc()
                return {
                    "success": False,
                    "error": error_msg
                }

    class KnowledgeBaseSetArticleContext(BaseTool):
        name: str = "KnowledgeBaseSetArticleContext"
        description: str = """
            useful for when you need to set focus on a specific article within the knowledge base.
            This establishes which article should be the current working context for detailed operations.
            Use this when user says things like "work on article 1", "focus on category 1", "main article 1", etc.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSetArticleContextInputModel(BaseModel):
            article_id: str = Field(description="article_id to set as current context")
            knowledge_base_id: str = Field(description="knowledge_base_id containing the article")

            @field_validator("article_id")
            def validate_article_id(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseSetArticleContext error: article_id parameter is empty")
                return article_id

            @field_validator("knowledge_base_id")
            def validate_knowledge_base_id(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseSetArticleContext error: knowledge_base_id parameter is empty")
                return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSetArticleContextInputModel
    
        def _run(self, knowledge_base_id: str, article_id: str) -> Dict[str, Any]:
            # Validate that the article exists
            article = kb_Operations.get_article_by_id(knowledge_base_id, article_id)
            if not article:
                return {
                    "success": False,
                    "error": f"Article with ID {article_id} not found in knowledge base {knowledge_base_id}"
                }
            
            return {
                "success": True,
                "knowledge_base_id": knowledge_base_id,
                "article_id": article_id,
                "article_title": article.title,
                "message": f"Article context set to: {article.title} (ID: {article_id})"
            }
        
    class KnowledgeBaseInsertKnowledgeBase(BaseTool):
        name: str = "KnowledgeBaseInsertKnowledgeBase"
        description: str = """
            Create a new Knowledge Base in the database.
            This tool will:
            1. Create the knowledge base in the database
            2. Set initial status (to_do, in_progress, or done)
            
            **NEW WORKFLOW**: GitLab projects are now created automatically when 
            a KB status is set to 'done' (not during initial creation).
            
            This allows for:
            - Faster KB creation without GitLab overhead
            - GitLab integration only when work is completed
            - Cleaner development workflow
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseInsertKnowledgeBaseInputModel(BaseModel):
            name: str = Field(description="Name/title of the knowledge base")
            description: str = Field(description="Description of the knowledge base content and purpose")
            author_id: int = Field(default=1, description="ID of the author (user) - defaults to 1")
            create_gitlab_project: bool = Field(default=False, description="Whether to automatically create a GitLab project (default: False - GitLab projects are now created when status is set to 'done')")
            gitlab_project_name: Optional[str] = Field(default=None, description="Custom GitLab project name (auto-generated if not provided)")
            status: str = Field(default="to_do", description="Initial workflow status: to_do (ready to start), in_progress (actively working), done (completed)")

            # Validation method to check parameter input from agent
            @field_validator("name")
            def validate_name_param(cls, name):
                if not name or not name.strip():
                    raise ValueError("KnowledgeBaseInsertKnowledgeBase error: name parameter is empty")
                return name.strip()

            @field_validator("status")
            def validate_status_param(cls, status):
                valid_statuses = ["to_do", "in_progress", "done"]
                if status not in valid_statuses:
                    raise ValueError(f"KnowledgeBaseInsertKnowledgeBase error: status must be one of {valid_statuses}")
                return status
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseInsertKnowledgeBaseInputModel
    
        def _run(self, name: str, description: str, author_id: int = 1, create_gitlab_project: bool = True, gitlab_project_name: Optional[str] = None, status: str = "to_do") -> str:
            try:
                print(f"🔧 TOOL: KnowledgeBaseInsertKnowledgeBase CALLED")
                print(f"📝 Parameters:")
                print(f"   - Name: {name}")
                print(f"   - Description: {description[:100]}{'...' if len(description) > 100 else ''}")
                print(f"   - Author ID: {author_id}")
                print(f"   - Create GitLab Project: {create_gitlab_project}")
                print(f"   - GitLab Project Name: {gitlab_project_name or 'auto-generated'}")
                print(f"   - Status: {status}")
                
                print(f"🏗️ Creating knowledge base...")
                # Create the knowledge base insert model
                from models.knowledge_base import KnowledgeBase
                knowledge_base = KnowledgeBase.InsertModel(
                    name=name,
                    description=description,
                    author_id=author_id,
                    status=status
                )
                
                # Step 1: Create the knowledge base
                print(f"📚 Inserting knowledge base into database...")
                kb_id = kb_Operations.insert_knowledge_base(knowledge_base)
                if not kb_id:
                    error_msg = "❌ Failed to create knowledge base. Please check the database connection and try again."
                    print(error_msg)
                    return error_msg
                
                print(f"✅ Knowledge base created with ID: {kb_id}")
                
                result = f"✅ **Knowledge Base Created Successfully!**\n\n"
                result += f"📚 **KB ID:** {kb_id}\n"
                result += f"📝 **Name:** {knowledge_base.name}\n"
                result += f"📄 **Description:** {knowledge_base.description}\n"
                result += f"📊 **Status:** {knowledge_base.status}\n\n"
                
                # Step 2: Handle GitLab project creation based on new workflow
                if create_gitlab_project:
                    print(f"🦊 Legacy GitLab project creation requested...")
                    result += f"⚠️ **GitLab Project Creation Override**\n"
                    result += f"   GitLab project creation during KB creation is deprecated.\n"
                    result += f"   **NEW WORKFLOW:** GitLab projects are now created automatically\n"
                    result += f"   when KB status is set to 'done'.\n\n"
                    result += f"💡 **To create GitLab project now:**\n"
                    result += f"   1. Use KnowledgeBaseUpdateStatus to set status to 'done'\n"
                    result += f"   2. GitLab project will be created automatically\n"
                    result += f"   3. Or use KnowledgeBaseCreateGitLabProject tool manually\n\n"
                elif knowledge_base.status == "done":
                    # If KB is created with status 'done', automatically create GitLab project
                    print(f"🦊 Auto-creating GitLab project for 'done' status KB...")
                    try:
                        # Import GitLab operations
                        from operations.gitlab_operations import GitLabOperations
                        gitlab_ops = GitLabOperations()
                        
                        # Generate project name if not provided
                        if not gitlab_project_name:
                            # Convert KB name to a valid project name
                            gitlab_project_name = knowledge_base.name.lower().replace(' ', '-').replace(':', '').replace('?', '').replace('!', '').replace('.', '').replace(',', '').replace('"', '').replace("'", '').replace('(', '').replace(')', '')
                            # Truncate if too long and ensure it's valid
                            gitlab_project_name = gitlab_project_name[:50].strip('-')
                            print(f"   Generated project name: {gitlab_project_name}")
                        
                        print(f"   Creating GitLab project: {gitlab_project_name}")
                        # Create GitLab project linked to KB
                        project = gitlab_ops.create_project_for_knowledge_base(
                            kb_id=kb_id,
                            name=gitlab_project_name,
                            description=f"Project management for {knowledge_base.name} knowledge base",
                            visibility="public"
                        )
                        
                        if project and project.get('id'):
                            print(f"   ✅ GitLab project created: ID {project['id']}")
                            result += f"🦊 **GitLab Project Created & Linked!**\n"
                            result += f"🆔 **Project ID:** {project['id']}\n"
                            result += f"📁 **Project Name:** {project['name']}\n"
                            result += f"🔗 **Project URL:** {project.get('web_url', 'Not available')}\n"
                            result += f"👁️ **Visibility:** {project.get('visibility', 'Unknown')}\n\n"
                            
                            # Step 3: Create KB management issues
                            print(f"   📋 Creating KB management issues...")
                            try:
                                issues = gitlab_ops.create_kb_management_issues(project['id'], knowledge_base.name)
                                if issues:
                                    print(f"   ✅ Created {len(issues)} management issues")
                                    result += f"📋 **KB Management Issues Created:** {len(issues)} issues\n"
                                    result += f"   Ready for project management and workflow tracking!\n\n"
                                else:
                                    print(f"   ⚠️ Issues creation returned empty result")
                                    result += f"⚠️ **Note:** GitLab project created but issues creation failed.\n"
                                    result += f"   You can manually create issues in the GitLab project.\n\n"
                            except Exception as e:
                                print(f"   ⚠️ Issues creation failed: {str(e)}")
                                result += f"⚠️ **Issues Creation Warning:** {str(e)}\n"
                                result += f"   GitLab project is ready, but you may need to create issues manually.\n\n"
                        else:
                            print(f"   ❌ GitLab project creation failed")
                            result += f"⚠️ **GitLab Project Creation Failed**\n"
                            result += f"   Knowledge base created successfully, but GitLab integration failed.\n"
                            result += f"   **Next Steps:**\n"
                            result += f"   1. Check GitLab server connection (should be at {gitlab_ops.gitlab_url})\n"
                            result += f"   2. Verify GitLab token permissions\n"
                            result += f"   3. Manually create project or use: GitLabCreateProjectForKBTool\n\n"
                    
                    except ImportError as e:
                        print(f"   ❌ GitLab integration unavailable: {str(e)}")
                        result += f"❌ **Critical Error: GitLab Integration Unavailable**\n"
                        result += f"   Missing dependency: {str(e)}\n"
                        result += f"   **REQUIRED:** GitLab project creation is critical for workflow!\n"
                        result += f"   **Fix:** Run 'pip install python-gitlab==4.13.0'\n"
                        result += f"   Knowledge base created but will not function properly without GitLab project.\n\n"
                    except Exception as e:
                        print(f"   ❌ GitLab project creation failed: {str(e)}")
                        result += f"❌ **Critical Error: GitLab Project Creation Failed**\n"
                        result += f"   Error: {str(e)}\n"
                        result += f"   **REQUIRED:** GitLab project is critical for agent workflow!\n"
                        result += f"   **Troubleshooting:**\n"
                        result += f"   1. Check GitLab server: {gitlab_ops.gitlab_url if 'gitlab_ops' in locals() else 'http://localhost:8929'}\n"
                        result += f"   2. Verify GITLAB_PAT environment variable\n"
                        result += f"   3. Ensure token has 'api' and 'write_repository' scopes\n"
                        result += f"   4. Check if GitLab user has project creation permissions\n"
                        result += f"   **Manual Fix:** Create GitLab project manually and link to KB ID {kb_id}\n\n"
                else:
                    print(f"📋 Using new workflow - GitLab project will be created when status is set to 'done'")
                    result += f"📋 **New Workflow Active**\n"
                    result += f"   Knowledge base created successfully without GitLab project.\n"
                    result += f"   **GitLab project will be created automatically when status is set to 'done'.**\n\n"
                    result += f"💡 **To create GitLab project:**\n"
                    result += f"   1. Complete your KB development work\n"
                    result += f"   2. Use KnowledgeBaseUpdateStatus to set status to 'done'\n"
                    result += f"   3. GitLab project will be created automatically\n\n"
                
                result += f"🎯 **Next Steps:**\n"
                result += f"   1. Use KnowledgeBaseSetContext with KB ID {kb_id}\n"
                result += f"   2. Start adding articles with KnowledgeBaseInsertArticle\n"
                result += f"   3. When ready, set status to 'done' for GitLab integration\n"
                result += f"   4. Use KnowledgeBaseUpdateStatus tool for status changes\n"
                
                print(f"✅ KnowledgeBaseInsertKnowledgeBase completed successfully")
                return result
                
            except Exception as e:
                error_msg = f"❌ **Knowledge Base Creation Failed:** {str(e)}\n\nPlease check your input parameters and database connection."
                print(f"❌ KnowledgeBaseInsertKnowledgeBase failed: {str(e)}")
                print(f"🔍 Full error traceback:")
                import traceback
                traceback.print_exc()
                return error_msg
    
    class KnowledgeBaseCreateGitLabProject(BaseTool):
        name: str = "KnowledgeBaseCreateGitLabProject"
        description: str = """
            Create a GitLab project for an existing Knowledge Base.
            Use this tool when automatic GitLab project creation failed during KB creation,
            or when you want to add GitLab integration to an existing KB.
            
            This tool will:
            1. Create a GitLab project
            2. Link it to the specified knowledge base
            3. Set up KB management issues
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseCreateGitLabProjectInputModel(BaseModel):
            knowledge_base_id: str = Field(description="ID of the existing knowledge base")
            gitlab_project_name: Optional[str] = Field(default=None, description="Custom GitLab project name (auto-generated if not provided)")
            description: Optional[str] = Field(default=None, description="Custom project description")
            visibility: str = Field(default="public", description="Project visibility: private, internal, or public")

            @field_validator("knowledge_base_id")
            def validate_kb_id(cls, v):
                if not v:
                    raise ValueError("KnowledgeBaseCreateGitLabProject error: knowledge_base_id parameter is empty")
                return v
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseCreateGitLabProjectInputModel
    
        def _run(self, knowledge_base_id: str, gitlab_project_name: Optional[str] = None, description: Optional[str] = None, visibility: str = "public") -> str:
            try:
                # Step 1: Verify the knowledge base exists
                kb = kb_Operations.get_knowledge_base_by_id(knowledge_base_id)
                if not kb:
                    return f"❌ **Knowledge Base Not Found:** No knowledge base found with ID {knowledge_base_id}.\n\nPlease check the KB ID and try again."
                
                # Check if KB already has a GitLab project
                if kb.gitlab_project_id:
                    return f"⚠️ **GitLab Project Already Exists:** Knowledge Base '{kb.name}' (ID: {knowledge_base_id}) is already linked to GitLab project ID {kb.gitlab_project_id}.\n\nUse GitLabGetProjectDetailsTool to view project details or GitLabCreateKBManagementIssuesTool to add issues."
                
                result = f"🔧 **Creating GitLab Project for Knowledge Base...**\n\n"
                result += f"📚 **KB:** {kb.name} (ID: {knowledge_base_id})\n\n"
                
                # Step 2: Create GitLab project
                try:
                    from operations.gitlab_operations import GitLabOperations
                    gitlab_ops = GitLabOperations()
                    
                    # Generate project name if not provided
                    if not gitlab_project_name:
                        gitlab_project_name = kb.name.lower().replace(' ', '-').replace(':', '').replace('?', '').replace('!', '').replace('.', '').replace(',', '').replace('"', '').replace("'", '').replace('(', '').replace(')', '')
                        gitlab_project_name = gitlab_project_name[:50].strip('-')
                    
                    # Generate description if not provided
                    if not description:
                        description = f"Project management for {kb.name} knowledge base"
                    
                    # Create GitLab project linked to KB
                    project = gitlab_ops.create_project_for_knowledge_base(
                        kb_id=int(knowledge_base_id),
                        name=gitlab_project_name,
                        description=description,
                        visibility=visibility
                    )
                    
                    if project:
                        result += f"✅ **GitLab Project Created & Linked!**\n"
                        result += f"🆔 **Project ID:** {project['id']}\n"
                        result += f"📁 **Project Name:** {project['name']}\n"
                        result += f"🔗 **Project URL:** {project.get('web_url', 'Not available')}\n"
                        result += f"👁️ **Visibility:** {project.get('visibility', 'Unknown')}\n\n"
                        
                        # Step 3: Create KB management issues
                        try:
                            issues = gitlab_ops.create_kb_management_issues(project['id'], kb.name)
                            if issues:
                                result += f"📋 **KB Management Issues Created:** {len(issues)} issues\n"
                                for issue in issues:
                                    result += f"   • Issue #{issue.get('iid', 'N/A')}: {issue.get('title', 'No title')}\n"
                                result += f"\n🎯 **Project is ready for KB development workflow!**\n"
                            else:
                                result += f"⚠️ **Issues Creation Failed:** Could not create management issues.\n"
                                result += f"   You can manually create issues in the GitLab project.\n"
                        except Exception as e:
                            result += f"⚠️ **Issues Creation Error:** {str(e)}\n"
                            result += f"   GitLab project created successfully, but issues need manual creation.\n"
                    else:
                        result += f"❌ **GitLab Project Creation Failed**\n"
                        result += f"   **Troubleshooting Steps:**\n"
                        result += f"   1. Check GitLab server connection (should be at {gitlab_ops.gitlab_url})\n"
                        result += f"   2. Verify GitLab token permissions (GITLAB_PAT environment variable)\n"
                        result += f"   3. Ensure project name '{gitlab_project_name}' doesn't already exist\n"
                        result += f"   4. Check GitLab server has sufficient storage/project limits\n"
                        
                except ImportError:
                    result += f"❌ **GitLab Integration Unavailable:** GitLab operations not available.\n"
                    result += f"   Install GitLab dependencies to enable project creation.\n"
                except Exception as e:
                    result += f"❌ **GitLab Integration Error:** {str(e)}\n"
                    result += f"   **Common Solutions:**\n"
                    result += f"   - Verify GitLab server is running and accessible\n"
                    result += f"   - Check GITLAB_PAT environment variable is set correctly\n"
                    result += f"   - Ensure GitLab token has 'api' and 'write_repository' scopes\n"
                    result += f"   - Try a different project name if there's a naming conflict\n"
                
                return result
                
            except Exception as e:
                return f"❌ **Error:** {str(e)}\n\nPlease check the knowledge base ID and try again."

    # KonowledgeBase Update KnowledgeBase
    class KnowledgeBaseUpdateKnowledgeBase(BaseTool):
        name: str = "KnowledgeBaseUpdateKnowledgeBase"
        description: str = """
            useful for when you need to update a Knowledge Base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseUpdateKnowledgeBaseInputModel(BaseModel):
            id: int = Field(description="ID of the knowledge base to update")
            name: str = Field(description="New name/title of the knowledge base")
            description: str = Field(description="New description of the knowledge base")
            author_id: int = Field(description="ID of the author (user)")
            is_active: bool = Field(default=True, description="Whether the knowledge base is active")
            gitlab_project_id: Optional[int] = Field(default=None, description="GitLab project ID")
            status: str = Field(description="Workflow status: to_do (ready to start), in_progress (actively working), done (completed)")

            # Validation method to check parameter input from agent
            @field_validator("id")
            def validate_id_param(cls, id_val):
                if not id_val or id_val <= 0:
                    raise ValueError("KnowledgeBaseUpdateKnowledgeBase error: id parameter must be a positive integer")
                return id_val

            @field_validator("status")
            def validate_status_param(cls, status):
                valid_statuses = ["to_do", "in_progress", "done"]
                if status not in valid_statuses:
                    raise ValueError(f"KnowledgeBaseUpdateKnowledgeBase error: status must be one of {valid_statuses}")
                return status
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseUpdateKnowledgeBaseInputModel
    
        def _run(self, id: int, name: str, description: str, author_id: int, is_active: bool = True, gitlab_project_id: Optional[int] = None, status: str = "to_do") -> KnowledgeBase.BaseModel:
            try:
                # Create the knowledge base update model
                from models.knowledge_base import KnowledgeBase
                knowledge_base = KnowledgeBase.UpdateModel(
                    id=id,
                    name=name,
                    description=description,
                    author_id=author_id,
                    is_active=is_active,
                    gitlab_project_id=gitlab_project_id,
                    status=status
                )
                
                # Update the knowledge base
                return kb_Operations.update_knowledge_base(knowledge_base)
            except Exception as e:
                raise Exception(f"Failed to update knowledge base: {str(e)}")

    class KnowledgeBaseUpdateStatus(BaseTool):
        name: str = "KnowledgeBaseUpdateStatus"
        description: str = """
            Update only the workflow status of a knowledge base.
            Use this tool for status transitions in the workflow: to_do -> in_progress -> done.
            Perfect for tracking progress without changing other KB details.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseUpdateStatusInputModel(BaseModel):
            knowledge_base_id: str = Field(description="ID of the knowledge base to update")
            status: str = Field(description="New workflow status: to_do (ready to start), in_progress (actively working), done (completed)")

            @field_validator("knowledge_base_id")
            def validate_kb_id(cls, kb_id):
                if not kb_id or not kb_id.strip():
                    raise ValueError("KnowledgeBaseUpdateStatus error: knowledge_base_id parameter is empty")
                return kb_id.strip()

            @field_validator("status")
            def validate_status_param(cls, status):
                valid_statuses = ["to_do", "in_progress", "done"]
                if status not in valid_statuses:
                    raise ValueError(f"KnowledgeBaseUpdateStatus error: status must be one of {valid_statuses}")
                return status
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseUpdateStatusInputModel
    
        def _run(self, knowledge_base_id: str, status: str) -> str:
            try:
                print(f"🔧 TOOL: KnowledgeBaseUpdateStatus CALLED")
                print(f"📝 Parameters:")
                print(f"   - KB ID: {knowledge_base_id}")
                print(f"   - New Status: {status}")
                
                # Get the current knowledge base to preserve other fields
                kb = kb_Operations.get_knowledge_base_by_id(knowledge_base_id)
                if not kb:
                    error_msg = f"❌ Knowledge Base with ID {knowledge_base_id} not found"
                    print(error_msg)
                    return error_msg
                
                print(f"📚 Current KB: {kb.name}")
                print(f"🔄 Status change: {getattr(kb, 'status', 'unknown')} → {status}")
                
                # Create update model with current values but new status
                from models.knowledge_base import KnowledgeBase
                knowledge_base = KnowledgeBase.UpdateModel(
                    id=int(knowledge_base_id),
                    name=kb.name,
                    description=kb.description,
                    author_id=kb.author_id,
                    is_active=kb.is_active,
                    gitlab_project_id=kb.gitlab_project_id,
                    status=status
                )
                
                # Update the knowledge base
                updated_kb = kb_Operations.update_knowledge_base(knowledge_base)
                if updated_kb:
                    result = f"✅ **Status Updated Successfully!**\n\n"
                    result += f"📚 **KB:** {updated_kb.name} (ID: {knowledge_base_id})\n"
                    result += f"📊 **New Status:** {status}\n"
                    result += f"📅 **Updated:** {getattr(updated_kb, 'updated_at', 'now')}\n\n"
                    
                    # AUTOMATIC GITLAB PROJECT CREATION FOR 'DONE' STATUS
                    if status == "done" and not updated_kb.gitlab_project_id:
                        print(f"🦊 Auto-creating GitLab project for completed KB...")
                        result += f"🦊 **GitLab Project Auto-Creation**\n"
                        result += f"   Creating GitLab project for completed knowledge base...\n\n"
                        
                        try:
                            # Import GitLab operations
                            from operations.gitlab_operations import GitLabOperations
                            gitlab_ops = GitLabOperations()
                            
                            # Generate project name from KB name
                            gitlab_project_name = updated_kb.name.lower().replace(' ', '-').replace(':', '').replace('?', '').replace('!', '').replace('.', '').replace(',', '').replace('"', '').replace("'", '').replace('(', '').replace(')', '')
                            gitlab_project_name = gitlab_project_name[:50].strip('-')
                            print(f"   Generated project name: {gitlab_project_name}")
                            
                            # Create GitLab project linked to KB
                            project = gitlab_ops.create_project_for_knowledge_base(
                                kb_id=int(knowledge_base_id),
                                name=gitlab_project_name,
                                description=f"Project management and collaboration for completed knowledge base: {updated_kb.name}",
                                visibility="public"
                            )
                            
                            if project and project.get('id'):
                                print(f"   ✅ GitLab project created: ID {project['id']}")
                                result += f"✅ **GitLab Project Created!**\n"
                                result += f"🆔 **Project ID:** {project['id']}\n"
                                result += f"📁 **Project Name:** {project['name']}\n"
                                result += f"🔗 **Project URL:** {project.get('web_url', 'Not available')}\n\n"
                                
                                # Create KB management issues for the completed KB
                                try:
                                    issues = gitlab_ops.create_kb_management_issues(project['id'], updated_kb.name)
                                    if issues:
                                        result += f"📋 **Management Issues Created:** {len(issues)} issues for collaboration\n"
                                        result += f"   Ready for ongoing maintenance and collaboration!\n\n"
                                    else:
                                        result += f"⚠️ **Issues Creation:** GitLab project created but issues need manual setup\n\n"
                                except Exception as e:
                                    result += f"⚠️ **Issues Warning:** {str(e)[:100]}...\n"
                                    result += f"   GitLab project created successfully, manually create issues if needed.\n\n"
                            else:
                                print(f"   ❌ GitLab project creation failed")
                                result += f"❌ **GitLab Creation Failed**\n"
                                result += f"   Status updated successfully, but GitLab project creation failed.\n"
                                result += f"   **Manual Fix:** Use KnowledgeBaseCreateGitLabProject tool\n\n"
                        
                        except ImportError:
                            result += f"⚠️ **GitLab Integration Unavailable**\n"
                            result += f"   Status updated, but GitLab dependencies missing.\n"
                            result += f"   Install python-gitlab to enable automatic project creation.\n\n"
                        except Exception as e:
                            result += f"⚠️ **GitLab Creation Error:** {str(e)[:100]}...\n"
                            result += f"   Status updated successfully, GitLab project creation failed.\n"
                            result += f"   Use KnowledgeBaseCreateGitLabProject tool manually.\n\n"
                    
                    elif status == "done" and updated_kb.gitlab_project_id:
                        result += f"🔗 **GitLab Project:** Already linked to project ID {updated_kb.gitlab_project_id}\n"
                        result += f"   Completed KB is ready for collaboration!\n\n"
                    
                    # Add workflow guidance
                    if status == "to_do":
                        result += f"🎯 **Next:** Ready to start work on this knowledge base\n"
                    elif status == "in_progress":
                        result += f"🚀 **Active:** Knowledge base is now being actively worked on\n"
                    elif status == "done":
                        result += f"🎉 **Complete:** Knowledge base work has been completed\n"
                        result += f"💼 **Collaboration:** GitLab project enables ongoing maintenance\n"
                        
                    print(f"✅ KnowledgeBaseUpdateStatus completed successfully")
                    return result
                else:
                    error_msg = f"❌ Failed to update knowledge base status"
                    print(error_msg)
                    return error_msg
                    
            except Exception as e:
                error_msg = f"❌ **Status Update Failed:** {str(e)}"
                print(f"❌ KnowledgeBaseUpdateStatus failed: {str(e)}")
                return error_msg

    class KnowledgeBaseHandleDoneStatus(BaseTool):
        name: str = "KnowledgeBaseHandleDoneStatus"
        description: str = """
            Handle the completion workflow when a knowledge base is marked as 'done'.
            This tool automatically creates a GitLab project for completed knowledge bases,
            enabling collaboration, issue tracking, and ongoing maintenance.
            
            Use this tool when:
            - A knowledge base has been completed (status = 'done')
            - You want to create a GitLab project for a finished KB
            - Setting up collaboration infrastructure for a completed knowledge base
            
            The tool will:
            1. Verify the KB is marked as 'done'
            2. Create a GitLab project with appropriate description
            3. Link the project to the knowledge base
            4. Set up initial management issues for ongoing work
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseHandleDoneStatusInputModel(BaseModel):
            knowledge_base_id: str = Field(description="ID of the knowledge base marked as done")

            @field_validator("knowledge_base_id")
            def validate_kb_id(cls, kb_id):
                if not kb_id or not kb_id.strip():
                    raise ValueError("KnowledgeBaseHandleDoneStatus error: knowledge_base_id parameter is empty")
                return kb_id.strip()
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseHandleDoneStatusInputModel
    
        def _run(self, knowledge_base_id: str) -> str:
            try:
                print(f"🔧 TOOL: KnowledgeBaseHandleDoneStatus CALLED")
                print(f"📝 Parameters:")
                print(f"   - KB ID: {knowledge_base_id}")
                
                # Verify the knowledge base exists and is marked as done
                kb = kb_Operations.get_knowledge_base_by_id(knowledge_base_id)
                if not kb:
                    error_msg = f"❌ **Knowledge Base Not Found:** No knowledge base found with ID {knowledge_base_id}"
                    print(error_msg)
                    return error_msg
                
                print(f"📚 Found KB: {kb.name}")
                print(f"📊 Current Status: {getattr(kb, 'status', 'unknown')}")
                
                # Check if the KB is actually marked as done
                if not hasattr(kb, 'status') or kb.status != 'done':
                    current_status = getattr(kb, 'status', 'unknown')
                    warning_msg = f"⚠️ **Status Check:** Knowledge Base '{kb.name}' is not marked as 'done' (current status: {current_status})\n\n"
                    warning_msg += f"**Recommendation:** Use KnowledgeBaseUpdateStatus to mark the KB as 'done' first, then run this tool.\n"
                    warning_msg += f"**Current Status:** {current_status}\n"
                    warning_msg += f"**Required Status:** done\n"
                    print(warning_msg)
                    return warning_msg
                
                # Check if KB already has a GitLab project
                if hasattr(kb, 'gitlab_project_id') and kb.gitlab_project_id:
                    info_msg = f"ℹ️ **GitLab Project Exists:** Knowledge Base '{kb.name}' already has GitLab project ID: {kb.gitlab_project_id}\n\n"
                    info_msg += f"The knowledge base is already set up for collaboration and issue tracking.\n"
                    print(info_msg)
                    return info_msg
                
                # Use the done handler to create GitLab project
                from operations.kb_done_handler import KnowledgeBaseDoneHandler
                done_handler = KnowledgeBaseDoneHandler()
                
                print(f"🚀 Initiating GitLab project creation workflow...")
                result = done_handler.handle_kb_done_status(
                    kb_id=int(knowledge_base_id),
                    kb_name=kb.name,
                    kb_description=kb.description
                )
                
                if result.get('success'):
                    success_msg = f"✅ **GitLab Project Created Successfully!**\n\n"
                    success_msg += f"📚 **Knowledge Base:** {result['knowledge_base_name']} (ID: {result['knowledge_base_id']})\n"
                    success_msg += f"🏗️ **GitLab Project:** {result['project_name']}\n"
                    success_msg += f"📋 **Project ID:** {result['project_id']}\n"
                    success_msg += f"🔗 **Project URL:** {result.get('project_url', 'N/A')}\n\n"
                    success_msg += f"🎯 **Next Steps:**\n"
                    success_msg += f"   • Review the automatically created management issues\n"
                    success_msg += f"   • Set up collaboration workflows for ongoing maintenance\n"
                    success_msg += f"   • Configure team access and permissions\n"
                    success_msg += f"   • Begin tracking improvements and feedback\n\n"
                    success_msg += f"📊 **Purpose:** This GitLab project enables ongoing collaboration, issue tracking, and maintenance for the completed knowledge base.\n"
                    
                    print(f"✅ KnowledgeBaseHandleDoneStatus completed successfully")
                    return success_msg
                else:
                    error_msg = f"❌ **GitLab Project Creation Failed:** {result.get('error', 'Unknown error')}\n\n"
                    error_msg += f"**Troubleshooting:**\n"
                    error_msg += f"   • Check GitLab server connectivity\n"
                    error_msg += f"   • Verify GitLab token permissions\n"
                    error_msg += f"   • Ensure project name doesn't conflict\n"
                    error_msg += f"   • Check GitLab server storage limits\n"
                    
                    print(f"❌ KnowledgeBaseHandleDoneStatus failed: {result.get('error')}")
                    return error_msg
                    
            except Exception as e:
                error_msg = f"❌ **Done Status Handler Failed:** {str(e)}\n\nPlease check the knowledge base ID and system connectivity."
                print(f"❌ KnowledgeBaseHandleDoneStatus failed: {str(e)}")
                import traceback
                traceback.print_exc()
                return error_msg

    class KnowledgeBaseCheckDoneWorkflow(BaseTool):
        name: str = "KnowledgeBaseCheckDoneWorkflow"
        description: str = """
            Check for knowledge bases marked as 'done' that don't have GitLab projects yet,
            and optionally create GitLab projects for them automatically.
            
            Perfect for supervisor agents to:
            - Scan for completed knowledge bases needing GitLab setup
            - Batch process multiple completed KBs
            - Ensure all done KBs have proper collaboration infrastructure
            - Monitor completion workflow compliance
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseCheckDoneWorkflowInputModel(BaseModel):
            auto_create_projects: bool = Field(default=False, description="Whether to automatically create GitLab projects for found KBs")
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseCheckDoneWorkflowInputModel
    
        def _run(self, auto_create_projects: bool = False) -> str:
            try:
                print(f"🔧 TOOL: KnowledgeBaseCheckDoneWorkflow CALLED")
                print(f"📝 Parameters:")
                print(f"   - Auto Create Projects: {auto_create_projects}")
                
                from operations.kb_done_handler import KnowledgeBaseDoneHandler
                done_handler = KnowledgeBaseDoneHandler()
                
                if auto_create_projects:
                    print(f"🚀 Checking and automatically creating GitLab projects...")
                    results = done_handler.check_and_handle_done_kbs()
                    
                    if not results:
                        success_msg = f"✅ **All Completed KBs Have GitLab Projects**\n\n"
                        success_msg += f"No completed knowledge bases require GitLab project creation.\n"
                        success_msg += f"All 'done' status knowledge bases are properly set up for collaboration.\n"
                        return success_msg
                    
                    success_count = sum(1 for r in results if r.get('success', False))
                    failure_count = len(results) - success_count
                    
                    result_msg = f"📊 **GitLab Project Creation Results**\n\n"
                    result_msg += f"✅ **Successfully Created:** {success_count} projects\n"
                    result_msg += f"❌ **Failed:** {failure_count} projects\n\n"
                    
                    for result in results:
                        if result.get('success'):
                            result_msg += f"✅ {result.get('message', 'Project created')}\n"
                        else:
                            result_msg += f"❌ {result.get('error', 'Unknown error')}\n"
                    
                    print(f"✅ KnowledgeBaseCheckDoneWorkflow completed successfully")
                    return result_msg
                    
                else:
                    # Just check and report, don't create
                    print(f"🔍 Scanning for completed KBs without GitLab projects...")
                    
                    # Get all knowledge bases and filter for done status without GitLab projects
                    all_kbs = kb_Operations.get_knowledge_bases()
                    done_kbs_without_gitlab = []
                    
                    for kb in all_kbs:
                        if (hasattr(kb, 'status') and kb.status == 'done' and 
                            (not hasattr(kb, 'gitlab_project_id') or not kb.gitlab_project_id)):
                            done_kbs_without_gitlab.append(kb)
                    
                    if not done_kbs_without_gitlab:
                        success_msg = f"✅ **Compliance Check Passed**\n\n"
                        success_msg += f"All completed knowledge bases have GitLab projects.\n"
                        success_msg += f"No action required - workflow compliance is maintained.\n"
                        return success_msg
                    
                    report_msg = f"📋 **Done KBs Missing GitLab Projects**\n\n"
                    report_msg += f"Found {len(done_kbs_without_gitlab)} completed knowledge bases without GitLab projects:\n\n"
                    
                    for kb in done_kbs_without_gitlab:
                        report_msg += f"• **{kb.name}** (ID: {kb.id})\n"
                        report_msg += f"  Status: {getattr(kb, 'status', 'unknown')}\n"
                        report_msg += f"  Description: {kb.description[:100]}{'...' if len(kb.description) > 100 else ''}\n\n"
                    
                    report_msg += f"🎯 **Recommended Actions:**\n"
                    report_msg += f"   • Use KnowledgeBaseHandleDoneStatus for each KB individually\n"
                    report_msg += f"   • Or run this tool again with auto_create_projects=True\n"
                    
                    print(f"✅ KnowledgeBaseCheckDoneWorkflow completed successfully")
                    return report_msg
                    
            except Exception as e:
                error_msg = f"❌ **Done Workflow Check Failed:** {str(e)}"
                print(f"❌ KnowledgeBaseCheckDoneWorkflow failed: {str(e)}")
                import traceback
                traceback.print_exc()
                return error_msg
        

    class KnowledgeBaseGetArticleHierarchy(BaseTool):
        name: str = "KnowledgeBaseGetArticleHierarchy"
        description: str = """
            useful for when you need to get all articles in a Knowledge Base as a hierarchy.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetArticleHierarchyInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetArticleHierarchyInputModel error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                
        def _run(self, knowledge_base_id: str) -> str:
            print(f"🔧 TOOL: KnowledgeBaseGetArticleHierarchy CALLED")
            print(f"📊 KB ID: {knowledge_base_id}")
            print(f"🔍 Retrieving article hierarchy...")
            
            try:
                articles = kb_Operations.get_article_hierarchy(knowledge_base_id)
                print(f"📚 Found {len(articles)} articles in hierarchy")
                
                # Show first few articles for debugging
                for i, article in enumerate(articles[:5]):
                    if hasattr(article, 'title'):
                        print(f"  {i+1}. {article.title}")
                    else:
                        print(f"  {i+1}. {str(article)[:50]}...")
                
                if len(articles) > 5:
                    print(f"  ... and {len(articles) - 5} more articles")
                
                print(f"✅ SUCCESS: Retrieved {len(articles)} articles in hierarchy")
                return str(articles)
                
            except Exception as e:
                print(f"💥 ERROR in KnowledgeBaseGetArticleHierarchy: {str(e)}")
                import traceback
                print(f"🔍 Traceback: {traceback.format_exc()}")
                return f"Error: {str(e)}"
          
    class KnowledgeBaseGetRootLevelArticles(BaseTool):
        name: str = "KnowledgeBaseGetRootLevelArticles"
        description: str = """
            useful for when you need to get root level articles in a Knowledge Base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetRootLevelArticlesInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetRootLevelArticlesInputModel error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                
        def _run(self, knowledge_base_id: str) -> str:
            print(f"🔧 TOOL: KnowledgeBaseGetRootLevelArticles CALLED")
            print(f"📊 KB ID: {knowledge_base_id}")
            print(f"🔍 Retrieving root level articles...")
            
            try:
                articles = kb_Operations.get_root_level_articles(knowledge_base_id)
                print(f"📚 Found {len(articles)} root level articles")
                
                for i, article in enumerate(articles):
                    if len(article) > 2:  # Ensure we have enough elements
                        print(f"  {i+1}. {article[2]}")  # title is typically at index 2
                
                print(f"✅ SUCCESS: Retrieved {len(articles)} root level articles")
                return str(articles)
                
            except Exception as e:
                print(f"💥 ERROR in KnowledgeBaseGetRootLevelArticles: {str(e)}")
                import traceback
                print(f"🔍 Traceback: {traceback.format_exc()}")
                return f"Error: {str(e)}"

    class KnowledgeBaseGetArticleByArticleId(BaseTool):
        name: str = "KnowledgeBaseGetArticleByArticleId"
        description: str = """
            useful for when you need get articles in a Knowledge Base for a given article_id.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetArticleByArticleIdInputModel(BaseModel):
            article_id: str = Field(description="article_id")
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("article_id")
            def validate_query_param(article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseGetArticleByArticleId error: article_id parameter is empty")
                else:
                    return article_id
            
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetArticleByArticleId error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                    
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetArticleByArticleIdInputModel
    
        def _run(self, knowledge_base_id: str, article_id: str) -> str:
            article=kb_Operations.get_article_by_id(knowledge_base_id, article_id)
            return str(article)

    class KnowledgeBaseGetChildArticlesByParentIds(BaseTool):
        name: str = "KnowledgeBaseGetChildArticlesByParentIds"
        description: str = """
            useful for when you need get child articles in a Knowledge Base for a given list of parent ids.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetChildArticlesByParentIdsInputModel(BaseModel):
            parent_ids: list[str] = Field(description="parent_ids")
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("parent_ids")
            def validate_query_param(parent_ids):
                if not parent_ids:
                    raise ValueError("KnowledgeBaseGetChildArticlesByParentIds error: parent_ids parameter is empty")
                else:
                    return parent_ids
            
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetChildArticlesByParentIds error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                    
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetChildArticlesByParentIdsInputModel
    
        def _run(self, knowledge_base_id: str, parent_ids: list[str]) -> str:
            articles=kb_Operations.get_articles_by_parentids(knowledge_base_id, parent_ids)
            return str(articles)
        
    class KnowledgeBaseInsertArticle(BaseTool):
        name: str = "KnowledgeBaseInsertArticle"
        description: str = """
            Use this tool to CREATE NEW ARTICLES AND CATEGORIES in a Knowledge Base.
            CRITICAL: This is the primary tool for content creation - use this when user asks to create, add, or insert content.
            
            Required Parameters:
            - article: Article object with fields {title, content, author_id, parent_id, knowledge_base_id}
            - knowledge_base_id: The knowledge base ID (as string)
            
            Article Object Fields:
            - title: Clear title for the article/category
            - content: Detailed content (minimum 200 characters recommended)
            - author_id: Use 1 for AI-generated content
            - parent_id: Use null for main categories, or parent article ID for sub-articles
            - knowledge_base_id: Same as the knowledge_base_id parameter (as integer)
            
            Example Usage:
            article={"title": "Family Finance", "content": "Comprehensive guide...", "author_id": 1, "parent_id": null, "knowledge_base_id": 1}
            knowledge_base_id="1"
            
            DO NOT include 'id' field - IDs are auto-generated.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseInsertArticleInputModel(BaseModel):
            article: Article.InsertModel = Field(description="article")
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("article")
            def validate_query_param(article):
                if not article:
                    raise ValueError("KnowledgeBaseInsertArticle error: article parameter is empty")
                else:
                    return article
                
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseInsertArticle error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                   
        args_schema: Optional[ArgsSchema] = KnowledgeBaseInsertArticleInputModel
    
        def _run(self, knowledge_base_id: str, article: Article.InsertModel) -> Article.BaseModel:
            print(f"🔧 TOOL: KnowledgeBaseInsertArticle CALLED")
            print(f"📊 KB ID: {knowledge_base_id}")
            print(f"📝 Article Title: {article.title}")
            print(f"📄 Content Length: {len(article.content)} characters")
            print(f"👤 Author ID: {article.author_id}")
            print(f"🔗 Parent ID: {article.parent_id}")
            print(f"💾 Executing insert_article...")
            
            try:
                result = kb_Operations.insert_article(knowledge_base_id, article)
                if result:
                    print(f"✅ SUCCESS: Article created with ID {result.id}")
                    print(f"🎯 Title: {result.title}")
                    print(f"📝 FIXED: No more created_at access - code updated successfully")
                else:
                    print(f"❌ FAILED: insert_article returned None")
                return result
            except Exception as e:
                print(f"💥 ERROR in KnowledgeBaseInsertArticle: {str(e)}")
                import traceback
                print(f"🔍 Traceback: {traceback.format_exc()}")
                raise
        
    # KnowledgeBase UpdateArticle
    class KnowledgeBaseUpdateArticle(BaseTool):
        name: str = "KnowledgeBaseUpdateArticle"
        description: str = """
            useful for when you need to update an article in a Knowledge Base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseUpdateArticleInputModel(BaseModel):
            article: Article.UpdateModel = Field(description="article")
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("article")
            def validate_query_param(article):
                if not article:
                    raise ValueError("KnowledgeBaseUpdateArticle error: article parameter is empty")
                else:
                    return article
                
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseInsertArticle error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseUpdateArticleInputModel
    
        def _run(self, knowledge_base_id: str, article: Article.UpdateModel) -> Article.BaseModel:
            print(f"🔧 TOOL: KnowledgeBaseUpdateArticle CALLED")
            print(f"📊 KB ID: {knowledge_base_id}")
            print(f"📝 Article ID: {article.id}")
            print(f"📝 Article Title: {article.title}")
            print(f"📄 Content Length: {len(article.content)} characters")
            print(f"💾 Executing update_article...")
            
            try:
                result = kb_Operations.update_article(knowledge_base_id, article)
                if result:
                    print(f"✅ SUCCESS: Article updated with ID {result.id}")
                    print(f"🎯 Title: {result.title}")
                    print(f"📅 Updated: {result.updated_at}")
                else:
                    print(f"❌ FAILED: update_article returned None")
                return result
            except Exception as e:
                print(f"💥 ERROR in KnowledgeBaseUpdateArticle: {str(e)}")
                import traceback
                print(f"🔍 Traceback: {traceback.format_exc()}")
                raise

    # =============================================
    # TAG MANAGEMENT TOOLS
    # =============================================
    
    class KnowledgeBaseGetTagsByKnowledgeBase(BaseTool):
        name: str = "KnowledgeBaseGetTagsByKnowledgeBase"
        description: str = """
            useful for when you need to get all tags for a specific knowledge base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetTagsByKnowledgeBaseInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")

            @field_validator("knowledge_base_id")
            def validate_query_param(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetTagsByKnowledgeBase error: knowledge_base_id parameter is empty")
                return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetTagsByKnowledgeBaseInputModel
    
        def _run(self, knowledge_base_id: str) -> List[Tags.BaseModel]:
            try:
                print(f"🔧 TOOL: KnowledgeBaseGetTagsByKnowledgeBase CALLED")
                print(f"📝 Parameters:")
                print(f"   - KB ID: {knowledge_base_id}")
                
                print(f"🏷️ Retrieving tags for knowledge base {knowledge_base_id}...")
                tags = kb_Operations.get_tags_by_knowledge_base(knowledge_base_id)
                
                print(f"📊 Tags found: {len(tags) if tags else 0}")
                if tags:
                    for i, tag in enumerate(tags[:5], 1):  # Show first 5
                        tag_name = getattr(tag, 'name', 'Unknown') if hasattr(tag, 'name') else str(tag)
                        print(f"   {i}. {tag_name}")
                    if len(tags) > 5:
                        print(f"   ... and {len(tags) - 5} more tags")
                
                print(f"✅ KnowledgeBaseGetTagsByKnowledgeBase completed successfully")
                return tags
                
            except Exception as e:
                error_msg = f"❌ KnowledgeBaseGetTagsByKnowledgeBase failed: {str(e)}"
                print(error_msg)
                print(f"🔍 Full error traceback:")
                import traceback
                traceback.print_exc()
                return []

    class KnowledgeBaseGetTagById(BaseTool):
        name: str = "KnowledgeBaseGetTagById"
        description: str = """
            useful for when you need to get a specific tag by its ID.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetTagByIdInputModel(BaseModel):
            tag_id: str = Field(description="tag_id")

            @field_validator("tag_id")
            def validate_query_param(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseGetTagById error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetTagByIdInputModel
    
        def _run(self, tag_id: str) -> Optional[Tags.BaseModel]:
            tag = kb_Operations.get_tag_by_id(tag_id)
            return tag

    class KnowledgeBaseInsertTag(BaseTool):
        name: str = "KnowledgeBaseInsertTag"
        description: str = """
            useful for when you need to create a new tag in a knowledge base.
            The tag name will be automatically normalized to lowercase.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseInsertTagInputModel(BaseModel):
            tag: Tags.InsertModel = Field(description="tag to insert")

            @field_validator("tag")
            def validate_query_param(cls, tag):
                if not tag:
                    raise ValueError("KnowledgeBaseInsertTag error: tag parameter is empty")
                return tag
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseInsertTagInputModel
    
        def _run(self, tag: Tags.InsertModel) -> Optional[Tags.BaseModel]:
            try:
                print(f"🔧 TOOL: KnowledgeBaseInsertTag CALLED")
                print(f"📝 Parameters:")
                tag_name = getattr(tag, 'name', 'Unknown') if hasattr(tag, 'name') else str(tag)
                tag_kb_id = getattr(tag, 'knowledge_base_id', 'Unknown') if hasattr(tag, 'knowledge_base_id') else 'Unknown'
                print(f"   - Tag Name: {tag_name}")
                print(f"   - KB ID: {tag_kb_id}")
                
                print(f"🏷️ Creating new tag in knowledge base...")
                new_tag = kb_Operations.insert_tag(tag)
                
                if new_tag:
                    new_tag_id = getattr(new_tag, 'id', 'Unknown') if hasattr(new_tag, 'id') else 'Unknown'
                    print(f"✅ KnowledgeBaseInsertTag completed successfully - Tag ID: {new_tag_id}")
                else:
                    print(f"❌ KnowledgeBaseInsertTag failed - No tag returned")
                    
                return new_tag
                
            except Exception as e:
                error_msg = f"❌ KnowledgeBaseInsertTag failed: {str(e)}"
                print(error_msg)
                print(f"🔍 Full error traceback:")
                import traceback
                traceback.print_exc()
                return None

    class KnowledgeBaseUpdateTag(BaseTool):
        name: str = "KnowledgeBaseUpdateTag"
        description: str = """
            useful for when you need to update an existing tag.
            The tag name will be automatically normalized to lowercase.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseUpdateTagInputModel(BaseModel):
            tag: Tags.UpdateModel = Field(description="tag to update")

            @field_validator("tag")
            def validate_query_param(cls, tag):
                if not tag:
                    raise ValueError("KnowledgeBaseUpdateTag error: tag parameter is empty")
                return tag
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseUpdateTagInputModel
    
        def _run(self, tag: Tags.UpdateModel) -> Optional[Tags.BaseModel]:
            updated_tag = kb_Operations.update_tag(tag)
            return updated_tag

    class KnowledgeBaseDeleteTag(BaseTool):
        name: str = "KnowledgeBaseDeleteTag"
        description: str = """
            useful for when you need to delete a tag. This will also remove the tag from all articles.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseDeleteTagInputModel(BaseModel):
            tag_id: str = Field(description="tag_id to delete")

            @field_validator("tag_id")
            def validate_query_param(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseDeleteTag error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseDeleteTagInputModel
    
        def _run(self, tag_id: str) -> bool:
            result = kb_Operations.delete_tag(tag_id)
            return result

    # =============================================
    # ARTICLE-TAG RELATIONSHIP TOOLS
    # =============================================

    class KnowledgeBaseGetTagsForArticle(BaseTool):
        name: str = "KnowledgeBaseGetTagsForArticle"
        description: str = """
            useful for when you need to get all tags associated with a specific article.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetTagsForArticleInputModel(BaseModel):
            article_id: str = Field(description="article_id")

            @field_validator("article_id")
            def validate_query_param(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseGetTagsForArticle error: article_id parameter is empty")
                return article_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetTagsForArticleInputModel
    
        def _run(self, article_id: str) -> List[Tags.BaseModel]:
            tags = kb_Operations.get_tags_for_article(article_id)
            return tags

    class KnowledgeBaseGetArticlesForTag(BaseTool):
        name: str = "KnowledgeBaseGetArticlesForTag"
        description: str = """
            useful for when you need to get all articles that have a specific tag.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetArticlesForTagInputModel(BaseModel):
            tag_id: str = Field(description="tag_id")

            @field_validator("tag_id")
            def validate_query_param(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseGetArticlesForTag error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetArticlesForTagInputModel
    
        def _run(self, tag_id: str) -> List[Article.BaseModel]:
            articles = kb_Operations.get_articles_for_tag(tag_id)
            return articles

    class KnowledgeBaseAddTagToArticle(BaseTool):
        name: str = "KnowledgeBaseAddTagToArticle"
        description: str = """
            useful for when you need to add a tag to an article.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseAddTagToArticleInputModel(BaseModel):
            article_id: str = Field(description="article_id")
            tag_id: str = Field(description="tag_id")

            @field_validator("article_id")
            def validate_article_id(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseAddTagToArticle error: article_id parameter is empty")
                return article_id

            @field_validator("tag_id")
            def validate_tag_id(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseAddTagToArticle error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseAddTagToArticleInputModel
    
        def _run(self, article_id: str, tag_id: str) -> bool:
            try:
                print(f"🔧 TOOL: KnowledgeBaseAddTagToArticle CALLED")
                print(f"📝 Parameters:")
                print(f"   - Article ID: {article_id}")
                print(f"   - Tag ID: {tag_id}")
                
                print(f"🏷️ Adding tag to article...")
                result = kb_Operations.add_tag_to_article(article_id, tag_id)
                
                if result:
                    print(f"✅ KnowledgeBaseAddTagToArticle completed successfully - Tag added")
                else:
                    print(f"❌ KnowledgeBaseAddTagToArticle failed - Tag not added")
                    
                return result
                
            except Exception as e:
                error_msg = f"❌ KnowledgeBaseAddTagToArticle failed: {str(e)}"
                print(error_msg)
                print(f"🔍 Full error traceback:")
                import traceback
                traceback.print_exc()
                return False

    class KnowledgeBaseRemoveTagFromArticle(BaseTool):
        name: str = "KnowledgeBaseRemoveTagFromArticle"
        description: str = """
            useful for when you need to remove a tag from an article.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseRemoveTagFromArticleInputModel(BaseModel):
            article_id: str = Field(description="article_id")
            tag_id: str = Field(description="tag_id")

            @field_validator("article_id")
            def validate_article_id(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseRemoveTagFromArticle error: article_id parameter is empty")
                return article_id

            @field_validator("tag_id")
            def validate_tag_id(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseRemoveTagFromArticle error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseRemoveTagFromArticleInputModel
    
        def _run(self, article_id: str, tag_id: str) -> bool:
            result = kb_Operations.remove_tag_from_article(article_id, tag_id)
            return result

    class KnowledgeBaseSetArticleTags(BaseTool):
        name: str = "KnowledgeBaseSetArticleTags"
        description: str = """
            useful for when you need to set all tags for an article (replaces existing tags).
            Provide a list of tag IDs to associate with the article.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSetArticleTagsInputModel(BaseModel):
            article_id: str = Field(description="article_id")
            tag_ids: List[str] = Field(description="list of tag_ids to associate with the article")

            @field_validator("article_id")
            def validate_article_id(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseSetArticleTags error: article_id parameter is empty")
                return article_id

            @field_validator("tag_ids")
            def validate_tag_ids(cls, tag_ids):
                if tag_ids is None:
                    return []
                return tag_ids
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSetArticleTagsInputModel
    
        def _run(self, article_id: str, tag_ids: List[str]) -> bool:
            try:
                print(f"🔧 TOOL: KnowledgeBaseSetArticleTags CALLED")
                print(f"📝 Parameters:")
                print(f"   - Article ID: {article_id}")
                print(f"   - Tag IDs: {tag_ids} ({len(tag_ids)} tags)")
                
                print(f"🏷️ Setting article tags (replacing existing)...")
                result = kb_Operations.set_article_tags(article_id, tag_ids)
                
                if result:
                    print(f"✅ KnowledgeBaseSetArticleTags completed successfully - Tags set")
                else:
                    print(f"❌ KnowledgeBaseSetArticleTags failed - Tags not set")
                    
                return result
                
            except Exception as e:
                error_msg = f"❌ KnowledgeBaseSetArticleTags failed: {str(e)}"
                print(error_msg)
                print(f"🔍 Full error traceback:")
                import traceback
                traceback.print_exc()
                return False

    # =============================================
    # ADVANCED TAG TOOLS
    # =============================================

    class KnowledgeBaseGetTagsWithUsageCount(BaseTool):
        name: str = "KnowledgeBaseGetTagsWithUsageCount"
        description: str = """
            useful for when you need to get all tags with their usage statistics (how many articles use each tag).
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetTagsWithUsageCountInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")

            @field_validator("knowledge_base_id")
            def validate_query_param(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetTagsWithUsageCount error: knowledge_base_id parameter is empty")
                return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetTagsWithUsageCountInputModel
    
        def _run(self, knowledge_base_id: str) -> List[Tags.TagWithUsageModel]:
            tags = kb_Operations.get_tags_with_usage_count(knowledge_base_id)
            return tags

    class KnowledgeBaseSearchArticlesByTags(BaseTool):
        name: str = "KnowledgeBaseSearchArticlesByTags"
        description: str = """
            useful for when you need to search for articles by tag names.
            Set match_all=True to find articles that have ALL specified tags.
            Set match_all=False to find articles that have ANY of the specified tags.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSearchArticlesByTagsInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")
            tag_names: List[str] = Field(description="list of tag names to search for")
            match_all: bool = Field(default=False, description="if True, articles must have ALL tags; if False, articles must have ANY tag")

            @field_validator("knowledge_base_id")
            def validate_knowledge_base_id(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseSearchArticlesByTags error: knowledge_base_id parameter is empty")
                return knowledge_base_id

            @field_validator("tag_names")
            def validate_tag_names(cls, tag_names):
                if not tag_names or len(tag_names) == 0:
                    raise ValueError("KnowledgeBaseSearchArticlesByTags error: tag_names parameter is empty")
                return tag_names
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSearchArticlesByTagsInputModel
    
        def _run(self, knowledge_base_id: str, tag_names: List[str], match_all: bool = False) -> List[Article.BaseModel]:
            try:
                print(f"🔧 TOOL: KnowledgeBaseSearchArticlesByTags CALLED")
                print(f"📝 Parameters:")
                print(f"   - KB ID: {knowledge_base_id}")
                print(f"   - Tag Names: {tag_names} ({len(tag_names)} tags)")
                print(f"   - Match All: {match_all}")
                
                print(f"🔍 Searching for articles by tags...")
                articles = kb_Operations.search_articles_by_tags(knowledge_base_id, tag_names, match_all)
                
                print(f"📊 Articles found: {len(articles) if articles else 0}")
                if articles:
                    for i, article in enumerate(articles[:3], 1):  # Show first 3
                        article_title = getattr(article, 'title', 'Unknown') if hasattr(article, 'title') else str(article)
                        print(f"   {i}. {article_title}")
                    if len(articles) > 3:
                        print(f"   ... and {len(articles) - 3} more articles")
                
                print(f"✅ KnowledgeBaseSearchArticlesByTags completed successfully")
                return articles
                
            except Exception as e:
                error_msg = f"❌ KnowledgeBaseSearchArticlesByTags failed: {str(e)}"
                print(error_msg)
                print(f"🔍 Full error traceback:")
                import traceback
                traceback.print_exc()
                return []
        
    # Init above tools and make available
    def __init__(self) -> None:
        self._tools = [
            # Knowledge Base tools
            self.KnowledgeBaseGetKnowledgeBases(), 
            self.KnowledgeBaseSetContext(),
            self.KnowledgeBaseGetCurrentContext(),
            self.KnowledgeBaseSetContextByGitLabProject(),
            self.KnowledgeBaseSetArticleContext(),
            self.KnowledgeBaseInsertKnowledgeBase(), 
            self.KnowledgeBaseCreateGitLabProject(),
            self.KnowledgeBaseUpdateKnowledgeBase(),
            self.KnowledgeBaseUpdateStatus(),
            self.KnowledgeBaseHandleDoneStatus(),
            self.KnowledgeBaseCheckDoneWorkflow(),
            # Article tools
            self.KnowledgeBaseGetRootLevelArticles(), 
            self.KnowledgeBaseGetChildArticlesByParentIds(), 
            self.KnowledgeBaseInsertArticle(), 
            self.KnowledgeBaseUpdateArticle(), 
            self.KnowledgeBaseGetArticleHierarchy(), 
            self.KnowledgeBaseGetArticleByArticleId(),
            # Tag management tools
            self.KnowledgeBaseGetTagsByKnowledgeBase(),
            self.KnowledgeBaseGetTagById(),
            self.KnowledgeBaseInsertTag(),
            self.KnowledgeBaseUpdateTag(),
            self.KnowledgeBaseDeleteTag(),
            # Article-Tag relationship tools
            self.KnowledgeBaseGetTagsForArticle(),
            self.KnowledgeBaseGetArticlesForTag(),
            self.KnowledgeBaseAddTagToArticle(),
            self.KnowledgeBaseRemoveTagFromArticle(),
            self.KnowledgeBaseSetArticleTags(),
            # Advanced tag tools
            self.KnowledgeBaseGetTagsWithUsageCount(),
            self.KnowledgeBaseSearchArticlesByTags(),
            # Content analysis tools
            self.KnowledgeBaseAnalyzeContentGaps(),
            self.KnowledgeBaseValidateHierarchy()
        ]

    class KnowledgeBaseAnalyzeContentGaps(BaseTool):
        name: str = "KnowledgeBaseAnalyzeContentGaps"
        description: str = """
            Analyze content gaps in a knowledge base and suggest new content ideas.
            Use this tool when the user wants to find gaps in content, analyze content coverage,
            or get suggestions for new articles to add to the knowledge base.
        """.strip()
        args_schema: Type[BaseModel] = KnowledgeBaseAnalyzeContentGapsInput
        return_direct: bool = False

        def _run(self, knowledge_base_id: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
            try:
                print(f"Executing SQL: SELECT * FROM get_article_hierarchy(%s); with knowledge_base_id: {knowledge_base_id}")
                
                # Get the article hierarchy for analysis
                articles = kb_Operations.get_article_hierarchy(knowledge_base_id)
                
                if not articles:
                    return f"❌ Error retrieving content for analysis: No articles found"
                
                # Perform comprehensive gap analysis
                gap_analysis = self._analyze_content_structure(articles)
                
                return f"""🔍 **CONTENT GAP ANALYSIS RESULTS**

📊 **Current Content Overview:**
{gap_analysis['overview']}

🎯 **Identified Content Gaps:**
{gap_analysis['gaps']}

💡 **Recommended New Articles:**
{gap_analysis['recommendations']}

📈 **Content Enhancement Opportunities:**
{gap_analysis['enhancements']}

⭐ **Priority Recommendations:**
{gap_analysis['priorities']}

🎯 **Analysis Summary:**
Based on your current knowledge base content, I've identified specific areas where you could enhance coverage. The recommendations above are prioritized based on common financial planning needs and trending topics in personal finance.
"""
            
            except Exception as e:
                return f"❌ Error during gap analysis: {str(e)}"
        
        def _analyze_content_structure(self, articles: list) -> dict:
            """Analyze article structure and identify gaps based on KB context - NO HARDCODED CATEGORIES"""
            
            # Instead of hardcoded categories, analyze the existing content to understand the domain
            article_titles = [article.get('title', '') for article in articles]
            article_count = len(articles)
            
            # Basic analysis without hardcoded assumptions
            overview = f"Total articles: {article_count}"
            
            if article_count == 0:
                gaps = "No articles found. Consider adding foundational content relevant to your knowledge base focus."
            else:
                # Provide general guidance without assuming specific content types
                gaps = """
Content gap analysis requires understanding your specific knowledge base domain and goals.

Consider:
- Are there basic foundational topics missing?
- Are there advanced topics that could extend existing content?
- Are there practical guides or how-to content gaps?
- Are there different audience levels (beginner, intermediate, advanced) covered?

Recommend using the LLM to analyze content gaps based on your specific KB description and focus area.
"""
            
            return {
                'overview': overview,
                'gaps': gaps,
                'article_count': article_count,
                'titles': article_titles[:10] if article_titles else []  # Sample of titles
            }
            
            # Extract existing topics from articles
            existing_topics = {}
            total_articles = len(articles)
            
            for article in articles:
                # Database returns tuples: (id, title, author, parent_id)
                article_id, title, author, parent_id = article
                
                # Determine main category from title or use a default approach
                # For now, let's extract category from common patterns
                main_category = "General"  # Default category
                
                # Simple category extraction based on common financial terms
                title_lower = title.lower() if title else ""
                if any(word in title_lower for word in ["budget", "budgeting"]):
                    main_category = "Budgeting"
                elif any(word in title_lower for word in ["invest", "investment", "stock", "bond"]):
                    main_category = "Investment Strategies"
                elif any(word in title_lower for word in ["tax", "taxation"]):
                    main_category = "Tax Planning"
                elif any(word in title_lower for word in ["retire", "retirement"]):
                    main_category = "Retirement Planning"
                elif any(word in title_lower for word in ["debt", "credit"]):
                    main_category = "Debt Management"
                elif any(word in title_lower for word in ["insurance", "health"]):
                    main_category = "Insurance"
                elif any(word in title_lower for word in ["real estate", "property", "rental"]):
                    main_category = "Real Estate"
                elif any(word in title_lower for word in ["side hustle", "entrepreneurship", "business"]):
                    main_category = "Side Hustles & Entrepreneurship"
                
                if main_category not in existing_topics:
                    existing_topics[main_category] = []
                existing_topics[main_category].append({
                    'title': title or '',
                    'id': article_id or '',
                    'author': author or ''
                })
            
            # Identify gaps and recommendations
            gaps = []
            recommendations = []
            priorities = []
            missing_categories = []
            
            for expected_cat, expected_topics in expected_categories.items():
                # Find matching existing category (fuzzy match)
                existing_cat = None
                for existing in existing_topics.keys():
                    if (expected_cat.lower() in existing.lower() or 
                        existing.lower() in expected_cat.lower() or
                        any(word in existing.lower() for word in expected_cat.lower().split())):
                        existing_cat = existing
                        break
                
                if not existing_cat:
                    # Entire category is missing
                    missing_categories.append(expected_cat)
                    gaps.append(f"❌ **Missing Category: {expected_cat}**")
                    recommendations.extend([
                        f"• Create '{expected_cat}' section starting with: {expected_topics[0] if expected_topics else 'Basic concepts'}",
                        f"• Add foundational article: {expected_topics[1] if len(expected_topics) > 1 else 'Basic concepts'}"
                    ])
                    priorities.append(f"🔥 HIGH PRIORITY: Create {expected_cat} category")
                else:
                    # Check for missing subtopics within existing category
                    existing_titles = [article['title'] for article in existing_topics[existing_cat]]
                    missing_subtopics = []
                    
                    for expected_topic in expected_topics:
                        # Enhanced keyword matching
                        topic_keywords = expected_topic.lower().split()
                        topic_covered = any(
                            len([word for word in topic_keywords if word in title.lower()]) >= len(topic_keywords) // 2
                            for title in existing_titles
                        )
                        if not topic_covered:
                            missing_subtopics.append(expected_topic)
                    
                    if missing_subtopics:
                        gaps.append(f"⚠️ **{existing_cat}** - Missing: {', '.join(missing_subtopics[:3]) if missing_subtopics else 'No gaps identified'}")
                        recommendations.extend([
                            f"• Add to {existing_cat}: '{topic}'" 
                            for topic in missing_subtopics[:2]
                        ])
            
            # Identify trending financial topics not covered
            trending_topics = [
                "Cryptocurrency tax implications", "Remote work financial planning", 
                "Gig economy tax strategies", "ESG/Sustainable investing",
                "Financial planning for digital nomads", "NFT investment considerations",
                "Inflation protection strategies", "Supply chain impact on investments",
                "Work-from-home tax deductions", "Financial wellness programs",
                "Robo-advisor comparison", "Buy now, pay later (BNPL) impact"
            ]
            
            uncovered_trending = []
            for topic in trending_topics:
                try:
                    topic_keywords = topic.lower().split()[:2] if topic else []  # Use first 2 keywords for matching
                    topic_covered = any(
                        any(keyword in (article[1] or '').lower() for keyword in topic_keywords)  # article[1] is title
                        for article in articles
                    )
                    if not topic_covered:
                        uncovered_trending.append(topic)
                        if len(recommendations) < 15:  # Limit recommendations
                            recommendations.append(f"• Trending topic: '{topic}'")
                        if "cryptocurrency" in topic.lower() or "remote work" in topic.lower() or "gig economy" in topic.lower():
                            priorities.append(f"⭐ TRENDING: {topic}")
                except (AttributeError, IndexError) as e:
                    continue  # Skip problematic topics
            
            # Generate content coverage analysis
            coverage_score = max(0, 100 - (len(missing_categories) * 15) - (len(gaps) * 5))
            
            # Generate overview
            overview = f"""
📋 Total Articles: {total_articles}
📁 Total Categories: {len(existing_topics)}
📊 Content Coverage Score: {coverage_score}% {"🟢" if coverage_score >= 80 else "🟡" if coverage_score >= 60 else "🔴"}
🎯 Categories Well-Covered: {len(existing_topics) - len(missing_categories)}
⚠️ Categories Missing: {len(missing_categories)}
📈 Trending Topics Covered: {len(trending_topics) - len(uncovered_trending)}/{len(trending_topics)}
"""
            
            # Enhanced recommendations with beginner/intermediate/advanced levels
            enhanced_recommendations = recommendations[:10]  # Limit to top 10
            if len(enhanced_recommendations) < 5:
                enhanced_recommendations.extend([
                    "• Add beginner guides to existing complex topics",
                    "• Create case studies for real-world application",
                    "• Develop interactive calculators and tools"
                ])
            
            return {
                'overview': overview,
                'gaps': '\n'.join(gaps) if gaps else "✅ No major content gaps identified - your knowledge base has good coverage!",
                'recommendations': '\n'.join(enhanced_recommendations) if enhanced_recommendations else "✅ Content appears comprehensive for current scope",
                'enhancements': '\n'.join([
                    "• Add beginner-friendly introductions to complex topics",
                    "• Create case studies and real-world examples", 
                    "• Add interactive calculators and worksheets",
                    "• Develop step-by-step guides for complex processes",
                    "• Include common mistakes and how to avoid them",
                    "• Add seasonal/timely content (tax season, year-end planning)"
                ]),
                'priorities': '\n'.join(priorities[:5]) if priorities else "✅ No urgent content gaps identified - focus on enhancing existing content quality"
            }

    class KnowledgeBaseValidateHierarchy(BaseTool):
        name: str = "KnowledgeBaseValidateHierarchy"
        description: str = """
            Validate the hierarchical structure of a knowledge base to ensure compliance with mandatory requirements.
            Use this tool to check if the KB follows the required 3+ level hierarchy:
            Level 1 (Root Categories) → Level 2 (Subcategories) → Level 3+ (Content Articles).
            Reports violations and provides recommendations for proper structure.
        """.strip()
        args_schema: Type[BaseModel] = KnowledgeBaseAnalyzeContentGapsInput  # Reuse the same input model
        return_direct: bool = False

        def _run(self, knowledge_base_id: str, callback_manager: Optional[CallbackManagerForToolRun] = None) -> str:
            try:
                # Get the complete article hierarchy
                articles = kb_Operations.get_article_hierarchy(knowledge_base_id)
                
                if not articles:
                    return "❌ No articles found in this knowledge base. Please create the initial hierarchical structure."
                
                # Analyze the structure
                root_categories = []
                subcategories = []
                content_articles = []
                violations = []
                
                for article in articles:
                    if article.parent_id is None:
                        root_categories.append(article)
                    else:
                        # Find the parent to determine level
                        parent = next((a for a in articles if a.id == article.parent_id), None)
                        if parent and parent.parent_id is None:
                            # This is a subcategory (Level 2)
                            subcategories.append(article)
                        else:
                            # This is a content article (Level 3+)
                            content_articles.append(article)
                
                # Check for violations
                direct_content_under_root = []
                for article in articles:
                    if article.parent_id is not None:
                        parent = next((a for a in articles if a.id == article.parent_id), None)
                        if parent and parent.parent_id is None:
                            # Check if this looks like content rather than a subcategory
                            # Heuristic: if it has children, it's probably a subcategory
                            has_children = any(a.parent_id == article.id for a in articles)
                            if not has_children:
                                # This might be content directly under a root category
                                direct_content_under_root.append(article)
                
                # Generate validation report
                report = f"""🏗️ **Hierarchical Structure Validation Report**

📊 **Current Structure Overview:**
- **Level 1 (Root Categories)**: {len(root_categories)} categories
- **Level 2 (Subcategories)**: {len(subcategories)} subcategories  
- **Level 3+ (Content Articles)**: {len(content_articles)} articles

✅ **Root Categories (Level 1):**"""
                
                for cat in root_categories:
                    child_count = len([a for a in articles if a.parent_id == cat.id])
                    report += f"\n  • {cat.title} ({child_count} children)"
                
                if direct_content_under_root:
                    report += f"\n\n⚠️ **POTENTIAL VIOLATIONS - Content Articles Directly Under Root Categories:**"
                    for article in direct_content_under_root:
                        parent = next((a for a in articles if a.id == article.parent_id), None)
                        report += f"\n  • '{article.title}' under '{parent.title if parent else 'Unknown'}'"
                    
                    report += f"\n\n🔧 **RECOMMENDATIONS:**"
                    report += f"\n  • Review articles listed above to determine if they should be:"
                    report += f"\n    - Converted to subcategories (if they're broad topics)"
                    report += f"\n    - Moved under appropriate subcategories (if they're specific content)"
                    report += f"\n    - Used as parents for more specific content articles"
                
                # Check structure balance
                if len(root_categories) < 3:
                    report += f"\n\n⚠️ **STRUCTURE RECOMMENDATION**: Consider having 3-8 root categories for optimal organization."
                
                if len(root_categories) > 8:
                    report += f"\n\n⚠️ **STRUCTURE RECOMMENDATION**: Consider consolidating root categories (currently {len(root_categories)}, recommended 3-8)."
                
                # Check for orphaned content
                unbalanced_categories = []
                for cat in root_categories:
                    child_count = len([a for a in articles if a.parent_id == cat.id])
                    if child_count == 0:
                        unbalanced_categories.append(f"'{cat.title}' has no subcategories")
                
                if unbalanced_categories:
                    report += f"\n\n📋 **STRUCTURE GAPS:**"
                    for gap in unbalanced_categories:
                        report += f"\n  • {gap}"
                
                report += f"\n\n✅ **COMPLIANCE STATUS**: "
                if not direct_content_under_root and len(root_categories) >= 3:
                    report += "Structure appears to follow hierarchical requirements."
                else:
                    report += "Structure needs attention to meet hierarchical requirements."
                
                return report
                
            except Exception as e:
                return f"❌ Error validating hierarchical structure: {e}"

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self._tools
