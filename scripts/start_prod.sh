#!/usr/bin/env bash
# ==============================================================================
# AI HEALTHCARE SYSTEM — UNIFIED PRODUCTION STARTUP ORCHESTRATOR
# ==============================================================================
# Starts Tier 2 Rust Backend Server (Axum + Tokio + ONNX Runtime) on port 8001
# Starts Tier 1 Bun ElysiaJS Edge Gateway (BFF + Static SPA) on $PORT (7860/8000)
# Zero Python dependency.
# ==============================================================================

set -e

PORT="${PORT:-7860}"
RUST_PORT="${RUST_PORT:-8001}"
RUST_BACKEND_URL="${RUST_BACKEND_URL:-http://127.0.0.1:8001}"
RUST_BINARY="${RUST_BINARY:-./rust_gateway/target/release/rust_gateway}"

echo "======================================================================"
echo "  AI HEALTHCARE SYSTEM — UNIFIED PRODUCTION BOOTSTRAP"
echo "======================================================================"
echo "  🚀 Edge Gateway Port : $PORT"
echo "  ⚡ Rust Backend Port : $RUST_PORT"
echo "  🔗 Upstream Route    : $RUST_BACKEND_URL"
echo "======================================================================"

# 1. Start Rust Backend Server in background
echo "[BOOT] Launching Rust Backend Server on port $RUST_PORT..."
export PORT="$RUST_PORT"
if [ -f "$RUST_BINARY" ]; then
    "$RUST_BINARY" &
    RUST_PID=$!
elif [ -f "./rust_gateway" ]; then
    ./rust_gateway &
    RUST_PID=$!
else
    echo "Rust binary not found at $RUST_BINARY. Attempting cargo run..."
    (cd rust_gateway && cargo run --release) &
    RUST_PID=$!
fi

# 2. Wait for Rust Backend to become healthy
echo "[BOOT] Awaiting Rust Backend health readiness..."
READY=0
for i in $(seq 1 30); do
    if curl -s -f "http://127.0.0.1:${RUST_PORT}/health" > /dev/null 2>&1 || \
       curl -s -f "http://127.0.0.1:${RUST_PORT}/healthz_rust" > /dev/null 2>&1; then
        echo "[BOOT] Rust Backend is HEALTHY and listening on port $RUST_PORT (took ${i}s)."
        READY=1
        break
    fi
    sleep 1
done

if [ "$READY" -ne 1 ]; then
    echo "[WARN] Rust backend readiness check timed out. Proceeding to launch edge gateway..."
fi

# 3. Handle shutdown signals to clean up background processes
trap "echo 'Shutting down AI Healthcare Stack...'; kill -TERM $RUST_PID 2>/dev/null || true; exit 0" SIGINT SIGTERM EXIT

# 4. Launch Bun ElysiaJS Edge Gateway as foreground PID 1 process
echo "[BOOT] Launching Bun ElysiaJS Edge Gateway on port $PORT..."
export PORT="$PORT"
export RUST_BACKEND_URL="$RUST_BACKEND_URL"

if [ -d "edge_gateway" ]; then
    cd edge_gateway
    exec bun run src/index.ts
else
    exec bun run src/index.ts
fi
