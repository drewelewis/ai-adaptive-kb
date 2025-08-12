# GitLab Agent User Setup

This directory contains scripts and configuration for setting up GitLab user accounts for AI agents in the autonomous swarming system.

## Overview

The autonomous swarming system requires each AI agent to have a GitLab user account for proper work attribution, issue assignment, and progress tracking. This setup enables:

- **Work Attribution**: Each agent's work is properly attributed in GitLab
- **Issue Assignment**: Issues can be assigned to specific agents
- **Progress Tracking**: Agent activity and contributions are visible
- **Audit Trail**: Complete history of who did what work
- **Collaboration**: Agents can communicate through GitLab comments and mentions

## Files

- `gitlab_add_agent_users.py` - Main script for creating/managing agent users
- `gitlab_agent_config.py` - Configuration file with agent definitions
- `_setup_gitlab_agents.bat` - Windows batch script for easy execution
- `README.md` - This documentation file

## Quick Start

### Windows (Batch Script)
```cmd
# From the ai-adaptive-kb root directory
_setup_gitlab_agents.bat
```

### Command Line (Any OS)
```bash
# Preview what would be created (dry run)
python scripts/gitlab_add_agent_users.py --dry-run

# Create all agent users
python scripts/gitlab_add_agent_users.py

# List existing agent users
python scripts/gitlab_add_agent_users.py --list

# Update existing users with current config
python scripts/gitlab_add_agent_users.py --update-existing
```

## Prerequisites

### 1. GitLab Admin Access
You need GitLab administrator privileges to create users. Set one of these environment variables:

```bash
# Primary (recommended)
GITLAB_ADMIN_PAT=your_admin_token_here

# Fallback
GITLAB_PAT=your_admin_token_here
```

### 2. GitLab Connection
Set your GitLab server URL:

```bash
# Default: http://localhost:8929
GITLAB_URL=http://your-gitlab-server.com
```

### 3. Python Dependencies
```bash
pip install python-gitlab
```

## Agent User Accounts

The script creates the following AI agent users:

| Agent | Username | Email | Role |
|-------|----------|-------|------|
| ContentManagementAgent | content-management-agent | content-management@ai-agents.local | Autonomous workflow coordination |
| ContentPlannerAgent | content-planner-agent | content-planner@ai-agents.local | Strategic planning and design |
| ContentCreatorAgent | content-creator-agent | content-creator@ai-agents.local | Content creation and research |
| ContentReviewerAgent | content-reviewer-agent | content-reviewer@ai-agents.local | Quality assurance and review |
| ContentRetrievalAgent | content-retrieval-agent | content-retrieval@ai-agents.local | Content search and analysis |
| SupervisorAgent | supervisor-agent | supervisor@ai-agents.local | Scrum Master coordination |
| UserProxyAgent | user-proxy-agent | user-proxy@ai-agents.local | Collaborative design leadership |

### User Properties
- **External Users**: All agents are marked as external users
- **Project Limit**: 100 projects per agent
- **Non-Admin**: Agents have regular user privileges (not admin)
- **Email Domain**: All use `@ai-agents.local` domain
- **Auto-Generated Passwords**: Secure passwords generated automatically

## Usage Examples

### Create All Agent Users
```bash
python scripts/gitlab_add_agent_users.py
```

Output:
```
✅ Created user content-management-agent (ID: 15) for ContentManagementAgent
✅ Created user content-planner-agent (ID: 16) for ContentPlannerAgent
...

🔐 Generated Passwords (SAVE THESE SECURELY):
content-management-agent: AgentA1b2C3d4...
content-planner-agent: AgentE5f6G7h8...
```

### Preview Changes (Dry Run)
```bash
python scripts/gitlab_add_agent_users.py --dry-run
```

### Update Existing Users
```bash
python scripts/gitlab_add_agent_users.py --update-existing
```

### List Current Agent Users
```bash
python scripts/gitlab_add_agent_users.py --list
```

