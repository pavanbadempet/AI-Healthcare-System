@echo off
echo ===================================================
echo     AI HEALTHCARE SYSTEM
echo ===================================================
echo.
echo [1/3] Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [2/3] Starting Secure Backend API...
start /B "Backend API" cmd /c "uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-server-header --log-level debug"

echo Waiting for backend (Model Loading)...
timeout /t 15 /nobreak >nul

echo [3/3] Launching Client Dashboard...
start "Healthcare Interface" cmd /c "cd /d frontend && npm run build && npm run start -- -p 3000"

echo.
echo ---------------------------------------------------
echo System Online: http://127.0.0.1:3000
echo ---------------------------------------------------
timeout /t 3 >nul
start http://127.0.0.1:3000
echo Press any key to shutdown...
pause >nul

echo Shutting down...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo Done.
