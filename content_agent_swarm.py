import sys
import os
import datetime
import warnings
import time
import logging
from dotenv import load_dotenv

# Suppress Pydantic warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')

# Configure comprehensive logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/content_agent_swarm.log', mode='a')
    ]
)

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
        print("🤖 Initializing Autonomous Agent Swarm...")
        print("=" * 80)
        print("🎯 Agent Initialization:")
        print("   • ContentManagement Agent → Prescriptive workflow orchestrator & KB operations")
        print("   • ContentPlanner Agent    → Strategic planning & architecture") 
        print("   • ContentCreator Agent    → Content generation & development")
        print("   • ContentReviewer Agent   → Quality assurance & optimization")
        print("   • ContentRetrieval Agent  → Research & analysis")
        print("   • Supervisor Agent        → Scrum Master coordination")
        print("=" * 80)
        print("⚡ AUTONOMOUS CONTENT GENERATION:")
        print("   • ContentManagement Agent defines prescriptive approach for all agents")
        print("   • When 'Define KB' gate closes → ContentManagement creates complete work pipeline")
        print("   • Other agents autonomously execute ContentManagement-created work items")
        print("=" * 80)
        print("🚪 DEFINE KB GATE:")
        print("   • 'Define KB' work item must be CLOSED before content creation")
        print("   • Agents contribute planning input while 'Define KB' is open")
        print("   • ContentManagement automatically creates content pipeline after gate closure")
        print("=" * 80)
        print("🌐 MULTI-KB ENVIRONMENT:")
        print("   • Agents work across MULTIPLE knowledge bases")
        print("   • Each work item must specify target KB context")
        print("   • Agents verify KB context before executing operations")
        print("=" * 80)
        logger.info("✅ Agent initialization display completed")
        
    def run_autonomous_cycle(self):
        """Run one cycle of autonomous agent work discovery and execution"""
        self.cycle_count += 1
        logger.info(f"🔄 Starting autonomous cycle #{self.cycle_count}")
        print(f"🔄 Autonomous Cycle #{self.cycle_count} - {datetime.datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        # Each agent checks GitLab for their assigned work and executes autonomously
        agents_with_work = 0
        
        # Define agent work patterns for more targeted GitLab queries
        agent_configs = {
            "ContentManagementAgent": {
                "labels": ["kb-management", "prescriptive-workflow", "gate-monitoring"],
                "priorities": ["high", "urgent"],
                "focus": "Prescriptive workflow orchestration, gate monitoring, and autonomous work item creation"
            },
            "ContentPlannerAgent": {
                "labels": ["planning", "architecture", "strategy"],
                "priorities": ["high", "medium"],
                "focus": "Strategic planning and sprint coordination"
            },
            "ContentCreatorAgent": {
                "labels": ["content-creation", "development", "writing"],
                "priorities": ["medium", "high"],
                "focus": "Content generation and development tasks"
            },
            "ContentReviewerAgent": {
                "labels": ["review", "qa", "quality-assurance"],
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
            print(f"  📋 {agent_name}: Checking for GitLab work assignments...")
            print(f"      Focus: {config['focus']}")
            
            try:
                # Real GitLab work discovery implementation
                labels_str = ", ".join(config['labels'])
                priorities_str = ", ".join(config['priorities'])
                
                logger.debug(f"Agent {agent_name} - Labels: {labels_str}, Priorities: {priorities_str}")
                
                work_discovery_message = f"""
                Check GitLab for work items assigned to {agent_name} across MULTIPLE KNOWLEDGE BASES.
                
                🌐 MULTI-KB CONTEXT REQUIREMENT:
                You work across multiple knowledge bases. Every work item MUST specify target KB context.
                Always verify which knowledge base you're working with before proceeding.
                
                � CRITICAL WORKFLOW GATE - "Define KB" REQUIREMENT:
                Before creating ANY content, you MUST verify that the "Define KB: [KB Name]" work item is CLOSED.
                - If "Define KB" is still OPEN: You can contribute input and ask questions but CANNOT create content
                - If "Define KB" is CLOSED: You may proceed with content creation work items
                - Always check the "Define KB" status before processing any content creation tasks
                
                �📋 STANDARDIZED WORK ITEM NAMING:
                Look for work items with standardized naming conventions:
                - Define KB: [KB Name] - REQUIRED FIRST (must be closed before content creation)
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
                - Gate Check: Verify "Define KB" status before content creation
                
                Look for:
                - Open issues assigned to or labeled for this agent BY THE SUPERVISOR
                - High priority items needing immediate attention FROM SUPERVISOR
                - "Define KB" work items where you can contribute planning input
                - Content work items ONLY if corresponding "Define KB" is CLOSED
                - Work items with CLEAR KB CONTEXT specified
                
                If supervisor-created work is found:
                1. Check if there's a "Define KB: [KB Name]" work item for the target KB
                2. If "Define KB" is OPEN: Contribute input but do NOT create content
                3. If "Define KB" is CLOSED: Proceed with content creation work
                4. Verify the target knowledge base context from the work item title
                5. Process the highest priority item for the specified KB
                6. Update GitLab with progress including KB context and gate status
                
                If no supervisor work items exist, report waiting status.
                Report specific work item details, target KB context, and "Define KB" gate status.
                """
                
                logger.debug(f"Sending work discovery message to {agent_name}")
                result = self.orchestrator.process_message(work_discovery_message, "system")
                logger.debug(f"Received result from {agent_name}: {type(result)}")
                
                if result and hasattr(result, 'content'):
                    content_lower = result.content.lower()
                    logger.debug(f"Agent {agent_name} response content (first 100 chars): {result.content[:100]}...")
                    
                    if any(keyword in content_lower for keyword in [
                        "found issue", "processing", "assigned", "working on", 
                        "started", "updated", "completing"
                    ]):
                        agents_with_work += 1
                        logger.info(f"✅ {agent_name} found and is processing work items")
                        print(f"    ✅ Found and processing work items")
                        # Extract and display work summary if available
                        if "issue" in content_lower:
                            print(f"    📝 {result.content[:80]}...")
                            logger.debug(f"Work summary for {agent_name}: {result.content[:200]}")
                    else:
                        logger.debug(f"💤 {agent_name} reported no supervisor work items available")
                        print(f"    💤 No supervisor work items available - waiting for Supervisor to create work items")
                else:
                    logger.warning(f"⚠️ {agent_name} provided no response or invalid response format")
                    print(f"    ⚠️  No response from agent")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {agent_name}: {str(e)}", exc_info=True)
                print(f"    ❌ Error: {str(e)[:50]}...")
                # Continue with other agents even if one fails
                
        logger.info(f"📊 Cycle #{self.cycle_count} completed: {agents_with_work}/{len(agent_configs)} agents found work")
        print(f"📊 Cycle Summary: {agents_with_work}/{len(agent_configs)} agents found work")
        print("-" * 60)
        
        return agents_with_work > 0
        
    def run_continuous_autonomous_mode(self, cycle_interval=30):
        """Run agents in continuous autonomous mode"""
        logger.info(f"🚀 Starting continuous autonomous mode with {cycle_interval}s interval")
        print("🚀 Starting Continuous Autonomous Agent Mode")
        print("=" * 80)
        print("🎯 Autonomous Operation:")
        print("   • Agents discover work from GitLab automatically")
        print("   • Content planning, creation, and review happen autonomously") 
        print("   • Supervisor coordinates and manages quality gates")
        print("   • All collaboration happens through GitLab workflows")
        print("   • PostgreSQL maintains full audit trail")
        print(f"   • Cycle interval: {cycle_interval} seconds")
        print("=" * 80)
        
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

def main():
    logger.info("=" * 80)
    logger.info("🔥 AI ADAPTIVE KNOWLEDGE BASE - AUTONOMOUS AGENT SWARM STARTING")
    logger.info("🚀 PostgreSQL State Management | GitLab Coordination | Autonomous Execution")
    logger.info("=" * 80)
    
    print("=" * 80)
    print("🔥 AI ADAPTIVE KNOWLEDGE BASE - AUTONOMOUS AGENT SWARM")
    print("🚀 PostgreSQL State Management | GitLab Coordination | Autonomous Execution")
    print("=" * 80)
    
    # Initialize the swarm
    logger.info("Initializing autonomous agent swarm")
    try:
        swarm = AutonomousAgentSwarm()
        swarm.initialize_agents()
        logger.info("✅ Swarm initialization completed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize swarm: {e}", exc_info=True)
        print(f"❌ Failed to initialize swarm: {e}")
        return
    
    print("💬 Commands:")
    print("   • Type 'start' to begin continuous autonomous mode")
    print("   • Type 'cycle' to run a single autonomous cycle")
    print("   • Type 'status' to show swarm status")
    print("   • Type 'stop' to stop autonomous mode")
    print("   • Type '/q' or '/quit' to exit")
    print("=" * 80)
    
    while True:
        try:
            user_input = input("\n> ").strip().lower()
            print("")
            logger.debug(f"User input received: '{user_input}'")
            
            if user_input in ["/q", "/quit", "quit", "exit"]:
                logger.info("👋 User initiated shutdown")
                print("👋 Autonomous Agent Swarm shutting down. Goodbye!")
                swarm.stop()
                break
                
            elif user_input == "start":
                logger.info("🚀 User requested start of continuous autonomous mode")
                print("🚀 Starting continuous autonomous mode...")
                print("   Press Ctrl+C to stop autonomous mode")
                swarm.run_continuous_autonomous_mode(cycle_interval=30)
                
            elif user_input == "cycle":
                logger.info("🔄 User requested single cycle execution")
                work_found = swarm.run_single_cycle()
                if work_found:
                    logger.info("🎯 Single cycle completed with work found")
                    print("🎯 Tip: Type 'start' for continuous autonomous mode")
                else:
                    logger.info("💤 Single cycle completed with no work found")
                    print("💡 Ensure Supervisor has created 'Define KB: [KB Name]' work item first")
                    
            elif user_input == "status":
                logger.debug("📊 User requested status")
                status = swarm.get_status()
                print("📊 Autonomous Agent Swarm Status:")
                print(f"   • Running: {status['is_running']}")
                print(f"   • Cycles Completed: {status['cycle_count']}")
                print(f"   • Session Active: {status['session_active']}")
                logger.info(f"Status displayed to user: {status}")
                
            elif user_input == "stop":
                logger.info("🛑 User requested stop")
                swarm.stop()
                print("✅ Autonomous mode stopped")
                
            else:
                logger.debug(f"❓ Unknown command received: '{user_input}'")
                print("❓ Unknown command. Available commands:")
                print("   • start - Begin continuous autonomous mode")
                print("   • cycle - Run single autonomous cycle") 
                print("   • status - Show swarm status")
                print("   • stop - Stop autonomous mode")
                print("   • quit - Exit program")

        except KeyboardInterrupt:
            logger.warning("⚠ User interrupted with KeyboardInterrupt")
            print("\n\n⚠ Interrupted by user.")
            swarm.stop()
            continue
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}", exc_info=True)
            print(f"❌ Error: {e}")
            print("💡 Tip: Type 'quit' to exit or 'status' to check swarm state")
            continue

if __name__ == "__main__":
    main()
