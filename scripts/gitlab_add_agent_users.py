#!/usr/bin/env python3
"""
GitLab Agent User Creation Script

Creates GitLab user accounts for each AI agent in the autonomous swarming system.
This enables proper work attribution, issue assignment, and progress tracking.

Requirements:
- GitLab admin privileges (GITLAB_ADMIN_PAT token)
- python-gitlab library
- Environment variables set for GitLab connection

Usage:
    python scripts/gitlab_add_agent_users.py [--dry-run] [--update-existing]
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import gitlab
    from gitlab.exceptions import GitlabCreateError, GitlabGetError
except ImportError:
    print("❌ Error: python-gitlab library not installed.")
    print("Install with: pip install python-gitlab")
    sys.exit(1)


class GitLabAgentUserManager:
    """Manages GitLab user accounts for AI agents"""
    
    # Agent definitions with their GitLab user properties
    AGENTS = {
        "ContentManagementAgent": {
            "username": "content-management-agent",
            "email": "content-management@ai-agents.local",
            "name": "Content Management Agent",
            "bio": "🤖 AI Agent specializing in autonomous content management and GitLab workflow coordination. Part of the autonomous swarming system for knowledge base development.",
            "projects_limit": 100,
            "can_create_group": False,
            "external": True,
            "admin": False,
            "website_url": "",
            "location": "AI Autonomous Swarming System"
        },
        "ContentPlannerAgent": {
            "username": "content-planner-agent", 
            "email": "content-planner@ai-agents.local",
            "name": "Content Planner Agent",
            "bio": "🤖 AI Agent specializing in strategic content planning and architecture design. Provides strategic guidance for knowledge base development through GitLab coordination.",
            "projects_limit": 100,
            "can_create_group": False,
            "external": True,
            "admin": False,
            "website_url": "",
            "location": "AI Autonomous Swarming System"
        },
        "ContentCreatorAgent": {
            "username": "content-creator-agent",
            "email": "content-creator@ai-agents.local", 
            "name": "Content Creator Agent",
            "bio": "🤖 AI Agent specializing in comprehensive content creation and research. Generates expert-level articles and documentation through autonomous GitLab workflows.",
            "projects_limit": 100,
            "can_create_group": False,
            "external": True,
            "admin": False,
            "website_url": "",
            "location": "AI Autonomous Swarming System"
        },
        "ContentReviewerAgent": {
            "username": "content-reviewer-agent",
            "email": "content-reviewer@ai-agents.local",
            "name": "Content Reviewer Agent", 
            "bio": "🤖 AI Agent specializing in quality assurance and content optimization. Ensures publication-ready quality through systematic review workflows in GitLab.",
            "projects_limit": 100,
            "can_create_group": False,
            "external": True,
            "admin": False,
            "website_url": "",
            "location": "AI Autonomous Swarming System"
        },
        "ContentRetrievalAgent": {
            "username": "content-retrieval-agent",
            "email": "content-retrieval@ai-agents.local",
            "name": "Content Retrieval Agent",
            "bio": "🤖 AI Agent specializing in content search, retrieval, and analysis. Provides research support and content gap analysis through GitLab coordination.",
            "projects_limit": 100,
            "can_create_group": False,
            "external": True,
            "admin": False,
            "website_url": "",
            "location": "AI Autonomous Swarming System"
        },
        "SupervisorAgent": {
            "username": "supervisor-agent",
            "email": "supervisor@ai-agents.local",
            "name": "Supervisor Agent",
            "bio": "🤖 AI Supervisor Agent acting as Scrum Master for autonomous agent coordination. Facilitates workflows, reviews completed work, and manages agent swarming through GitLab.",
            "projects_limit": 100,
            "can_create_group": True,
            "external": True,
            "admin": False,
            "website_url": "",
            "location": "AI Autonomous Swarming System"
        },
        "UserProxyAgent": {
            "username": "user-proxy-agent",
            "email": "user-proxy@ai-agents.local", 
            "name": "User Proxy Agent",
            "bio": "🤖 AI Agent specializing in collaborative KB design and user interaction. Facilitates multi-agent design sessions and coordinates autonomous work initiation through GitLab.",
            "projects_limit": 100,
            "can_create_group": False,
            "external": True,
            "admin": False,
            "website_url": "",
            "location": "AI Autonomous Swarming System"
        }
    }
    
    def __init__(self, gitlab_url: str = None, admin_token: str = None, dry_run: bool = False):
        """Initialize GitLab connection with admin privileges"""
        self.gitlab_url = gitlab_url or os.getenv('GITLAB_URL', 'http://localhost:8929')
        self.admin_token = admin_token or os.getenv('GITLAB_ADMIN_PAT') or os.getenv('GITLAB_PAT')
        self.dry_run = dry_run
        
        if not self.admin_token:
            raise ValueError("GitLab admin token required. Set GITLAB_ADMIN_PAT or GITLAB_PAT environment variable.")
        
        # Initialize GitLab connection
        try:
            self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.admin_token)
            self.gl.auth()
            
            # Verify admin privileges
            current_user = self.gl.user
            if not current_user.is_admin:
                logging.warning("⚠️ Current user is not a GitLab admin. User creation may fail.")
            
            logging.info(f"✅ Connected to GitLab at {self.gitlab_url} as {current_user.name}")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to GitLab: {e}")
    
    def generate_secure_password(self, agent_name: str) -> str:
        """Generate a secure password for an agent"""
        import hashlib
        import secrets
        import string
        
        # Generate a strong password with mixed case, numbers, and symbols
        length = 24
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        random_part = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Ensure at least one of each character type
        if not any(c.islower() for c in random_part):
            random_part = random_part[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isupper() for c in random_part):
            random_part = random_part[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in random_part):
            random_part = random_part[:-1] + secrets.choice(string.digits)
        if not any(c in "!@#$%^&*" for c in random_part):
            random_part = random_part[:-1] + secrets.choice("!@#$%^&*")
        
        return random_part
    
    def check_user_exists(self, username: str) -> Optional[Any]:
        """Check if a user already exists"""
        try:
            users = self.gl.users.list(username=username)
            return users[0] if users else None
        except Exception as e:
            logging.error(f"Error checking user {username}: {e}")
            return None
    
    def create_agent_user(self, agent_name: str, agent_config: Dict[str, Any], 
                         update_existing: bool = False) -> Dict[str, Any]:
        """Create a GitLab user for an AI agent"""
        username = agent_config['username']
        
        # Check if user already exists
        existing_user = self.check_user_exists(username)
        if existing_user:
            if update_existing:
                return self.update_agent_user(existing_user, agent_config)
            else:
                return {
                    'status': 'exists',
                    'username': username,
                    'id': existing_user.id,
                    'message': f"User {username} already exists (ID: {existing_user.id})"
                }
        
        if self.dry_run:
            return {
                'status': 'dry_run',
                'username': username,
                'message': f"[DRY RUN] Would create user {username} for {agent_name}"
            }
        
        # Generate secure password
        password = self.generate_secure_password(agent_name)
        
        # Prepare user data
        user_data = {
            'username': username,
            'email': agent_config['email'],
            'name': agent_config['name'],
            'password': password,
            'bio': agent_config['bio'],
            'projects_limit': agent_config['projects_limit'],
            'can_create_group': agent_config['can_create_group'],
            'external': agent_config['external'],
            'admin': agent_config['admin'],
            'website_url': agent_config['website_url'],
            'location': agent_config['location'],
            'skip_confirmation': True  # Skip email confirmation for automated accounts
        }
        
        try:
            # Create the user
            user = self.gl.users.create(user_data)
            
            logging.info(f"✅ Created user {username} (ID: {user.id}) for {agent_name}")
            
            return {
                'status': 'created',
                'username': username,
                'id': user.id,
                'password': password,
                'email': agent_config['email'],
                'message': f"Successfully created user {username} for {agent_name}"
            }
            
        except GitlabCreateError as e:
            error_msg = f"Failed to create user {username}: {e}"
            logging.error(error_msg)
            return {
                'status': 'error',
                'username': username,
                'error': str(e),
                'message': error_msg
            }
    
    def update_agent_user(self, user: Any, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent user with current configuration"""
        username = agent_config['username']
        
        if self.dry_run:
            return {
                'status': 'dry_run',
                'username': username,
                'id': user.id,
                'message': f"[DRY RUN] Would update user {username}"
            }
        
        try:
            # Update user attributes
            user.name = agent_config['name']
            user.bio = agent_config['bio']
            user.location = agent_config['location']
            user.website_url = agent_config['website_url']
            user.projects_limit = agent_config['projects_limit']
            user.can_create_group = agent_config['can_create_group']
            user.external = agent_config['external']
            
            user.save()
            
            logging.info(f"✅ Updated user {username} (ID: {user.id})")
            
            return {
                'status': 'updated',
                'username': username,
                'id': user.id,
                'message': f"Successfully updated user {username}"
            }
            
        except Exception as e:
            error_msg = f"Failed to update user {username}: {e}"
            logging.error(error_msg)
            return {
                'status': 'error',
                'username': username,
                'id': user.id,
                'error': str(e),
                'message': error_msg
            }
    
    def update_env_file_with_passwords(self, passwords: Dict[str, str]) -> bool:
        """Update the .env file with agent usernames and passwords"""
        try:
            env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
            
            # Read existing .env file
            env_lines = []
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Remove existing agent password lines
            filtered_lines = []
            for line in env_lines:
                if not any(f"GITLAB_AGENT_{username.upper().replace('-', '_')}_" in line 
                          for username in passwords.keys()):
                    filtered_lines.append(line)
            
            # Add agent credentials section
            if filtered_lines and not filtered_lines[-1].endswith('\n'):
                filtered_lines.append('\n')
            
            filtered_lines.append('\n# GitLab Agent User Credentials\n')
            filtered_lines.append('# Generated automatically by gitlab_add_agent_users.py\n')
            
            for username, password in passwords.items():
                env_var_base = username.upper().replace('-', '_')
                filtered_lines.append(f'GITLAB_AGENT_{env_var_base}_USERNAME={username}\n')
                filtered_lines.append(f'GITLAB_AGENT_{env_var_base}_PASSWORD={password}\n')
            
            # Write updated .env file
            with open(env_file_path, 'w') as f:
                f.writelines(filtered_lines)
            
            logging.info(f"✅ Updated .env file with {len(passwords)} agent credentials")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to update .env file: {e}")
            return False

    def create_all_agent_users(self, update_existing: bool = False) -> Dict[str, Any]:
        """Create GitLab users for all AI agents"""
        results = {}
        summary = {
            'created': 0,
            'updated': 0,
            'exists': 0,
            'errors': 0,
            'passwords': {}
        }
        
        logging.info(f"🚀 Starting agent user creation process...")
        if self.dry_run:
            logging.info("🔍 DRY RUN MODE - No actual changes will be made")
        
        for agent_name, agent_config in self.AGENTS.items():
            logging.info(f"Processing {agent_name}...")
            
            result = self.create_agent_user(agent_name, agent_config, update_existing)
            results[agent_name] = result
            
            # Update summary
            status = result['status']
            if status == 'created':
                summary['created'] += 1
                summary['passwords'][result['username']] = result.get('password', 'N/A')
            elif status == 'updated':
                summary['updated'] += 1
            elif status == 'exists':
                summary['exists'] += 1
            elif status == 'error':
                summary['errors'] += 1
        
        # Update .env file with passwords for newly created users
        if summary['passwords'] and not self.dry_run:
            self.update_env_file_with_passwords(summary['passwords'])
        
        return {
            'results': results,
            'summary': summary
        }
    
    def list_agent_users(self) -> List[Dict[str, Any]]:
        """List all existing agent users in GitLab"""
        agent_users = []
        
        for agent_name, agent_config in self.AGENTS.items():
            username = agent_config['username']
            user = self.check_user_exists(username)
            
            if user:
                agent_users.append({
                    'agent_name': agent_name,
                    'username': username,
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'state': user.state,
                    'created_at': user.created_at,
                    'last_activity_on': getattr(user, 'last_activity_on', 'N/A'),
                    'is_admin': user.is_admin,
                    'external': getattr(user, 'external', False)
                })
        
        return agent_users
    
    def delete_agent_user(self, username: str, force: bool = False) -> Dict[str, Any]:
        """Delete an agent user (use with caution)"""
        user = self.check_user_exists(username)
        if not user:
            return {
                'status': 'not_found',
                'username': username,
                'message': f"User {username} not found"
            }
        
        if self.dry_run:
            return {
                'status': 'dry_run',
                'username': username,
                'id': user.id,
                'message': f"[DRY RUN] Would delete user {username}"
            }
        
        if not force:
            return {
                'status': 'requires_force',
                'username': username,
                'id': user.id,
                'message': f"User deletion requires --force flag for safety"
            }
        
        try:
            user.delete()
            logging.info(f"🗑️ Deleted user {username} (ID: {user.id})")
            
            return {
                'status': 'deleted',
                'username': username,
                'id': user.id,
                'message': f"Successfully deleted user {username}"
            }
            
        except Exception as e:
            error_msg = f"Failed to delete user {username}: {e}"
            logging.error(error_msg)
            return {
                'status': 'error',
                'username': username,
                'id': user.id,
                'error': str(e),
                'message': error_msg
            }


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def print_summary_report(results: Dict[str, Any]):
    """Print a formatted summary report"""
    summary = results['summary']
    
    print("\n" + "="*60)
    print("🤖 AI AGENT GITLAB USER CREATION SUMMARY")
    print("="*60)
    
    print(f"✅ Created: {summary['created']}")
    print(f"🔄 Updated: {summary['updated']}")
    print(f"ℹ️  Already Exists: {summary['exists']}")
    print(f"❌ Errors: {summary['errors']}")
    
    if summary['passwords']:
        print("\n🔐 Generated Passwords (SAVE THESE SECURELY):")
        print("-" * 50)
        for username, password in summary['passwords'].items():
            print(f"{username}: {password}")
    
    print("\n📋 Detailed Results:")
    print("-" * 50)
    for agent_name, result in results['results'].items():
        status_emoji = {
            'created': '✅',
            'updated': '🔄', 
            'exists': 'ℹ️',
            'error': '❌',
            'dry_run': '🔍'
        }.get(result['status'], '?')
        
        print(f"{status_emoji} {agent_name}: {result['message']}")


