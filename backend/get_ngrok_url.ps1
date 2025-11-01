# PowerShell script to get the current ngrok URL
# This queries the ngrok API to get the forwarding URL

Write-Host "Getting ngrok tunnel URL..." -ForegroundColor Green

try {
    $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get
    $tunnels = $response.tunnels
    
    if ($tunnels -and $tunnels.Count -gt 0) {
        $httpsUrl = $tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
        $httpUrl = $tunnels | Where-Object { $_.proto -eq "http" } | Select-Object -First 1
        
        if ($httpsUrl) {
            Write-Host ""
            Write-Host "✅ ngrok HTTPS URL found!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Your ngrok URL:" -ForegroundColor Cyan
            Write-Host "  $($httpsUrl.public_url)" -ForegroundColor Yellow -BackgroundColor Black
            Write-Host ""
            Write-Host "Update this in: frontend/services/routeService.ts" -ForegroundColor White
            Write-Host "Replace the API_BASE_URL with:" -ForegroundColor White
            Write-Host "  const API_BASE_URL = '$($httpsUrl.public_url)';" -ForegroundColor Yellow
            Write-Host ""
            
            # Copy to clipboard if available
            try {
                $httpsUrl.public_url | Set-Clipboard
                Write-Host "✅ URL copied to clipboard!" -ForegroundColor Green
            } catch {
                # Clipboard not available, that's ok
            }
        } elseif ($httpUrl) {
            Write-Host ""
            Write-Host "⚠️  Only HTTP URL found (HTTPS recommended)" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Your ngrok URL:" -ForegroundColor Cyan
            Write-Host "  $($httpUrl.public_url)" -ForegroundColor Yellow
            Write-Host ""
        } else {
            Write-Host "No tunnels found" -ForegroundColor Red
        }
    } else {
        Write-Host ""
        Write-Host "⚠️  No ngrok tunnels found" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Make sure ngrok is running:" -ForegroundColor Cyan
        Write-Host "  ngrok http 8000" -ForegroundColor White
        Write-Host ""
        Write-Host "Or check: http://localhost:4040" -ForegroundColor White
    }
} catch {
    Write-Host ""
    Write-Host "❌ Could not connect to ngrok API" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "1. ngrok is running: ngrok http 8000" -ForegroundColor White
    Write-Host "2. Check the ngrok web interface: http://localhost:4040" -ForegroundColor White
    Write-Host ""
}

