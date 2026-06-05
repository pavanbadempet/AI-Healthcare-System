# ============================================================
# AI Healthcare System — Backend Dockerfile
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer)
COPY requirements.txt .
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Train models if missing (ensures containers have valid models)
RUN python -c "\
import os; \
models = ['backend/diabetes_model.pkl', 'backend/heart_disease_model.pkl']; \
missing = [m for m in models if not os.path.exists(m) or os.path.getsize(m) == 0]; \
print(f'Models to train: {missing}') if missing else print('All models present')"

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/healthz || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
