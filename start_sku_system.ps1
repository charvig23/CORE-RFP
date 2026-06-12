# Quick Start Script for SKU Matching Integration
# Run this script to test the SKU matching functionality

Write-Host "🚀 Starting SKU Matching System..." -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if Node is available
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan

# Install Flask dependencies
Write-Host "Installing Flask API dependencies..." -ForegroundColor Yellow
Set-Location "BackendCodes"
pip install -r requirements_flask.txt
Set-Location ".."

# Install FastAPI dependencies
Write-Host "Installing FastAPI dependencies..." -ForegroundColor Yellow
Set-Location "agentSystem"
pip install -r requirements.txt
Set-Location ".."

# Install React dependencies
Write-Host "Installing React dependencies..." -ForegroundColor Yellow
Set-Location "C.O.R.E"
npm install
Set-Location ".."

Write-Host ""
Write-Host "✅ Dependencies installed!" -ForegroundColor Green
Write-Host ""

# Instructions
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎯 NEXT STEPS" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start Flask API (Terminal 1):" -ForegroundColor Yellow
Write-Host "   cd BackendCodes" -ForegroundColor White
Write-Host "   python sku_matching_api.py" -ForegroundColor White
Write-Host ""
Write-Host "2. Start FastAPI Backend (Terminal 2):" -ForegroundColor Yellow
Write-Host "   cd agentSystem" -ForegroundColor White
Write-Host "   uvicorn app:app --reload --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "3. Start React Frontend (Terminal 3):" -ForegroundColor Yellow
Write-Host "   cd C.O.R.E" -ForegroundColor White
Write-Host "   npm start" -ForegroundColor White
Write-Host ""
Write-Host "4. Access the application:" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Flask API: http://localhost:8080" -ForegroundColor White
Write-Host "   FastAPI: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 For detailed documentation, see:" -ForegroundColor Cyan
Write-Host "   SKU_MATCHING_GUIDE.md" -ForegroundColor White
Write-Host ""
