# ============================================================
# AI Healthcare System — Backend Dockerfile (Multi-Stage)
# ============================================================
# Stage 1: Build dependencies (cached independently from code)
# Stage 2: Runtime with only production dependencies
# ============================================================

# --- Stage 1: Dependency Builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency manifests for layer caching
COPY requirements.txt .
COPY backend/requirements.txt ./backend/requirements.txt

# Install Python dependencies to a separate prefix
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Production Runtime ---
FROM python:3.12-slim

WORKDIR /app

# Install only runtime system dependencies (no build-essential)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code (changes frequently — last layer)
COPY . .

# Train models if missing (ensures containers have valid models)
RUN python -c "\
import os; \
models = ['backend/diabetes_model.pkl', 'backend/heart_disease_model.pkl']; \
missing = [m for m in models if not os.path.exists(m) or os.path.getsize(m) == 0]; \
print(f'Models to train: {missing}') if missing else print('All models present')"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/healthz || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
