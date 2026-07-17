# AI Agent Architecture - AI Healthcare System

> Maintainer-facing architecture doc for the DevX + Product AI stack.
> Ported from [Universe Dex Singularity AI Engine](../docs/ai_architecture_export/).

---

## Overview

This codebase implements a two-pillar AI architecture:

1. **DevX Agent Infrastructure** - Makes the repo "AI-maintainable" so that LLM coding assistants (Copilot, Cursor, Claude, Gemini) operate with deterministic, domain-aware context instead of hallucinating.
2. **Product AI Integration** - Embeds multi-tier AI inference directly into the application for medical chat, risk assessment, and health record analysis.

---

## Pillar 1: DevX Agent Infrastructure

### 1.1 Hierarchical Context Resolution (`AGENTS.md`)

Instead of a single massive `.cursorrules` file, instructions are broken into a filesystem hierarchy:

| Level | File | Purpose |
|-------|------|---------|
| Root | `AGENTS.md` | Global rules (host-bound local URLs use `127.0.0.1`, PII handling, etc.) |
| Scoped | `backend/AGENTS.md` | Backend-specific rules (AI provider abstraction, DB sessions) |
| Scoped | `frontend/AGENTS.md` | Frontend-specific rules (Next.js App Router, browser API URLs) |
| Scoped | `frontend_legacy/AGENTS.md` | Legacy Streamlit frontend rules |
| Scoped | `tests/AGENTS.md` | Backend pytest rules (mocking, isolation) |
| Deep Ref | `backend/CONTEXT.md` | Verbose module-level documentation (read only when needed) |

**Why it works**: When an agent edits a backend file, it reads Root `AGENTS.md` + `backend/AGENTS.md`. It's shielded from frontend Next.js rules, saving tokens and eliminating context confusion.

### 1.2 Automated Adapter Synchronization

Different AI tools expect instructions in proprietary formats. Canonical rules live in `AGENTS.md` files. The adapter manifest contains thin tool-specific summaries and references to those canonical files, then the sync engine distributes them:

