#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

print("🔧 Creating GitLab Project for Knowledge Base")
print("=" * 50)

# Which KB do you want to create a project for?
kb_id = "2"  # Most recent: "Comprehensive Guide to Building AI Solutions"
kb_name = "Comprehensive Guide to Building AI Solutions"

print(f"📚 Creating GitLab project for: {kb_name}")
print(f"🆔 Knowledge Base ID: {kb_id}")

try:
    # Import the knowledge base tools
    from tools.knowledge_base_tools import KnowledgeBaseTools
    
    # Create the tool instance
    kb_tools = KnowledgeBaseTools()
    gitlab_project_tool = kb_tools.KnowledgeBaseCreateGitLabProject()
    
    print("\n🚀 Executing GitLab project creation...")
    
    # Create GitLab project for the KB
    result = gitlab_project_tool._run(
        knowledge_base_id=kb_id,
        gitlab_project_name="ai-solutions-guide",  # Custom project name
        description="Project management for Comprehensive Guide to Building AI Solutions knowledge base",
        visibility="public"
    )
    
    print("\n📋 Result:")
    print(result)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n🔍 Troubleshooting:")
    print("1. Check if GitLab server is running at http://localhost:8929")
    print("2. Verify GITLAB_PAT token has project creation permissions")
    print("3. Ensure GitLab token is valid and not expired")

print("\n" + "=" * 50)
