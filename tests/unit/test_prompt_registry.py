"""
Tests for prompt_registry.py.

Covers: registration, versioning, activation, get, get_info, list_all,
summary, duplicate version update, error paths, and default prompts.
"""
import pytest

from backend.prompt_registry import PromptRegistry, get_prompt, register_prompt

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def registry():
    """Fresh registry with no defaults pre-loaded (for isolation)."""
    r = PromptRegistry.__new__(PromptRegistry)
    r._prompts = {}
    r._active = {}
    return r


# ── register ─────────────────────────────────────────────────────────────────

def test_register_new_prompt(registry):
    pv = registry.register("greet", "1.0", "Hello, {name}!")
    assert pv.name == "greet"
    assert pv.version == "1.0"
    assert pv.template == "Hello, {name}!"


def test_register_sets_active_version(registry):
    registry.register("greet", "1.0", "Hi {name}")
    assert registry._active["greet"] == "1.0"


def test_register_second_version_replaces_active(registry):
    registry.register("greet", "1.0", "Hi {name}")
    registry.register("greet", "2.0", "Hello {name}")
    assert registry._active["greet"] == "2.0"


def test_register_with_activate_false_does_not_change_active(registry):
    registry.register("greet", "1.0", "Hi {name}")
    registry.register("greet", "2.0", "Hello {name}", activate=False)
    assert registry._active["greet"] == "1.0"


def test_register_duplicate_version_updates_in_place(registry):
    registry.register("greet", "1.0", "Original")
    registry.register("greet", "1.0", "Updated")
    versions = registry._prompts["greet"]
    assert len(versions) == 1
    assert versions[0].template == "Updated"


def test_register_stores_description_and_metadata(registry):
    registry.register("greet", "1.0", "Hi", description="Greeting prompt", metadata={"env": "prod"})
    pv = registry._prompts["greet"][0]
    assert pv.description == "Greeting prompt"
    assert pv.metadata["env"] == "prod"


# ── get ───────────────────────────────────────────────────────────────────────

def test_get_returns_active_template(registry):
    registry.register("greet", "1.0", "Hello!")
    assert registry.get("greet") == "Hello!"


def test_get_specific_version(registry):
    registry.register("greet", "1.0", "Hello v1")
    registry.register("greet", "2.0", "Hello v2")
    assert registry.get("greet", version="1.0") == "Hello v1"
    assert registry.get("greet", version="2.0") == "Hello v2"


def test_get_raises_for_unknown_prompt(registry):
    with pytest.raises(KeyError, match="Unknown prompt"):
        registry.get("nonexistent")


def test_get_raises_when_no_active_version(registry):
    registry.register("greet", "1.0", "Hi", activate=False)
    # No active version set
    registry._active.pop("greet", None)
    with pytest.raises(KeyError, match="No active version"):
        registry.get("greet")


def test_get_raises_for_unknown_version(registry):
    registry.register("greet", "1.0", "Hi")
    with pytest.raises(KeyError, match="not found"):
        registry.get("greet", version="99.0")


# ── activate ─────────────────────────────────────────────────────────────────

def test_activate_switches_active_version(registry):
    registry.register("greet", "1.0", "Hi v1")
    registry.register("greet", "2.0", "Hi v2")
    registry.activate("greet", "1.0")
    assert registry._active["greet"] == "1.0"
    assert registry.get("greet") == "Hi v1"


def test_activate_raises_for_unknown_prompt(registry):
    with pytest.raises(KeyError, match="Unknown prompt"):
        registry.activate("nonexistent", "1.0")


def test_activate_raises_for_unknown_version(registry):
    registry.register("greet", "1.0", "Hi")
    with pytest.raises(KeyError, match="not found"):
        registry.activate("greet", "99.0")


# ── get_info ──────────────────────────────────────────────────────────────────

