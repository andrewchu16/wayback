# PowerShell script to start backend with ngrok tunnel
# This will start the backend server and ngrok in one go

Write-Host "Starting Route Finder Backend with ngrok..." -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check if backend server is already running
$serverRunning = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($serverRunning) {
    Write-Host "Backend server is already running on port 8000" -ForegroundColor Yellow
    Write-Host "Starting ngrok tunnel..." -ForegroundColor Cyan
} else {
    Write-Host "Starting backend server..." -ForegroundColor Cyan
    
    # Start backend in background
    $backendProcess = Start-Process python -ArgumentList "start_server.py" -PassThru -WorkingDirectory $PSScriptRoot -WindowStyle Minimized
    
    Write-Host "Waiting for server to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    Write-Host "Backend server started (PID: $($backendProcess.Id))" -ForegroundColor Green
    Write-Host "Starting ngrok tunnel..." -ForegroundColor Cyan
}

# Start ngrok
Start-Process ngrok -ArgumentList "http", "8000" -WindowStyle Normal

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "ngrok tunnel is starting..." -ForegroundColor Yellow
Write-Host "A browser window should open with the ngrok dashboard" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Copy the 'Forwarding' URL from ngrok (e.g., https://abc123.ngrok.io)" -ForegroundColor White
Write-Host "2. Update frontend/services/routeService.ts with that URL" -ForegroundColor White
Write-Host "3. Make sure to use HTTPS (not HTTP)" -ForegroundColor White
Write-Host ""
Write-Host "Your ngrok URL will be something like:" -ForegroundColor Cyan
Write-Host "  https://xxxx-xxxx-xxxx-xxxx.ngrok-free.app" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in this window to stop everything" -ForegroundColor Yellow

