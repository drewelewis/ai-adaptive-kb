import sys
import os
import datetime
import warnings
import time
from dotenv import load_dotenv

# Suppress Pydantic warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')

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
        self.orchestrator = Orchestrator()
        self.is_running = False
        self.cycle_count = 0
        
    def initialize_agents(self):
        """Initialize all autonomous agents"""
        print("🤖 Initializing Autonomous Agent Swarm...")
        print("=" * 80)
        print("🎯 Agent Initialization:")
        print("   • ContentManagement Agent → GitLab work discovery & KB operations")
        print("   • ContentPlanner Agent    → Strategic planning & architecture") 
        print("   • ContentCreator Agent    → Content generation & development")
        print("   • ContentReviewer Agent   → Quality assurance & optimization")
        print("   • ContentRetrieval Agent  → Research & analysis")
        print("   • Supervisor Agent        → Scrum Master coordination")
        print("=" * 80)
        
    def run_autonomous_cycle(self):
        """Run one cycle of autonomous agent work discovery and execution"""
        self.cycle_count += 1
        print(f"🔄 Autonomous Cycle #{self.cycle_count} - {datetime.datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        # Each agent checks GitLab for their assigned work and executes autonomously
        agents_with_work = 0
        
        # Define agent work patterns for more targeted GitLab queries
        agent_configs = {
            "ContentManagementAgent": {
                "labels": ["kb-management", "basic-operations"],
                "priorities": ["high", "urgent"],
                "focus": "KB CRUD operations and GitLab work tracking"
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
        
        for agent_name, config in agent_configs.items():
            print(f"  📋 {agent_name}: Checking for GitLab work assignments...")
            print(f"      Focus: {config['focus']}")
            
            try:
                # Real GitLab work discovery implementation
                labels_str = ", ".join(config['labels'])
                priorities_str = ", ".join(config['priorities'])
                
                work_discovery_message = f"""
                Check GitLab for work items assigned to {agent_name}.
                Search criteria:
                - Agent: {agent_name.lower()}
                - Labels: {labels_str}
                - Priorities: {priorities_str}
                - Focus area: {config['focus']}
                
                Look for:
                - Open issues assigned to or labeled for this agent
                - High priority items needing immediate attention
                - Blocked work that needs resolution
                
                If work is found, process the highest priority item and update GitLab with progress.
                Coordinate with other agents through GitLab issue comments as needed.
                Report specific work item details in your response.
                """
                
                result = self.orchestrator.process_message(work_discovery_message, "system")
                
                if result and hasattr(result, 'content'):
                    content_lower = result.content.lower()
                    if any(keyword in content_lower for keyword in [
                        "found issue", "processing", "assigned", "working on", 
                        "started", "updated", "completing"
                    ]):
                        agents_with_work += 1
                        print(f"    ✅ Found and processing work items")
                        # Extract and display work summary if available
                        if "issue" in content_lower:
                            print(f"    📝 {result.content[:80]}...")
                    else:
                        print(f"    💤 No work items available")
                else:
                    print(f"    ⚠️  No response from agent")
                    
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:50]}...")
                # Continue with other agents even if one fails
                
        print(f"📊 Cycle Summary: {agents_with_work}/{len(agent_configs)} agents found work")
        print("-" * 60)
        
        return agents_with_work > 0
        
    def run_continuous_autonomous_mode(self, cycle_interval=30):
        """Run agents in continuous autonomous mode"""
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
        
        try:
            while self.is_running:
                work_found = self.run_autonomous_cycle()
                
                if work_found:
                    consecutive_idle_cycles = 0  # Reset idle counter
                    print(f"🎯 Work in progress - checking again in {cycle_interval} seconds...")
                else:
                    consecutive_idle_cycles += 1
                    
                    if consecutive_idle_cycles >= max_idle_cycles:
                        # Increase interval for idle periods to reduce resource usage
                        extended_interval = cycle_interval * 3
                        print(f"💤 Extended idle period - checking again in {extended_interval} seconds...")
                        print("   💡 Tip: Create GitLab issues for agents to discover and execute")
                        time.sleep(extended_interval)
                        consecutive_idle_cycles = 0  # Reset after extended wait
                        continue
                    else:
                        print(f"💤 No active work - checking again in {cycle_interval} seconds...")
                
                # Wait for next cycle
                time.sleep(cycle_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Autonomous mode interrupted by user")
            self.stop()
            
    def run_single_cycle(self):
        """Run a single autonomous cycle"""
        print("🔄 Running Single Autonomous Cycle")
        print("=" * 50)
        
        work_found = self.run_autonomous_cycle()
        
        if work_found:
            print("✅ Autonomous cycle completed - work was processed")
        else:
            print("💤 Autonomous cycle completed - no work available")
            
        return work_found
        
    def stop(self):
        """Stop autonomous mode"""
        self.is_running = False
        print("🛑 Autonomous Agent Swarm stopped")
        
    def get_status(self):
        """Get current swarm status"""
        session_summary = None
        if hasattr(self.orchestrator, 'get_session_summary'):
            session_summary = self.orchestrator.get_session_summary()
            
        status = {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "session_active": session_summary.get('is_active', False) if session_summary else False
        }
        
        return status

def main():
    print("=" * 80)
    print("🔥 AI ADAPTIVE KNOWLEDGE BASE - AUTONOMOUS AGENT SWARM")
    print("🚀 PostgreSQL State Management | GitLab Coordination | Autonomous Execution")
    print("=" * 80)
    
    # Initialize the swarm
    swarm = AutonomousAgentSwarm()
    swarm.initialize_agents()
    
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
            
            if user_input in ["/q", "/quit", "quit", "exit"]:
                print("👋 Autonomous Agent Swarm shutting down. Goodbye!")
                swarm.stop()
                break
                
            elif user_input == "start":
                print("� Starting continuous autonomous mode...")
                print("   Press Ctrl+C to stop autonomous mode")
                swarm.run_continuous_autonomous_mode(cycle_interval=30)
                
            elif user_input == "cycle":
                work_found = swarm.run_single_cycle()
                if work_found:
                    print("� Tip: Type 'start' for continuous autonomous mode")
                else:
                    print("💡 Create GitLab work items for agents to discover and execute")
                    
            elif user_input == "status":
                status = swarm.get_status()
                print("📊 Autonomous Agent Swarm Status:")
                print(f"   • Running: {status['is_running']}")
                print(f"   • Cycles Completed: {status['cycle_count']}")
                print(f"   • Session Active: {status['session_active']}")
                
            elif user_input == "stop":
                swarm.stop()
                print("✅ Autonomous mode stopped")
                
            else:
                print("❓ Unknown command. Available commands:")
                print("   • start - Begin continuous autonomous mode")
                print("   • cycle - Run single autonomous cycle") 
                print("   • status - Show swarm status")
                print("   • stop - Stop autonomous mode")
                print("   • quit - Exit program")

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user.")
            swarm.stop()
            continue
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 Tip: Type 'quit' to exit or 'status' to check swarm state")
            continue

if __name__ == "__main__":
    main()
