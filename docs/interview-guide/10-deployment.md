# 10 — Deployment & DevOps

> How the application goes from your laptop to the internet — every step explained.

---

## Q: How is your application deployed?

### The Architecture:

```
YOUR LAPTOP (Development)
├── Frontend: Next.js on localhost:3000
├── Backend: FastAPI on 127.0.0.1:8000
└── Database: SQLite file (healthcare.db)

                    ↓ git push → GitHub → deploy

THE INTERNET (Production)
├── Frontend: Vercel (free tier)
│   └── https://your-app.vercel.app
│   └── Built from /frontend folder
│   └── Connects to backend API via NEXT_PUBLIC_API_URL
│
├── Backend: Render (free tier)
│   └── https://your-api.onrender.com
│   └── Runs: uvicorn backend.main:app --host 0.0.0.0 --port 8000
│   └── Docker container with all dependencies
│
└── Database: Neon (managed PostgreSQL)
    └── postgresql://user:pass@ep-cool.neon.tech/healthcare
    └── Free tier: 0.5GB storage, auto-suspend after 5 min idle
```

### What is Docker? (Explained Simply)

**Problem**: "It works on my machine!" — Your app works on your laptop but breaks on the server because of different Python versions, missing packages, or OS differences.

**Solution**: Docker packages your application + ALL its dependencies into a container — a standardized box that runs identically everywhere.

**Analogy**: Shipping containers in the real world. Before containers, cargo was loaded loosely onto ships — things broke, got mixed up, were hard to move. Shipping containers standardized everything. Docker does the same for software.

```dockerfile
# Dockerfile — recipe for building the container

# Step 1: Start from a known base image (Python 3.11 on Linux)
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# This installs EXACT versions of every package
# --no-cache-dir saves disk space in the container

# Step 4: Copy your application code
COPY backend/ ./backend/
COPY data/ ./data/

# Step 5: Expose port 8000 (where FastAPI listens)
EXPOSE 8000

# Step 6: Command to run when container starts
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Docker concepts:**
- **Image**: The blueprint (your Dockerfile baked into a binary). Like a recipe.
- **Container**: A running instance of an image. Like the actual cake made from the recipe.
- **Registry**: Where images are stored (Docker Hub, GitHub Container Registry). Like a recipe book.
- **Layer**: Each instruction in Dockerfile creates a layer. Layers are cached — if `requirements.txt` hasn't changed, Docker reuses the cached layer instead of reinstalling everything.

### What is Docker Compose?

Docker Compose runs MULTIPLE containers together. Your app needs frontend + backend + database:

```yaml
# docker-compose.yml
version: "3.8"

services:
  backend:
    build: .                        # Build from Dockerfile
    ports:
      - "8000:8000"                 # Map host:container port
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/healthcare
      - GEMINI_API_KEY=${GEMINI_API_KEY}  # From .env file
    depends_on:
      - db                          # Start database FIRST

  db:
    image: postgres:16              # Official PostgreSQL image
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=healthcare
    volumes:
      - pgdata:/var/lib/postgresql/data  # Persist data across restarts

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

volumes:
  pgdata:  # Named volume for database persistence
```

**Run everything with ONE command:**
```bash
docker-compose up -d
# Starts: PostgreSQL → Backend → Frontend
# -d = detached (runs in background)
```

---

## Q: How do you handle environment configuration?

**The problem**: Development and production need different settings. You can't hardcode "localhost" in production or production database URLs in development.

**The solution**: Environment variables. Same code, different config.

```python
# backend/database.py
import os

# ONE line of code handles both environments:
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")
#                        ↑                ↑
#                   If env var exists     If env var is NOT set
#                   (production)          (development default)
```

### Environment Variable Comparison:

| Variable | Development | Production |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./healthcare.db` | `postgresql://user:pass@neon.tech/db` |
| `SECRET_KEY` | `dev-fallback-key` | `a8f2k9x1m...` (random 64 chars) |
| `GEMINI_API_KEY` | Your API key | Production API key |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | `https://your-api.onrender.com` |
| `DEBUG` | `true` | `false` |

