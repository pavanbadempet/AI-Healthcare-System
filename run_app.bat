@echo off
echo ========================================
echo      Stopping Old Processes...
echo ========================================
taskkill /F /IM python.exe /T >nul 2>&1
echo Done.

echo.
echo ========================================
echo      Starting Backend Server...
echo ========================================
start cmd /k "uvicorn backend.main:app --reload"

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
streamlit run Healthcare-System.py
pause
