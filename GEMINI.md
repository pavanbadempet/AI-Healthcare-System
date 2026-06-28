# Gemini Developer Guide (GEMINI.md)

This guide documents the integration patterns and configuration standards when developing or interacting with Google Gemini models within the AI Healthcare System.

## LLM Configurations & Roles

The system operates a 3-tier fallback architecture (`Ollama` -> `Gemini` -> `Cloud Fallback`) orchestrated inside [backend/core_ai.py](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/core_ai.py).

- **Default Model:** `gemini-1.5-flash` for high-throughput, low-latency reasoning and chat sessions.
- **Embedding Model:** `text-embedding-004` (1536-dimensional vectors) for indexing and RAG retrieval.
- **Configuration Keys:**
  - `GOOGLE_API_KEY`: API authentication key.
  - `GEMINI_MODEL`: Defaults to `gemini-1.5-flash` in the `.env` configuration.

## Developer Quick Reference

### 1. Vector Embeddings Generation
All text chunking and indexing for the RAG search utilizes the Gemini API client abstraction in `core_ai.py`:
```python
from backend.core_ai import embed_text

vector = embed_text("Patient reports history of asthma.")
# Returns List[float] of size 1536
```

### 2. Multi-Agent Reasoning (LangGraph)
The clinical supervisor agent routes tasks between specialized nodes. System prompts are versioned and stored in [backend/prompt_registry.py](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/prompt_registry.py).

- **Prompt Guidelines:**
  - Keep prompts clean and structured.
  - Incorporate strict medical disclaimer clauses:
    > "This assistant is a clinical decision support tool. It does not certify diagnosis or replace professional medical advice. Always consult a qualified clinician."

### 3. API Mocking in Unit Tests
To run unit tests without incurring API costs or requiring external keys, always mock `core_ai` calls:
```python
from unittest.mock import patch

@patch("backend.core_ai.generate")
def test_chat_stream(mock_generate):
    mock_generate.return_value = "Mocked clinical response"
    # execute test logic...
```
