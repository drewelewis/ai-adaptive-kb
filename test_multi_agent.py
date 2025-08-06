#!/usr/bin/env python3
"""
Test script for the multi-agent system
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("🔍 Testing multi-agent system imports...")
    
    # Test basic imports
    from dotenv import load_dotenv
    print("✓ dotenv imported successfully")
    
    load_dotenv(override=True)
    print("✓ Environment loaded successfully")
    
    # Test LangChain imports
    try:
        from langchain_core.messages import BaseMessage
        print("✓ langchain_core imported successfully")
    except ImportError as e:
        print(f"❌ langchain_core import failed: {e}")
        sys.exit(1)
    
    # Test agent type imports
    from agents.agent_types import AgentState, AgentMessage
    print("✓ Agent types imported successfully")
    
    # Test LLM initialization
    from langchain_openai import AzureChatOpenAI
    print("✓ AzureChatOpenAI imported successfully")
    
    print("\n🎉 Basic imports successful!")
    print("🚀 Multi-agent system core components are ready.")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