### How environment variables are managed:

```bash
# LOCAL DEVELOPMENT — .env file (NEVER committed to git!)
# .env
DATABASE_URL=sqlite:///./healthcare.db
SECRET_KEY=dev-fallback-key-not-for-production
GEMINI_API_KEY=AIzaSy...your-key...

# .gitignore includes:
.env          # NEVER commit secrets to git!
*.db          # Don't commit SQLite database
__pycache__/  # Don't commit compiled Python files

# PRODUCTION — Set in Render/Vercel dashboard
# Render → Service → Environment → Add Variable
# DATABASE_URL = postgresql://...
# SECRET_KEY = (generated secure random string)
```

**Security rule**: NEVER commit `.env` to git. If you accidentally commit a secret, rotate it immediately — git history retains it forever even after deletion.

---

## Q: What is CI/CD?

**CI (Continuous Integration)** = Automatically test code when you push to GitHub.
**CD (Continuous Deployment)** = Automatically deploy code when tests pass.

```
Developer pushes code
        ↓
GitHub Actions runs:
  ├── Install dependencies
  ├── Run linting (code style checks)
  ├── Run pytest (141 unit tests + 28 integration)
  │     ├── All pass? → Continue
  │     └── Any fail? → STOP. Don't deploy. Notify developer.
  └── All green? → Deploy automatically
        ↓
Render pulls latest code → Builds Docker image → Deploys
Vercel pulls latest code → Builds Next.js → Deploys
```

### What a GitHub Actions workflow looks like:

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main]        # Run on every push to main
  pull_request:
    branches: [main]        # Run on every PR targeting main

jobs:
  test:
    runs-on: ubuntu-latest  # Free Linux VM from GitHub

    steps:
      - uses: actions/checkout@v4          # Download your code

      - uses: actions/setup-python@v5      # Install Python
        with:
          python-version: "3.11"

      - run: pip install -r requirements.txt  # Install dependencies

      - run: python -m pytest tests/ -v       # Run all tests
        env:
          DATABASE_URL: sqlite:///./test.db   # Use test database
          # Tests must NOT depend on external APIs (mock everything)
```

---

## Q: How does Render deployment work?

```
1. You push code to GitHub
        ↓
2. Render detects the push (webhook)
        ↓
3. Render builds your Docker image
   - Installs Python 3.11
   - pip install -r requirements.txt
   - Copies your code
        ↓
4. Render starts the container
   - Runs: uvicorn backend.main:app --host 0.0.0.0 --port 8000
   - Sets environment variables from dashboard
        ↓
5. Render routes traffic to your container
   - URL: https://your-api.onrender.com
   - Free tier: spins down after 15 minutes of inactivity
   - First request after spin-down takes ~30 seconds (cold start)
```

**Cold start** = When Render spins down your service to save resources, the next request has to wait for the container to start up again. This is normal on free tier. On paid tier, the service stays warm.

---

## Q: What's the difference between Vercel and Render?

| | Vercel | Render |
|---|---|---|
| Best for | Frontend (Next.js, React) | Backend (APIs, Docker) |
| Your usage | Next.js frontend | FastAPI backend |
| Free tier | Very generous | 750 hours/month |
| Cold starts | None (edge functions) | ~30 seconds on free tier |
| Custom domain | Yes | Yes |
| SSL/HTTPS | Automatic | Automatic |
| Build process | Next.js optimized | Docker-based |

---

## Q: How do you ensure development and production are in sync?

| Practice | Implementation |
|---|---|
| Same code, different config | Environment variables (`DATABASE_URL`, `SECRET_KEY`) |
| Same dependencies | `requirements.txt` pinned versions (`fastapi==0.115.12`) |
| Same runtime | Docker ensures identical Python version and OS |
| Same database schema | SQLAlchemy creates tables on startup, runs migrations |
| Same tests | CI runs the exact same test suite before every deploy |
| Same API contract | Pydantic models validate requests in both environments |
