# AGENTS.md - AI Healthcare System

> Canonical repo-wide instructions for AI coding agents.
> Keep this file short. Put subtree rules in scoped `AGENTS.md` files and deeper reference material in `CONTEXT.md`.

## Session Start

1. Run `python scripts/ai_context.py`.
2. Read this file, then the nearest scoped `AGENTS.md` for any files you will touch.
3. Read the matching `CONTEXT.md` if you need deeper module detail.
4. Read `active_handoff.md` at the root of the workspace if it exists, to capture the exact context of where the last session left off.

## Instruction Architecture

- Root `AGENTS.md` is the canonical repo-wide instruction file.
- Scoped `AGENTS.md` files hold subtree rules and take precedence inside their subtree.
- `CONTEXT.md` files are extended reference docs, not the main source of always-on rules.
- Tool-specific files such as `CLAUDE.md`, `GEMINI.md`, `.github/instructions/`, `.cursor/rules/`, and `.kiro/steering/` should stay thin and defer to this hierarchy.

## Repo Map

- `backend/main.py` -> FastAPI application entry point
- `backend/` -> All API routes, models, services, ML, AI modules
- `frontend/` -> Vite React SPA (`src/pages`, components, Vitest tests, lib)
- `frontend_legacy/` -> Old Python UI (for reference/legacy only)
- `scripts/` -> Dev utilities, DB management, deployment checks
- `tests/` -> Pytest test suite
- `docs/` -> Architecture docs, whitepapers, analysis
- `data/` -> Training datasets for ML models
- `airflow/`, `mlops/`, `monitoring/` -> Infrastructure & pipeline configs

## Always True

- Use `127.0.0.1` for host-bound local dev URLs, never `localhost`. Container/service DNS names such as `backend` are allowed inside container networks. For frontend, port is `3000`.
- Application/runtime code must read database location from `DATABASE_URL`. Tests must use isolated temp or in-memory databases and never touch `healthcare.db`.
- Provider-backed AI/LLM/embedding/vision inference must go through `backend/core_ai.py` - never call provider APIs directly. Local sklearn prediction models remain owned by `backend/prediction.py`.
- Never log or expose PII (patient names, DOBs, health data) in error messages or debug output.
- AI-generated health advice must include a medical disclaimer and recommend consulting a qualified clinician for diagnosis, treatment, or emergencies.
- Do not add tests, fixtures, logs, screenshots, or docs containing real patient data.
- Route handlers must obtain database sessions through `backend.database.get_db`, usually via `Depends(database.get_db)`. Never create `SessionLocal()` directly in route handlers.
- Database schema changes must update SQLAlchemy models, Pydantic schemas, and migration/startup logic together.
- ML model artifacts currently live in `backend/` and `models/`; loading is owned by `prediction.py` -> `initialize_models()`.
- Prompts are owned by `prompt_registry.py` - never inline system prompts in route handlers.
- Add backend runtime dependencies to `backend/requirements.txt`. Keep root `requirements.txt` as the thin include file, and update `requirements-full.txt` only when the dependency is needed for full local/ML/data-pipeline development.
- Tests must not depend on external API keys; mock all AI/embedding calls.
- Always run pytest using `pytest-xdist` parallelization (i.e. `-n auto` flag) to optimize test run times.
- Before claiming completion, run the narrowest relevant tests or checks and report any that were skipped.

## Scoped Instructions

| File | Use when |
| --- | --- |
| [backend/AGENTS.md](backend/AGENTS.md) | Editing backend API, services, or AI modules |
| [frontend/AGENTS.md](frontend/AGENTS.md) | Editing the Vite React SPA, frontend Vitest tests, or frontend Playwright tests |
| [frontend_legacy/AGENTS.md](frontend_legacy/AGENTS.md) | Editing the legacy Streamlit frontend |
| [tests/AGENTS.md](tests/AGENTS.md) | Editing backend pytest test infrastructure |

## Core Commands

```bash
# Backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
python -m pytest tests/ -n auto -v

# Frontend (Vite SPA)
npm --prefix frontend run dev

# DevX
python scripts/ai_context.py
python scripts/ai_context.py --json
python scripts/sync_agent_adapters.py
python scripts/sync_agent_adapters.py --check
```

## Session Efficiency

- **Minimize file reads**: Request specific line ranges (e.g. `StartLine` and `EndLine` in `view_file`) instead of reading whole large files.
- **Start clean sessions**: For unrelated tasks, start a new session or compact the history.
- **Short outputs**: Keep explanations concise and focused. Avoid verbose code repeats.
- **Avoid deep recursive scans**: Use targeted file listing on specific directories rather than running recursive file listings or global searches.

