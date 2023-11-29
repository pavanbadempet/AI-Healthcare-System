@echo off
setlocal

echo ====================================================
echo   AIO Healthcare System - Complete Verification
echo ====================================================

echo.
echo [1/3] Running Backend Unit and Integration Tests...
echo ----------------------------------------------------
pytest tests/unit tests/integration --cov=backend
if %errorlevel% neq 0 (
    echo [ERROR] Backend Tests Failed!
    exit /b %errorlevel%
)
echo [PASS] Backend Verified.

echo.
echo [2/3] Running MLOps Pipeline Tests...
echo ----------------------------------------------------
pytest tests/unit/test_mlops.py
if %errorlevel% neq 0 (
    echo [ERROR] MLOps Pipeline Tests Failed!
    exit /b %errorlevel%
)
echo [PASS] MLOps Verified.

echo.
echo [3/3] Running Frontend E2E Tests (Playwright)...
echo [NOTE] The application must be running at http://localhost:8501
echo ----------------------------------------------------
pytest tests/e2e/test_ui.py
if %errorlevel% neq 0 (
    echo [WARNING] UI Tests Failed. Ensure the app is running!
) else (
    echo [PASS] Frontend Verified.
)

echo.
echo ====================================================
echo   FULL SYSTEM VERIFICATION COMPLETE
echo ====================================================
pause
