"""
Tests for rag.py — vector store, RAG pipeline, and public API.

Covers: RetrievedChunk, Citation, RAGResult, assemble_context,
SimpleVectorStore (add/search/delete/save/load), ACL filtering,
public API (add_checkup_to_db, add_interaction_to_db,
search_similar_records, delete_record_from_db), and metadata ACL helpers.
"""
from unittest.mock import patch

import pytest

from backend.rag import (
    Citation,
    RAGResult,
    RetrievedChunk,
    SimpleVectorStore,
    _build_acl_filter,
    _metadata_matches_filter,
    _normalize_acl_value,
    add_checkup_to_db,
    add_interaction_to_db,
    assemble_context,
    delete_record_from_db,
    search_similar_records,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _zero_embed(text, **kwargs):
    """Deterministic zero vector for tests — never calls the real API."""
    return [0.0] * 768


def _unit_embed(text, **kwargs):
    """All-ones vector so cosine similarity is well-defined."""
    return [1.0] * 768


# ── RetrievedChunk ────────────────────────────────────────────────────────────

def test_retrieved_chunk_citation_key():
    chunk = RetrievedChunk(record_type="diabetes", record_id="42", text="High risk", similarity=0.9)
    assert chunk.citation_key == "diabetes:42"


def test_retrieved_chunk_estimated_tokens():
    chunk = RetrievedChunk(record_type="heart", record_id="1", text="a" * 400, similarity=0.8)
    assert chunk.estimated_tokens() == 100


def test_retrieved_chunk_estimated_tokens_minimum_one():
    chunk = RetrievedChunk(record_type="heart", record_id="1", text="", similarity=0.5)
    assert chunk.estimated_tokens() == 1


# ── RAGResult ─────────────────────────────────────────────────────────────────

def test_rag_result_to_dict_structure():
    citation = Citation(
        record_type="diabetes",
        record_id="1",
        record_name="Diabetes Checkup",
        relevance=0.95,
        excerpt="High risk",
    )
    result = RAGResult(
        answer="Your risk is high.",
        citations=[citation],
        context_chunks_used=1,
        total_context_tokens=50,
        model_used="llama3.2",
        grounded=True,
    )
    d = result.to_dict()
    assert d["answer"] == "Your risk is high."
    assert len(d["citations"]) == 1
    assert d["citations"][0]["record_type"] == "diabetes"
    assert d["metadata"]["grounded"] is True
    assert d["metadata"]["model_used"] == "llama3.2"


def test_rag_result_to_dict_rounds_relevance():
    citation = Citation("diabetes", "1", "Checkup", relevance=0.9512345)
    result = RAGResult(answer="ok", citations=[citation])
    d = result.to_dict()
    assert d["citations"][0]["relevance"] == 0.951


# ── assemble_context ──────────────────────────────────────────────────────────

def test_assemble_context_respects_token_budget():
    chunks = [
        RetrievedChunk("diabetes", "1", "x" * 400, 0.9),  # ~100 tokens
        RetrievedChunk("heart", "2", "y" * 400, 0.8),      # ~100 tokens
        RetrievedChunk("liver", "3", "z" * 400, 0.7),      # ~100 tokens
    ]
    ctx, tokens, selected = assemble_context(chunks, token_budget=150)
    assert tokens <= 150
    assert len(selected) <= 2


def test_assemble_context_includes_source_label():
    chunks = [RetrievedChunk("diabetes", "99", "High risk patient", 0.95)]
    ctx, _, _ = assemble_context(chunks)
    assert "Diabetes" in ctx or "diabetes" in ctx
    assert "#99" in ctx


def test_assemble_context_respects_max_chunks():
    chunks = [RetrievedChunk("heart", str(i), f"data {i}", 0.9 - i * 0.01) for i in range(20)]
    _, _, selected = assemble_context(chunks, max_chunks=5)
    assert len(selected) <= 5


def test_assemble_context_empty_on_no_chunks():
    ctx, tokens, selected = assemble_context([])
    assert ctx == ""
    assert tokens == 0
    assert selected == []


# ── ACL helpers ───────────────────────────────────────────────────────────────

def test_normalize_acl_value_strips_whitespace():
    assert _normalize_acl_value("  42  ") == "42"


def test_normalize_acl_value_converts_int():
    assert _normalize_acl_value(42) == "42"


def test_build_acl_filter_user_only():
    f = _build_acl_filter("7")
    assert f == {"user_id": "7"}


def test_build_acl_filter_with_facility():
    f = _build_acl_filter("7", facility_id="3")
    assert f == {"user_id": "7", "facility_id": "3"}


def test_build_acl_filter_ignores_empty_facility():
    f = _build_acl_filter("7", facility_id="")
    assert "facility_id" not in f


def test_metadata_matches_filter_exact_match():
    meta = {"user_id": "7", "type": "diabetes"}
    assert _metadata_matches_filter(meta, {"user_id": "7"}) is True


def test_metadata_matches_filter_value_mismatch():
    meta = {"user_id": "7"}
    assert _metadata_matches_filter(meta, {"user_id": "99"}) is False


def test_metadata_matches_filter_missing_key():
    meta = {"type": "diabetes"}
    assert _metadata_matches_filter(meta, {"user_id": "7"}) is False


def test_metadata_matches_filter_empty_filter():
    assert _metadata_matches_filter({"user_id": "1"}, {}) is True


# ── SimpleVectorStore ─────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    """Fresh in-memory-like store backed by a temp file."""
    db_file = str(tmp_path / "vector_store.json")
    with patch("backend.rag.DB_FILE", db_file), \
         patch("backend.rag.get_embedding", side_effect=_unit_embed), \
         patch("backend.rag.get_query_embedding", side_effect=_unit_embed):
        s = SimpleVectorStore()
        yield s


def test_store_add_and_search(store):
    with patch("backend.rag.get_embedding", side_effect=_unit_embed), \
         patch("backend.rag.get_query_embedding", side_effect=_unit_embed):
        store.add("Diabetes high risk", {"user_id": "1", "type": "diabetes"}, "rec_1")
        results = store.search("diabetes", filter_meta={"user_id": "1"})
    assert len(results) == 1
    assert "Diabetes high risk" in results[0]


def test_store_add_updates_existing_record(store):
    with patch("backend.rag.get_embedding", side_effect=_unit_embed):
        store.add("Original text", {"user_id": "1"}, "rec_1")
        store.add("Updated text", {"user_id": "1"}, "rec_1")
    assert len(store.ids) == 1
    assert store.documents[0] == "Updated text"


def test_store_delete_removes_record(store):
    with patch("backend.rag.get_embedding", side_effect=_unit_embed):
        store.add("Some record", {"user_id": "1"}, "rec_del")
    assert store.delete("rec_del") is True
    assert "rec_del" not in store.ids


def test_store_delete_returns_false_for_missing_id(store):
    assert store.delete("nonexistent_id") is False


def test_store_search_empty_returns_empty(store):
    results = store.search("anything")
    assert results == []


def test_store_acl_filter_blocks_other_user(store):
    with patch("backend.rag.get_embedding", side_effect=_unit_embed), \
         patch("backend.rag.get_query_embedding", side_effect=_unit_embed):
        store.add("User 1 record", {"user_id": "1"}, "rec_u1")
        results = store.search("record", filter_meta={"user_id": "2"})
    assert results == []


def test_store_search_respects_k_limit(store):
    with patch("backend.rag.get_embedding", side_effect=_unit_embed), \
         patch("backend.rag.get_query_embedding", side_effect=_unit_embed):
        for i in range(10):
            store.add(f"Record {i}", {"user_id": "1"}, f"rec_{i}")
        results = store.search("record", filter_meta={"user_id": "1"}, k=3)
    assert len(results) <= 3


def test_store_save_and_load_persists_data(tmp_path):
    db_file = str(tmp_path / "vector_store.json")
    with patch("backend.rag.DB_FILE", db_file), \
         patch("backend.rag.get_embedding", side_effect=_unit_embed):
        s1 = SimpleVectorStore()
        s1.add("Persistent record", {"user_id": "42"}, "persist_1")

    # Load a fresh instance from the same file
    with patch("backend.rag.DB_FILE", db_file), \
         patch("backend.rag.get_embedding", side_effect=_unit_embed):
        s2 = SimpleVectorStore()

    assert "persist_1" in s2.ids
    assert s2.documents[s2.ids.index("persist_1")] == "Persistent record"


def test_store_load_handles_missing_file(tmp_path):
    db_file = str(tmp_path / "no_such_file.json")
    with patch("backend.rag.DB_FILE", db_file):
        s = SimpleVectorStore()
    assert s.documents == []
    assert s.ids == []


def test_store_load_handles_corrupt_json(tmp_path):
    db_file = str(tmp_path / "corrupt.json")
    with open(db_file, "w") as f:
        f.write("NOT VALID JSON {{{")
    with patch("backend.rag.DB_FILE", db_file):
        s = SimpleVectorStore()
    assert s.documents == []


# ── Public API ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_store(tmp_path):
    """Ensure each test gets a fresh global store backed by a temp file."""
    db_file = str(tmp_path / "test_vector_store.json")
    turbovec_index_path = str(tmp_path / "turbovec_index")
    import backend.rag as rag_module
    original_store = rag_module._store
    rag_module._store = None
    with patch("backend.rag.DB_FILE", db_file), \
         patch("backend.rag.get_embedding", side_effect=_unit_embed), \
         patch("backend.rag.get_query_embedding", side_effect=_unit_embed), \
         patch("backend.turbovec_store.get_embedding", side_effect=_unit_embed), \
         patch("backend.turbovec_store.get_query_embedding", side_effect=_unit_embed), \
         patch.dict("os.environ", {"TURBOVEC_INDEX_PATH": turbovec_index_path}):
        yield
    rag_module._store = original_store


def test_add_checkup_to_db_returns_true():
    with patch("backend.rag.get_embedding", side_effect=_unit_embed):
        result = add_checkup_to_db(
            user_id="1",
            record_id="100",
            record_type="diabetes",
            data={"glucose": 140, "bmi": 28.5},
            prediction="High Risk",
            timestamp="2024-01-01 10:00:00",
        )
    assert result is True


def test_add_checkup_to_db_includes_clinical_data_in_document():
    from backend.rag import get_vector_store
    with patch("backend.rag.get_embedding", side_effect=_unit_embed), \
         patch("backend.rag.get_query_embedding", side_effect=_unit_embed), \
         patch("backend.turbovec_store.get_query_embedding", side_effect=_unit_embed):
        add_checkup_to_db("2", "200", "heart", {"chol": 250}, "Detected", "2024-01-01")
        store = get_vector_store()
        # Use the backend-agnostic search interface to verify the document content.
        results = store.search("heart checkup", k=5)

    assert any("chol" in doc for doc in results)


def test_add_checkup_to_db_with_facility_id():
    with patch("backend.rag.get_embedding", side_effect=_unit_embed):
        result = add_checkup_to_db(
            "3", "300", "kidney", {}, "Healthy", "2024-01-01", facility_id="5"
        )
    assert result is True


def test_add_interaction_to_db_returns_true():
    with patch("backend.rag.get_embedding", side_effect=_unit_embed):
        result = add_interaction_to_db(
            user_id="1",
            interaction_id="chat_1",
            role="user",
            content="What is my risk?",
            timestamp="2024-01-01 10:00:00",
        )
    assert result is True


def test_add_interaction_to_db_uses_chat_prefix_for_id():
    from backend.rag import get_vector_store
    with patch("backend.rag.get_embedding", side_effect=_unit_embed):
        add_interaction_to_db("1", "999", "user", "How are you?", "2024-01-01")
        store = get_vector_store()
    # Use the backend-agnostic _texts/_str_to_int mapping, or count() > 0 as a proxy.
    # The canonical check is that "chat_999" is a known record_id in the store.
    if hasattr(store, "ids"):
        # SimpleVectorStore path
        assert "chat_999" in store.ids
    else:
        # TurboVecVectorStore (and future backends) — verify via count and _texts
        assert "chat_999" in store._texts


def test_search_similar_records_returns_results():
    with patch("backend.rag.get_embedding", side_effect=_unit_embed), \
         patch("backend.rag.get_query_embedding", side_effect=_unit_embed):
        add_checkup_to_db("1", "501", "diabetes", {"glucose": 180}, "High Risk", "2024-01-01")
        results = search_similar_records("1", "diabetes risk")
    assert len(results) > 0


def test_search_similar_records_isolates_by_user():
    with patch("backend.rag.get_embedding", side_effect=_unit_embed), \
         patch("backend.rag.get_query_embedding", side_effect=_unit_embed):
        add_checkup_to_db("user_a", "601", "heart", {}, "Healthy", "2024-01-01")
        results = search_similar_records("user_b", "heart")
    assert results == []


def test_search_similar_records_returns_empty_on_error():
    with patch("backend.rag.get_vector_store", side_effect=Exception("db error")):
        results = search_similar_records("1", "anything")
    assert results == []


def test_delete_record_from_db_returns_true_for_existing():
    with patch("backend.rag.get_embedding", side_effect=_unit_embed):
        add_checkup_to_db("1", "701", "liver", {}, "Healthy", "2024-01-01")
    result = delete_record_from_db("701")
    assert result is True


def test_delete_record_from_db_returns_false_for_missing():
    result = delete_record_from_db("nonexistent_99999")
    assert result is False
