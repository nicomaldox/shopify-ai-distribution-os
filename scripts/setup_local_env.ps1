# PowerShell script to set up local development environment on Windows
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Shopify AI Distribution OS — Local Environment Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.11+."
    exit 1
}
Write-Host "[✓] $pythonVersion detected." -ForegroundColor Green

# 2. Setup Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "[*] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "[✓] Virtual environment (.venv) already exists." -ForegroundColor Green
}

# 3. Upgrade pip and install requirements
Write-Host "[*] Installing Python dependencies into .venv..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt

# 4. Check Docker Desktop for Postgres/Valkey
Write-Host "[*] Checking Docker..." -ForegroundColor Yellow
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    Write-Host "[✓] Docker CLI detected. Starting PostgreSQL and Valkey containers..." -ForegroundColor Green
    docker compose up -d postgres valkey
} else {
    Write-Host "[!] Docker Desktop is not yet running or not in PATH." -ForegroundColor Yellow
    Write-Host "    If running Docker Desktop, please start Docker Desktop and run:" -ForegroundColor Yellow
    Write-Host "    docker compose up -d postgres valkey" -ForegroundColor Cyan
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Setup complete!" -ForegroundColor Green
Write-Host " To start Core API locally:" -ForegroundColor Cyan
Write-Host "   .\.venv\Scripts\uvicorn.exe main:app --app-dir src/apps/core-api --reload --port 8000" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
