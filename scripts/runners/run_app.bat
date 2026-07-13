@echo off
echo ========================================
echo      Stopping Old Processes...
echo ========================================
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
echo Done.

echo.
echo ========================================
echo      Starting Backend Server...
echo ========================================
start cmd /k "uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

echo.
echo ========================================
echo      Starting MLflow Dashboard...
echo ========================================
start cmd /k "mlflow ui"

echo.
echo Waiting 3 seconds for backend to start...
timeout /t 3

echo.
echo ========================================
echo      Starting Healthcare Frontend...
echo ========================================
cd /d frontend
npm run dev -- -H 127.0.0.1 -p 3000
pause
