#!/usr/bin/env python3

"""
Debug agent initialization - quick test
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

print("Starting agent debug test...")

try:
    # Test basic imports
    from config.model_config import ModelConfig
    from agents.user_proxy_agent import UserProxyAgent
    from agents.supervisor_agent import SupervisorAgent
    
    print("✅ All imports successful")
    
    # Test model config
    model_config = ModelConfig()
    print("✅ ModelConfig created")
    
    # Test LLM creation
    user_llm = model_config.get_standard_model()
    print("✅ User LLM created")
    
    supervisor_llm = model_config.get_premium_model()
    print("✅ Supervisor LLM created")
    
    # Test agent creation
    user_proxy = UserProxyAgent(llm=user_llm)
    print("✅ UserProxyAgent created")
    
    supervisor = SupervisorAgent(llm=supervisor_llm)
    print("✅ SupervisorAgent created")
    
    print("🎉 All tests passed! Agents can be initialized correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
