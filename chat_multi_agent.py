import sys
import os
import datetime
import warnings
from dotenv import load_dotenv

# Suppress Pydantic warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')

# Import the orchestrator with PostgreSQL state management
from agents.orchestrator import Orchestrator

# Import new autonomous content creation agents
from agents.content_planner_agent import ContentPlannerAgent
from agents.content_creator_agent import ContentCreatorAgent  
from agents.content_reviewer_agent import ContentReviewerAgent

load_dotenv(override=True)

# Initialize the orchestrator
orchestrator = Orchestrator()
print("🔥 PostgreSQL state management enabled!")

def stream_graph_updates(role: str, content: str):
    """Stream multi-agent graph updates with PostgreSQL state management"""
    return orchestrator.process_message(content, role)

def clear_conversation_state():
    """Clear all conversation state from memory."""
    orchestrator.clear_conversation_state()

def get_session_summary():
    """Get session summary"""
    if hasattr(orchestrator, 'get_session_summary'):
        return orchestrator.get_session_summary()
    return None

def debug_state():
    """Debug state management"""
    if hasattr(orchestrator, 'debug_state'):
        orchestrator.debug_state()
    else:
        print("⚠️  State debugging not available")

def main():
    print("=" * 80)
    print("🔥 AI ADAPTIVE KNOWLEDGE BASE - AUTONOMOUS CONTENT CREATION SYSTEM")
    print("🚀 PostgreSQL State Management | Expert Content Generation | Publication Ready")
    print("=" * 80)
    print("🎯 Enhanced System Architecture:")
    print("   • UserProxy Agent      → User interaction & communication")
    print("   • Router Agent         → Intent classification & routing") 
    print("   • Supervisor Agent     → Workflow coordination & management")
    print("   • ContentPlanner Agent → Strategic planning & structure design")
    print("   • ContentCreator Agent → Expert content generation & research")
    print("   • ContentReviewer Agent → Quality assurance & optimization")
    print("   • State Manager        → PostgreSQL persistence & audit trails")
    print("=" * 80)
    print("🎯 Content Creation Capabilities:")
    print("   • Autonomous KB creation from high-level ideas")
    print("   • Expert-level content across any domain")
    print("   • Publication-ready output for ebooks, blogs, books")
    print("   • Intelligent clarification when needed")
    print("   • Comprehensive coverage with minimal oversight")
    print("=" * 80)
    
    # Display session information
    session_summary = get_session_summary()
    if session_summary:
        session_id = session_summary.get('session_id', 'unknown')[:12]
        is_active = session_summary.get('is_active', False)
        print(f"🔗 Session: {session_id}... | Active: {is_active}")
        
        # Show conversation stats if available
        conv_stats = session_summary.get('conversation_stats', {})
        if conv_stats:
            msg_count = conv_stats.get('message_count', 0)
            print(f"💬 Conversation: {msg_count} messages in history")
    
    # Knowledge base selection happens during orchestrator initialization
    # Display agent status
    if hasattr(orchestrator, 'get_agent_status'):
        status = orchestrator.get_agent_status()
        print(f"📊 System Status: {status['total_agents']} agents active")
        for agent_name, agent_info in status.items():
            if isinstance(agent_info, dict) and 'name' in agent_info:
                print(f"   • {agent_info['name']}: {agent_info['tools_count']} tools available")
    else:
        print("📊 Multi-Agent System Ready")
    
    
    print("=" * 80)
    print("💬 Commands:")
    print("   • Type your question or command to interact with the AI")
    if hasattr(orchestrator, 'get_agent_status'):
        print("   • Type '/agents' to show agent status")
    print("   • Type '/debug' to show state information")
    print("   • Type '/session' to show session summary")
    print("   • Type '/audit' to show recent state changes")
    print("   • Type '/reset' or '/r' to clear conversation state")
    print("   • Type '/q' or '/quit' to exit")
    print("=" * 80)
    
    while True:
        try:
            user_input = input("\n> ")
            print("")
            
            if user_input.lower() in ["/q", "/quit"]:
                print("👋 Multi-agent system shutting down. Goodbye!")
                break
                
            elif user_input.lower() in ["/reset", "/r"]:
                print("🔄 Clearing multi-agent conversation state...")
                clear_conversation_state()
                print("✅ State cleared from PostgreSQL")
                print("=" * 80)
                continue
            
            elif user_input.lower() in ["/agents"] and hasattr(orchestrator, 'get_agent_status'):
                print("🤖 Multi-Agent System Status:")
                status = orchestrator.get_agent_status()
                for agent_name, agent_info in status.items():
                    if isinstance(agent_info, dict) and 'name' in agent_info:
                        print(f"   • {agent_info['name']}: {agent_info['status']} ({agent_info['tools_count']} tools)")
                print(f"   • Max Recursions: {status['max_recursions']}")
                continue
            
            elif user_input.lower() in ["/debug"]:
                print("🔍 State Debug Information:")
                print(f"🔍 Debug: hasattr(orchestrator, 'debug_state') = {hasattr(orchestrator, 'debug_state')}")
                debug_state()
                continue
            
            elif user_input.lower() in ["/session"]:
                print("📊 Session Summary:")
                print(f"🔍 Debug: hasattr(orchestrator, 'get_session_summary') = {hasattr(orchestrator, 'get_session_summary')}")
                session_summary = get_session_summary()
                if session_summary:
                    for key, value in session_summary.items():
                        if isinstance(value, dict):
                            print(f"   {key}:")
                            for sub_key, sub_value in value.items():
                                print(f"     {sub_key}: {sub_value}")
                        else:
                            print(f"   {key}: {value}")
                continue
            
            elif user_input.lower() in ["/audit"]:
                print("📋 Recent State Changes:")
                if hasattr(orchestrator, 'get_audit_trail'):
                    audit = orchestrator.get_audit_trail(10)
                    for i, change in enumerate(audit):
                        timestamp = change['change_timestamp']
                        change_type = change['change_type']
                        path = change['change_path']
                        agent = change['agent_name']
                        print(f"   {i+1:2}. {timestamp} | {change_type:15} | {path:25} | {agent}")
                continue
            
            # Process normal user input through multi-agent system
            print("🚀 Processing through multi-agent system...")
            
            ai_message = stream_graph_updates("user", user_input)
            
            # Check if we need to suggest a reset due to recursion limit
            if hasattr(ai_message, 'content') and "recursion limit" in str(ai_message.content).lower():
                print("\n💡 Tip: Type '/reset' to start a new conversation with fresh agent context.")

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user. Type '/q' to quit properly.")
            continue
        except Exception as e:
            print(f"❌ Multi-agent system error: {e}")
            print("💡 Tip: Type '/reset' to restart agents or '/q' to quit.")
            continue

if __name__ == "__main__":
    main()