### Verbose Logging
```bash
python scripts/gitlab_add_agent_users.py --verbose
```

## Configuration

### Modifying Agent Configuration
Edit `gitlab_agent_config.py` to customize:

- Agent usernames and emails
- User properties (project limits, permissions)
- Agent descriptions and roles
- GitLab project templates
- Issue templates for agent work

### Environment Variables
```bash
# GitLab connection
GITLAB_URL=http://localhost:8929
GITLAB_ADMIN_PAT=your_admin_token

# Alternative token name
GITLAB_PAT=your_admin_token
```

## Security Considerations

### Password Management
- **Generated Passwords**: Script generates secure random passwords
- **Save Securely**: Store passwords in a secure password manager
- **Token Alternative**: Consider using GitLab API tokens instead of passwords for agent authentication

### User Permissions
- **External Users**: Agents are marked as external to limit access
- **Project-Specific**: Agents should only have access to relevant projects
- **Regular Users**: Agents don't have admin privileges

### Email Addresses
- **Local Domain**: Uses `@ai-agents.local` to indicate these are system accounts
- **Non-Functional**: These emails are for identification only

## Troubleshooting

### Common Issues

#### "GitLab admin token required"
**Solution**: Set `GITLAB_ADMIN_PAT` environment variable with your admin token

#### "Failed to connect to GitLab"
**Solutions**:
- Check `GITLAB_URL` is correct
- Verify GitLab server is running
- Confirm network connectivity
- Validate token permissions

#### "Current user is not a GitLab admin"
**Solutions**:
- Use a token from a GitLab admin user
- Ask your GitLab admin to create the users
- Upgrade your GitLab permissions

#### "User already exists"
**Solutions**:
- Use `--update-existing` to update existing users
- Use `--list` to see current agent users
- Delete existing users if recreation is needed

### Validation Commands
```bash
# Test GitLab connection
python -c "
import gitlab
gl = gitlab.Gitlab('http://localhost:8929', private_token='your_token')
gl.auth()
print(f'Connected as: {gl.user.name}')
print(f'Admin: {gl.user.is_admin}')
"

# Validate configuration
python scripts/gitlab_add_agent_users.py --dry-run --verbose
```

## Integration with Autonomous Swarming

### Issue Assignment
Once agents are created, GitLab issues can be assigned to them:

```python
# Assign issue to ContentCreatorAgent
issue.assignee_ids = [creator_agent_user_id]
issue.save()
```

### Agent Authentication
Configure agents to authenticate with GitLab:

```python
# In agent code
gitlab_token = get_agent_gitlab_token("content-creator-agent")
gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
```

### Work Attribution
All agent actions in GitLab will be attributed to their user accounts:
- Issue comments
- Issue status changes
- Work item updates
- Project activity

## Next Steps

After creating agent users:

1. **Save Passwords**: Store generated passwords securely
2. **Configure Authentication**: Set up agent GitLab authentication
3. **Test Access**: Verify agents can access GitLab
4. **Project Access**: Add agents to relevant GitLab projects
5. **Label Setup**: Create standard labels for agent work classification
6. **Workflow Testing**: Test the autonomous swarming workflow

## API Reference

### GitLabAgentUserManager Class

#### `create_all_agent_users(update_existing=False)`
Creates GitLab users for all configured agents.

#### `list_agent_users()`
Returns list of existing agent users in GitLab.

#### `check_user_exists(username)`
Checks if a specific agent user exists.

#### `delete_agent_user(username, force=False)`
Deletes an agent user (use with caution).

## Contributing

To add new agents or modify configuration:

1. Update `AGENT_USERS` in `gitlab_agent_config.py`
2. Add agent-specific templates if needed
3. Update this README with new agent information
4. Test with `--dry-run` before creating users

## Support

For issues or questions:
1. Check the troubleshooting section
2. Run with `--verbose` for detailed logging
3. Validate configuration with `--dry-run`
4. Check GitLab server logs if connection issues persist
