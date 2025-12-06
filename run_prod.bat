@echo off
echo ===================================================
echo     AIO HEALTHCARE SYSTEM - ENTERPRISE EDITION
echo ===================================================
echo.
echo [1/3] Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8501" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [2/3] Starting Secure Backend API...
start /B "Backend API" cmd /c "uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-server-header --log-level error"

echo Waiting for backend...
timeout /t 5 /nobreak >nul

echo [3/3] Launching Client Dashboard...
start "Healthcare Interface" cmd /c "streamlit run Healthcare-System.py --server.port 8501 --server.address 127.0.0.1 --server.headless true --ui.hideTopBar true --theme.base dark"

echo.
echo ---------------------------------------------------
echo System Online: http://127.0.0.1:8501
echo ---------------------------------------------------
echo Press any key to shutdown...
pause >nul

echo Shutting down...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8501" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo Done.
