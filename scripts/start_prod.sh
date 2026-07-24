#!/bin/bash
# ==============================================================================
# AI HEALTHCARE SYSTEM — FAILSAFE PRODUCTION STARTUP SCRIPT
# ==============================================================================

PORT="${PORT:-7860}"
echo "Starting AI Healthcare System on port $PORT..."

# Normalize environment variables
export LICENSE_KEY="${LICENSE_KEY:-CLINIC-TRIAL-2026}"
if [ -z "$DOPPLER_TOKEN" ] && [ -z "$DATABASE_URL" ]; then
    echo "DOPPLER_TOKEN and DATABASE_URL not set. Defaulting to local SQLite database."
    export SQLALCHEMY_URL="sqlite:///./healthcare.db"
    export SQLX_URL="sqlite://healthcare.db"
    export DATABASE_URL=$SQLALCHEMY_URL
elif [ -n "$DATABASE_URL" ]; then
    export SQLALCHEMY_URL=$DATABASE_URL
    export SQLX_URL=$DATABASE_URL
fi

# Download models on-demand if needed
echo "Checking model weights..."
python backend/download_models.py || true

# Initialize database schema
echo "Initializing database schema..."
python -c "from backend.database import engine; from backend.models import Base; Base.metadata.create_all(bind=engine)" || true

# Start PySpark or Vitals streaming if configured
if [ -n "$UPSTASH_KAFKA_SERVERS" ]; then
    echo "UPSTASH_KAFKA_SERVERS detected. Starting PySpark Kafka streaming..."
    python scripts/runners/simulate_vitals_stream.py --kafka --kafka-servers "$UPSTASH_KAFKA_SERVERS" &
    python scripts/runners/run_telemetry_streaming.py --kafka --kafka-servers "$UPSTASH_KAFKA_SERVERS" &
elif [ -n "$ENABLE_PYSPARK_STREAMING" ]; then
    echo "ENABLE_PYSPARK_STREAMING detected. Starting local PySpark streaming..."
    python scripts/runners/simulate_vitals_stream.py &
    python scripts/runners/run_telemetry_streaming.py &
fi

# Try starting Rust Gateway if binary exists
RUST_BINARY="./rust_gateway/target/release/rust_gateway"
if [ -f "$RUST_BINARY" ]; then
    echo "Rust Gateway binary found. Attempting to start on socket /tmp/healthcare.sock..."
    uvicorn backend.main:app --uds /tmp/healthcare.sock --workers 4 &
    cd rust_gateway
    if [ -n "$DOPPLER_TOKEN" ]; then
        doppler run -- ./target/release/rust_gateway &
    else
        ./target/release/rust_gateway &
    fi
    RUST_PID=$!
    cd ..
    sleep 2
    if kill -0 $RUST_PID 2>/dev/null; then
        echo "Rust Gateway running on PID $RUST_PID on port $PORT. Holding PID 1..."
        wait $RUST_PID
        echo "Rust Gateway process terminated. Falling back to direct Uvicorn..."
    else
        echo "Rust Gateway failed to run. Falling back to direct Uvicorn on port $PORT..."
    fi
fi

# Primary/Fallback: Direct Uvicorn on $PORT serving FastAPI + React SPA
echo "Launching FastAPI Uvicorn Application directly on port $PORT..."
if [ -n "$DOPPLER_TOKEN" ]; then
    exec doppler run -- uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --workers 4
else
    exec uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --workers 4
fi
