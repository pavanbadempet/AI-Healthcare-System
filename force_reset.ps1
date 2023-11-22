# Force Reset Script
Write-Host "Stopping all Python processes..."
taskkill /F /IM python.exe /T

Start-Sleep -Seconds 2

Write-Host "Deleting Database..."
if (Test-Path "healthcare.db") {
    Remove-Item "healthcare.db" -Force
    Write-Host "Database deleted."
} else {
    Write-Host "Database not found (already clean)."
}

Write-Host "Clearing Session..."
if (Test-Path "session.json") {
    Remove-Item "session.json" -Force
    Write-Host "Session cleared."
}

Write-Host "Cleanup Complete."
Write-Host "You can now run 'run_app.bat' to start fresh."
