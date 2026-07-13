# Clinical Chat Agent Tools Design

Date: 2026-05-24
Status: Approved design, pending implementation plan

## Goal

Replace the clinical chat agent's placeholder analysis behavior with a real, safe, record-aware analysis layer. The chat agent should use the patient's scoped health context to produce better answers while avoiding unsafe free-text diagnosis or direct model invocation from ambiguous chat text.

## Scope

This spec covers the synchronous chat agent path:

- `backend/agent.py`
- `backend/chat.py`
- `backend/prompt_registry.py`
- focused unit tests under `tests/unit/`

This spec does not add chat-driven automatic prediction execution. Structured ML predictions remain behind existing prediction endpoints, where required inputs are validated by schema.

## Current Problem

The agent can route "risk", "predict", "chance", "probability", and "analyze" questions to `analyst_node`, but that node only returns a generic placeholder:

```text
ML Models (Heart, Diabetes, Liver) are available for invocation.
```

The generated answer also does not receive `analysis_results` as a first-class prompt section, so even the placeholder does not reliably influence the final response.

## Recommended Approach

Add a deterministic clinical analysis layer inside `backend/agent.py`.

The analysis layer will read only already-scoped state provided to the agent:

- current user message
- `available_reports`
- `rag_memories`
- `user_profile`

It will produce a concise analysis context with:

- relevant patient record context found in the scoped history
- applicable model areas from the existing ML model families
- a safety note that validated prediction forms are required for actual risk scores
- recommended next step language suitable for the final assistant response

The generation prompt will include this as a dedicated `Clinical Analysis Context` section.

## Architecture

### Agent Analysis Helper

Create a small helper in `backend/agent.py` named `build_clinical_analysis_context(state)`.

Responsibilities:

- inspect the latest user message and scoped context
- identify supported model categories: heart, diabetes, liver, kidney, lungs when mentioned or present in records
- summarize relevant context without logging or exposing raw errors
- return a readable analysis string for prompt injection

The helper must be deterministic and unit-testable without external services.

### Analyst Node

Replace the placeholder body of `analyst_node` with a call to the helper.

Expected behavior:

- If relevant records exist, mention them in compact form.
- If no records exist, state that no prior scoped records were provided.
- If a supported model area is relevant, mention the matching structured prediction area.
- If the user asks for a risk score, state that validated structured inputs are required before producing one.

### Prompt Registry

Update the `chat_system` prompt in `backend/prompt_registry.py` to include:

```text
Clinical Analysis Context:
{analysis_context}
```

`generation_node` must pass `analysis_context=...` when formatting the prompt, defaulting to `N/A`.

### Chat Endpoint

Keep `backend/chat.py` ownership and user scoping unchanged. The endpoint already passes patient-owned recent records and RAG memories to the agent. No direct database access should be added inside `backend/agent.py`.

## Data Flow

1. User sends a chat message.
2. `backend/chat.py` builds scoped profile, recent health record context, RAG context, and message history.
3. `supervisor_node` routes analysis-like requests to `analyst_node`.
4. `analyst_node` builds deterministic clinical analysis context.
5. `generation_node` injects profile, history, RAG, web, and clinical analysis into the registered prompt.
6. `CoreAIWrapper` sends the composed prompt through `backend/core_ai.py`.

## Safety And Privacy

- Do not call AI providers outside `backend/core_ai.py`.
- Do not log patient profile, records, predictions, or user messages.
- Do not expose raw exception text to the user.
- Do not infer a diagnosis.
- Do not produce a numeric risk score from free text.
- Keep the medical disclaimer and clinician recommendation in the system prompt.
- Use only context already scoped to `current_user.id`.

## Error Handling

The new deterministic helper should not raise for missing or malformed context. It should tolerate empty strings and unexpected record text by returning a conservative analysis context.

Existing AI generation failure handling remains unchanged.

## Tests

Follow TDD:

1. Add failing tests for the current placeholder behavior.
2. Verify `analyst_node` returns record-aware analysis instead of generic placeholder text.
3. Verify unsupported or empty context returns a conservative no-records message.
4. Verify `generation_node` injects `analysis_results` into the system prompt.
5. Keep all AI calls mocked through the existing `llm` patching pattern.

Focused tests:

```bash
python -m pytest tests/unit/test_agent.py tests/unit/test_agent_extended.py -q
```

Broader verification after implementation:

```bash
python -m pytest tests/unit -q
python -m pytest tests/integration tests/test_api.py -q
```

## Out Of Scope

- New ML models
- Automatic prediction endpoint calls from chat
- Frontend UI changes
- Streaming chat parity
- Persistent long-term memory writes
- Database schema changes

## Acceptance Criteria

- The placeholder analyst response is gone.
- Analysis-like chat requests receive context-aware analysis in the final prompt.
- The implementation is deterministic before the final LLM call.
- No tests require external API keys.
- Relevant tests pass.
