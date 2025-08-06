#!/usr/bin/env python3
"""
Demo script for the multi-agent system
Run this to test the multi-agent knowledge base system
"""

import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)

try:
    print("🚀 Initializing Multi-Agent AI Knowledge Base System...")
    print("=" * 80)
    
    # Import the orchestrator
    from multi_agent_orchestrator import MultiAgentOrchestrator
    
    # Initialize the system
    orchestrator = MultiAgentOrchestrator()
    
    print("System ready! You can now:")
    print("1. Ask questions about knowledge bases")
    print("2. Request to create or update content")
    print("3. Search for information")
    print("4. Get help with system operations")
    print("=" * 80)
    
    # Demo interaction
    demo_message = "Hello! I'd like to understand how this multi-agent system works."
    print(f"Demo query: {demo_message}")
    print("\nProcessing through multi-agent system...")
    print("-" * 50)
    
    # Process demo message
    result = orchestrator.stream_graph_updates("user", demo_message)
    
    print("-" * 50)
    print("✅ Demo completed successfully!")
    print("\nTo run the full interactive system, use: python chat_multi_agent.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
