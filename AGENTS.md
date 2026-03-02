# AGENTS.md - AI Healthcare System

> Canonical repo-wide instructions for AI coding agents.
> Keep this file short. Put subtree rules in scoped `AGENTS.md` files and deeper reference material in `CONTEXT.md`.

## Session Start

1. Run `python scripts/ai_context.py`.
2. Read this file, then the nearest scoped `AGENTS.md` for any files you will touch.
3. Read the matching `CONTEXT.md` if you need deeper module detail.

## Instruction Architecture

- Root `AGENTS.md` is the canonical repo-wide instruction file.
- Scoped `AGENTS.md` files hold subtree rules and take precedence inside their subtree.
- `CONTEXT.md` files are extended reference docs, not the main source of always-on rules.
- Tool-specific files such as `CLAUDE.md`, `GEMINI.md`, `.github/instructions/`, `.cursor/rules/`, and `.kiro/steering/` should stay thin and defer to this hierarchy.

## Repo Map

- `backend/main.py` → FastAPI application entry point
- `backend/` → All API routes, models, services, ML, AI modules
- `frontend/` → Next.js App Router (UI, components, hooks, lib)
- `frontend_legacy/` → Old Streamlit UI (for reference/legacy only)
- `scripts/` → Dev utilities, DB management, deployment checks
- `tests/` → Pytest test suite
- `docs/` → Architecture docs, whitepapers, analysis
- `data/` → Training datasets for ML models
- `airflow/`, `mlops/`, `monitoring/` → Infrastructure & pipeline configs

## Always True

- Use `127.0.0.1`, never `localhost`. For frontend, port is `3000`.
- Never hardcode database paths; use `DATABASE_URL` from env.
- All AI inference must go through `backend/core_ai.py` — never call provider APIs directly.
- Never log or expose PII (patient names, DOBs, health data) in error messages or debug output.
- Always include medical disclaimers in AI-generated health advice.
- Use `Depends(database.get_db)` for database sessions in route handlers.
- ML model loading is owned by `prediction.py` → `initialize_models()`.
- Prompts are owned by `prompt_registry.py` — never inline system prompts in route handlers.
- Keep `requirements.txt` and `requirements-full.txt` in sync when adding dependencies.
- Tests must not depend on external API keys; mock all AI/embedding calls.

## Scoped Instructions

| File | Use when |
| --- | --- |
| [backend/AGENTS.md](backend/AGENTS.md) | Editing backend API, services, or AI modules |
| [frontend/AGENTS.md](frontend/AGENTS.md) | Editing the Next.js frontend |
| [tests/AGENTS.md](tests/AGENTS.md) | Editing test infrastructure |

## Core Commands

```bash
# Backend
uvicorn backend.main:app --reload --port 8000
python -m pytest tests/ -v

# Frontend (Next.js)
cd frontend && npm run dev -- -p 3000

# DevX
python scripts/ai_context.py
python scripts/ai_context.py --json
python scripts/sync_agent_adapters.py
python scripts/sync_agent_adapters.py --check
```

## Documentation Sync Rules

After codebase changes, update:

- [docs/AI_AGENT_ARCHITECTURE.md](docs/AI_AGENT_ARCHITECTURE.md) if AI modules were added, removed, or restructured
- The relevant scoped `AGENTS.md` if local instructions changed
- `backend/CONTEXT.md` if backend module responsibilities changed
