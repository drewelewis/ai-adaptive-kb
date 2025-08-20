@echo off
REM PostgreSQL Schema Deployment Script
REM Reads database configuration from .env file

echo ================================
echo  Knowledge Base Schema Deployment
echo ================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create a .env file with database configuration.
    echo Example:
    echo   POSTGRES_HOST=localhost
    echo   POSTGRES_PORT=5432
    echo   POSTGRES_DB=knowledge_base
    echo   POSTGRES_USER=postgres
    echo   POSTGRES_PASSWORD=your_password
    echo.
    pause
    exit /b 1
)

echo Loading configuration from .env file...
echo.

REM Read .env file and set environment variables (format: KEY=VALUE with no spaces around =)
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if "%%a"=="POSTGRES_HOST" set POSTGRES_HOST=%%b
    if "%%a"=="POSTGRES_PORT" set POSTGRES_PORT=%%b
    if "%%a"=="POSTGRES_DB" set POSTGRES_DB=%%b
    if "%%a"=="POSTGRES_USER" set POSTGRES_USER=%%b
    if "%%a"=="POSTGRES_PASSWORD" set POSTGRES_PASSWORD=%%b
)

REM Set defaults if not found in .env
if not defined POSTGRES_HOST set POSTGRES_HOST=localhost
if not defined POSTGRES_PORT set POSTGRES_PORT=5432
if not defined POSTGRES_DB set POSTGRES_DB=kb_postgres
if not defined POSTGRES_USER set POSTGRES_USER=postgres
if not defined POSTGRES_PASSWORD set POSTGRES_PASSWORD=postgres

echo Host: %POSTGRES_HOST%:%POSTGRES_PORT%
echo Database: %POSTGRES_DB%
echo User: %POSTGRES_USER%
echo.

REM Check if psql is available, if not use docker
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo psql not found in PATH. Using Docker container to execute PostgreSQL commands...
    set PSQL_CMD=docker exec kb_postgres psql -U %POSTGRES_USER%
    echo Running schema deployment via Docker...
) else (
    echo psql found. Using local installation...
    set PSQL_CMD=psql -h %POSTGRES_HOST% -p %POSTGRES_PORT% -U %POSTGRES_USER% --set=sslmode=prefer
    echo Running schema deployment...
    
    REM Set PGPASSWORD environment variable if password is provided
    if defined POSTGRES_PASSWORD (
        set PGPASSWORD=%POSTGRES_PASSWORD%
        echo Using password from .env file
    )
)
echo.

REM First, check if the database exists, if not create it
echo Checking if database '%POSTGRES_DB%' exists...
%PSQL_CMD% -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='%POSTGRES_DB%'" | findstr /C:"1" >nul

if %errorlevel% neq 0 (
    echo Database '%POSTGRES_DB%' does not exist. Creating it...
    %PSQL_CMD% -d postgres -c "CREATE DATABASE %POSTGRES_DB%;"
    if %errorlevel% equ 0 (
        echo Database '%POSTGRES_DB%' created successfully.
    ) else (
        echo Failed to create database '%POSTGRES_DB%'.
        echo Please ensure you have the necessary privileges.
        pause
        exit /b 1
    )
) else (
    echo Database '%POSTGRES_DB%' already exists.
)

echo.
echo Deploying schema to database '%POSTGRES_DB%'...

REM Execute the schema file with appropriate command
%PSQL_CMD% -d %POSTGRES_DB% -f sql\knowledgebase_schema.sql

if %errorlevel% equ 0 (
    echo.
    echo ================================
    echo  Schema deployed successfully!
    echo ================================
) else (
    echo.
    echo ================================
    echo  Schema deployment failed!
    echo ================================
)

pause
