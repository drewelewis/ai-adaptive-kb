@echo off
REM GitLab Agent User Setup Script for Windows
REM Creates GitLab users for all AI agents in the autonomous swarming system

echo.
echo ========================================
echo  GitLab AI Agent User Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "scripts\gitlab_add_agent_users.py" (
    echo ERROR: Please run this script from the ai-adaptive-kb root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check for environment variables
if "%GITLAB_URL%"=="" (
    echo WARNING: GITLAB_URL environment variable not set
    echo Using default: http://localhost:8929
)

if "%GITLAB_ADMIN_PAT%"=="" (
    if "%GITLAB_PAT%"=="" (
        echo ERROR: Neither GITLAB_ADMIN_PAT nor GITLAB_PAT environment variable is set
        echo Please set one of these variables with your GitLab admin token
        pause
        exit /b 1
    ) else (
        echo INFO: Using GITLAB_PAT as admin token
    )
) else (
    echo INFO: Using GITLAB_ADMIN_PAT as admin token
)

echo.
echo Available Options:
echo 1. Create all agent users (default)
echo 2. List existing agent users
echo 3. Create with dry-run (preview only)
echo 4. Update existing agent users
echo 5. Exit
echo.

set /p choice="Select option (1-5): "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo Creating GitLab users for all AI agents...
    python scripts\gitlab_add_agent_users.py
) else if "%choice%"=="2" (
    echo.
    echo Listing existing agent users...
    python scripts\gitlab_add_agent_users.py --list
) else if "%choice%"=="3" (
    echo.
    echo Running dry-run (preview only)...
    python scripts\gitlab_add_agent_users.py --dry-run
) else if "%choice%"=="4" (
    echo.
    echo Updating existing agent users...
    python scripts\gitlab_add_agent_users.py --update-existing
) else if "%choice%"=="5" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Exiting...
    pause
    exit /b 1
)

echo.
echo ========================================
echo Script completed!
echo ========================================

REM Check if any errors occurred
if errorlevel 1 (
    echo.
    echo WARNING: Script completed with errors
    echo Check the output above for details
)

echo.
pause
