@echo off
REM Quick GitLab Environment Setup and Agent User Creation
REM This script loads .env file and sets up GitLab agent users

echo.
echo ========================================
echo  GitLab Agent Setup with .env file
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found in current directory
    echo Please ensure you have a .env file with GitLab configuration
    echo Expected location: %CD%\.env
    pause
    exit /b 1
)

echo INFO: Found .env file, loading environment variables...

REM Load environment variables from .env file
for /f "usebackq tokens=1,* delims==" %%i in (".env") do (
    if not "%%i"=="" (
        if not "%%i"=="rem" (
            if not "%%i"=="#" (
                set "%%i=%%j"
            )
        )
    )
)

echo INFO: Environment variables loaded from .env file

REM Validate required GitLab variables
if "%GITLAB_URL%"=="" (
    echo ERROR: GITLAB_URL not found in .env file
    echo Please add: GITLAB_URL=http://your-gitlab-server:port
    pause
    exit /b 1
)

if "%GITLAB_ADMIN_PAT%"=="" (
    if "%GITLAB_PAT%"=="" (
        echo ERROR: Neither GITLAB_ADMIN_PAT nor GITLAB_PAT found in .env file
        echo Please add one of these to your .env file:
        echo   GITLAB_ADMIN_PAT=your_admin_token_here
        echo   GITLAB_PAT=your_admin_token_here
        pause
        exit /b 1
    ) else (
        echo INFO: Using GITLAB_PAT from .env file
    )
) else (
    echo INFO: Using GITLAB_ADMIN_PAT from .env file
)

echo INFO: GitLab URL: %GITLAB_URL%

echo.
echo Available Actions:
echo 1. Validate GitLab setup and connection
echo 2. Preview agent users (dry-run)
echo 3. Create all agent users
echo 4. List existing agent users
echo 5. Update existing agent users
echo 6. Exit
echo.

set /p choice="Select action (1-6): "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo === Validating GitLab Setup ===
    python scripts\validate_gitlab_setup.py
) else if "%choice%"=="2" (
    echo.
    echo === Preview Agent Users (Dry Run) ===
    python scripts\gitlab_add_agent_users.py --dry-run
) else if "%choice%"=="3" (
    echo.
    echo === Creating GitLab Agent Users ===
    python scripts\gitlab_add_agent_users.py
) else if "%choice%"=="4" (
    echo.
    echo === Listing Existing Agent Users ===
    python scripts\gitlab_add_agent_users.py --list
) else if "%choice%"=="5" (
    echo.
    echo === Updating Existing Agent Users ===
    python scripts\gitlab_add_agent_users.py --update-existing
) else if "%choice%"=="6" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Exiting...
    pause
    exit /b 1
)

echo.
if errorlevel 1 (
    echo ========================================
    echo WARNING: Command completed with errors
    echo Check the output above for details
    echo ========================================
) else (
    echo ========================================
    echo Command completed successfully!
    echo ========================================
)

echo.
pause
