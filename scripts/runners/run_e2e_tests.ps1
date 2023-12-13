$ErrorActionPreference = "Stop"

# --- Cleanup ---
Write-Host "Cleaning up previous state..." -ForegroundColor Cyan
if (Test-Path "healthcare.db") { Remove-Item "healthcare.db" -Force }
if (Test-Path "session.json") { Remove-Item "session.json" -Force }

# --- Start Backend ---
Write-Host "Starting Backend API..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "backend.main:app", "--port", "8000" -PassThru -NoNewWindow

# Wait for Backend
$backendUrl = "http://localhost:8000/docs" # Health check endpoint usually
$maxRetries = 30
$retryCount = 0
$backendReady = $false

Write-Host "Waiting for Backend to be ready at localhost:8000..." -ForegroundColor Yellow
while ($retryCount -lt $maxRetries) {
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $connect = $tcpClient.BeginConnect("localhost", 8000, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(1000, $false)
        
        if ($tcpClient.Connected) {
            $backendReady = $true
            Write-Host "`nBackend is ready!" -ForegroundColor Green
            $tcpClient.Close()
            break
        }
        $tcpClient.Close()
    }
    catch { }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
    $retryCount++
}

if (-not $backendReady) {
    Write-Host "`nBackend failed to start." -ForegroundColor Red
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# --- Start Streamlit ---
Write-Host "`nStarting Streamlit App..." -ForegroundColor Cyan
$appProcess = Start-Process -FilePath "streamlit" -ArgumentList "run", "frontend/main.py", "--server.port=8501", "--server.headless=true" -PassThru -NoNewWindow
$appReady = $false
$retryCount = 0

Write-Host "Waiting for Streamlit to be ready at localhost:8501..." -ForegroundColor Yellow
while ($retryCount -lt $maxRetries) {
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $connect = $tcpClient.BeginConnect("localhost", 8501, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(1000, $false)
        
        if ($tcpClient.Connected) {
            $appReady = $true
            Write-Host "`nStreamlit is ready!" -ForegroundColor Green
            $tcpClient.Close()
            break
        }
        $tcpClient.Close()
    }
    catch { }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
    $retryCount++
}

if (-not $appReady) {
    Write-Host "`nStreamlit failed to start." -ForegroundColor Red
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $appProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# --- Run Tests ---
try {
    Write-Host "`nRunning E2E Tests..." -ForegroundColor Cyan
    python -m pytest tests/e2e/test_full_flow.py

    if ($LASTEXITCODE -eq 0) {
        Write-Host "E2E Tests Passed!" -ForegroundColor Green
    }
    else {
        Write-Host "E2E Tests Failed!" -ForegroundColor Red
        exit 1
    }
}
finally {
    Write-Host "Stopping Services..." -ForegroundColor Cyan
    if ($appProcess) { Stop-Process -Id $appProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($backendProcess) { Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue }
}
