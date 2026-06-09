# =======================================================
# AI HEALTHCARE - HUGGING FACE SPACES BACKEND & FRONTEND
# =======================================================
# Hugging Face Spaces (Docker Space) requires port 7860
# and running as a non-root user (uid 1000).
# =======================================================

# Stage 1: Build Frontend React SPA
FROM node:26-alpine AS frontend-builder
WORKDIR /build

# Copy frontend package list and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build the production bundle
COPY frontend/ ./
RUN npm run build

# Stage 2: Final image with Python backend and frontend assets
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user required by Hugging Face Spaces
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy requirements
COPY --chown=user backend/requirements.txt $HOME/app/backend/requirements.txt
COPY --chown=user requirements.txt $HOME/app/

# Install dependencies based on backend requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy source code
COPY --chown=user . $HOME/app/

# Copy built frontend assets from Stage 1 to home app dir
COPY --from=frontend-builder --chown=user /build/dist $HOME/app/frontend/dist

# Generate placeholder AI models (so the backend doesn't crash if models are missing)
RUN python scripts/generate_placeholder_models.py

# Expose the specific port Hugging Face Spaces uses
EXPOSE 7860

# Run FastAPI backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
