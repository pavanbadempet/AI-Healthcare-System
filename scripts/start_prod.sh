#!/bin/bash
# ==============================================================================
# AI HEALTHCARE SYSTEM — STARTUP SCRIPT
# ==============================================================================
# Runs uvicorn with Doppler secrets injection if DOPPLER_TOKEN is configured.
# Falls back to standard environment variables if DOPPLER_TOKEN is absent.
# ==============================================================================

# Download models on-demand before starting the server
# Hugging Face Spaces automatically injects a Postgres DATABASE_URL if the add-on is enabled.
# Since the Rust gateway is compiled specifically for SQLite, we must override it here.
# NOTE: SQLAlchemy and SQLx have different URI formats for SQLite!
# If DOPPLER_TOKEN is NOT set, and DATABASE_URL is missing, we use the Neon DB by default.
if [ -z "$DOPPLER_TOKEN" ] && [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DOPPLER_TOKEN and DATABASE_URL are not set. Using local SQLite database."
    export SQLALCHEMY_URL="sqlite:///./healthcare.db"
    export SQLX_URL="sqlite://healthcare.db"
    export DATABASE_URL=$SQLALCHEMY_URL
elif [ -n "$DATABASE_URL" ]; then
    # Normalize DATABASE_URL for Postgres/SQLAlchemy if provided via standard env var
    export SQLALCHEMY_URL=$DATABASE_URL
    export SQLX_URL=$DATABASE_URL
fi

# Download models on-demand before starting the server
echo "Checking model weights..."
python backend/download_models.py

if [ -n "$UPSTASH_KAFKA_SERVERS" ]; then
    echo "UPSTASH_KAFKA_SERVERS detected. Starting PySpark real-time streaming architecture..."
    # 1. Start the Kafka Producer (hospital monitors) in the background
    python scripts/runners/simulate_vitals_stream.py --kafka --kafka-servers "$UPSTASH_KAFKA_SERVERS" &
    # 2. Start the PySpark Consumer (Data Engineering pipeline) in the background
    python scripts/runners/run_telemetry_streaming.py --kafka --kafka-servers "$UPSTASH_KAFKA_SERVERS" &
elif [ -n "$ENABLE_PYSPARK_STREAMING" ]; then
    echo "ENABLE_PYSPARK_STREAMING detected. Starting PySpark local filesystem streaming architecture..."
    # 1. Start the JSON File Producer (hospital monitors) in the background
    python scripts/runners/simulate_vitals_stream.py &
    # 2. Start the PySpark Consumer (Data Engineering pipeline) in the background
    python scripts/runners/run_telemetry_streaming.py &
fi

# Rust gateway is already built via Docker multi-stage build

# Run Python Backend using SOTA IPC Unix Domain Socket on Linux (HF Spaces) and TCP loopback on Windows fallback
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]] || [ -f /proc/self/cgroup ]; then
    if [ -n "$DOPPLER_TOKEN" ]; then
        echo "Starting Python server with Doppler Secrets Manager on Unix Domain Socket /tmp/healthcare.sock..."
        doppler run -- uvicorn backend.main:app --uds /tmp/healthcare.sock --workers 4 &
    else
        echo "DOPPLER_TOKEN not found. Starting Python server on Unix Domain Socket /tmp/healthcare.sock..."
        uvicorn backend.main:app --uds /tmp/healthcare.sock --workers 4 &
    fi
else
    if [ -n "$DOPPLER_TOKEN" ]; then
        echo "Starting Python server with Doppler Secrets Manager on port 8001..."
        doppler run -- uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 4 &
    else
        echo "DOPPLER_TOKEN not found. Starting Python server with standard environment variables on port 8001..."
        uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 4 &
    fi
fi

echo "Initializing database to ensure Rust gateway can connect..."
if [ -n "$DOPPLER_TOKEN" ]; then doppler run -- python -c "from backend.database import engine; from backend.models import Base; Base.metadata.create_all(bind=engine)"; else python -c "from backend.database import engine; from backend.models import Base; Base.metadata.create_all(bind=engine)"; fi

echo "Starting Rust Gateway on port 7860..."
if [ -n "$SQLX_URL" ]; then
    export DATABASE_URL=$SQLX_URL
fi
cd rust_gateway
if [ -n "$DOPPLER_TOKEN" ]; then doppler run -- ./target/release/rust_gateway; else ./target/release/rust_gateway; fi
