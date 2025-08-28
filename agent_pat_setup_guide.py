#!/usr/bin/env python3
"""
Agent PAT Token Setup Guide
===========================

Since the API approach for creating PAT tokens isn't available in this GitLab version,
here's a step-by-step guide to manually create PAT tokens for all agent users.
"""

import os
from dotenv import load_dotenv
load_dotenv()

GITLAB_URL = os.getenv('GITLAB_URL', 'http://localhost:8929')

def main():
    """Provide manual setup instructions"""
    
    agents = [
        ('content-management-agent', 'GITLAB_AGENT_CONTENT_MANAGEMENT_AGENT_PAT'),
        ('content-planner-agent', 'GITLAB_AGENT_CONTENT_PLANNER_AGENT_PAT'),
        ('content-creator-agent', 'GITLAB_AGENT_CONTENT_CREATOR_AGENT_PAT'),
        ('content-reviewer-agent', 'GITLAB_AGENT_CONTENT_REVIEWER_AGENT_PAT'),
        ('content-retrieval-agent', 'GITLAB_AGENT_CONTENT_RETRIEVAL_AGENT_PAT'),
        ('supervisor-agent', 'GITLAB_AGENT_SUPERVISOR_AGENT_PAT'),
        ('user-proxy-agent', 'GITLAB_AGENT_USER_PROXY_AGENT_PAT'),
    ]
    
    print("🔑 Agent PAT Token Setup Guide")
    print("=" * 45)
    print("\n📋 Current Issue:")
    print("   • Agent user passwords have expired")
    print("   • Cannot create PAT tokens programmatically")
    print("   • Need manual intervention through GitLab web interface")
    
    print(f"\n🚀 SOLUTION 1: Admin Impersonation (Recommended)")
    print("=" * 55)
    print(f"1. Go to GitLab Admin panel: {GITLAB_URL}/admin/users")
    print(f"2. For each agent user below:")
    print(f"   a. Click on the username")
    print(f"   b. Click 'Impersonate' button")
    print(f"   c. Go to User Settings > Access Tokens")
    print(f"   d. Create new Personal Access Token with:")
    print(f"      • Name: [username]-agent-pat-all-projects")
    print(f"      • Expiration: 1 year from now")
    print(f"      • Scopes: api, read_api, read_user, read_repository, write_repository")
    print(f"   e. Copy the generated token")
    print(f"   f. Stop impersonation")
    print(f"   g. Update .env file with the token")
    
    print(f"\n👥 Agent Users to Process:")
    for i, (username, env_var) in enumerate(agents, 1):
        print(f"{i}. {username}")
        print(f"   • Admin URL: {GITLAB_URL}/admin/users")
        print(f"   • Search for: {username}")
        print(f"   • .env variable: {env_var}")
        print()
    
    print(f"🚀 SOLUTION 2: Password Reset + Manual Login")
    print("=" * 50)
    print(f"1. Reset passwords through GitLab admin panel")
    print(f"2. Login as each user manually")
    print(f"3. Create PAT tokens from their profile")
    
    print(f"\n🚀 SOLUTION 3: Use Admin PAT for All Agents (Quick Fix)")
    print("=" * 60)
    print(f"If you want a quick solution for testing:")
    print(f"1. Use the main admin PAT token for all agents")
    print(f"2. Update .env file to use admin PAT for all agent operations")
    
    # Show current admin PAT
    admin_pat = os.getenv('GITLAB_PAT')
    if admin_pat:
        print(f"\nCurrent admin PAT: {admin_pat}")
        print(f"\nTo use admin PAT for all agents, update .env file:")
        for username, env_var in agents:
            print(f"{env_var}={admin_pat}")
    
    print(f"\n📝 After Creating PAT Tokens:")
    print(f"1. Update .env file with new tokens")
    print(f"2. Run: python quick_pat_test.py")
    print(f"3. Run: python test_current_pat_access.py")
    print(f"4. Verify agents can access all projects")
    
    print(f"\n💡 Pro Tip:")
    print(f"   • PAT tokens inherit the user's project permissions")
    print(f"   • To access ALL projects, ensure agent users are:")
    print(f"     - Added as members to all relevant projects/groups")
    print(f"     - Or given appropriate GitLab role (Developer/Maintainer)")
    
    print(f"\n🔧 Quick Test Commands:")
    print(f"   python quick_pat_test.py          # Test one token")
    print(f"   python test_current_pat_access.py # Test all tokens")

if __name__ == "__main__":
    main()
