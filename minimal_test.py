#!/usr/bin/env python3

"""
Minimal test of the chat system
"""

from chat_multi_agent import SimplifiedMultiAgentChat

print("Creating SimplifiedMultiAgentChat...")
try:
    chat = SimplifiedMultiAgentChat()
    print("✅ Chat system created")
    
    print("Initializing agents...")
    chat.initialize_agents()
    print("✅ Agents initialized")
    
    print("Testing agent status...")
    status = chat.get_agent_status()
    print(f"✅ Agent status: {status}")
    
    print("Testing a simple message...")
    response = chat.process_user_message("Hello, how are you?")
    print(f"✅ Response: {response}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
