@echo off
echo ===================================================
echo     AI HEALTHCARE SYSTEM - PRODUCTION RUNNER
echo ===================================================
echo.
echo [1/3] Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [2/3] Starting Pure Rust Gateway (Axum 0.8, Tokio, ORT ONNX)...
set ENV=production
set ENVIRONMENT=production
if exist rust_gateway\target\release\rust_gateway.exe (
    start /B "Rust Gateway" cmd /c "rust_gateway\target\release\rust_gateway.exe"
) else (
    start /B "Rust Gateway" cmd /c "cargo run --release --manifest-path rust_gateway/Cargo.toml --bin rust_gateway"
)

echo Waiting for Rust Gateway initialization...
timeout /t 5 /nobreak >nul

echo [3/3] Launching Client Dashboard (Bun + React Vite)...
start "Healthcare Interface" cmd /c "cd /d frontend && bun run build && bun run start"

echo.
echo ---------------------------------------------------
echo System Online: http://127.0.0.1:3000 (Gateway: http://127.0.0.1:8000)
echo ---------------------------------------------------
timeout /t 3 >nul
start http://127.0.0.1:3000
echo Press any key to shutdown...
pause >nul

echo Shutting down...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo Done.
