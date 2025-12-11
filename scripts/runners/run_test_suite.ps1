# PowerShell Test Runner
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    AIO HEALTHCARE - AUTOMATED QA SUITE    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Run Unit Tests (Backend Logic)
Write-Host "`n[STEP 1] Running Unit Tests..." -ForegroundColor Yellow
python -m pytest tests/unit/test_auth_logic.py --disable-warnings
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Unit Tests Passed" -ForegroundColor Green } else { Write-Host "❌ Unit Tests Failed" -ForegroundColor Red; exit 1 }

# 2. Run Integration Tests (API Layer)
Write-Host "`n[STEP 2] Running Integration Tests (API)..." -ForegroundColor Yellow
python -m pytest tests/integration/test_api_endpoints.py --disable-warnings
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Integration Tests Passed" -ForegroundColor Green } else { Write-Host "❌ Integration Tests Failed" -ForegroundColor Red; exit 1 }

# 3. Code Coverage Report
Write-Host "`n[STEP 3] Generating Coverage Report..." -ForegroundColor Yellow
python -m pytest --cov=backend tests/unit tests/integration --cov-report=term-missing --disable-warnings

Write-Host "`n🎉 ALL TESTS PASSED! System is healthy." -ForegroundColor Green
Write-Host "To run full E2E UI tests (Browser), run: .\run_e2e_tests.ps1" -ForegroundColor Gray
