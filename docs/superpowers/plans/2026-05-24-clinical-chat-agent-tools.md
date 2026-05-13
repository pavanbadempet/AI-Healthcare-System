# Clinical Chat Agent Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the clinical chat agent placeholder analysis path with deterministic, record-aware clinical analysis that is injected into the final chat prompt.

**Architecture:** Keep database access in `backend/chat.py` and AI provider access in `backend/core_ai.py`. Add a pure helper in `backend/agent.py` that summarizes already-scoped agent state, then pass its output into the registered `chat_system` prompt through a new `analysis_context` placeholder.

**Tech Stack:** Python, FastAPI backend modules, LangGraph/LangChain message types, pytest with mocked AI calls.

---

## File Structure

- Modify `tests/unit/test_agent_extended.py`: add red tests for deterministic clinical analysis behavior and replace the placeholder expectation.
- Modify `tests/unit/test_agent.py`: verify `generation_node` injects clinical analysis into the system prompt sent to `llm.invoke`.
- Modify `backend/agent.py`: add `SUPPORTED_ANALYSIS_AREAS`, text helpers, `build_clinical_analysis_context(state)`, and wire `analyst_node` to it.
- Modify `backend/prompt_registry.py`: add the `Clinical Analysis Context` prompt section.
- Modify `docs/AI_AGENT_ARCHITECTURE.md`: only if the public agent architecture description needs a small note after implementation.

---

### Task 1: Add Red Tests For Clinical Analysis

**Files:**
- Modify: `tests/unit/test_agent_extended.py`

- [x] **Step 1: Write failing tests**

Add `build_clinical_analysis_context` to the import list and add tests like:

```python
def test_clinical_analysis_uses_scoped_records_and_supported_models():
    state = {
        "messages": [HumanMessage(content="Analyze my heart and diabetes risk")],
        "available_reports": "History: heart:High risk, diabetes:Low risk",
        "rag_memories": "Previous diabetes checkup showed elevated glucose.",
    }

    result = build_clinical_analysis_context(state)

    assert "Relevant patient context" in result
    assert "heart" in result.lower()
    assert "diabetes" in result.lower()
    assert "validated structured prediction form" in result
    assert "ML Models (Heart, Diabetes, Liver)" not in result
```

Add a conservative empty-context test:

```python
def test_clinical_analysis_handles_missing_records_conservatively():
    state = {"messages": [HumanMessage(content="What is my risk?")]}

    result = build_clinical_analysis_context(state)

    assert "No prior scoped health records were provided" in result
    assert "validated structured prediction form" in result
```

Update `test_analyst_node`:

```python
def test_analyst_node_returns_record_aware_analysis():
    state = {
        "messages": [HumanMessage(content="analyze my liver risk")],
        "available_reports": "History: liver:Needs follow-up",
    }

    result = analyst_node(state)

    assert "analysis_results" in result
    assert "liver" in result["analysis_results"].lower()
    assert "ML Models (Heart, Diabetes, Liver)" not in result["analysis_results"]
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/unit/test_agent_extended.py -q
```

Expected: FAIL because `build_clinical_analysis_context` does not exist and `analyst_node` still returns placeholder text.

---

### Task 2: Add Red Test For Prompt Injection

**Files:**
- Modify: `tests/unit/test_agent.py`

- [x] **Step 1: Write failing prompt injection assertion**

Extend `test_generation_node`:

```python
def test_generation_node(mock_agent_env):
    state = {
        "messages": [HumanMessage(content="Hello")],
        "user_id": 123,
        "user_profile": "Male, 30",
        "psych_profile": "Friendly",
        "tavily_results": "Some web info",
        "analysis_results": "Clinical analysis says use structured heart form.",
    }

    result = generation_node(state)

    mock_instance = mock_agent_env["gemini"]
    assert mock_instance.invoke.called
    system_prompt = mock_instance.invoke.call_args.args[0][0].content
    assert "Clinical Analysis Context" in system_prompt
    assert "Clinical analysis says use structured heart form." in system_prompt
    assert isinstance(result["messages"][-1], AIMessage)
    assert result["messages"][-1].content == "Mocked AI Response"
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/unit/test_agent.py -q
```

Expected: FAIL because `chat_system` lacks `analysis_context` and `generation_node` does not pass it.

---

### Task 3: Implement Deterministic Clinical Analysis

**Files:**
- Modify: `backend/agent.py`

- [x] **Step 1: Add supported analysis metadata and text helpers**

Add near the constants:

