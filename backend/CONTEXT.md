# CONTEXT.md — Backend Deep Reference

> Extended reference for `backend/`. Read `backend/AGENTS.md` first — this file is for when you need deeper detail.

---

## Module Responsibilities

### AI Layer

| Module | Role |
|--------|------|
| `core_ai.py` | **Canonical AI entry point.** Multi-tier inference engine (Ollama → Gemini → Cloud). Exposes `generate()`, `chat()`, `chat_stream()`, `is_available()`. No other module may call AI provider APIs directly. |
| `prompt_registry.py` | Version-controlled prompt templates. All system prompts are registered here. Supports versioning, A/B testing, activation. |
| `agent.py` | LangGraph-based medical agent with supervisor routing (research / analyze / respond / guardrail). Uses `CoreAIWrapper` which delegates to `core_ai.py`. |
| `chat_context.py` | Medical-domain RAG context builder. Analyzes questions, queries health records/predictions/chat history, assembles structured context with citation tracking. |
| `streaming_chat.py` | SSE streaming chat endpoint. `POST /chat/stream` with heartbeat keepalive, cloud provider override via headers. |

### Data Layer

| Module | Role |
|--------|------|
| `models.py` | SQLAlchemy ORM models: `User`, `HealthRecord`, `ChatLog`, `Appointment` |
| `database.py` | Engine creation from `DATABASE_URL`, `SessionLocal` factory, `get_db()` dependency |
| `schemas.py` | Pydantic request/response schemas |
| `rag.py` | Vector store (pickle-backed), Gemini embeddings, semantic search. Enhanced with `RetrievedChunk`, `Citation`, `RAGResult` dataclasses and token budget management. |

### ML Layer

| Module | Role |
|--------|------|
| `prediction.py` | ML model loading (`initialize_models()`) and prediction endpoints for diabetes, heart, liver |
| `train_diabetes.py` | Diabetes model training script |
| `train_heart.py` | Heart disease model training script |
| `train_liver.py` | Liver disease model training script |
| `advanced_ai.py` | Enterprise features: ensemble prediction, model monitoring, WebSocket streaming |
| `explainability.py` | SHAP-based model explanation |
| `explanation.py` | Prediction explanation endpoints |

### Service Layer

| Module | Role |
|--------|------|
| `auth.py` | JWT authentication, user registration, login, `get_current_user()` dependency |
| `chat.py` | Synchronous chat endpoint + health records CRUD + PDF download |
| `admin.py` | Admin panel endpoints (user management) |
| `payments.py` | Razorpay subscription management |
| `appointments.py` | Telemedicine appointment booking |
| `email_service.py` | Email notifications |
| `security.py` | Rate limiting middleware |
| `pdf_service.py` / `pdf_generator.py` | Medical report PDF generation |

---

## AI Inference Fallback Chain

```
Request arrives
    │
    ├─ Has x-ai-provider + x-ai-api-key headers?
    │   └─ Yes → Cloud API (OpenAI / Anthropic / OpenRouter)
    │
    ├─ Ollama running at OLLAMA_BASE_URL?
    │   └─ Yes → Ollama local inference (zero cost, HIPAA-safe)
    │
    ├─ GOOGLE_API_KEY set and valid?
    │   └─ Yes → Gemini cloud inference (free tier)
    │
    └─ All unavailable → Return error / fallback message
```

---

## Database Schema (Key Tables)

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `users` | id, username, email, hashed_password, role, full_name, dob, gender, height, weight, blood_type, about_me, diet, activity_level, sleep_hours, stress_level, plan_tier | Extended with lifestyle fields for context |
| `health_records` | id, user_id, record_type, data (JSON), prediction, timestamp | Stores all checkup results |
| `chat_logs` | id, user_id, role, content, timestamp | Chat history for RAG |
| `appointments` | id, patient_id, doctor_id, date, status | Telemedicine scheduling |

---

## Adding New Endpoints

1. Create or extend a router file in `backend/`
2. Use `Depends(database.get_db)` for DB sessions
3. Use `Depends(auth.get_current_user)` for authenticated routes
4. For AI features: call `core_ai.generate()` / `core_ai.chat()` — never import provider SDKs
5. For prompts: register in `prompt_registry.py`, retrieve via `get_prompt()`
6. Mount the router in `main.py`
7. Update `backend/AGENTS.md` module table if adding a new module
