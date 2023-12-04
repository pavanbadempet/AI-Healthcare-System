@echo off
echo Starting AIO Healthcare System (NiceGUI)...
echo.
REM Kill existing processes
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

REM Start Backend (Port 8000)
start /B "Backend API" cmd /c "uvicorn backend.main:app --host 127.0.0.1 --port 8000 --log-level error"

echo Waiting for backend...
timeout /t 5 /nobreak >nul

REM Start NiceGUI (Port 8080)
python main_nicegui.py
pause
