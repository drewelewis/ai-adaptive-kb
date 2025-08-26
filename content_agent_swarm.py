import sys
import os
import datetime
import warnings
import time
import logging
import locale
from typing import Dict, Any, List
from dotenv import load_dotenv
from agents.agent_types import AgentState

# Suppress Pydantic warnings
warnings.filterwarnings('ignore', category=UserWarning)

"""
🎯 AUTONOMOUS CONTENT AGENT SWARM - GITLAB PROJECT ACTIVATION SYSTEM
================================================================

This autonomous agent swarm activates immediately when GitLab projects become available for knowledge bases.

🚀 GITLAB PROJECT ACTIVATION GATE:
As soon as a GitLab project is available for a knowledge base, you can begin content work.
- If GitLab project EXISTS: You may proceed with all content creation and planning work
- If GitLab project MISSING: Focus on helping create the project infrastructure
- Always verify which GitLab project you're working with before proceeding.

📋 KNOWLEDGE BASE PROJECT DISCOVERY:
Look for GitLab projects linked to knowledge bases and automatically create work items:
- KB projects created by Supervisor when status = 'done'
- New KB projects needing initial content development 
- Projects with existing management issues ready for content work
- Projects needing comprehensive content planning and execution
"""

# Set up Unicode-safe logging for Windows
def setup_unicode_logging():
    """Set up logging that works with Unicode on Windows"""
    try:
        # Try to set UTF-8 encoding for stdout
        if sys.platform.startswith('win'):
            # For Windows, configure console to handle UTF-8
            os.system('chcp 65001 >nul 2>&1')  # Set console to UTF-8
            
            # Create a custom formatter that handles Unicode gracefully
            class UnicodeFormatter(logging.Formatter):
                def format(self, record):
                    # Get the standard formatted message
                    msg = super().format(record)
                    # Replace problematic Unicode characters with ASCII equivalents
                    replacements = {
                        '🚀': '[START]',
                        '✅': '[OK]',
                        '❌': '[FAIL]',
                        '🔧': '[TOOL]',
                        '📝': '[PARAMS]',
                        '📊': '[STATS]',
                        '🔍': '[SEARCH]',
                        '📚': '[KB]',
                        '📋': '[LIST]',
                        '🎯': '[TARGET]',
                        '🤖': '[AGENT]',
                        '🏷️': '[TAG]',
                        '🦊': '[GITLAB]',
                        '⚠️': '[WARN]',
                        '💬': '[CHAT]',
                        '🌐': '[MULTI]',
                        '🚪': '[GATE]',
                        '⚡': '[AUTO]',
                        '🔄': '[SYNC]',
                        '📄': '[DOC]',
                        '📁': '[FOLDER]',
                        '🆔': '[ID]',
                        '🔗': '[LINK]',
                        '👁️': '[VIEW]',
                        '🎯': '[AIM]'
                    }
                    
                    # Replace Unicode emojis with ASCII equivalents for console compatibility
                    for emoji, replacement in replacements.items():
                        msg = msg.replace(emoji, replacement)
                    
                    return msg
            
            # Configure logging with Unicode-safe formatter
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler('logs/content_agent_swarm.log', mode='a', encoding='utf-8')
                ]
            )
            
            # Apply the Unicode formatter to console handler only
            console_handler = logging.getLogger().handlers[0]  # StreamHandler
            console_handler.setFormatter(UnicodeFormatter('%(asctime)s | %(levelname)8s | %(name)s | %(message)s'))
            
        else:
            # For non-Windows systems, use standard UTF-8 logging
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler('logs/content_agent_swarm.log', mode='a', encoding='utf-8')
                ]
            )
    except Exception as e:
        # Fallback to basic logging if Unicode setup fails
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/content_agent_swarm.log', mode='a')
            ]
        )
        print(f"Warning: Unicode logging setup failed, using fallback: {e}")

# Set up Unicode-safe logging
setup_unicode_logging()

# Create logger for this module
logger = logging.getLogger('ContentAgentSwarm')

# Import the orchestrator with PostgreSQL state management
from agents.orchestrator import Orchestrator

# Import autonomous content creation agents
from agents.content_planner_agent import ContentPlannerAgent
from agents.content_creator_agent import ContentCreatorAgent  
from agents.content_reviewer_agent import ContentReviewerAgent
from agents.content_retrieval_agent import ContentRetrievalAgent
from agents.content_management_agent import ContentManagementAgent
from agents.supervisor_agent import SupervisorAgent

# Import Unicode-safe printing
from utils.unicode_safe_print import safe_print

load_dotenv(override=True)