def print_agent_users_list(agent_users: List[Dict[str, Any]]):
    """Print formatted list of agent users"""
    if not agent_users:
        print("No agent users found in GitLab.")
        return
    
    print("\n🤖 AI Agent Users in GitLab:")
    print("="*80)
    
    for user in agent_users:
        print(f"Agent: {user['agent_name']}")
        print(f"  Username: {user['username']} (ID: {user['id']})")
        print(f"  Name: {user['name']}")
        print(f"  Email: {user['email']}")
        print(f"  State: {user['state']}")
        print(f"  External: {user['external']}")
        print(f"  Created: {user['created_at']}")
        print(f"  Last Activity: {user['last_activity_on']}")
        print("-" * 40)


def main():
    """Main script execution"""
    parser = argparse.ArgumentParser(
        description="Manage GitLab user accounts for AI agents in autonomous swarming system"
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help="Show what would be done without making changes"
    )
    
    parser.add_argument(
        '--update-existing',
        action='store_true', 
        help="Update existing agent users with current configuration"
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help="List all existing agent users"
    )
    
    parser.add_argument(
        '--delete',
        type=str,
        help="Delete specific agent user by username"
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help="Force deletion (required for --delete)"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        '--gitlab-url',
        type=str,
        help="GitLab URL (defaults to GITLAB_URL env var or localhost:8929)"
    )
    
    parser.add_argument(
        '--admin-token',
        type=str,
        help="GitLab admin token (defaults to GITLAB_ADMIN_PAT env var)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        # Initialize manager
        manager = GitLabAgentUserManager(
            gitlab_url=args.gitlab_url,
            admin_token=args.admin_token,
            dry_run=args.dry_run
        )
        
        if args.list:
            # List existing agent users
            agent_users = manager.list_agent_users()
            print_agent_users_list(agent_users)
            
        elif args.delete:
            # Delete specific user
            result = manager.delete_agent_user(args.delete, args.force)
            print(f"{result['status']}: {result['message']}")
            
        else:
            # Create/update agent users
            results = manager.create_all_agent_users(args.update_existing)
            print_summary_report(results)
            
            if not args.dry_run and results['summary']['created'] > 0:
                print("\n💡 Next Steps:")
                print("1. Check the updated .env file for agent credentials")
                print("2. Save the generated passwords securely (they're now in .env)")
                print("3. Configure agent authentication in your application")
                print("4. Test agent GitLab access with the new credentials")
                print("5. Consider setting up API tokens for agents instead of passwords")
    
    except Exception as e:
        logging.error(f"Script execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
