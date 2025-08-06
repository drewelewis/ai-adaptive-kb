# PostgreSQL Schema Deployment Script
# PowerShell version - Reads from .env file

Write-Host "================================" -ForegroundColor Cyan
Write-Host " Knowledge Base Schema Deployment" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with database configuration." -ForegroundColor Yellow
    Write-Host "Example:" -ForegroundColor Yellow
    Write-Host "  DB_HOST=localhost" -ForegroundColor Yellow
    Write-Host "  DB_PORT=5432" -ForegroundColor Yellow
    Write-Host "  DB_NAME=knowledge_base" -ForegroundColor Yellow
    Write-Host "  DB_USER=postgres" -ForegroundColor Yellow
    Write-Host "  DB_PASSWORD=your_password" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Loading configuration from .env file..." -ForegroundColor Yellow
Write-Host ""

# Read .env file and set variables
$envVars = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        $envVars[$matches[1]] = $matches[2]
    }
}

# Set database variables with defaults
$DbHost = if ($envVars["DB_HOST"]) { $envVars["DB_HOST"] } else { "localhost" }
$DbPort = if ($envVars["DB_PORT"]) { $envVars["DB_PORT"] } else { "5432" }
$Database = if ($envVars["DB_NAME"]) { $envVars["DB_NAME"] } else { "knowledge_base" }
$Username = if ($envVars["DB_USER"]) { $envVars["DB_USER"] } else { "postgres" }
$Password = $envVars["DB_PASSWORD"]

Write-Host "Host: $DbHost`:$DbPort" -ForegroundColor Yellow
Write-Host "Database: $Database" -ForegroundColor Yellow
Write-Host "User: $Username" -ForegroundColor Yellow
Write-Host "SSL Mode: prefer" -ForegroundColor Yellow
Write-Host ""

# Check if psql is available
try {
    $version = psql --version
    Write-Host "PostgreSQL client found: $version" -ForegroundColor Green
} catch {
    Write-Host "ERROR: psql is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install PostgreSQL client tools" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Running schema deployment..." -ForegroundColor Yellow
Write-Host ""

# Set PGPASSWORD environment variable if password is provided
if ($Password) {
    $env:PGPASSWORD = $Password
    Write-Host "Using password from .env file" -ForegroundColor Green
}

# First, check if the database exists, if not create it
Write-Host "Checking if database '$Database' exists..." -ForegroundColor Yellow
try {
    $dbCheck = psql -h $DbHost -p $DbPort -U $Username -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='$Database'" --set=sslmode=prefer
    
    if ($dbCheck -notmatch "1") {
        Write-Host "Database '$Database' does not exist. Creating it..." -ForegroundColor Yellow
        psql -h $DbHost -p $DbPort -U $Username -d postgres -c "CREATE DATABASE $Database;" --set=sslmode=prefer
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Database '$Database' created successfully." -ForegroundColor Green
        } else {
            throw "Failed to create database '$Database'. Please ensure you have the necessary privileges."
        }
    } else {
        Write-Host "Database '$Database' already exists." -ForegroundColor Green
    }
} catch {
    Write-Host "Error checking/creating database: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Deploying schema to database '$Database'..." -ForegroundColor Yellow

# Execute the schema file with SSL mode prefer
try {
    psql -h $DbHost -p $DbPort -U $Username -d $Database -f "sql\knowledgebase_schema.sql" --set=sslmode=prefer
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================" -ForegroundColor Green
        Write-Host " Schema deployed successfully!" -ForegroundColor Green
        Write-Host "================================" -ForegroundColor Green
    } else {
        throw "psql returned exit code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Red
    Write-Host " Schema deployment failed!" -ForegroundColor Red
    Write-Host " Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "================================" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
