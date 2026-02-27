# AI Agent Architecture — AI Healthcare System

> Maintainer-facing architecture doc for the DevX + Product AI stack.
> Ported from [Universe Dex Singularity AI Engine](../docs/ai_architecture_export/).

---

## Overview

This codebase implements a two-pillar AI architecture:

1. **DevX Agent Infrastructure** — Makes the repo "AI-maintainable" so that LLM coding assistants (Copilot, Cursor, Claude, Gemini) operate with deterministic, domain-aware context instead of hallucinating.
2. **Product AI Integration** — Embeds multi-tier AI inference directly into the application for medical chat, risk assessment, and health record analysis.

---

## Pillar 1: DevX Agent Infrastructure

### 1.1 Hierarchical Context Resolution (`AGENTS.md`)

Instead of a single massive `.cursorrules` file, instructions are broken into a filesystem hierarchy:

| Level | File | Purpose |
|-------|------|---------|
| Root | `AGENTS.md` | Global, unbreakable rules (use `127.0.0.1`, PII handling, etc.) |
| Scoped | `backend/AGENTS.md` | Backend-specific rules (AI provider abstraction, DB sessions) |
| Scoped | `frontend/AGENTS.md` | Frontend-specific rules (Streamlit patterns, session state) |
| Scoped | `tests/AGENTS.md` | Test-specific rules (mocking, isolation) |
| Deep Ref | `backend/CONTEXT.md` | Verbose module-level documentation (read only when needed) |

**Why it works**: When an agent edits a backend file, it reads Root `AGENTS.md` + `backend/AGENTS.md`. It's completely shielded from frontend Streamlit rules, saving tokens and eliminating context confusion.

### 1.2 Automated Adapter Synchronization

Different AI tools expect instructions in proprietary formats. We write rules **once** in canonical `AGENTS.md` files, then a sync engine distributes them:

```
AGENTS.md (canonical)
    ↓ scripts/sync_agent_adapters.py
    ├── .cursorrules
    ├── .cursor/rules/00-root.mdc
    ├── .cursor/rules/01-backend.mdc
    ├── .github/copilot-instructions.md
    ├── .github/instructions/backend.instructions.md
    ├── CLAUDE.md
    ├── GEMINI.md
    └── .kiro/steering/*.md
```

**Manifest**: `scripts/agent_adapter_manifest.json` defines the mapping schema.
**Sync**: `python scripts/sync_agent_adapters.py` writes all adapter files.
**Check**: `python scripts/sync_agent_adapters.py --check` verifies sync in CI.

### 1.3 Dynamic Context Injection (`ai_context.py`)

At session start, agents run `python scripts/ai_context.py` to get instant situational awareness:

```json
{
  "project": "AI Healthcare System",
  "database": {"type": "sqlite", "path": "healthcare.db", "exists": true, "size_mb": 0.1},
  "git": {"branch": "main", "dirty_count": 3},
  "services": [
    {"name": "Backend (FastAPI)", "port": 8000, "running": true},
    {"name": "Frontend (Streamlit)", "port": 8501, "running": false}
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

All AI inference routes through a single module with automatic fallback:

```
Tier A: Ollama (Local)     → Zero cost, HIPAA-friendly, data never leaves machine
Tier B: Gemini (Cloud)     → Google API free tier, reliable
Tier C: OpenAI/Anthropic   → Optional, via request headers or env vars
```

**Public API** (the ONLY functions external modules should call):
- `generate(prompt, system)` → Single-shot text generation
- `chat(messages, system)` → Multi-turn chat
- `chat_stream(messages, system)` → SSE streaming chat
- `is_available()` → Check if any backend is online

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

### 2.3 SSE Streaming Chat (`backend/streaming_chat.py`)

Real-time token streaming with heartbeat keepalive:

```
POST /chat/stream     → SSE stream with {sources, reply chunks, status}
GET  /chat/context    → Debug: view assembled RAG context
GET  /chat/suggestions → Dynamic starter questions
```

Architecture (adapted from Universe Dex `chat_routes.py`):
1. Build RAG context via `chat_context.py`
2. Send sources immediately to client
3. Stream AI response via `core_ai.chat_stream()` with 15s heartbeat
4. Handle errors gracefully with structured SSE error events

### 2.4 Medical RAG Context Builder (`backend/chat_context.py`)

Analyzes patient questions and queries the DB to build structured context:

```
Patient question → Intent detection
    ├── Patient Profile (name, age, vitals, lifestyle)
    ├── Condition-specific records (if "diabetes" mentioned → diabetes records)
    ├── General health records (if no specific condition)
    ├── Health trend stats (if "trend" / "summary" mentioned)
    └── Recent chat history (for continuity)
→ (context_string, sources_list)
```

Token budget management truncates context to fit within model limits.

### 2.5 Enhanced RAG Pipeline (`backend/rag.py`)

The existing vector store is enhanced with Singularity Engine patterns:
- `RetrievedChunk` — Typed context chunks with similarity scores
- `Citation` — Source tracking for grounded answers
- `RAGResult` — Structured return type with citation metadata
- `assemble_context()` — Token-budgeted context assembly

---

## Module Dependency Graph

```
streaming_chat.py ──→ core_ai.py ──→ Ollama / Gemini / Cloud
       │                    ↑
       ├──→ chat_context.py │
       │         │          │
       ├──→ prompt_registry.py
       │
       └──→ auth.py / models.py / database.py

agent.py ──→ core_ai.py (via CoreAIWrapper)
   │
   └──→ prompt_registry.py

chat.py ──→ agent.py ──→ core_ai.py
   │
   └──→ rag.py (vector store)
```

---

## Adding a New AI Feature

1. Register the prompt in `prompt_registry.py`
2. Build the context in `chat_context.py` (or a new context builder)
3. Call `core_ai.generate()` or `core_ai.chat()` — never import provider SDKs
4. Add the route in a new or existing router file
5. Mount in `main.py`
6. Update this document
