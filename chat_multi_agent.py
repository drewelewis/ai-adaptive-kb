import sys
import os
import datetime
from dotenv import load_dotenv
from multi_agent_orchestrator import MultiAgentOrchestrator

load_dotenv(override=True)

# Initialize the multi-agent orchestrator
orchestrator = MultiAgentOrchestrator()

def stream_graph_updates(role: str, content: str):
    """Stream multi-agent graph updates"""
    return orchestrator.stream_graph_updates(role, content)

def clear_conversation_state():
    """Clear all conversation state from memory."""
    orchestrator.clear_conversation_state()



def main():
    print("=" * 80)
    print("🤖 AI ADAPTIVE KNOWLEDGE BASE - MULTI-AGENT SYSTEM")
    print("=" * 80)
    print("🎯 System Architecture:")
    print("   • UserProxy Agent    → Handles user interactions & communication")
    print("   • Supervisor Agent   → Coordinates workflows & task management") 
    print("   • ContentMgmt Agent  → Executes knowledge base operations")
    print("=" * 80)
    
    # Knowledge base selection happens during orchestrator initialization
    # Display agent status
    status = orchestrator.get_agent_status()
    print(f"📊 System Status: {status['total_agents']} agents active")
    for agent_name, agent_info in status.items():
        if isinstance(agent_info, dict) and 'name' in agent_info:
            print(f"   • {agent_info['name']}: {agent_info['tools_count']} tools available")
    
    print("=" * 80)
    print("💬 Commands:")
    print("   • Type your question or command to interact with the AI")
    print("   • Type '/agents' to show agent status")
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
                print("� Restarting knowledge base selection...")
                # Re-initialize KB context after reset
                orchestrator._initialize_knowledge_base_context()
                print("=" * 80)
                continue
            
            elif user_input.lower() in ["/agents"]:
                print("🤖 Multi-Agent System Status:")
                status = orchestrator.get_agent_status()
                for agent_name, agent_info in status.items():
                    if isinstance(agent_info, dict) and 'name' in agent_info:
                        print(f"   • {agent_info['name']}: {agent_info['status']} ({agent_info['tools_count']} tools)")
                print(f"   • Max Recursions: {status['max_recursions']}")
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