```
AGENTS.md (canonical)
    -> scripts/sync_agent_adapters.py
    |-- .cursorrules
    |-- .cursor/rules/00-root.mdc
    |-- .cursor/rules/01-backend.mdc
    |-- .cursor/rules/04-frontend-legacy.mdc
    |-- .github/copilot-instructions.md
    |-- .github/instructions/backend.instructions.md
    |-- CLAUDE.md
    |-- GEMINI.md
    `-- .kiro/steering/*.md
```

**Manifest**: `scripts/agent_adapter_manifest.json` defines the generated adapter mapping and short compatibility summaries.
**Sync**: `python scripts/sync_agent_adapters.py` writes all adapter files.
**Check**: `python scripts/sync_agent_adapters.py --check` verifies sync, obsolete-file removal, and unmanaged adapter files in CI.

### 1.3 Dynamic Context Injection (`ai_context.py`)

At session start, agents run `python scripts/ai_context.py` to get instant situational awareness:

```json
{
  "project": "AI Healthcare System",
  "database": {"type": "sqlite", "path": "healthcare.db", "exists": true, "size_mb": 0.1},
  "git": {"branch": "main", "dirty_count": 3},
  "services": [
    {"name": "Backend (FastAPI)", "port": 8000, "running": true},
    {"name": "Frontend (Next.js)", "port": 3000, "running": false}
  ],
  "ml_models": [
    {"name": "Diabetes_Model.pkl", "exists": true, "size_mb": 0.5},
    {"name": "Heart_Model.pkl", "exists": false}
  ]
}
```

The agent immediately knows what's running, what models are trained, and what context files exist.

---

## Pillar 2: Product AI Integration

### 2.1 Multi-Tier Inference Engine (`backend/core_ai.py`)

Provider-backed AI/LLM/embedding/vision inference routes through a single module with automatic fallback:

```
Tier A: Ollama (Local)     -> Zero cloud-provider cost when local; prompts stay on the configured Ollama host
Tier B: Gemini (Cloud)     -> Google API free tier, reliable
Tier C: OpenAI/Anthropic   -> Optional, via request headers or env vars
```

**Public API** (the ONLY functions external modules should call):
- `generate(prompt, system)` -> Single-shot text generation
- `chat(messages, system)` -> Multi-turn chat
- `chat_stream(messages, system)` -> SSE streaming chat
- `embed_text(text, task_type)` -> Text embeddings for RAG
- `generate_vision_content(prompt, image)` -> Vision analysis boundary
- Ollama model helpers -> local model listing, pulling, and deletion
- `is_available()` -> Check if any backend is online

**Rule**: No module outside `core_ai.py` may import `google.generativeai`, `httpx` for AI calls, or any provider SDK directly.

### 2.2 Version-Controlled Prompt Registry (`backend/prompt_registry.py`)

Every system prompt is registered, versioned, and auditable:

```python
from backend.prompt_registry import get_prompt

template = get_prompt("medical_qa")  # Returns the active version
template = get_prompt("medical_qa", version="2.0")  # Specific version
```

**Registered Prompts**:
| Name | Purpose |
|------|---------|
| `chat_system` | Main chatbot system prompt with full context injection |
| `medical_qa` | RAG-grounded medical Q&A with citations |
| `symptom_analysis` | Structured symptom analysis |
| `report_summary` | Health record summarization |
| `risk_assessment` | Disease risk explanation |
| `streaming_system` | Compact prompt for SSE streaming (token-efficient) |

**Rule**: Never inline system prompts in route handlers. Register in the registry, retrieve via `get_prompt()`.

Prompt templates include instruction-hierarchy guardrails for retrieved records, uploaded report content, RAG memory, web research context, and patient-provided fields. Those inputs are treated as untrusted data: prompts tell the model not to follow instructions embedded inside them and to use them only as clinical evidence for the current user.

### 2.3 AI Function Governance Registry (`backend/ai_function_registry.py`)

AI-facing backend functions are listed in a static governance inventory exposed to admins at `GET /admin/ai-functions`. Each entry declares:

- intended audience and endpoint/module ownership
- clinical risk category
- whether medical disclaimers, human review, and basis transparency are required
- whether the function calls an AI provider and, if so, that the provider boundary is `backend.core_ai`
- prompt keys when a registered prompt is part of the workflow

The registry is anchored to practical governance expectations from WHO AI governance, FDA clinical decision-support transparency, and EU AI Act human-oversight principles. It is not a certification artifact; it is a control inventory for review, testing, and deployment readiness.

### 2.4 Model And Dataset Cards (`backend/model_cards.py`)

Prediction models and their public training artifacts are described through admin-visible cards at `GET /admin/model-cards`. Cards include intended use, model family, endpoint, artifact presence, dataset source, known limitations, human-review requirement, medical-disclaimer requirement, and post-deployment monitoring requirement.

The endpoint does not load models, read dataset rows, expose training samples, or return patient identifiers. It is an evidence surface for pilots and internal review, not a certification claim.

Clinician/admin review of AI prediction outputs is auditable through `POST /predict/reviews`. The route records whether a prediction was accepted, overridden, or ignored, and writes a PHI-safe `REVIEW_AI_PREDICTION` audit event without storing raw review notes or prediction payloads in audit details.

### 2.5 SSE Streaming Chat (`backend/streaming_chat.py`)

Real-time token streaming with heartbeat keepalive:

```
POST /chat/stream      -> SSE stream with {sources, reply chunks, status}
GET  /chat/context     -> Debug: view assembled RAG context
GET  /chat/suggestions -> Dynamic starter questions
```

Architecture (adapted from Universe Dex `chat_routes.py`):
1. Build RAG context via `chat_context.py`
2. Send sources immediately to client
3. Stream AI response via `core_ai.chat_stream()` with 15s heartbeat
4. Handle errors gracefully with structured SSE error events

### 2.6 Medical RAG Context Builder (`backend/chat_context.py`)

Analyzes patient questions and queries the DB to build structured context:

```
Patient question -> Intent detection
    |-- Patient Profile (name, age, vitals, lifestyle)
    |-- Condition-specific records (if "diabetes" mentioned -> diabetes records)
    |-- General health records (if no specific condition)
    |-- Health trend stats (if "trend" / "summary" mentioned)
    `-- Recent chat history (for continuity)
-> (context_string, sources_list)
```

Token budget management truncates context to fit within model limits.

### 2.7 Enhanced RAG Pipeline (`backend/rag.py`)

The existing vector store is enhanced with Singularity Engine patterns:
- `RetrievedChunk` - Typed context chunks with similarity scores
- `Citation` - Source tracking for grounded answers
- `RAGResult` - Structured return type with citation metadata
- `assemble_context()` - Token-budgeted context assembly
- Embeddings are requested through `core_ai.embed_text()` so RAG never imports provider SDKs directly
- Retrieval uses an explicit `user_id` ACL filter and optional `facility_id` filter; facility-scoped searches do not return legacy documents without matching facility metadata

---

---

## Pillar 3: SOTA Clinical AI Agent Suite

ClinOS includes three dedicated SOTA AI agents specialized in auditing, care transitions, and shift handoffs. They leverage structured prompting and JSON output parsing for high reliability.

### 3.1 Clinical Billing Agent (`ClinicalBillingAgent`)
*   **Module**: [billing_agent.py](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/agents/billing_agent.py)
*   **Workflow**:
    *   Accepts a clinical SOAP note or provider narrative.
    *   Generates recommended ICD-10 and CPT codes.
    *   Estimates claims denial risk (LOW/MEDIUM/HIGH) based on documentation completeness.
    *   Flags missing elements or formatting warnings.
*   **REST Integration**: `POST /v1/billing/invoices/{invoice_id}/audit`

### 3.2 Clinical Discharge Agent (`ClinicalDischargeAgent`)
*   **Module**: [discharge_agent.py](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/agents/discharge_agent.py)
*   **Workflow**:
    *   Fetches patient demographic context.
    *   Queries recent vital telemetry trends (last 5 records).
    *   Retrieves recent ML disease risk predictions.
    *   Outputs a structured care transition plan: discharge summary, patient instructions, follow-up schedule, and safety warning indicators.
*   **REST Integration**: `POST /v1/discharge/summaries/generate/{patient_id}`

### 3.3 Clinical Nursing Agent (`ClinicalNursingAgent`)
*   **Module**: [nursing_agent.py](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/agents/nursing_agent.py)
*   **Workflow**:
    *   Gathers patient profile data and active clinical conditions.
    *   Summarizes telemetry trends (vitals over the last 24 hours).
    *   Ingests active clinical warnings/alerts.
    *   Produces a structured nursing shift-handoff card detailing patient status, priority nursing tasks, monitoring frequency, and safety concerns.
*   **REST Integration**: `POST /v1/nursing/patients/{patient_id}/handoff`

---

## Pillar 4: SOTA System Maintenance & Data Retention

To maintain performance and adhere to strict compliance policies (GDPR/HIPAA/clinical data protection), the system runs automated optimizations and record pruning.

### 4.1 Maintenance Coordinator (`backend/maintenance.py`)
*   **Database Optimizations**:
    *   Detects SQLite database and runs `VACUUM` and `ANALYZE`.
    *   Detects PostgreSQL database and runs transaction-safe `ANALYZE` (bypassing transaction restrictions on `VACUUM`).
    *   Runs SQLite Vector Store vacuuming/optimizations via the `turbovec_store` interface.
*   **HIPAA/GDPR Data Pruning**:
    *   Leverages `backend/data_retention.py` to evaluate retention policy parameters.
    *   Queries and safely deletes expired Audit Logs, ChatLogs, and medical event histories.
*   **REST Integration**: `POST /v1/admin/maintenance` (requires admin authorization).

### 4.2 DevOps Automation (`scripts/run_maintenance.py`)
*   A standalone, cron-ready CLI script that authenticates via administrative credentials and executes the full maintenance pipeline.
*   **Usage**:
    ```bash
    python scripts/run_maintenance.py
    ```

---

## Module Dependency Graph

```
streaming_chat.py -> core_ai.py -> Ollama / Gemini / Cloud
       |               ^
       |-- chat_context.py
       |-- prompt_registry.py
       `-- auth.py / models.py / database.py

admin.py -> ai_function_registry.py
admin.py -> model_cards.py
admin.py -> maintenance.py -> data_retention.py

billing.py   -> agents/billing_agent.py   -> core_ai.py
discharge.py -> agents/discharge_agent.py -> core_ai.py
nursing.py   -> agents/nursing_agent.py   -> core_ai.py

agent.py -> core_ai.py (via CoreAIWrapper)
   `-- prompt_registry.py

chat.py -> agent.py -> core_ai.py
   `-- rag.py (vector store)
```

---

## Adding a New AI Feature

1. Register the prompt in `prompt_registry.py`
2. Build the context in `chat_context.py` (or a new context builder)
3. Call the relevant `core_ai` function - never import provider SDKs
4. Add the route in a new or existing router file
5. Mount in `main.py`
6. Add the function to `ai_function_registry.py` with clinical safety controls
7. Add or update `model_cards.py` if the feature introduces or materially changes a prediction model or dataset
8. Update this document

