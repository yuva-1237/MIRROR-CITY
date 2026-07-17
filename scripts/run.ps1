# Mirror City Platform Bootstrapper for Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "🚀 MIRROR CITY — AI-Powered Smart City Digital Twin" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan

# 1. Seed Database
Write-Host "📦 Stage 1: Seeding SQLite database and generating city graph..." -ForegroundColor Yellow
try {
    python database/seed.py
    Write-Host "✅ Seeding successful!" -ForegroundColor Green
} catch {
    Write-Host "❌ Seeding failed. Ensure Python 3 is on your system path." -ForegroundColor Red
    exit 1
}

# 2. Check and Install Node Modules
if (-not (Test-Path "frontend/node_modules")) {
    Write-Host "📥 Stage 2: Installing frontend Node dependencies..." -ForegroundColor Yellow
    Push-Location frontend
    try {
        npm install
        Write-Host "✅ NPM install complete!" -ForegroundColor Green
    } catch {
        Write-Host "❌ NPM install failed. Make sure Node.js is installed." -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
} else {
    Write-Host "✅ Stage 2: Node modules already installed. Skipping." -ForegroundColor Green
}

# 3. Spin up API server in a separate process
Write-Host "📡 Stage 3: Booting FastAPI backend on http://localhost:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python backend/main.py" -Title "Mirror City - FastAPI Backend"

# 4. Spin up Frontend dev server in a separate process
Write-Host "💻 Stage 4: Booting React Vite app on http://localhost:5173..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -Title "Mirror City - React Frontend"

Write-Host "--------------------------------------------------------" -ForegroundColor Green
Write-Host "🎉 SUCCESS: Both servers are booting up in the background!" -ForegroundColor Green
Write-Host "👉 API docs available at: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "👉 Open Dashboard at: http://localhost:5173" -ForegroundColor Green
Write-Host "--------------------------------------------------------" -ForegroundColor Green
