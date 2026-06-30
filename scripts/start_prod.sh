#!/bin/bash
# ==============================================================================
# AI HEALTHCARE SYSTEM — STARTUP SCRIPT
# ==============================================================================
# Runs uvicorn with Doppler secrets injection if DOPPLER_TOKEN is configured.
# Falls back to standard environment variables if DOPPLER_TOKEN is absent.
# ==============================================================================

# Download models on-demand before starting the server
echo "Checking model weights..."
python backend/download_models.py

if [ -n "$DOPPLER_TOKEN" ]; then
    echo "Starting server with Doppler Secrets Manager..."
    exec doppler run -- uvicorn backend.main:app --host 0.0.0.0 --port 7860
else
    echo "DOPPLER_TOKEN not found. Starting server with standard environment variables..."
    exec uvicorn backend.main:app --host 0.0.0.0 --port 7860
fi
