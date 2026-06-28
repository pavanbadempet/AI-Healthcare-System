# Claude Developer Guide (CLAUDE.md)

This guide documents the core commands, build instructions, and styling guidelines for developing in the AI Healthcare System using Claude.

## Core Commands

### 1. Backend Development
- **Run API Server (reload mode):**
  ```bash
  uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
  ```
- **Execute Pytest Suite (parallelized):**
  ```bash
  python -m pytest tests/ -n auto -v
  ```
- **Execute Pytest (single test):**
  ```bash
  python -m pytest tests/unit/test_auth.py -v -o addopts=""
  ```

### 2. Frontend Development
- **Install Dependencies:**
  ```bash
  npm --prefix frontend install
  ```
- **Run Developer Server:**
  ```bash
  npm --prefix frontend run dev
  ```
- **Build Production SPA:**
  ```bash
  npm --prefix frontend run build
  ```
- **Run Unit Tests (Vitest):**
  ```bash
  npm --prefix frontend run test
  ```
- **Run E2E Tests (Playwright):**
  ```bash
  npm --prefix frontend run test:e2e
  ```

### 3. Repository CLI Dashboard
- **Run terminal TUI dashboard:**
  ```bash
  python scripts/clinic_dashboard.py
  ```

## Code Guidelines

- **Linting & Formatting:** Always run Ruff to format and check code before committing:
  ```bash
  ruff format .
  ruff check . --fix
  ```
- **Database Scope:** Databases must read connection configuration from `DATABASE_URL`. Route handlers must fetch database sessions via dependency injection (`Depends(database.get_db)`), never manual creation.
- **HIPAA Compliance:** Sanitization and masking of PII/PHI is enforced. Avoid logging raw user input, exceptions stack traces, or diagnostic payloads.
- **Inference Gateways:** All LLM inference must channel through `backend/core_ai.py`. Never instantiate API clients directly in router handlers.
