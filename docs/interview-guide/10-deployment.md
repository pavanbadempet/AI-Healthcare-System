# 10 — Deployment & DevOps

## Q: How do you deploy the backend?

**Platform**: Render.com (or any Docker-capable host)

```
GitHub Push → Render auto-deploys → Uvicorn starts → Models loaded
```

**Start command:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Environment variables on Render:**
```
DATABASE_URL=postgresql://user:pass@host/db
GEMINI_API_KEY=<key>
SECRET_KEY=<jwt-secret>
RAZORPAY_KEY_ID=<key>
RAZORPAY_KEY_SECRET=<secret>
```

## Q: How do you deploy the frontend?

**Platform**: Vercel or Render

```bash
npm run build   # Generates .next/ directory
npm start       # Serves on port 3000
```

**Environment variable:**
```
NEXT_PUBLIC_API_URL=https://aio-health-backend.onrender.com
```

## Q: Do you have Docker support?

Yes. Example Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ backend/
COPY data/ data/

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose** (full stack):
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/healthcare
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=healthcare
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

## Q: How would you set up CI/CD?

```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run unit tests
        run: python -m pytest tests/ -v
        env:
          TESTING: "1"
      
      - name: Build frontend
        run: cd frontend && npm ci && npm run build

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Render
        run: curl -X POST $RENDER_DEPLOY_HOOK
```

## Q: How do you handle different environments?

| Variable | Development | Production |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./healthcare.db` | `postgresql://...` |
| `GEMINI_API_KEY` | Local `.env` file | Render env vars |
| `SECRET_KEY` | `dev-secret` | Strong random string |
| `CORS origins` | `http://127.0.0.1:3000` | `https://yourdomain.com` |
| `TrustedHost` | `127.0.0.1` | `yourdomain.com` |
| `TESTING` | `1` (in test runs) | Not set |

## Q: How do model files get deployed?

Models are committed to git (~1.6MB total). On deploy:
1. Git clone includes `.pkl` files
2. FastAPI lifespan loads them at startup
3. Models stay in RAM

**For larger models** (>100MB): Use cloud storage (S3/GCS), download during Docker build or startup.
