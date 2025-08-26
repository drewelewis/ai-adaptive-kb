#!/usr/bin/env python3
"""
Quick method signature test
"""

def test_methods():
    """Test that all expected methods exist"""
    try:
        print("🧪 Testing Method Signatures...")
        
        from agents.content_creator_agent import ContentCreatorAgent
        
        # Check if methods exist without creating full agent
        methods_to_check = [
            "_scan_assigned_gitlab_work",
            "_scan_available_gitlab_work",
            "_execute_gitlab_work", 
            "_claim_and_execute_work",
            "_claim_gitlab_work_item"
        ]
        
        print("   Checking ContentCreatorAgent methods...")
        for method_name in methods_to_check:
            if hasattr(ContentCreatorAgent, method_name):
                print(f"     ✅ {method_name}")
            else:
                print(f"     ❌ {method_name} MISSING")
                return False
        
        print("✅ All methods exist!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_methods()