```python
SUPPORTED_ANALYSIS_AREAS = {
    "heart": ("heart", "Heart disease structured prediction"),
    "cardiac": ("heart", "Heart disease structured prediction"),
    "diabetes": ("diabetes", "Diabetes structured prediction"),
    "glucose": ("diabetes", "Diabetes structured prediction"),
    "liver": ("liver", "Liver disease structured prediction"),
    "kidney": ("kidney", "Kidney disease structured prediction"),
    "renal": ("kidney", "Kidney disease structured prediction"),
    "lung": ("lungs", "Lung health structured prediction"),
    "lungs": ("lungs", "Lung health structured prediction"),
}
```

Add helper functions:

```python
def _coerce_context(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _compact_context(value: object, *, limit: int = 700) -> str:
    text = " ".join(_coerce_context(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
```

- [x] **Step 2: Add `build_clinical_analysis_context`**

```python
def build_clinical_analysis_context(state: AgentState) -> str:
    messages = state.get("messages", [])
    latest_message = messages[-1].content if messages else ""
    available_reports = _compact_context(state.get("available_reports"))
    rag_memories = _compact_context(state.get("rag_memories"), limit=500)
    combined_text = f"{latest_message} {available_reports} {rag_memories}".lower()

    matched = []
    seen = set()
    for keyword, (area, label) in SUPPORTED_ANALYSIS_AREAS.items():
        if keyword in combined_text and area not in seen:
            matched.append((area, label))
            seen.add(area)

    lines = []
    if available_reports or rag_memories:
        lines.append("Relevant patient context:")
        if available_reports:
            lines.append(f"- Recent records: {available_reports}")
        if rag_memories:
            lines.append(f"- Related memory: {rag_memories}")
    else:
        lines.append("No prior scoped health records were provided for this analysis request.")

    if matched:
        model_labels = ", ".join(label for _, label in matched)
        lines.append(f"Applicable structured prediction areas: {model_labels}.")
    else:
        lines.append(
            "No supported prediction area was clearly identified from the request or scoped records."
        )

    lines.append(
        "Do not produce a numeric risk score from chat text alone; ask the user to use the validated structured prediction form before giving a model-based risk estimate."
    )
    lines.append(
        "Frame the answer as educational support, mention uncertainty, and recommend a qualified clinician for diagnosis, treatment, or urgent symptoms."
    )
    return "\n".join(lines)
```

- [x] **Step 3: Replace `analyst_node` body**

```python
def analyst_node(state: AgentState):
    """Builds deterministic clinical analysis context from scoped records."""
    return {"analysis_results": build_clinical_analysis_context(state)}
```

- [x] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/unit/test_agent_extended.py -q
```

Expected: PASS for analysis tests, prompt injection test may still fail until Task 4.

---

### Task 4: Inject Analysis Context Into Registered Prompt

**Files:**
- Modify: `backend/prompt_registry.py`
- Modify: `backend/agent.py`

- [x] **Step 1: Add prompt section**

In the `chat_system` template, add after RAG memory:

```python
"Clinical Analysis Context:\n{analysis_context}\n\n"
```

- [x] **Step 2: Pass analysis context from `generation_node`**

In `generation_node`, define:

```python
analysis_context = state.get("analysis_results", "")
```

Then format the prompt with:

```python
analysis_context=analysis_context if analysis_context else "N/A",
```

- [x] **Step 3: Run focused tests**

Run:

```bash
python -m pytest tests/unit/test_agent.py tests/unit/test_agent_extended.py -q
```

Expected: PASS.

---

### Task 5: Verification And Documentation Check

**Files:**
- Possibly modify: `docs/AI_AGENT_ARCHITECTURE.md`

- [x] **Step 1: Decide whether architecture docs need a small update**

Search:

```bash
rg -n "analyst|analysis_results|placeholder|LangGraph|agent" docs/AI_AGENT_ARCHITECTURE.md backend/CONTEXT.md
```

If `docs/AI_AGENT_ARCHITECTURE.md` describes the analyst node as a placeholder, update that sentence to say it builds deterministic scoped clinical analysis context.

- [x] **Step 2: Run verification**

Run:

```bash
python -m py_compile backend/agent.py backend/prompt_registry.py
python -m pytest tests/unit/test_agent.py tests/unit/test_agent_extended.py -q
python -m pytest tests/unit -q
python -m pytest tests/integration tests/test_api.py -q
python scripts/sync_agent_adapters.py --check
git diff --check -- backend/agent.py backend/prompt_registry.py tests/unit/test_agent.py tests/unit/test_agent_extended.py docs/AI_AGENT_ARCHITECTURE.md
```

Expected: all commands pass.

---

## Self-Review Notes

- Spec coverage: tasks cover deterministic analysis, analyst node replacement, prompt injection, privacy constraints, and tests.
- Scope: no database schema changes, no frontend work, no direct ML invocation from chat.
- Type consistency: the helper is named `build_clinical_analysis_context(state)` throughout, and prompt formatting uses `analysis_context`.
