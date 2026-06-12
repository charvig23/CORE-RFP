# C.O.R.E Complete System Startup Script
# Run this to start all backend services

Write-Host "🚀 Starting C.O.R.E Agent System..." -ForegroundColor Cyan
Write-Host ""

# Check if running in correct directory
$rootPath = "C:\Users\CHARVI\OneDrive\Desktop\COLLEGE\EY TECHATHON 6.0\R2"
if (-not (Test-Path $rootPath)) {
    Write-Host "❌ Error: Root directory not found!" -ForegroundColor Red
    Write-Host "Please update the script with the correct path." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Root directory found" -ForegroundColor Green
Write-Host ""

# Function to start a service in a new terminal
function Start-Service {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Command,
        [string]$Icon
    )
    
    Write-Host "$Icon Starting $Name..." -ForegroundColor Yellow
    
    $fullPath = Join-Path $rootPath $Path
    
    if (-not (Test-Path $fullPath)) {
        Write-Host "  ❌ Directory not found: $fullPath" -ForegroundColor Red
        return $false
    }
    
    # Start in new PowerShell window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$fullPath'; Write-Host '$Icon $Name Running' -ForegroundColor Green; $Command"
    
    Write-Host "  ✓ $Name started in new terminal" -ForegroundColor Green
    Start-Sleep -Seconds 2
    return $true
}

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  STARTING BACKEND SERVICES" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Start Flask Tool API (Port 8080)
$flaskStarted = Start-Service `
    -Name "Flask Tool API" `
    -Path "BackendCodes" `
    -Command "python sku_matching_api.py" `
    -Icon "🔧"

if (-not $flaskStarted) {
    Write-Host "Failed to start Flask API" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 3

# Start FastAPI Agent System (Port 8000)
$fastapiStarted = Start-Service `
    -Name "FastAPI Agent System" `
    -Path "agentSystem" `
    -Command "python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000" `
    -Icon "⚡"

if (-not $fastapiStarted) {
    Write-Host "Failed to start FastAPI" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  BACKEND SERVICES STARTED" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "✓ Flask Tool API:     http://localhost:8080" -ForegroundColor Green
Write-Host "✓ FastAPI System:     http://localhost:8000" -ForegroundColor Green
Write-Host "✓ FastAPI Docs:       http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  NEXT STEPS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open a NEW terminal for the frontend:" -ForegroundColor Yellow
Write-Host "   cd 'C:\Users\CHARVI\OneDrive\Desktop\COLLEGE\EY TECHATHON 6.0\R2\C.O.R.E'" -ForegroundColor White
Write-Host "   npm install" -ForegroundColor White
Write-Host "   npm start" -ForegroundColor White
Write-Host ""
Write-Host "2. Open browser to:" -ForegroundColor Yellow
Write-Host "   http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Upload an RFP and watch the magic! ✨" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop services" -ForegroundColor Gray
Write-Host ""

# Keep this terminal open
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SYSTEM MONITOR" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Checking service health..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

# Check Flask health
try {
    $flaskHealth = Invoke-RestMethod -Uri "http://localhost:8080/api/health" -Method Get -TimeoutSec 5
    Write-Host "✓ Flask API: " -NoNewline -ForegroundColor Green
    Write-Host "HEALTHY" -ForegroundColor Green
} catch {
    Write-Host "⚠ Flask API: " -NoNewline -ForegroundColor Yellow
    Write-Host "NOT RESPONDING (may still be starting)" -ForegroundColor Yellow
}

# Check FastAPI health
try {
    $fastapiHealth = Invoke-RestMethod -Uri "http://localhost:8000/docs" -Method Get -TimeoutSec 5
    Write-Host "✓ FastAPI:   " -NoNewline -ForegroundColor Green
    Write-Host "HEALTHY" -ForegroundColor Green
} catch {
    Write-Host "⚠ FastAPI:   " -NoNewline -ForegroundColor Yellow
    Write-Host "NOT RESPONDING (may still be starting)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "All services launched! Check individual terminal windows for logs." -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit this monitor..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
