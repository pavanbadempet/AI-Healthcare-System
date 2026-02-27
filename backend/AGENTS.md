# AGENTS.md - Backend

> Scoped rules for `backend/`. Read root `AGENTS.md` first.

## Module Ownership

| Module | Responsibility |
| --- | --- |
| `main.py` | FastAPI app, middleware, router mounting |
| `core_ai.py` | **All AI inference** — multi-tier (Ollama → Gemini → Cloud). Single entry point. |
| `agent.py` | LangGraph medical agent orchestration (supervisor → research/analyze → generate) |
| `chat.py` | Synchronous chat + health records CRUD |
| `streaming_chat.py` | SSE streaming chat with RAG context and heartbeat |
| `chat_context.py` | Medical-domain RAG context builder |
| `prompt_registry.py` | Version-controlled prompt templates |
| `rag.py` | Vector store, embeddings, semantic search |
| `prediction.py` | ML model loading and prediction (diabetes, heart, liver) |
| `auth.py` | JWT authentication, password hashing |
| `models.py` | SQLAlchemy ORM models |
| `database.py` | Engine, session factory, `get_db()` |

## Rules

- **AI Provider Abstraction**: Never import `google.generativeai` or `httpx` for AI calls outside `core_ai.py`. Use `core_ai.generate()`, `core_ai.chat()`, or `core_ai.chat_stream()`.
- **Prompt Management**: Never inline system prompts in route handlers. Register them in `prompt_registry.py` and retrieve via `get_prompt("name")`.
- **Database Sessions**: Always use `Depends(database.get_db)` in FastAPI routes. Never create `SessionLocal()` manually in route handlers.
- **Error Handling**: Log errors with `logger.error()`, never expose stack traces to clients. Return structured `{"detail": "..."}` errors.
- **HIPAA Awareness**: Health data (predictions, records, chat logs) must be scoped to `current_user.id`. Never return another user's data.
- **ML Models**: Model files (`*.pkl`) live in project root or `models/`. Loading is centralized in `prediction.initialize_models()`.

## Recommended Tests

```bash
python -m pytest tests/ -v -k "test_chat or test_auth or test_prediction"
```
