#!/usr/bin/env python3
"""
GitLab Agent Configuration Validator

Validates the agent configuration and tests GitLab connectivity.
Run this before attempting to create agent users.
"""

import os
import sys
import json
from typing import Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import gitlab
except ImportError:
    print("❌ Error: python-gitlab library not installed.")
    print("Install with: pip install python-gitlab")
    sys.exit(1)

from scripts.gitlab_agent_config import AGENT_USERS, validate_agent_config, GITLAB_CONFIG


def test_gitlab_connection() -> Dict[str, Any]:
    """Test GitLab connection and admin privileges"""
    gitlab_url = os.getenv('GITLAB_URL', GITLAB_CONFIG['default_url'])
    admin_token = os.getenv(GITLAB_CONFIG['admin_token_env']) or os.getenv(GITLAB_CONFIG['fallback_token_env'])
    
    if not admin_token:
        return {
            'success': False,
            'error': f"No GitLab token found. Set {GITLAB_CONFIG['admin_token_env']} environment variable."
        }
    
    try:
        gl = gitlab.Gitlab(gitlab_url, private_token=admin_token)
        gl.auth()
        
        current_user = gl.user
        
        return {
            'success': True,
            'gitlab_url': gitlab_url,
            'user_name': current_user.name,
            'user_id': current_user.id,
            'username': current_user.username,
            'is_admin': current_user.is_admin,
            'email': getattr(current_user, 'email', 'N/A')
        }
        
    except Exception as e:
        return {
            'success': False,
            'gitlab_url': gitlab_url,
            'error': str(e)
        }


def validate_environment() -> Dict[str, Any]:
    """Validate environment setup"""
    issues = []
    warnings = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ required, found {sys.version}")
    
    # Check environment variables
    gitlab_url = os.getenv('GITLAB_URL')
    if not gitlab_url:
        warnings.append("GITLAB_URL not set, will use default: http://localhost:8929")
    
    admin_token = os.getenv(GITLAB_CONFIG['admin_token_env'])
    fallback_token = os.getenv(GITLAB_CONFIG['fallback_token_env'])
    
    if not admin_token and not fallback_token:
        issues.append(f"No GitLab token found. Set {GITLAB_CONFIG['admin_token_env']} or {GITLAB_CONFIG['fallback_token_env']}")
    elif not admin_token and fallback_token:
        warnings.append(f"Using {GITLAB_CONFIG['fallback_token_env']} as admin token")
    
    return {
        'python_version': sys.version,
        'issues': issues,
        'warnings': warnings
    }


def check_existing_users(gl: gitlab.Gitlab) -> Dict[str, Any]:
    """Check which agent users already exist"""
    existing_users = {}
    conflicts = []
    
    for agent_name, config in AGENT_USERS.items():
        username = config['username']
        email = config['email']
        
        try:
            # Check by username
            users_by_username = gl.users.list(username=username)
            if users_by_username:
                existing_users[agent_name] = {
                    'username': username,
                    'user_id': users_by_username[0].id,
                    'name': users_by_username[0].name,
                    'email': users_by_username[0].email,
                    'state': users_by_username[0].state
                }
                
                # Check if email matches
                if users_by_username[0].email != email:
                    conflicts.append(f"{username}: email mismatch (GitLab: {users_by_username[0].email}, Config: {email})")
            
        except Exception as e:
            print(f"Warning: Could not check user {username}: {e}")
    
    return {
        'existing_users': existing_users,
        'conflicts': conflicts,
        'total_existing': len(existing_users),
        'total_configured': len(AGENT_USERS)
    }


def main():
    """Main validation function"""
    print("🔍 GitLab Agent Configuration Validator")
    print("="*50)
    
    # 1. Validate agent configuration
    print("\n1️⃣ Validating agent configuration...")
    config_issues = validate_agent_config()
    
    has_config_issues = any(config_issues.values())
    if has_config_issues:
        print("❌ Configuration issues found:")
        for issue_type, issues in config_issues.items():
            if issues:
                print(f"   {issue_type}: {', '.join(issues)}")
    else:
        print("✅ Agent configuration is valid")
    
    # 2. Validate environment
    print("\n2️⃣ Validating environment...")
    env_result = validate_environment()
    
    if env_result['issues']:
        print("❌ Environment issues:")
        for issue in env_result['issues']:
            print(f"   • {issue}")
    else:
        print("✅ Environment setup is valid")
    
    if env_result['warnings']:
        print("⚠️ Environment warnings:")
        for warning in env_result['warnings']:
            print(f"   • {warning}")
    
    # 3. Test GitLab connection
    print("\n3️⃣ Testing GitLab connection...")
    connection_result = test_gitlab_connection()
    
    if connection_result['success']:
        print("✅ GitLab connection successful")
        print(f"   URL: {connection_result['gitlab_url']}")
        print(f"   User: {connection_result['user_name']} ({connection_result['username']})")
        print(f"   Admin: {'Yes' if connection_result['is_admin'] else 'No'}")
        
        if not connection_result['is_admin']:
            print("⚠️ Warning: Current user is not a GitLab admin. User creation may fail.")
        
        # 4. Check existing users
        print("\n4️⃣ Checking existing agent users...")
        try:
            gl = gitlab.Gitlab(
                connection_result['gitlab_url'],
                private_token=os.getenv(GITLAB_CONFIG['admin_token_env']) or os.getenv(GITLAB_CONFIG['fallback_token_env'])
            )
            
            users_result = check_existing_users(gl)
            
            print(f"📊 Found {users_result['total_existing']}/{users_result['total_configured']} agent users already exist")
            
            if users_result['existing_users']:
                print("\n   Existing agent users:")
                for agent_name, user_info in users_result['existing_users'].items():
                    print(f"   • {agent_name}: {user_info['username']} (ID: {user_info['user_id']}, State: {user_info['state']})")
            
            if users_result['conflicts']:
                print("\n❌ Configuration conflicts:")
                for conflict in users_result['conflicts']:
                    print(f"   • {conflict}")
            
        except Exception as e:
            print(f"❌ Could not check existing users: {e}")
    else:
        print("❌ GitLab connection failed")
        print(f"   URL: {connection_result.get('gitlab_url', 'Unknown')}")
        print(f"   Error: {connection_result['error']}")
    
    # 5. Summary and recommendations
    print("\n5️⃣ Summary and Recommendations")
    print("-"*30)
    
    if has_config_issues:
        print("❌ Fix configuration issues before proceeding")
        return False
    
    if env_result['issues']:
        print("❌ Fix environment issues before proceeding")
        return False
    
    if not connection_result['success']:
        print("❌ Fix GitLab connection before proceeding")
        return False
    
    print("✅ Validation successful! You can proceed with agent user creation.")
    
    # Provide next steps
    print("\n💡 Next steps:")
    
    if connection_result.get('is_admin'):
        print("   1. Run: python scripts/gitlab_add_agent_users.py --dry-run")
        print("   2. If satisfied, run: python scripts/gitlab_add_agent_users.py")
    else:
        print("   1. Get GitLab admin privileges or ask an admin to run the script")
        print("   2. Alternatively, create users manually in GitLab UI")
    
    existing_count = users_result.get('total_existing', 0) if 'users_result' in locals() else 0
    if existing_count > 0:
        print(f"   3. Consider using --update-existing to update {existing_count} existing users")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
