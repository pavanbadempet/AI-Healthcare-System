from clinical_rag_cache.prompt_registry import get_prompt
from clinical_rag_cache.semantic_cache import SemanticCache


def test_semantic_cache_operations():
    cache = SemanticCache(threshold=0.9)
    # Perform lookup on empty cache
    res = cache.lookup("query", [0.1] * 128)
    assert res is None

    # Add item and lookup
    cache.add("query", [0.1] * 128, "cached-response")
    # Exact match should hit
    assert cache.lookup("query", [0.1] * 128) == "cached-response"


def test_prompt_registry():
    from clinical_rag_cache.prompt_registry import register_prompt

    register_prompt("test_prompt", "1.0", "You are a test assistant.")
    prompt = get_prompt("test_prompt", "1.0")
    assert prompt == "You are a test assistant."
