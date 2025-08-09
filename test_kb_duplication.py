#!/usr/bin/env python3
"""
Test script to verify KB duplication fix
"""

import os
import sys
import traceback
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_kb_count():
    """Check current KB count"""
    try:
        from operations.knowledge_base_operations import KnowledgeBaseOperations
        
        print("🔗 Connecting to database...")
        kb_ops = KnowledgeBaseOperations()
        
        print("📊 Fetching knowledge bases...")
        kbs = kb_ops.get_knowledge_bases()
        
        print(f"📊 Current knowledge bases in database: {len(kbs)}")
        print("=" * 50)
        
        for kb in kbs:
            print(f"🗂️  KB {kb.id}: {kb.name}")
            if hasattr(kb, 'description') and kb.description:
                print(f"   📝 {kb.description[:100]}...")
            print()
            
        return len(kbs)
        
    except Exception as e:
        print(f"❌ Error checking KBs: {str(e)}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    print("🔍 Testing KB duplication fix...")
    print()
    
    # Test database connection first
    try:
        import psycopg2
        print("✅ psycopg2 available")
    except ImportError:
        print("❌ psycopg2 not available")
    
    initial_count = test_kb_count()
    
    if initial_count is not None:
        print(f"✅ Successfully retrieved {initial_count} knowledge bases")
    else:
        print("❌ Failed to retrieve knowledge bases")
