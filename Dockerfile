# ==============================================================================
# AI HEALTHCARE SYSTEM — UNIFIED PRODUCTION DOCKERFILE (RUST + BUN)
# ==============================================================================
# Dual-tier high-performance architecture:
# Tier 1 (PID 1): Bun + ElysiaJS Edge Gateway & API Orchestration Layer
# Tier 2 (Compute): Rust Axum/Tokio Backend Server + ONNX Runtime (Zero Python)
# Compatible with Hugging Face Spaces (Port 7860, UID 1000), AWS EKS, and Docker Compose.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend React 19 SPA
# ------------------------------------------------------------------------------
FROM oven/bun:1.2-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile || bun install

COPY frontend/ ./
RUN bun run build

# ------------------------------------------------------------------------------
# Stage 2: Build Rust Gateway & ONNX Inference Server
# ------------------------------------------------------------------------------
FROM rust:latest AS rust-builder
RUN apt-get update && apt-get install -y protobuf-compiler libssl-dev pkg-config && rm -rf /var/lib/apt/lists/*
WORKDIR /build

COPY rust_gateway/ ./rust_gateway/
WORKDIR /build/rust_gateway
RUN cargo build --release

# ------------------------------------------------------------------------------
# Stage 3: Unified Production Runtime (Bun + Rust, Zero Python)
# ------------------------------------------------------------------------------
FROM oven/bun:debian AS runtime

# Install system runtime libraries (SSL, curl for healthchecks)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Set up app directory permissions while root
RUN mkdir -p /home/bun/app/backend /home/bun/app/models /home/bun/app/frontend/dist /home/bun/app/edge_gateway /home/bun/app/rust_gateway/target/release && \
    chown -R 1000:1000 /home/bun

# Switch to non-root user (UID 1000)
USER 1000
ENV HOME=/home/bun \
    PATH=/home/bun/.local/bin:$PATH \
    PORT=7860 \
    HOST=0.0.0.0 \
    RUST_BACKEND_URL=http://127.0.0.1:8001 \
    RUST_WS_URL=ws://127.0.0.1:8001 \
    STATIC_DIR=/home/bun/app/frontend/dist \
    DATABASE_URL=sqlite:///home/bun/app/healthcare.db

WORKDIR /home/bun/app

# Copy built Rust Gateway binary from Stage 2
COPY --from=rust-builder --chown=1000:1000 /build/rust_gateway/target/release/rust_gateway /home/bun/app/rust_gateway/target/release/rust_gateway

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder --chown=1000:1000 /build/dist /home/bun/app/frontend/dist

# Copy Edge Gateway source and install production dependencies
COPY --chown=1000:1000 edge_gateway/ /home/bun/app/edge_gateway/
WORKDIR /home/bun/app/edge_gateway
RUN bun install --production

WORKDIR /home/bun/app

# Copy application files
COPY --chown=1000:1000 . /home/bun/app/

# Ensure executable permissions
RUN chmod +x /home/bun/app/scripts/start_prod.sh && \
    chmod +x /home/bun/app/rust_gateway/target/release/rust_gateway

# Expose ports (7860 for Hugging Face Spaces / default, 8000 for standard HTTP)
EXPOSE 7860 8000 8001

# Health check against edge gateway health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT}/healthz/live || exit 1

# Start unified Rust + Bun dual stack via startup orchestrator
CMD ["bash", "scripts/start_prod.sh"]
