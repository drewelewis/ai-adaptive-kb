#!/usr/bin/env python3

"""
Simple test script to debug agent initialization
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    print("1. Testing imports...")
    from config.model_config import ModelConfig
    print("   ✅ ModelConfig imported")
    
    from agents.user_proxy_agent import UserProxyAgent
    print("   ✅ UserProxyAgent imported")
    
    from agents.supervisor_agent import SupervisorAgent
    print("   ✅ SupervisorAgent imported")
    
    from agents.postgresql_state_manager import PostgreSQLStateManager
    print("   ✅ PostgreSQLStateManager imported")
    
    print("\n2. Testing model configuration...")
    model_config = ModelConfig()
    print("   ✅ ModelConfig instance created")
    
    print("\n3. Testing LLM creation...")
    try:
        user_llm = model_config.get_standard_model()
        print("   ✅ User LLM created")
    except Exception as e:
        print(f"   ❌ User LLM failed: {e}")
        
    try:
        supervisor_llm = model_config.get_premium_model()
        print("   ✅ Supervisor LLM created")
    except Exception as e:
        print(f"   ❌ Supervisor LLM failed: {e}")
    
    print("\n4. Testing agent creation...")
    try:
        user_proxy = UserProxyAgent(llm=user_llm)
        print("   ✅ UserProxyAgent created")
    except Exception as e:
        print(f"   ❌ UserProxyAgent failed: {e}")
        
    try:
        supervisor = SupervisorAgent(llm=supervisor_llm)
        print("   ✅ SupervisorAgent created")
    except Exception as e:
        print(f"   ❌ SupervisorAgent failed: {e}")
    
    print("\n5. Testing PostgreSQL state manager...")
    try:
        import uuid
        session_id = str(uuid.uuid4())
        state_manager = PostgreSQLStateManager(session_id)
        print("   ✅ PostgreSQLStateManager created")
    except Exception as e:
        print(f"   ❌ PostgreSQLStateManager failed: {e}")
    
    print("\n✅ All tests completed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
