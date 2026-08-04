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
    echo "UPSTASH_KAFKA_SERVERS detected. Starting PySpark Kafka streaming in background..."
    python scripts/runners/simulate_vitals_stream.py --kafka --kafka-servers "$UPSTASH_KAFKA_SERVERS" > /dev/null 2>&1 &
    python scripts/runners/run_telemetry_streaming.py --kafka --kafka-servers "$UPSTASH_KAFKA_SERVERS" > /dev/null 2>&1 &
elif [ "$ENABLE_PYSPARK_STREAMING" = "true" ] || [ "$ENABLE_PYSPARK_STREAMING" = "1" ]; then
    echo "ENABLE_PYSPARK_STREAMING detected. Starting local PySpark streaming in background..."
    python scripts/runners/simulate_vitals_stream.py > /dev/null 2>&1 &
    python scripts/runners/run_telemetry_streaming.py > /dev/null 2>&1 &
fi

WORKERS="${WEB_CONCURRENCY:-1}"
RUST_BINARY="./rust_gateway/target/release/rust_gateway"
ENABLE_RUST_GATEWAY="${ENABLE_RUST_GATEWAY:-1}"

# On Hugging Face Spaces (detected by SPACE_ID or SPACES_ID), run Uvicorn directly
# using in-process PyO3 Rust FFI bindings to avoid UNIX domain socket IPC contention on shared vCPUs.
if [ -n "$SPACE_ID" ] || [ -n "$SPACES_ID" ]; then
    echo "Hugging Face Space detected ($SPACE_ID). Running high-throughput direct Uvicorn with PyO3 Rust FFI..."
    ENABLE_RUST_GATEWAY=0
fi

if [ -f "$RUST_BINARY" ] && [ "$ENABLE_RUST_GATEWAY" != "0" ]; then
        echo "Starting FastAPI Uvicorn background worker on socket /tmp/healthcare.sock..."
        if [ -n "$DOPPLER_TOKEN" ]; then
            doppler run -- uvicorn backend.main:app --uds /tmp/healthcare.sock --workers "$WORKERS" &
        else
            uvicorn backend.main:app --uds /tmp/healthcare.sock --workers "$WORKERS" &
        fi

        echo "Waiting for Uvicorn domain socket /tmp/healthcare.sock to be ready..."
        for i in {1..30}; do
            if [ -S "/tmp/healthcare.sock" ]; then
                echo "Domain socket ready."
                break
            fi
            sleep 1
        done

        echo "Launching Rust Gateway as PRIMARY PID 1 on port $PORT..."
        cd rust_gateway
        if [ -n "$DOPPLER_TOKEN" ]; then
            exec doppler run -- ./target/release/rust_gateway
        else
            exec ./target/release/rust_gateway
        fi
fi


echo "Running FastAPI Uvicorn directly as PRIMARY PID 1 on port $PORT with $WORKERS worker(s)..."
if [ -n "$DOPPLER_TOKEN" ]; then
    exec doppler run -- uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
else
    exec uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
fi
