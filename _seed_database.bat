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

REM Read .env file and set environment variables
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
if not defined POSTGRES_DB set POSTGRES_DB=kb-postgres
if not defined POSTGRES_USER set POSTGRES_USER=postgres
if not defined POSTGRES_PASSWORD set POSTGRES_PASSWORD=postgres

echo Host: %POSTGRES_HOST%:%POSTGRES_PORT%
echo Database: %POSTGRES_DB%
echo User: %POSTGRES_USER%
echo.

REM Check if psql is available
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: psql is not installed or not in PATH
    echo Please install PostgreSQL client tools
    pause
    exit /b 1
)

echo Running schema deployment...
echo.

REM Set PGPASSWORD environment variable if password is provided
if defined POSTGRES_PASSWORD (
    set PGPASSWORD=%POSTGRES_PASSWORD%
    echo Using password from .env file
)

REM First, check if the database exists, if not create it
echo Checking if database '%POSTGRES_DB%' exists...
psql -h %POSTGRES_HOST% -p %POSTGRES_PORT% -U %POSTGRES_USER% -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='%POSTGRES_DB%'" --set=sslmode=prefer | findstr /C:"1" >nul

if %errorlevel% neq 0 (
    echo Database '%POSTGRES_DB%' does not exist. Creating it...
    psql -h %POSTGRES_HOST% -p %POSTGRES_PORT% -U %POSTGRES_USER% -d postgres -c "CREATE DATABASE %POSTGRES_DB%;" --set=sslmode=prefer
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

REM Execute the schema file with SSL mode prefer
psql -h %POSTGRES_HOST% -p %POSTGRES_PORT% -U %POSTGRES_USER% -d %POSTGRES_DB% -f sql\knowledgebase_schema.sql --set=sslmode=prefer

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