def test_get_info_returns_version_list(registry):
    registry.register("greet", "1.0", "Hi v1", description="First")
    registry.register("greet", "2.0", "Hi v2", description="Second")
    info = registry.get_info("greet")
    assert info["name"] == "greet"
    assert info["active_version"] == "2.0"
    assert len(info["versions"]) == 2


def test_get_info_marks_active_version(registry):
    registry.register("greet", "1.0", "Hi")
    registry.register("greet", "2.0", "Hello")
    registry.activate("greet", "1.0")
    info = registry.get_info("greet")
    active = [v for v in info["versions"] if v["active"]]
    assert len(active) == 1
    assert active[0]["version"] == "1.0"


def test_get_info_raises_for_unknown_prompt(registry):
    with pytest.raises(KeyError, match="Unknown prompt"):
        registry.get_info("nonexistent")


# ── list_all / summary ────────────────────────────────────────────────────────

def test_list_all_returns_all_prompts(registry):
    registry.register("a", "1.0", "A")
    registry.register("b", "1.0", "B")
    listing = registry.list_all()
    names = {p["name"] for p in listing}
    assert {"a", "b"} == names


def test_summary_counts_correctly(registry):
    registry.register("a", "1.0", "A1")
    registry.register("a", "2.0", "A2")
    registry.register("b", "1.0", "B1")
    summary = registry.summary()
    assert summary["total_prompts"] == 2
    assert summary["total_versions"] == 3


# ── Default prompts ───────────────────────────────────────────────────────────

def test_default_registry_has_required_prompts():
    r = PromptRegistry()
    required = [
        "chat_system", "medical_qa", "symptom_analysis",
        "report_summary", "lab_report_vision", "risk_assessment",
        "streaming_system",
    ]
    for name in required:
        template = r.get(name)
        assert isinstance(template, str) and len(template) > 10, f"Prompt '{name}' is empty"


def test_default_prompts_include_medical_disclaimer():
    r = PromptRegistry()
    for name in ("chat_system", "medical_qa", "symptom_analysis", "report_summary", "risk_assessment"):
        template = r.get(name)
        assert "disclaimer" in template.lower() or "consult" in template.lower(), \
            f"Prompt '{name}' missing disclaimer"


def test_default_prompts_include_security_guard():
    """All prompts that accept untrusted data must include a SECURITY instruction."""
    r = PromptRegistry()
    for name in ("chat_system", "medical_qa", "symptom_analysis",
                 "report_summary", "lab_report_vision", "risk_assessment", "streaming_system"):
        template = r.get(name)
        assert "SECURITY" in template or "untrusted" in template.lower(), \
            f"Prompt '{name}' missing SECURITY guard"


def test_chat_system_prompt_has_all_placeholders():
    r = PromptRegistry()
    template = r.get("chat_system")
    for placeholder in ("{user_profile}", "{medical_history}", "{rag_context}",
                        "{analysis_context}", "{web_context}", "{engagement_style}"):
        assert placeholder in template


def test_medical_qa_prompt_has_context_and_query_placeholders():
    r = PromptRegistry()
    template = r.get("medical_qa")
    assert "{context}" in template
    assert "{query}" in template


def test_streaming_system_prompt_has_context_placeholder():
    r = PromptRegistry()
    template = r.get("streaming_system")
    assert "{context}" in template


def test_risk_assessment_prompt_has_prediction_placeholders():
    r = PromptRegistry()
    template = r.get("risk_assessment")
    for ph in ("{prediction_type}", "{prediction}", "{confidence}", "{input_data}"):
        assert ph in template


# ── Convenience functions ─────────────────────────────────────────────────────

def test_get_prompt_convenience_function():
    # Uses the global registry which has defaults
    template = get_prompt("chat_system")
    assert "{user_profile}" in template


def test_register_prompt_convenience_function():
    pv = register_prompt("test_convenience", "1.0", "Test template {x}")
    assert pv.name == "test_convenience"
    assert get_prompt("test_convenience") == "Test template {x}"