class AutonomousAgentSwarm:
    """Autonomous Agent Swarm - Runs agents independently to discover and complete work"""
    
    def __init__(self):
        logger.info("🚀 Initializing AutonomousAgentSwarm")
        try:
            self.orchestrator = Orchestrator()
            logger.info("✅ Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestrator: {e}")
            raise
            
        self.is_running = False
        self.cycle_count = 0
        logger.debug(f"Initial state: is_running={self.is_running}, cycle_count={self.cycle_count}")
        
    def initialize_agents(self):
        """Initialize all autonomous agents"""
        logger.info("🤖 Starting agent initialization process")
        safe_print("🤖 Initializing Autonomous Agent Swarm...")
        safe_print("=" * 80)
        
        # Display comprehensive knowledge base summary during initialization
        safe_print("📊 KNOWLEDGE BASE ANALYSIS - Current Context Overview")
        safe_print("-" * 60)
        self.display_knowledge_base_summary()
        
        safe_print("")
        safe_print("🎯 Agent Initialization:")
        safe_print("   • ContentManagement Agent → Prescriptive workflow orchestrator & KB operations")
        safe_print("   • ContentPlanner Agent    → Strategic planning & architecture") 
        safe_print("   • ContentCreator Agent    → Content generation & development")
        safe_print("   • ContentReviewer Agent   → Quality assurance & optimization")
        safe_print("   • ContentRetrieval Agent  → Research & analysis")
        safe_print("   • Supervisor Agent        → Scrum Master coordination")
        safe_print("=" * 80)
        safe_print("⚡ AUTONOMOUS CONTENT GENERATION:")
        safe_print("   • ContentManagement Agent defines prescriptive approach for all agents")
        safe_print("   • When GitLab project is available → ContentManagement creates complete work pipeline")
        safe_print("   • Other agents autonomously execute ContentManagement-created work items")
        safe_print("=" * 80)
        safe_print("🚪 GITLAB PROJECT AVAILABILITY GATE:")
        safe_print("   • Agents activate as soon as GitLab project is available")
        safe_print("   • No waiting for specific work items to close")
        safe_print("   • ContentManagement creates work pipeline when GitLab project exists")
        safe_print("=" * 80)
        safe_print("🌐 MULTI-KB ENVIRONMENT:")
        safe_print("   • Agents work across MULTIPLE knowledge bases")
        safe_print("   • Each work item must specify target KB context")
        safe_print("   • Agents verify KB context before executing operations")
        safe_print("=" * 80)
        logger.info("✅ Agent initialization display completed")
        
    def run_autonomous_cycle(self):
        """Run one cycle of autonomous agent work discovery and execution"""
        self.cycle_count += 1
        logger.info(f"🔄 Starting autonomous cycle #{self.cycle_count}")
        safe_print(f"🔄 Autonomous Cycle #{self.cycle_count} - {datetime.datetime.now().strftime('%H:%M:%S')}")
        safe_print("-" * 60)
        
        # Display comprehensive knowledge base summary at the start of each cycle
        safe_print("📊 Displaying Current KB Context Summary for This Cycle...")
        self.display_knowledge_base_summary()
        safe_print("")
        safe_print("🔄 Continuing with Agent Work Discovery...")
        safe_print("-" * 60)
        
        # Discover available KB projects ready for agent work
        available_projects = self.discover_available_kb_projects()
        if available_projects:
            safe_print(f"🎯 Available KB Projects: {len(available_projects)}")
            for project in available_projects[:3]:  # Show first 3
                safe_print(f"   • {project['kb_name']} (Status: {project['kb_status']}) → GitLab Project: {project['gitlab_project_id']}")
            if len(available_projects) > 3:
                safe_print(f"   ... and {len(available_projects) - 3} more projects")
        else:
            safe_print("💤 No KB projects available for agent work")
        
        # Each agent checks GitLab for their assigned work and executes autonomously
        agents_with_work = 0
        
        # Define agent work patterns for more targeted GitLab queries
        agent_configs = {
            "ContentManagementAgent": {
                "labels": ["kb-management", "prescriptive-workflow", "project-monitoring"],
                "priorities": ["high", "urgent"],
                "focus": "Prescriptive workflow orchestration, GitLab project monitoring, and autonomous work item creation"
            },
            "ContentPlannerAgent": {
                "labels": ["planning", "architecture", "strategy"],
                "priorities": ["high", "medium"],
                "focus": "Strategic planning and sprint coordination"
            },
            "ContentCreatorAgent": {
                "labels": ["content-creation", "content-generation", "development", "writing"],
                "priorities": ["medium", "high"],
                "focus": "Content generation and development tasks"
            },
            "ContentReviewerAgent": {
                "labels": ["review", "qa", "quality-assurance", "quality-review"],
                "priorities": ["high", "urgent"],
                "focus": "Quality assurance and content optimization"
            },
            "ContentRetrievalAgent": {
                "labels": ["research", "analysis", "retrieval"],
                "priorities": ["medium", "low"],
                "focus": "Research and analysis support"
            },
            "SupervisorAgent": {
                "labels": ["coordination", "scrum", "management"],
                "priorities": ["urgent", "high"],
                "focus": "Scrum Master coordination and team facilitation"
            }
        }
        
        logger.debug(f"Processing {len(agent_configs)} agent configurations")
        
        for agent_name, config in agent_configs.items():
            logger.debug(f"Processing agent: {agent_name}")
            safe_print(f"  📋 {agent_name}: Scanning for appropriate work...")
            safe_print(f"      Focus: {config['focus']}")
            
            try:
                # Real GitLab work discovery implementation
                labels_str = ", ".join(config['labels'])
                priorities_str = ", ".join(config['priorities'])
                
                logger.debug(f"Agent {agent_name} - Labels: {labels_str}, Priorities: {priorities_str}")
                
                work_discovery_message = f"""
                Scan GitLab for work items appropriate for {agent_name} across MULTIPLE KNOWLEDGE BASES.
                
                🎯 AGENT SELF-SELECTION PRINCIPLE:
                You scan for and select work that matches your capabilities and focus area.
                You are NOT assigned specific work - you autonomously choose appropriate work items.
                Look for work items that align with your expertise and current capacity.
                
                💬 AGENT COMMUNICATION THROUGH GITLAB COMMENTS:
                If you have questions about any work item, use GitLab issue comments to communicate.
                Post questions, clarifications, or requests for help as comments on the relevant issue.
                Other agents monitor issue comments and will respond to provide assistance.
                All inter-agent communication happens through GitLab issue comments and status updates.
                
                🌐 MULTI-KB CONTEXT REQUIREMENT:
                You work across multiple knowledge bases. Every work item MUST specify target KB context.
                Always verify which knowledge base you're working with before proceeding.
                
                🚀 GITLAB PROJECT AVAILABILITY:
                As soon as a GitLab project is available for a knowledge base, you can begin content work.
                - If GitLab project EXISTS: You may proceed with all content creation and planning work
                - If GitLab project MISSING: Focus on helping create the project infrastructure
                - Always verify which GitLab project you're working with before proceeding.
                
                �📋 STANDARDIZED WORK ITEM NAMING:
                Look for work items with standardized naming conventions:
                - KB Content Planning: [KB Name] - Comprehensive content architecture
                - KB Content Creation: [KB Name] - Active content development
                - KB Content Review: [KB Name] - Quality assurance and optimization
                - KB Enhancement: [KB Name] - Ongoing improvements and updates
                - KB-PLAN: [KB Name] - Content Planning & Strategy
                - KB-CREATE: [KB Name] - Content Development
                - KB-REVIEW: [KB Name] - Quality Assurance & Review
                - KB-RESEARCH: [KB Name] - Research & Analysis
                - KB-UPDATE: [KB Name] - Knowledge Base Updates
                
                CRITICAL: Content agents ONLY work on items created by the Supervisor Agent.
                If no supervisor-created work items exist, you must wait for them.
                
                Search criteria:
                - Agent: {agent_name.lower()}
                - Labels: {labels_str}, supervisor-created
                - Priorities: {priorities_str}
                - Focus area: {config['focus']}
                - Creator: Must be created or assigned by Supervisor Agent
                - KB Context: Must include target knowledge base identification
                - Naming: Must follow standardized naming conventions
                - Project Check: Verify GitLab project availability before content creation
                
                Look for:
                - Open issues assigned to or labeled for this agent BY THE SUPERVISOR
                - High priority items needing immediate attention FROM SUPERVISOR
                - GitLab projects linked to knowledge bases needing content work
                - Content work items for projects with available GitLab infrastructure
                - Work items with CLEAR KB CONTEXT and linked GitLab project
                
                If supervisor-created work is found:
                1. Verify there's a GitLab project linked to the target KB
                2. If GitLab project EXISTS: Proceed with all content creation and planning work
                3. If GitLab project MISSING: Help create project infrastructure or wait for Supervisor
                4. Verify the target knowledge base context from the work item title
                5. Process the highest priority item for the specified KB
                6. Update GitLab with progress including KB context and project status
                
                If no supervisor work items exist, scan for available KB projects and create appropriate work items.
                Report specific work item details, target KB context, and GitLab project availability.
                
                AVAILABLE KB PROJECTS FOR WORK:
                {self._format_available_projects(available_projects)}
                """
                
                logger.debug(f"Calling {agent_name} work discovery directly")
                
                # Call agent's work discovery directly instead of through LangGraph
                try:
                    if agent_name == "ContentManagementAgent":
                        work_result = self._call_content_management_work_discovery()
                    elif agent_name == "ContentPlannerAgent":
                        work_result = self._call_content_planner_work_discovery()  
                    elif agent_name == "ContentCreatorAgent":
                        work_result = self._call_content_creator_work_discovery()
                    elif agent_name == "ContentReviewerAgent":
                        work_result = self._call_content_reviewer_work_discovery()
                    elif agent_name == "ContentRetrievalAgent":
                        work_result = self._call_content_retrieval_work_discovery()
                    elif agent_name == "SupervisorAgent":
                        work_result = self._call_supervisor_work_discovery()
                    else:
                        work_result = {"found_work": False, "message": f"Unknown agent: {agent_name}"}
                    
                    logger.debug(f"Work discovery result from {agent_name}: {work_result}")
                    
                    # Debug: Check the exact value
                    found_work_value = work_result.get("found_work", False)
                    logger.debug(f"DEBUG: found_work value for {agent_name}: {found_work_value} (type: {type(found_work_value)})")
                    
                    if found_work_value:
                        agents_with_work += 1
                        logger.info(f"✅ {agent_name} found and selected appropriate work")
                        safe_print(f"    ✅ Found and selected appropriate work")
                        safe_print(f"    📝 {work_result.get('message', 'Working on GitLab issue')}")
                        
                        # Execute the work that was found
                        try:
                            safe_print(f"    🚀 Executing work...")
                            logger.debug(f"DEBUG: About to execute work for {agent_name}")
                            
                            # NEW STANDARDIZED EXECUTION: Agents handle their own work through process() method
                            # The work discovery already set up the agent's internal state for GitLab work
                            # So we just need to call the agent's process method with a basic state
                            work_state = AgentState(
                                current_kb_id=getattr(self.orchestrator, 'knowledge_base_id', '1'),
                                agent_username=agent_name.replace("Agent", "").lower()
                            )
                            
                            # Get the appropriate agent
                            if agent_name == "ContentManagementAgent":
                                agent = self.orchestrator.content_manager
                            elif agent_name == "ContentPlannerAgent":
                                agent = self.orchestrator.content_planner
                            elif agent_name == "ContentCreatorAgent":
                                agent = self.orchestrator.content_creator
                            elif agent_name == "ContentReviewerAgent":
                                agent = self.orchestrator.content_reviewer
                            elif agent_name == "ContentRetrievalAgent":
                                agent = self.orchestrator.content_retrieval
                            elif agent_name == "SupervisorAgent":
                                agent = self.orchestrator.supervisor
                            else:
                                safe_print(f"    ❌ Unknown agent: {agent_name}")
                                continue
                            
                            # Execute using standardized process method
                            result_state = agent.process(work_state)
                            
                            if result_state:
                                safe_print(f"    ✅ Work completed successfully")
                                logger.debug(f"DEBUG: {agent_name} completed work successfully")
                            else:
                                safe_print(f"    ⚠️  Work execution returned empty state")
                                logger.debug(f"DEBUG: {agent_name} returned empty state")
                                
                        except Exception as exec_error:
                            logger.error(f"❌ Work execution error for {agent_name}: {str(exec_error)}", exc_info=True)
                            safe_print(f"    ❌ Execution failed: {str(exec_error)[:50]}...")
                            
                    else:
                        logger.debug(f"💤 {agent_name} found no appropriate work items")
                        safe_print(f"    💤 No appropriate work items available - waiting for suitable work to be created")
                        
                except Exception as work_error:
                    logger.error(f"❌ Work discovery error for {agent_name}: {str(work_error)}")
                    safe_print(f"    ❌ Work discovery failed: {str(work_error)[:50]}...")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {agent_name}: {str(e)}", exc_info=True)
                safe_print(f"    ❌ Error: {str(e)[:50]}...")
                # Continue with other agents even if one fails
                
        logger.info(f"📊 Cycle #{self.cycle_count} completed: {agents_with_work}/{len(agent_configs)} agents found work")
        safe_print(f"📊 Cycle Summary: {agents_with_work}/{len(agent_configs)} agents found work")
        safe_print("-" * 60)
        
        return agents_with_work > 0
    
    def _call_content_management_work_discovery(self) -> Dict[str, Any]:
        """Direct work discovery for ContentManagementAgent using KB analysis"""
        try:
            # Get the current knowledge base ID from the orchestrator
            current_kb_id = getattr(self.orchestrator, 'knowledge_base_id', None)
            if not current_kb_id:
                # Fallback: Try to get the default KB ID from environment or use 1
                import os
                current_kb_id = os.getenv('DEFAULT_KNOWLEDGE_BASE_ID', '1')
            
            # Create a minimal state for work discovery
            work_state = {
                "messages": [],
                "agent_messages": [],
                "current_agent": "ContentManagement",
                "recursions": 0,
                "knowledge_base_id": str(current_kb_id),
                "execution_mode": "autonomous_swarming"
            }
            
            # Get the agent directly from orchestrator
            agent = self.orchestrator.content_manager
            
            # Call the NEW knowledge base analysis method
            available_work = agent._analyze_knowledge_base_gaps(work_state)
            
            if available_work:
                # Execute the first work item using new KB-focused execution
                work_item = available_work[0]
                
                try:
                    execution_result = agent._execute_kb_work_to_completion(work_item, work_state)
                    if execution_result.get("success"):
                        return {
                            "found_work": True,
                            "message": f"Completed KB work: {work_item.get('title', 'Unknown')} - {execution_result.get('work_type', 'unknown')}",
                            "work_item": work_item,
                            "execution_result": execution_result
                        }
                    else:
                        return {
                            "found_work": True,
                            "message": f"Found KB work but execution failed: {work_item.get('title', 'Unknown')}",
                            "work_item": work_item,
                            "execution_error": execution_result.get("error", "Unknown error")
                        }
                except Exception as exec_error:
                    return {
                        "found_work": True,
                        "message": f"KB work execution error: {work_item.get('title', 'Unknown')} - Error: {str(exec_error)}",
                        "work_item": work_item,
                        "execution_error": str(exec_error)
                    }
            else:
                return {
                    "found_work": False,
                    "message": "No knowledge base improvement work identified"
                }
                
        except Exception as e:
            return {
                "found_work": False,
                "message": f"Work discovery error: {str(e)}"
            }
    
    def _call_content_creator_work_discovery(self) -> Dict[str, Any]:
        """Direct work discovery for ContentCreatorAgent - Use agent's own GitLab scanning"""
        try:
            # Let the agent handle its own work discovery using its new scanning methods
            agent = self.orchestrator.content_creator
            
            # Create a minimal state for the agent
            work_state = AgentState(
                current_kb_id=getattr(self.orchestrator, 'knowledge_base_id', '1'),
                agent_username="content-creator-agent"
            )
            
            # Check assigned work first
            assigned_work = agent._scan_assigned_gitlab_work()
            if assigned_work.get("found_work", False):
                return assigned_work
            
            # Then check available work
            available_work = agent._scan_available_gitlab_work()
            if available_work.get("found_work", False):
                return available_work
            
            # Fallback to autonomous content gap analysis
            return agent.analyze_content_gaps(work_state)
        except Exception as e:
            return {"found_work": False, "message": f"Error: {str(e)}"}

    def _call_content_planner_work_discovery(self) -> Dict[str, Any]:
        """Direct work discovery for ContentPlannerAgent - Use agent's own GitLab scanning"""
        try:
            # Let the agent handle its own work discovery using its new scanning methods
            agent = self.orchestrator.content_planner
            
            # Create a minimal state for the agent
            work_state = AgentState(
                current_kb_id=getattr(self.orchestrator, 'knowledge_base_id', '1'),
                agent_username="content-planner-agent"
            )
            
            # Check assigned work first
            assigned_work = agent._scan_assigned_gitlab_work()
            if assigned_work.get("found_work", False):
                return assigned_work
            
            # Then check available work
            available_work = agent._scan_available_gitlab_work()
            if available_work.get("found_work", False):
                return available_work
            
            # Fallback to autonomous content gap analysis
            return agent.analyze_content_gaps(work_state)
        except Exception as e:
            return {"found_work": False, "message": f"Error: {str(e)}"}

    def _call_content_reviewer_work_discovery(self) -> Dict[str, Any]:
        """Direct work discovery for ContentReviewerAgent - Use agent's own GitLab scanning"""
        try:
            # Let the agent handle its own work discovery using its new scanning methods
            agent = self.orchestrator.content_reviewer
            
            # Create a minimal state for the agent
            work_state = AgentState(
                current_kb_id=getattr(self.orchestrator, 'knowledge_base_id', '1'),
                agent_username="content-reviewer-agent"
            )
            
            # Check assigned work first
            assigned_work = agent._scan_assigned_gitlab_work()
            if assigned_work.get("found_work", False):
                return assigned_work
            
            # Then check available work
            available_work = agent._scan_available_gitlab_work()
            if available_work.get("found_work", False):
                return available_work
            
            # Fallback to autonomous content gap analysis
            return agent.analyze_content_gaps(work_state)
        except Exception as e:
            return {"found_work": False, "message": f"Error: {str(e)}"}
            work_result = self._discover_agent_work("content-reviewer-agent", ["review", "qa", "quality-assurance", "quality-review", "validation"])
            if work_result.get("found_work", False):
                return work_result
            
            # Fallback to autonomous content gap analysis
            return self.orchestrator.content_reviewer.analyze_content_gaps()
        except Exception as e:
            return {"found_work": False, "message": f"Error: {str(e)}"}
    
    def _call_content_retrieval_work_discovery(self) -> Dict[str, Any]:
        """Direct work discovery for ContentRetrievalAgent - GitLab issues first, then content gaps"""
        try:
            # First check GitLab for existing issues this agent can work on
            work_result = self._discover_agent_work("content-retrieval-agent", ["research", "analysis", "retrieval", "data-gathering"])
            if work_result.get("found_work", False):
                return work_result
            
            # Fallback to autonomous content gap analysis
            return self.orchestrator.content_retrieval.analyze_content_gaps()
        except Exception as e:
            return {"found_work": False, "message": f"Error: {str(e)}"}
    
    def _call_supervisor_work_discovery(self) -> Dict[str, Any]:
        """Direct work discovery for SupervisorAgent"""
        try:
            # Get the supervisor agent directly
            agent = self.orchestrator.supervisor
            
            # Create a minimal state for work discovery
            work_state = {
                "messages": [],
                "agent_messages": [],
                "current_agent": "Supervisor",
                "recursions": 0
            }
            
            # Check if supervisor needs to create GitLab projects for available KBs
            # This would scan for KBs that don't have GitLab projects yet
            return {
                "found_work": False,
                "message": "Supervisor checking for work orchestration needs"
            }
        except Exception as e:
            return {"found_work": False, "message": f"Error: {str(e)}"}
    
    def _discover_agent_work(self, agent_username: str, relevant_labels: List[str]) -> Dict[str, Any]:
        """Generic work discovery method for any agent using GitLab"""
        try:
            # Get GitLab operations instance
            from operations.gitlab_operations import GitLabOperations
            gitlab_ops = GitLabOperations()
            
            # Get all projects to search for work
            projects = gitlab_ops.get_projects_list()
            
            for project in projects:
                project_id = project.get("id")
                if not project_id:
                    continue
                
                # Get open issues for this project
                issues = gitlab_ops.get_project_issues(project_id, state="opened")
                
                # Look for issues that this agent can handle (autonomous work discovery)
                for issue in issues:
                    assigned_users = issue.get("assignees", [])
                    issue_labels = issue.get("labels", [])
                    
                    # Check if this agent can handle this work
                    has_relevant_label = any(label in issue_labels for label in relevant_labels)
                    
                    # Priority 1: Issues assigned to this agent
                    agent_assigned = any(user.get("username") == agent_username for user in assigned_users)
                    
                    # Priority 2: Unassigned issues with relevant labels (autonomous pickup)
                    is_unassigned = len(assigned_users) == 0
                    
                    # Priority 3: Issues not in progress by other agents
                    not_in_progress = "in-progress" not in issue_labels
                    
                    # Agent can take this work if:
                    # 1. Assigned to them, OR
                    # 2. Has relevant labels AND (unassigned OR not in progress)
                    can_take_work = (agent_assigned and has_relevant_label) or \
                                   (has_relevant_label and (is_unassigned or not_in_progress))
                    
                    if can_take_work:
                        return {
                            "found_work": True,
                            "message": f"Found work: {issue.get('title')} (#{issue.get('iid')})",
                            "work_item": {
                                "id": issue.get("id"),
                                "iid": issue.get("iid"),
                                "project_id": project_id,
                                "title": issue.get("title"),
                                "description": issue.get("description"),
                                "labels": issue_labels,
                                "assignees": assigned_users,
                                "state": issue.get("state"),
                                "web_url": issue.get("web_url"),
                                "created_at": issue.get("created_at"),
                                "updated_at": issue.get("updated_at")
                            }
                        }
            
            return {
                "found_work": False,
                "message": f"No available work items found for {agent_username} with capabilities: {relevant_labels}"
            }
            
        except Exception as e:
            return {
                "found_work": False,
                "message": f"Error discovering work for {agent_username}: {str(e)}"
            }
        
    def _execute_agent_work(self, agent_name: str, work_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the work found by an agent"""
        print(f"DEBUG: _execute_agent_work method called for {agent_name}")
        try:
            work_type = work_result.get("work_type", "unknown")
            work_details = work_result.get("work_details", {})
            
            print(f"DEBUG: _execute_agent_work called with agent_name={agent_name}, work_type={work_type}")
            
            # Get the appropriate agent
            agent = None
            if agent_name == "ContentCreatorAgent":
                agent = self.orchestrator.content_creator
            elif agent_name == "ContentPlannerAgent":
                agent = self.orchestrator.content_planner
            elif agent_name == "ContentReviewerAgent":
                agent = self.orchestrator.content_reviewer
            elif agent_name == "ContentRetrievalAgent":
                agent = self.orchestrator.content_retrieval
            elif agent_name == "ContentManagementAgent":
                agent = self.orchestrator.content_manager
            elif agent_name == "SupervisorAgent":
                agent = self.orchestrator.supervisor
            else:
                return {"success": False, "error": f"Unknown agent: {agent_name}"}
            
            # Execute based on work type
            print(f"DEBUG: Checking execution routing for work_type={work_type}, agent_name={agent_name}")
            
            # Check if this is a GitLab issue (has work_item with GitLab properties)
            work_item = work_result.get("work_item")
            if work_item and "iid" in work_item and "project_id" in work_item:
                print(f"DEBUG: Routing to GitLab issue execution")
                return self._execute_gitlab_issue_work(agent, work_item, agent_name)
            elif work_type == "autonomous_strategic" and agent_name == "ContentCreatorAgent":
                # Execute strategic content creation
                print(f"DEBUG: Routing to _execute_strategic_content_creation")
                return self._execute_strategic_content_creation(agent, work_details)
            elif work_type == "autonomous_content_gaps" and agent_name == "ContentCreatorAgent":
                # Execute content gap filling
                return self._execute_content_gap_creation(agent, work_details)
            elif work_type == "autonomous_quality_review" and agent_name == "ContentReviewerAgent":
                # Execute quality review work
                return self._execute_quality_review_work(agent, work_details)
            elif work_type == "autonomous_structure_planning" and agent_name == "ContentPlannerAgent":
                # Execute structure planning work
                return self._execute_structure_planning_work(agent, work_details)
            elif work_type == "autonomous_research_gaps" and agent_name == "ContentRetrievalAgent":
                # Execute research work
                return self._execute_research_work(agent, work_details)
            else:
                # For now, log that work was created but not executed
                work_created = work_result.get("work_created", {})
                if work_created.get("created", False):
                    count = work_created.get("count", 0)
                    return {
                        "success": True, 
                        "summary": f"Created {count} GitLab work items for {work_type}",
                        "note": "Work items created - execution will happen in future cycles"
                    }
                else:
                    return {"success": False, "error": f"Unknown work type: {work_type}"}
            
        except Exception as e:
            print(f"DEBUG: Exception in _execute_agent_work for {agent_name}: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"Execution error: {str(e)}"}
    
    def _execute_gitlab_issue_work(self, agent, work_item: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Execute work for a GitLab issue using standardized agent entry points"""
        try:
            issue_id = work_item.get("iid")
            issue_title = work_item.get("title", "")
            project_id = work_item.get("project_id")
            
            print(f"DEBUG: Executing GitLab issue #{issue_id}: {issue_title}")
            
            # Create a work state for the execution
            work_state = AgentState(
                current_kb_id=project_id,
                kb_project_id=project_id,
                agent_username=agent_name.replace("Agent", "").lower()
            )
            
            # STANDARDIZED EXECUTION: All agents use their process() method
            print(f"DEBUG: Calling standardized process() method for {agent_name}")
            
            try:
                # All agents now use the standardized process() method
                result = agent.process(work_state)
                
                print(f"DEBUG: Agent {agent_name} execution completed")
                
                # Process method returns AgentState, so we need to extract success info
                if result:
                    return {
                        "success": True,
                        "summary": f"Successfully executed GitLab issue #{issue_id} using standardized process method",
                        "details": {"state_returned": True, "agent_name": agent_name}
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Agent {agent_name} process method returned None or empty result"
                    }
                    
            except Exception as agent_exception:
                print(f"DEBUG: Exception during {agent_name} execution: {agent_exception}")
                import traceback
                traceback.print_exc()
                return {
                    "success": False,
                    "error": f"Agent execution exception: {str(agent_exception)}"
                }
            
        except Exception as e:
            print(f"DEBUG: Exception in _execute_gitlab_issue_work: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"GitLab issue execution error: {str(e)}"}
    
    def _execute_strategic_content_creation(self, agent, work_details: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic content creation work"""
        try:
            import sys
            sys.stderr.write("DEBUG: _execute_strategic_content_creation called with work_details\n")
            sys.stderr.flush()
            print(f"DEBUG: _execute_strategic_content_creation called with work_details: {work_details}")
            opportunities = work_details.get("opportunities", [])
            if not opportunities:
                return {"success": False, "error": "No opportunities found"}
            
            # Take the first opportunity and create content for it
            opportunity = opportunities[0]
            description = opportunity.get("description", "Strategic content")
            
            # Use the ContentManagementAgent's strategic content execution
            content_manager = self.orchestrator.content_manager
            if hasattr(content_manager, '_execute_strategic_content_work'):
                # Create a work item for strategic content with proper structure
                strategic_work = {
                    "type": "strategic_content",
                    "description": description,
                    "priority": opportunity.get("priority", "medium"),
                    "scope": "content_creation",
                    "opportunities": [opportunity]  # Pass the full opportunity structure
                }
                
                # Create a minimal state for the execution (KB ID now comes from environment)
                work_state = AgentState(
                    messages=[],
                    agent_messages=[],
                    current_agent="ContentCreatorAgent",
                    recursions=0,
                    knowledge_base_id=None,  # No longer needed - method uses environment
                    execution_mode="autonomous_strategic_content"
                )
                
                # Execute the strategic content work (KB ID comes from environment)
                result = content_manager._execute_strategic_content_work(strategic_work, work_state)
                if result:  # _execute_strategic_content_work returns bool, not dict
                    return {
                        "success": True,
                        "summary": f"Created strategic content: {description}",
                        "article_title": description
                    }
                else:
                    return {"success": False, "error": "Strategic content creation returned False"}
            else:
                return {"success": False, "error": "Strategic content execution method not available"}
                
        except Exception as e:
            return {"success": False, "error": f"Strategic content execution error: {str(e)}"}
    
    def _execute_content_gap_creation(self, agent, work_details: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content gap creation work"""
        # For now, just report that work items were created
        return {"success": True, "summary": "Content gap work items created"}
    
    def _execute_quality_review_work(self, agent, work_details: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quality review work"""
        # For now, just report that work items were created  
        return {"success": True, "summary": "Quality review work items created"}
    
    def _execute_structure_planning_work(self, agent, work_details: Dict[str, Any]) -> Dict[str, Any]:
        """Execute structure planning work"""
        # For now, just report that work items were created
        return {"success": True, "summary": "Structure planning work items created"}
    
    def _execute_research_work(self, agent, work_details: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research work"""
        # For now, just report that work items were created
        return {"success": True, "summary": "Research work items created"}

    def run_continuous_autonomous_mode(self, cycle_interval=30):
        """Run agents in continuous autonomous mode"""
        logger.info(f"🚀 Starting continuous autonomous mode with {cycle_interval}s interval")
        safe_print("🚀 Starting Continuous Autonomous Agent Mode")
        safe_print("=" * 80)
        safe_print("🎯 Autonomous Operation:")
        safe_print("   • Agents scan for and self-select appropriate work automatically")
        safe_print("   • Agents use GitLab comments to ask questions and communicate")
        safe_print("   • Content planning, creation, and review happen autonomously") 
        safe_print("   • Supervisor coordinates and manages quality gates")
        safe_print("   • All collaboration happens through GitLab workflows")
        safe_print("   • PostgreSQL maintains full audit trail")
        safe_print(f"   • Cycle interval: {cycle_interval} seconds")
        safe_print("=" * 80)
        
        self.is_running = True
        consecutive_idle_cycles = 0
        max_idle_cycles = 5  # Increase interval after 5 idle cycles
        
        logger.info(f"Autonomous mode starting: max_idle_cycles={max_idle_cycles}")
        
        try:
            while self.is_running:
                logger.debug(f"Starting cycle {self.cycle_count + 1}, consecutive_idle={consecutive_idle_cycles}")
                work_found = self.run_autonomous_cycle()
                
                if work_found:
                    consecutive_idle_cycles = 0  # Reset idle counter
                    logger.info(f"🎯 Work found in cycle {self.cycle_count}, resetting idle counter")
                    print(f"🎯 Work in progress - checking again in {cycle_interval} seconds...")
                else:
                    consecutive_idle_cycles += 1
                    logger.debug(f"No work found, consecutive_idle_cycles now: {consecutive_idle_cycles}")
                    
                    if consecutive_idle_cycles >= max_idle_cycles:
                        # Increase interval for idle periods to reduce resource usage
                        extended_interval = cycle_interval * 3
                        logger.info(f"💤 Extended idle period activated: {extended_interval}s interval after {consecutive_idle_cycles} idle cycles")
                        print(f"💤 Extended idle period - checking again in {extended_interval} seconds...")
                        print("   💡 Tip: Create GitLab issues for agents to discover and execute")
                        time.sleep(extended_interval)
                        consecutive_idle_cycles = 0  # Reset after extended wait
                        continue
                    else:
                        logger.debug(f"💤 Regular idle cycle {consecutive_idle_cycles}/{max_idle_cycles}")
                        print(f"💤 No active work - checking again in {cycle_interval} seconds...")
                
                # Wait for next cycle
                logger.debug(f"Sleeping for {cycle_interval} seconds before next cycle")
                time.sleep(cycle_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Autonomous mode interrupted by user (KeyboardInterrupt)")
            print("\n🛑 Autonomous mode interrupted by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Unexpected error in continuous autonomous mode: {e}", exc_info=True)
            print(f"\n❌ Unexpected error: {e}")
            self.stop()
            raise
            
    def run_single_cycle(self):
        """Run a single autonomous cycle"""
        logger.info("🔄 Starting single autonomous cycle")
        print("🔄 Running Single Autonomous Cycle")
        print("=" * 50)
        
        work_found = self.run_autonomous_cycle()
        
        if work_found:
            logger.info("✅ Single cycle completed with work processed")
            print("✅ Autonomous cycle completed - work was processed")
        else:
            logger.info("💤 Single cycle completed with no work available")
            print("💤 Autonomous cycle completed - no work available")
            
        return work_found
        
    def stop(self):
        """Stop autonomous mode"""
        logger.info("🛑 Stopping autonomous agent swarm")
        self.is_running = False
        print("🛑 Autonomous Agent Swarm stopped")
        
    def get_status(self):
        """Get current swarm status"""
        logger.debug("Getting swarm status")
        session_summary = None
        if hasattr(self.orchestrator, 'get_session_summary'):
            try:
                session_summary = self.orchestrator.get_session_summary()
                logger.debug(f"Session summary retrieved: {session_summary}")
            except Exception as e:
                logger.warning(f"Failed to get session summary: {e}")
            
        status = {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "session_active": session_summary.get('is_active', False) if session_summary else False
        }
        
        logger.debug(f"Status: {status}")
        return status

    def discover_available_kb_projects(self):
        """
        Discover GitLab projects linked to knowledge bases that are ready for content work.
        This replaces the old 'Define KB' gate with GitLab project availability checking.
        
        Returns:
            List of available KB projects ready for agent work
        """
        try:
            logger.info("🔍 Discovering available KB projects for agent work")
            
            # Get all knowledge bases with GitLab projects
            from operations.knowledge_base_operations import KnowledgeBaseOperations
            kb_ops = KnowledgeBaseOperations()
            all_kbs = kb_ops.get_all_knowledge_bases()
            
            available_projects = []
            
            for kb in all_kbs:
                # Check if KB has a linked GitLab project
                if hasattr(kb, 'gitlab_project_id') and kb.gitlab_project_id:
                    try:
                        # Verify the GitLab project exists and is accessible
                        from operations.gitlab_operations import GitLabOperations
                        gitlab_ops = GitLabOperations()
                        project_details = gitlab_ops.get_project_details(str(kb.gitlab_project_id))
                        
                        if project_details:
                            project_info = {
                                "kb_id": kb.id,
                                "kb_name": kb.name,
                                "kb_description": kb.description,
                                "kb_status": getattr(kb, 'status', 'unknown'),
                                "gitlab_project_id": kb.gitlab_project_id,
                                "gitlab_project_name": project_details.get('name'),
                                "gitlab_project_url": project_details.get('web_url'),
                                "project_created": project_details.get('created_at'),
                                "ready_for_work": True
                            }
                            available_projects.append(project_info)
                            logger.debug(f"✅ Available KB project: {kb.name} (Project ID: {kb.gitlab_project_id})")
                        else:
                            logger.warning(f"⚠️ KB {kb.name} has GitLab project ID {kb.gitlab_project_id} but project not accessible")
                    except Exception as e:
                        logger.error(f"❌ Error checking GitLab project {kb.gitlab_project_id} for KB {kb.name}: {e}")
                else:
                    logger.debug(f"📋 KB {kb.name} (ID: {kb.id}) has no GitLab project - not ready for agent work")
            
            logger.info(f"🎯 Found {len(available_projects)} KB projects ready for agent work")
            
            # Log available projects for debugging
            if available_projects:
                logger.info("📋 Available KB Projects:")
                for project in available_projects:
                    logger.info(f"   • {project['kb_name']} (Status: {project['kb_status']}) → GitLab Project: {project['gitlab_project_id']}")
            else:
                logger.info("💤 No KB projects currently available for agent work")
            
            return available_projects
        
        except Exception as e:
            logger.error(f"❌ Error discovering KB projects: {e}")
            return []

    def _format_available_projects(self, projects):
        """Format available projects for agent consumption"""
        if not projects:
            return "No KB projects currently available."
        
        formatted = []
        for project in projects:
            formatted.append(f"- KB: {project['kb_name']} | Project: {project['gitlab_project_name']} | URL: {project['gitlab_project_url']}")
        
        return "\n".join(formatted)

    def display_knowledge_base_summary(self):
        """Display a comprehensive summary of the current knowledge base in context"""
        try:
            logger.info("📊 Generating knowledge base summary for current context")
            safe_print("📊 KNOWLEDGE BASE ANALYSIS SUMMARY")
            safe_print("=" * 80)
            
            # Get the current knowledge base ID from context
            current_kb_id = getattr(self.orchestrator, 'knowledge_base_id', None)
            if not current_kb_id:
                # Fallback: Try to get the default KB ID from environment or use 1
                import os
                current_kb_id = os.getenv('DEFAULT_KNOWLEDGE_BASE_ID', '1')
                safe_print(f"⚠️ Using fallback KB ID: {current_kb_id}")
            
            safe_print(f"🎯 CURRENT KNOWLEDGE BASE CONTEXT: ID {current_kb_id}")
            safe_print("")
            
            # Get knowledge base operations
            from operations.knowledge_base_operations import KnowledgeBaseOperations
            kb_ops = KnowledgeBaseOperations()
            
            # Get the specific knowledge base details
            try:
                all_kbs = kb_ops.get_all_knowledge_bases()
                current_kb = None
                for kb in all_kbs:
                    if str(kb.id) == str(current_kb_id):
                        current_kb = kb
                        break
                
                if not current_kb:
                    safe_print(f"❌ Knowledge base with ID {current_kb_id} not found")
                    return
                
                # Display current KB details
                safe_print(f"📚 KNOWLEDGE BASE: {current_kb.name}")
                safe_print(f"   ID: {current_kb.id}")
                safe_print(f"   Description: {current_kb.description[:100]}{'...' if len(current_kb.description) > 100 else ''}")
                safe_print(f"   Status: {getattr(current_kb, 'status', 'unknown')}")
                safe_print(f"   GitLab Project: {getattr(current_kb, 'gitlab_project_id', 'Not linked')}")
                safe_print("-" * 60)
                
                # Get articles summary for current KB
                all_articles = kb_ops.get_articles_by_knowledge_base_id(str(current_kb.id))
                root_articles = kb_ops.get_root_level_articles(str(current_kb.id))
                
                # Calculate article hierarchy
                total_articles = len(all_articles)
                root_count = len(root_articles)
                child_articles = [article for article in all_articles if article.get('parent_id') is not None]
                child_count = len(child_articles)
                
                safe_print(f"📄 ARTICLE SUMMARY:")
                safe_print(f"   • Total Articles: {total_articles}")
                safe_print(f"   • Root Articles: {root_count}")
                safe_print(f"   • Sub/Child Articles: {child_count}")
                
                # Display root articles if any exist
                if root_articles:
                    safe_print(f"   📋 Root Articles:")
                    for j, root_article in enumerate(root_articles[:5], 1):  # Show first 5
                        title = root_article[2] if len(root_article) > 2 else "Untitled"  # Assuming title is at index 2
                        safe_print(f"      {j}. {title[:50]}{'...' if len(title) > 50 else ''}")
                    if len(root_articles) > 5:
                        safe_print(f"      ... and {len(root_articles) - 5} more root articles")
                else:
                    safe_print(f"   📋 No root articles found")
                
                # Get and display tags with usage count for current KB
                tags_with_usage = kb_ops.get_tags_with_usage_count(str(current_kb.id))
                
                safe_print(f"🏷️ TAG SUMMARY:")
                safe_print(f"   • Total Tags: {len(tags_with_usage)}")
                
                if tags_with_usage:
                    # Show top 10 most used tags
                    safe_print(f"   📈 Most Used Tags:")
                    for j, tag in enumerate(tags_with_usage[:10], 1):
                        safe_print(f"      {j}. {tag.name} (used {tag.usage_count} times)")
                    
                    if len(tags_with_usage) > 10:
                        safe_print(f"      ... and {len(tags_with_usage) - 10} more tags")
                    
                    # Calculate tag usage statistics
                    total_tag_usage = sum(tag.usage_count for tag in tags_with_usage)
                    unused_tags = len([tag for tag in tags_with_usage if tag.usage_count == 0])
                    
                    safe_print(f"   📊 Tag Statistics:")
                    safe_print(f"      • Total Tag Applications: {total_tag_usage}")
                    safe_print(f"      • Average Tags per Article: {total_tag_usage / max(total_articles, 1):.1f}")
                    safe_print(f"      • Unused Tags: {unused_tags}")
                else:
                    safe_print(f"   📊 No tags found for this knowledge base")
                
                # Show article hierarchy structure if available
                try:
                    hierarchy = kb_ops.get_article_hierarchy(str(current_kb.id))
                    if hierarchy:
                        safe_print(f"🌳 ARTICLE HIERARCHY STRUCTURE:")
                        # Group by hierarchy level for better visualization
                        levels = {}
                        for article in hierarchy:
                            level = article.get('level', 0)
                            if level not in levels:
                                levels[level] = []
                            levels[level].append(article)
                        
                        for level in sorted(levels.keys())[:3]:  # Show first 3 levels
                            articles_at_level = levels[level]
                            safe_print(f"      Level {level}: {len(articles_at_level)} articles")
                            
                            # Show first few articles at each level
                            for article in articles_at_level[:3]:
                                title = article.get('title', 'Untitled')
                                indent = "  " * (level + 1)
                                safe_print(f"      {indent}• {title[:40]}{'...' if len(title) > 40 else ''}")
                            
                            if len(articles_at_level) > 3:
                                safe_print(f"      {indent}... and {len(articles_at_level) - 3} more")
                    else:
                        safe_print(f"   🌳 No article hierarchy found")
                except Exception as hierarchy_error:
                    safe_print(f"   ⚠️ Could not load article hierarchy: {hierarchy_error}")
                
                # GitLab Project Summary
                safe_print(f"🔗 GITLAB PROJECT SUMMARY:")
                gitlab_project_id = getattr(current_kb, 'gitlab_project_id', None)
                if gitlab_project_id:
                    try:
                        from operations.gitlab_operations import GitLabOperations
                        gitlab_ops = GitLabOperations()
                        project_details = gitlab_ops.get_project_details(str(gitlab_project_id))
                        
                        if project_details:
                            safe_print(f"   • Project ID: {gitlab_project_id}")
                            safe_print(f"   • Project Name: {project_details.get('name', 'Unknown')}")
                            safe_print(f"   • Project URL: {project_details.get('web_url', 'Not available')}")
                            safe_print(f"   • Created: {project_details.get('created_at', 'Unknown')}")
                            safe_print(f"   • Last Activity: {project_details.get('last_activity_at', 'Unknown')}")
                            safe_print(f"   • Visibility: {project_details.get('visibility', 'Unknown')}")
                            safe_print(f"   • Default Branch: {project_details.get('default_branch', 'Unknown')}")
                            
                            # Get additional project statistics if available
                            if 'statistics' in project_details:
                                stats = project_details['statistics']
                                safe_print(f"   • Repository Size: {stats.get('repository_size', 0)} bytes")
                                safe_print(f"   • Commit Count: {stats.get('commit_count', 0)}")
                            
                            # Check for open issues/merge requests
                            open_issues = project_details.get('open_issues_count', 0)
                            
                            # If open_issues_count is not available or is 0, try to get actual count
                            if open_issues == 0:
                                try:
                                    # Get actual issues to provide accurate count
                                    issues = self.gitlab_operations.get_project_issues(str(gitlab_project_id), state="opened")
                                    if issues:
                                        open_issues = len(issues)
                                except Exception as issue_count_error:
                                    logger.debug(f"Could not get accurate issue count: {issue_count_error}")
                            
                            safe_print(f"   • Open Issues: {open_issues}")
                            
                            # Project status
                            if project_details.get('archived', False):
                                safe_print(f"   ⚠️ Status: Archived")
                            else:
                                safe_print(f"   ✅ Status: Active")
                                
                        else:
                            safe_print(f"   ❌ GitLab project {gitlab_project_id} not accessible or not found")
                            
                    except Exception as gitlab_error:
                        safe_print(f"   ❌ Error accessing GitLab project {gitlab_project_id}: {gitlab_error}")
                        logger.error(f"GitLab project access error: {gitlab_error}")
                else:
                    safe_print(f"   📋 No GitLab project linked to this knowledge base")
                    safe_print(f"   💡 Link a GitLab project to enable agent collaboration features")
                
                # Summary statistics for current KB
                safe_print("")
                safe_print("🌟 KNOWLEDGE BASE DATABASE SUMMARY")
                safe_print("-" * 40)
                safe_print(f"📚 Knowledge Base: {current_kb.name}")
                safe_print(f"📄 Total Articles: {total_articles}")
                safe_print(f"🏷️ Total Tags: {len(tags_with_usage)}")
                if total_articles > 0:
                    safe_print(f"📊 Content Depth: {child_count}/{total_articles} articles have sub-content ({(child_count/total_articles)*100:.1f}%)")
                safe_print("-" * 40)
                
            except Exception as kb_error:
                safe_print(f"   ❌ Error analyzing current KB: {kb_error}")
                logger.error(f"Error analyzing current KB {current_kb_id}: {kb_error}")
            
            logger.info("✅ Knowledge base summary completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error generating knowledge base summary: {e}")
            safe_print(f"❌ Error generating knowledge base summary: {e}")

def main():
    logger.info("=" * 80)
    logger.info("🔥 AI ADAPTIVE KNOWLEDGE BASE - AUTONOMOUS AGENT SWARM STARTING")
    logger.info("🚀 PostgreSQL State Management | GitLab Coordination | Autonomous Execution")
    logger.info("=" * 80)
    
    safe_print("=" * 80)
    safe_print("🔥 AI ADAPTIVE KNOWLEDGE BASE - AUTONOMOUS AGENT SWARM")
    safe_print("🚀 PostgreSQL State Management | GitLab Coordination | Autonomous Execution")
    safe_print("=" * 80)
    
    # Initialize the swarm
    logger.info("Initializing autonomous agent swarm")
    try:
        swarm = AutonomousAgentSwarm()
        swarm.initialize_agents()
        logger.info("✅ Swarm initialization completed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize swarm: {e}", exc_info=True)
        safe_print(f"❌ Failed to initialize swarm: {e}")
        return
    
    safe_print("💬 Commands:")
    safe_print("   • Type 'start' to begin continuous autonomous mode")
    safe_print("   • Type 'cycle' to run a single autonomous cycle")
    safe_print("   • Type 'status' to show swarm status")
    safe_print("   • Type 'stop' to stop autonomous mode")
    safe_print("   • Type '/q' or '/quit' to exit")
    safe_print("=" * 80)
    
    while True:
        try:
            user_input = input("\n> ").strip().lower()
            safe_print("")
            logger.debug(f"User input received: '{user_input}'")
            
            if user_input in ["/q", "/quit", "quit", "exit"]:
                logger.info("👋 User initiated shutdown")
                safe_print("👋 Autonomous Agent Swarm shutting down. Goodbye!")
                swarm.stop()
                break
                
            elif user_input == "start":
                logger.info("🚀 User requested start of continuous autonomous mode")
                safe_print("🚀 Starting continuous autonomous mode...")
                safe_print("   Press Ctrl+C to stop autonomous mode")
                swarm.run_continuous_autonomous_mode(cycle_interval=30)
                
            elif user_input == "cycle":
                logger.info("🔄 User requested single cycle execution")
                work_found = swarm.run_single_cycle()
                if work_found:
                    logger.info("🎯 Single cycle completed with work found")
                    safe_print("🎯 Tip: Type 'start' for continuous autonomous mode")
                else:
                    logger.info("💤 Single cycle completed with no work found")
                    safe_print("💡 Ensure Supervisor has created GitLab project for KB first")
                    
            elif user_input == "status":
                logger.debug("📊 User requested status")
                status = swarm.get_status()
                safe_print("📊 Autonomous Agent Swarm Status:")
                safe_print(f"   • Running: {status['is_running']}")
                safe_print(f"   • Cycles Completed: {status['cycle_count']}")
                safe_print(f"   • Session Active: {status['session_active']}")
                logger.info(f"Status displayed to user: {status}")
                
            elif user_input == "stop":
                logger.info("🛑 User requested stop")
                swarm.stop()
                safe_print("✅ Autonomous mode stopped")
                
            else:
                logger.debug(f"❓ Unknown command received: '{user_input}'")
                safe_print("❓ Unknown command. Available commands:")
                safe_print("   • start - Begin continuous autonomous mode")
                safe_print("   • cycle - Run single autonomous cycle") 
                safe_print("   • status - Show swarm status")
                safe_print("   • stop - Stop autonomous mode")
                safe_print("   • quit - Exit program")

        except KeyboardInterrupt:
            logger.warning("⚠ User interrupted with KeyboardInterrupt")
            safe_print("\n\n⚠ Interrupted by user.")
            swarm.stop()
            continue
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}", exc_info=True)
            safe_print(f"❌ Error: {e}")
            safe_print("💡 Tip: Type 'quit' to exit or 'status' to check swarm state")
            continue

if __name__ == "__main__":
    main()
