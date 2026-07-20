# =======================================================
# AI HEALTHCARE - HUGGING FACE SPACES BACKEND & FRONTEND
# =======================================================
# Hugging Face Spaces (Docker Space) requires port 7860
# and running as a non-root user (uid 1000).
# =======================================================

# Stage 1: Build Frontend React SPA
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# Copy frontend package list and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build the production bundle
COPY frontend/ ./
RUN npx vite build

# Stage 2: Build Rust Gateway
FROM rust:latest AS rust-builder
RUN apt-get update && apt-get install -y protobuf-compiler python3-dev
WORKDIR /build

# Copy rust gateway source and build it
COPY rust_gateway/ ./rust_gateway/
WORKDIR /build/rust_gateway
RUN cargo build --release


# Stage 3: Final image with Python backend, frontend assets, and Rust gateway
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ca-certificates \
    gnupg \
    && curl -sLf --retry 3 https://cli.doppler.com/install.sh | sh \
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

# Install local private packages
RUN pip install --no-cache-dir \
    ./packages/fastapi-license-gate \
    ./packages/clinical-tabular \
    ./packages/clinical-fhir-abdm \
    ./packages/clinical-rag-cache

# Copy built frontend assets from Stage 1 to home app dir
COPY --from=frontend-builder --chown=user /build/dist $HOME/app/frontend/dist

# Copy built Rust gateway from Stage 2
COPY --from=rust-builder --chown=user /build/rust_gateway/target/release/rust_gateway $HOME/app/rust_gateway/target/release/rust_gateway

# Download AI model weights from Hugging Face Model Registry
RUN python backend/download_models.py

# Make startup script executable
RUN chmod +x scripts/start_prod.sh

# Expose the specific port Hugging Face Spaces uses
EXPOSE 7860

# Run FastAPI backend with Doppler/standard fallback
CMD ["bash", "scripts/start_prod.sh"]

