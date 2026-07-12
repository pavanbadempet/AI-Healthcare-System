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
if [ -z "$DATABASE_URL" ]; then
    if [ -d "/data" ]; then
        export SQLALCHEMY_URL="sqlite:////data/healthcare.db"
        export SQLX_URL="sqlite:///data/healthcare.db"
    else
        export SQLALCHEMY_URL="sqlite:///healthcare.db"
        export SQLX_URL="sqlite://../healthcare.db"
    fi
    export DATABASE_URL=$SQLALCHEMY_URL
else
    # Normalize DATABASE_URL for Postgres/SQLAlchemy
    export SQLALCHEMY_URL=$DATABASE_URL
    export SQLX_URL=$DATABASE_URL
fi

# Download models on-demand before starting the server
echo "Checking model weights..."
python backend/download_models.py

echo "Building Rust API Gateway..."
cd rust_gateway && cargo build --release && cd ..

if [ -n "$DOPPLER_TOKEN" ]; then
    echo "Starting Python server with Doppler Secrets Manager on port 8001..."
    doppler run -- uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 4 &
else
    echo "DOPPLER_TOKEN not found. Starting Python server with standard environment variables on port 8001..."
    uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 4 &
fi

echo "Initializing database to ensure Rust gateway can connect..."
python -c "from backend.database import engine; from backend.models import Base; Base.metadata.create_all(bind=engine)"

echo "Starting Rust Gateway on port 7860..."
export DATABASE_URL=$SQLX_URL
cd rust_gateway
exec ./target/release/rust_gateway
