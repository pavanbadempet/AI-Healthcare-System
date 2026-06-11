# AGENTS.md - Backend

> Scoped rules for `backend/`. Read root `AGENTS.md` first.

## Key Module Ownership

For a deep reference of all 50+ backend modules, check [CONTEXT.md](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/CONTEXT.md#L7-L78). Here is a high-level summary:

- **AI Layer**: `core_ai.py` (Central entry point for all LLM/Ollama inference), `prompt_registry.py` (Prompt templates), `agent.py` (Supervisor agent), `chat_context.py` (RAG builder).
- **Data & DB**: `models.py` (SQLAlchemy models), `database.py` (Session engine), `schemas/` (Pydantic schemas), `rag.py` (Vector store).
- **ML & Predictions**: `prediction.py` (Initializes and runs disease prediction models diabetes/heart/liver/kidney/lungs), `explainability.py` (SHAP).
- **Hospital Workflows**: `hospital_operations.py`, `monitoring.py`, `diagnostics.py`, `pharmacy.py`, `billing.py`, `discharge.py`, `nursing.py`, `care_events.py`.
- **Interoperability & Compliance**: `abdm.py` (India ABDM API), `fhir.py` (FHIR R4 helpers), `interoperability.py` (Bundle exports), `audit.py` (PHI-safe auditing).

## Rules

- **AI Provider Abstraction**: Never import `google.generativeai` or `httpx` for AI calls outside `core_ai.py`. Use `core_ai.generate()`, `core_ai.chat()`, `core_ai.chat_stream()`, `core_ai.embed_text()`, or the relevant `core_ai` provider helper.
- **Prompt Management**: Never inline system prompts in route handlers. Register them in `prompt_registry.py` and retrieve via `get_prompt("name")`.
- **Database Sessions**: Route handlers must use `backend.database.get_db`, usually as `Depends(database.get_db)`. Never create `SessionLocal()` manually in route handlers.
- **Schema Changes**: Update `models.py`, `schemas.py`, and `main.py` migration/startup logic together when changing persisted fields.
- **Error Handling**: Log errors with `logger.error()`, never expose stack traces to clients. Return structured `{"detail": "..."}` errors.
- **HIPAA Awareness**: Health data (predictions, records, chat logs) must be scoped to `current_user.id`. Never return another user's data.
- **ML Models**: Model files (`*.pkl`) currently live in `backend/` and `models/`. Loading is centralized in `prediction.initialize_models()`.

## Recommended Tests

```bash
python -m pytest tests/ -v -k "test_chat or test_auth or test_prediction"
```
