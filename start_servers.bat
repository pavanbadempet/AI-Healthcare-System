@echo off
echo ===================================================
echo    Starting AI Healthcare System Servers
echo ===================================================
echo.

echo [1/2] Starting FastAPI Backend on port 8000...
start "AI Healthcare - Backend" cmd /c "uvicorn backend.main:app --reload --port 8000"

echo [2/2] Starting Next.js Frontend on port 3000...
start "AI Healthcare - Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo Both servers are booting up in separate windows!
echo - Backend API will be available at: http://localhost:8000
echo - Frontend UI will be available at: http://localhost:3000
echo.
echo You can close this window now. Close the newly opened terminal windows to stop the servers.
pause
