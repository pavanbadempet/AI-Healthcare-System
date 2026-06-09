"""
Tests for TurboVecVectorStore — turbovec ANN backend integration.

All tests mock turbovec.IdMapIndex with DictIdMapIndex (a pure-Python stub)
so the test suite runs in CI without the turbovec native extension installed.

Test coverage:
  - Example-based unit tests (interface, load, add, delete, search, env vars)
  - Edge-case / error-path tests
  - Property-based tests using Hypothesis (9 correctness properties)
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import types
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# DictIdMapIndex stub — pure-Python replacement for turbovec.IdMapIndex
# ---------------------------------------------------------------------------

class DictIdMapIndex:
    """
    Minimal stub that mimics turbovec.IdMapIndex using a plain dict.
    search() uses dot-product similarity (all test vectors are [1.0]*N
    by convention, giving equal scores; use distinct vectors for ordering tests).
    """

    def __init__(self, bits: int = 4) -> None:
        self.bits = bits
        self._store: Dict[str, List[float]] = {}
        self._save_called = 0
        self._load_called = 0

    def add(self, record_id: str, vector: List[float]) -> None:
        self._store[record_id] = list(vector)

    def delete(self, record_id: str) -> None:
        self._store.pop(record_id, None)

    def search(
        self,
        query_vector: List[float],
        k: int = 3,
        allowlist: Optional[List[str]] = None,
    ) -> List[Tuple[str, float]]:
        candidates = (
            {rid: v for rid, v in self._store.items() if rid in allowlist}
            if allowlist is not None
            else self._store
        )
        scores: List[Tuple[str, float]] = []
        for rid, vec in candidates.items():
            dot = sum(a * b for a, b in zip(query_vector, vec))
            norm_q = sum(a * a for a in query_vector) ** 0.5
            norm_v = sum(b * b for b in vec) ** 0.5
            score = dot / (norm_q * norm_v) if norm_q and norm_v else 0.0
            scores.append((rid, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def save(self, path: str) -> None:
        self._save_called += 1
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._store, f)

    @classmethod
    def load(cls, path: str) -> "DictIdMapIndex":
        inst = cls()
        inst._load_called += 1
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                inst._store = json.load(f)
        return inst

    def __len__(self) -> int:
        return len(self._store)


# ---------------------------------------------------------------------------
# Helpers to inject the turbovec stub into sys.modules
# ---------------------------------------------------------------------------

def _make_turbovec_module() -> types.ModuleType:
    """Create a fake 'turbovec' module with DictIdMapIndex."""
    mod = types.ModuleType("turbovec")
    mod.IdMapIndex = DictIdMapIndex  # type: ignore[attr-defined]
    return mod


def _inject_turbovec() -> None:
    sys.modules["turbovec"] = _make_turbovec_module()


def _remove_turbovec() -> None:
    sys.modules.pop("turbovec", None)
    # Remove cached turbovec_store module so it re-imports fresh
    for key in list(sys.modules):
        if "turbovec_store" in key:
            sys.modules.pop(key, None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def inject_turbovec_stub():
    """Inject stub before each test, remove after."""
    _inject_turbovec()
    yield
    _remove_turbovec()
    # Reset rag._store singleton
    try:
        import backend.rag as rag_mod
        rag_mod._store = None
    except Exception:
        pass


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh TurboVecVectorStore with tmp index path and mocked embeddings."""
    index_path = str(tmp_path / "turbovec_index")
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setenv("TURBOVEC_QUANTIZATION", "4")

    # Reset rag._store singleton
    import backend.rag as rag_mod
    rag_mod._store = None

    # Import fresh turbovec_store (stub already injected)
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    from backend.turbovec_store import TurboVecVectorStore

    _embed = lambda text, task_type="retrieval_document": [1.0] * 768  # noqa: E731
    with patch("backend.rag.core_ai.embed_text", side_effect=_embed):
        s = TurboVecVectorStore()
        s.load()
        yield s


# ---------------------------------------------------------------------------
# ── Example-based unit tests ──
# ---------------------------------------------------------------------------

class TestTurboVecInterface:
    def test_is_vector_store_backend(self, store):
        """Req 1.1 — implements VectorStoreBackend."""
        from backend.vector_store_base import VectorStoreBackend
        assert isinstance(store, VectorStoreBackend)

    def test_implements_all_abstract_methods(self, store):
        """Req 1.1 — no abstract method left unimplemented."""
        for method in ("add", "delete", "search", "search_with_scores", "count", "load", "save"):
            assert callable(getattr(store, method))


class TestLoadPaths:
    def test_load_no_index_creates_empty_store(self, store):
        """Req 1.2 — no existing index → empty count."""
        assert store.count() == 0

    def test_load_existing_index_reads_sidecar(self, tmp_path, monkeypatch):
        """Req 1.2, 5.3 — existing index + sidecar is loaded."""
        index_path = str(tmp_path / "tv_idx")
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)

        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]
        from backend.turbovec_store import TurboVecVectorStore

        _embed = lambda text, **kw: [1.0] * 768  # noqa: E731
        with patch("backend.rag.core_ai.embed_text", side_effect=_embed):
            s1 = TurboVecVectorStore()
            s1.load()
            s1.add("hello world", {"user_id": "u1"}, "rec1")

            # Reload fresh instance
            del sys.modules["backend.turbovec_store"]
            from backend.turbovec_store import TurboVecVectorStore as TV2
            s2 = TV2()
            s2.load()

        assert s2.count() == 1
        assert s2._texts["rec1"] == "hello world"
        assert s2._metas["rec1"]["user_id"] == "u1"


class TestAdd:
    def test_add_uses_retrieval_document_task_type(self, tmp_path, monkeypatch):
        """Req 2.3 — get_embedding called with task_type='retrieval_document'."""
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "idx"))
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]
        from backend.turbovec_store import TurboVecVectorStore

        calls = []

        def mock_embed(text, task_type="retrieval_document"):
            calls.append(task_type)
            return [1.0] * 768

        with patch("backend.rag.core_ai.embed_text", side_effect=mock_embed):
            s = TurboVecVectorStore()
            s.load()
            s.add("some text", {"user_id": "u1"}, "r1")

        assert "retrieval_document" in calls

    def test_add_new_record_increases_count(self, store):
        """Req 2.1 — new record_id increases count by 1."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store.add("text a", {"user_id": "u1"}, "r1")
        assert store.count() == 1

    def test_add_existing_record_no_count_change(self, store):
        """Req 2.2 — update does not grow store."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store.add("text a", {"user_id": "u1"}, "r1")
            store.add("text b", {"user_id": "u1"}, "r1")
        assert store.count() == 1
        assert store._texts["r1"] == "text b"

    def test_add_reraises_embedding_exception_without_modifying_store(self, store):
        """Req 1.6, 2.4 — embed raises → store unchanged, exception re-raised."""
        with patch("backend.rag.core_ai.embed_text", side_effect=RuntimeError("embed fail")):
            with pytest.raises(RuntimeError, match="embed fail"):
                store.add("text", {"user_id": "u1"}, "r1")
        assert store.count() == 0


class TestDelete:
    def test_delete_existing_returns_true(self, store):
        """Req 3.1 — deleting existing record returns True."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store.add("text", {"user_id": "u1"}, "r1")
        result = store.delete("r1")
        assert result is True
        assert store.count() == 0

    def test_delete_nonexistent_returns_false(self, store):
        """Req 3.2 — deleting absent ID returns False, count unchanged."""
        result = store.delete("nonexistent")
        assert result is False
        assert store.count() == 0

    def test_delete_save_exception_returns_false(self, store):
        """Req 3.3 — save() raises during delete → returns False, logs error."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store.add("text", {"user_id": "u1"}, "r1")

        with patch.object(store, "save", side_effect=IOError("disk full")):
            result = store.delete("r1")
        assert result is False


class TestSearch:
    def test_search_empty_index_returns_empty_list(self, store):
        """Req 4.5 — empty store → empty list."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            result = store.search("query")
        assert result == []

    def test_search_embedding_exception_returns_empty_list(self, store):
        """Req 4.8 — embedding fails during search → []."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store.add("text", {"user_id": "u1"}, "r1")
        with patch("backend.rag.core_ai.embed_text", side_effect=RuntimeError("fail")):
            result = store.search("query")
        assert result == []

    def test_search_returns_matching_text(self, store):
        """Req 4.1 — search returns document text."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store.add("hello patient", {"user_id": "u1"}, "r1")
            result = store.search("hello")
        assert "hello patient" in result

    def test_search_with_scores_has_required_keys(self, store):
        """Req 4.6 — search_with_scores dicts have text/metadata/id/score keys."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store.add("text", {"user_id": "u1"}, "r1")
            results = store.search_with_scores("query")
        assert len(results) > 0
        for r in results:
            assert set(r.keys()) >= {"text", "metadata", "id", "score"}

    def test_search_acl_filter_excludes_other_users(self, store):
        """Req 4.2, 4.4 — ACL filter keeps only matching user's records."""
        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store.add("user1 record", {"user_id": "u1"}, "r1")
            store.add("user2 record", {"user_id": "u2"}, "r2")
            results = store.search("query", filter_meta={"user_id": "u1"})
        assert "user1 record" in results
        assert "user2 record" not in results


class TestEnvVars:
    def test_turbovec_index_path_env_var(self, tmp_path, monkeypatch):
        """Req 8.1 — TURBOVEC_INDEX_PATH is respected."""
        custom = str(tmp_path / "custom" / "path")
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", custom)
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]
        from backend.turbovec_store import TurboVecVectorStore
        s = TurboVecVectorStore()
        assert s._index_path == custom

    def test_turbovec_quantization_env_var(self, tmp_path, monkeypatch):
        """Req 8.2 — TURBOVEC_QUANTIZATION=2 → _quantization == 2."""
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "idx"))
        monkeypatch.setenv("TURBOVEC_QUANTIZATION", "2")
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]
        from backend.turbovec_store import TurboVecVectorStore
        s = TurboVecVectorStore()
        assert s._quantization == 2

    def test_save_creates_missing_directory(self, tmp_path, monkeypatch):
        """Req 8.3 — save() creates parent directory if missing."""
        deep_path = str(tmp_path / "a" / "b" / "c" / "turbovec_index")
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", deep_path)
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]
        from backend.turbovec_store import TurboVecVectorStore

        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            s = TurboVecVectorStore()
            s.load()
            s.add("text", {"user_id": "u1"}, "r1")  # triggers save()

        assert os.path.exists(os.path.dirname(deep_path))


class TestPersistence:
    def test_save_creates_meta_json_sidecar(self, tmp_path, monkeypatch):
        """Req 5.2 — .meta.json sidecar is written atomically (no .tmp leftover)."""
        idx_path = str(tmp_path / "idx")
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", idx_path)
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]
        from backend.turbovec_store import TurboVecVectorStore

        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            s = TurboVecVectorStore()
            s.load()
            s.add("text", {"user_id": "u1"}, "r1")

        assert os.path.exists(idx_path + ".meta.json")
        assert not os.path.exists(idx_path + ".meta.json.tmp")

    def test_save_exception_silently_swallowed(self, store):
        """Req 5.5 — standalone save() does not propagate exceptions."""
        with patch.object(store._index, "save", side_effect=IOError("disk full")):
            store.save()  # must not raise


class TestMigration:
    def test_migration_imports_valid_records(self, tmp_path, monkeypatch):
        """Req 6.1, 6.2 — valid JSON records are migrated and saved."""
        json_path = str(tmp_path / "vector_store.json")
        idx_path = str(tmp_path / "turbovec_index")
        data = {
            "documents": ["doc1", "doc2"],
            "vectors": [[1.0] * 768, [0.5] * 768],
            "metadatas": [{"user_id": "u1"}, {"user_id": "u2"}],
            "ids": ["r1", "r2"],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        monkeypatch.setenv("TURBOVEC_INDEX_PATH", idx_path)
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]

        import backend.turbovec_store as ts_mod
        importlib.reload(ts_mod)
        with patch.object(ts_mod, "_DEFAULT_JSON_PATH", json_path):
            s = ts_mod.TurboVecVectorStore()
            s.load()

        assert s.count() == 2
        assert "r1" in s._texts
        assert "r2" in s._texts

    def test_migration_skips_malformed_records_and_logs_warning(
        self, tmp_path, monkeypatch, caplog
    ):
        """Req 6.4 — malformed vector → skipped with WARNING."""
        json_path = str(tmp_path / "vector_store.json")
        idx_path = str(tmp_path / "turbovec_index")
        data = {
            "documents": ["good", "bad"],
            "vectors": [[1.0] * 768, "not-a-list"],
            "metadatas": [{"user_id": "u1"}, {"user_id": "u2"}],
            "ids": ["r_good", "r_bad"],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        monkeypatch.setenv("TURBOVEC_INDEX_PATH", idx_path)
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]

        import backend.turbovec_store as ts_mod
        importlib.reload(ts_mod)

        import logging
        with patch.object(ts_mod, "_DEFAULT_JSON_PATH", json_path):
            with caplog.at_level(logging.WARNING, logger="backend.turbovec_store"):
                s = ts_mod.TurboVecVectorStore()
                s.load()

        assert s.count() == 1
        assert "r_good" in s._texts
        assert "r_bad" not in s._texts
        assert any("r_bad" in r.message for r in caplog.records)

    def test_load_no_json_no_index_is_empty(self, tmp_path, monkeypatch):
        """Req 6.5 — neither file → empty store, no crash."""
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "turbovec_index"))
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]

        import backend.turbovec_store as ts_mod
        importlib.reload(ts_mod)
        with patch.object(ts_mod, "_DEFAULT_JSON_PATH", str(tmp_path / "nonexistent.json")):
            s = ts_mod.TurboVecVectorStore()
            s.load()

        assert s.count() == 0

    def test_load_exception_initialises_empty_store(self, tmp_path, monkeypatch, caplog):
        """Req 5.6 — corrupt index → empty store, no crash."""
        idx_path = str(tmp_path / "turbovec_index")
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", idx_path)
        # Create a corrupt index file
        with open(idx_path, "w") as f:
            f.write("corrupt")

        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]
        from backend.turbovec_store import TurboVecVectorStore

        # Patch IdMapIndex.load to raise
        with patch("turbovec.IdMapIndex.load", side_effect=ValueError("corrupt")):
            import logging
            with caplog.at_level(logging.ERROR, logger="backend.turbovec_store"):
                s = TurboVecVectorStore()
                s.load()

        assert s.count() == 0


class TestFallback:
    def test_get_vector_store_returns_turbovec_when_importable(self, monkeypatch, tmp_path):
        """Req 7.1 — turbovec importable → TurboVecVectorStore returned."""
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "idx"))
        import backend.rag as rag_mod
        rag_mod._store = None
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]

        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            store = rag_mod.get_vector_store()

        from backend.turbovec_store import TurboVecVectorStore
        assert isinstance(store, TurboVecVectorStore)

    def test_get_vector_store_returns_simple_on_import_error(self, monkeypatch):
        """Req 7.2 — ImportError → SimpleVectorStore returned."""
        import backend.rag as rag_mod
        rag_mod._store = None
        _remove_turbovec()  # ensure turbovec is NOT importable

        store = rag_mod.get_vector_store()
        from backend.rag import SimpleVectorStore
        assert isinstance(store, SimpleVectorStore)
        _inject_turbovec()  # restore for other tests

    def test_get_vector_store_singleton(self, monkeypatch, tmp_path):
        """Req 7.3 — repeated calls return the same object."""
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "idx"))
        import backend.rag as rag_mod
        rag_mod._store = None
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]

        with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
            s1 = rag_mod.get_vector_store()
            s2 = rag_mod.get_vector_store()
        assert s1 is s2


class TestInvalidQuantization:
    def test_invalid_quantization_falls_back_to_4bit(self, tmp_path, monkeypatch, caplog):
        """Req 1.3 — invalid TURBOVEC_QUANTIZATION → warn + 4-bit fallback."""
        monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "idx"))
        monkeypatch.setenv("TURBOVEC_QUANTIZATION", "99")
        if "backend.turbovec_store" in sys.modules:
            del sys.modules["backend.turbovec_store"]
        from backend.turbovec_store import TurboVecVectorStore

        import logging
        with caplog.at_level(logging.WARNING, logger="backend.turbovec_store"):
            s = TurboVecVectorStore()

        assert s._quantization == 4
        assert any("4" in r.message or "invalid" in r.message.lower() for r in caplog.records)


# ---------------------------------------------------------------------------
# ── Property-Based Tests (Hypothesis) ──
# ---------------------------------------------------------------------------

# Shared strategies
_text_st = st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=("Cs",)))
_uid_st = st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789_")
_rid_st = st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-")
_meta_st = st.fixed_dictionaries({"user_id": _uid_st})
_record_st = st.fixed_dictionaries({"text": _text_st, "metadata": _meta_st, "id": _rid_st})


def _make_store_for_pbt(tmp_path):
    """Create a fresh TurboVecVectorStore with DictIdMapIndex for PBT."""
    _inject_turbovec()
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    from backend.turbovec_store import TurboVecVectorStore

    idx_path = str(tmp_path / "tv_pbt_idx")
    s = TurboVecVectorStore()
    s._index_path = idx_path
    s._meta_path = idx_path + ".meta.json"
    import turbovec
    s._index = turbovec.IdMapIndex(bits=4)
    return s


@given(
    text=_text_st,
    metadata=_meta_st,
    record_id=_rid_st,
)
@settings(max_examples=100)
def test_property_1_add_roundtrip(text, metadata, record_id, tmp_path):
    """
    # Feature: turbovec-vector-store-integration, Property 1: Add round-trip
    After add(text, metadata, record_id), _texts and _metas contain the values,
    and search_with_scores with the same vector returns a matching result.
    Validates: Requirements 1.4, 1.5, 2.1, 10.1, 10.2
    """
    s = _make_store_for_pbt(tmp_path)
    fixed_vec = [1.0] * 768

    with patch("backend.rag.core_ai.embed_text", return_value=fixed_vec):
        s.add(text, metadata, record_id)

    assert s._texts[record_id] == text
    assert s._metas[record_id] == metadata

    with patch("backend.rag.core_ai.embed_text", return_value=fixed_vec):
        results = s.search_with_scores("query")

    ids_in_results = [r["id"] for r in results]
    assert record_id in ids_in_results
    match = next(r for r in results if r["id"] == record_id)
    assert match["text"] == text
    assert match["metadata"] == metadata
    assert match["score"] > 0.0


@given(
    record_id=_rid_st,
    text1=_text_st,
    meta1=_meta_st,
    text2=_text_st,
    meta2=_meta_st,
)
@settings(max_examples=100)
def test_property_2_update_idempotence(record_id, text1, meta1, text2, meta2, tmp_path):
    """
    # Feature: turbovec-vector-store-integration, Property 2: Update idempotence
    Calling add() twice with the same record_id does not grow count().
    Validates: Requirement 2.2
    """
    s = _make_store_for_pbt(tmp_path)
    fixed_vec = [1.0] * 768

    with patch("backend.rag.core_ai.embed_text", return_value=fixed_vec):
        s.add(text1, meta1, record_id)
        s.add(text2, meta2, record_id)

    assert s.count() == 1
    assert s._texts[record_id] == text2
    assert s._metas[record_id] == meta2


@given(
    record_ids=st.lists(_rid_st, min_size=1, max_size=10, unique=True),
)
@settings(max_examples=100)
def test_property_3_delete_isolation(record_ids, tmp_path):
    """
    # Feature: turbovec-vector-store-integration, Property 3: Delete isolation
    Deleted records never appear in search results; deleting absent IDs returns False.
    Validates: Requirements 3.1, 3.2, 10.3
    """
    s = _make_store_for_pbt(tmp_path)
    fixed_vec = [1.0] * 768

    with patch("backend.rag.core_ai.embed_text", return_value=fixed_vec):
        for rid in record_ids:
            s.add(f"text for {rid}", {"user_id": "u1"}, rid)

    initial_count = s.count()
    to_delete = record_ids[0]

    result = s.delete(to_delete)
    assert result is True
    assert s.count() == initial_count - 1
    assert to_delete not in s._texts
    assert to_delete not in s._metas

    with patch("backend.rag.core_ai.embed_text", return_value=fixed_vec):
        search_results = s.search("query")
        scored_results = s.search_with_scores("query")

    assert to_delete not in [r for r in search_results]
    assert to_delete not in [r["id"] for r in scored_results]

    # Deleting already-absent ID
    result2 = s.delete(to_delete)
    assert result2 is False
    assert s.count() == initial_count - 1


@given(
    records=st.lists(
        st.fixed_dictionaries({
            "user_id": _uid_st,
            "text": _text_st,
            "id": _rid_st,
        }),
        min_size=2,
        max_size=8,
        unique_by=lambda r: r["id"],
    ).filter(lambda recs: len({r["user_id"] for r in recs}) >= 2),
)
@settings(max_examples=100)
def test_property_4_acl_filter_isolation(records, tmp_path):
    """
    # Feature: turbovec-vector-store-integration, Property 4: ACL filter isolation
    search() with a user_id filter never returns records from other users.
    Validates: Requirements 4.2, 4.3, 4.4
    """
    s = _make_store_for_pbt(tmp_path)
    fixed_vec = [1.0] * 768

    with patch("backend.rag.core_ai.embed_text", return_value=fixed_vec):
        for r in records:
            s.add(r["text"], {"user_id": r["user_id"]}, r["id"])

    user_ids = list({r["user_id"] for r in records})
    target_uid = user_ids[0]
    target_ids = {r["id"] for r in records if r["user_id"] == target_uid}

    with patch("backend.rag.core_ai.embed_text", return_value=fixed_vec):
        results = s.search("query", filter_meta={"user_id": target_uid}, k=len(records))

    for text in results:
        matching_record = next(
            (r for r in records if r["text"] == text), None
        )
        if matching_record:
            assert matching_record["user_id"] == target_uid


@given(
    k=st.integers(min_value=1, max_value=10),
    n=st.integers(min_value=1, max_value=15),
)
@settings(max_examples=100)
def test_property_5_search_result_shape_and_ordering(k, n, tmp_path):
    """
    # Feature: turbovec-vector-store-integration, Property 5: Search result shape and ordering
    search_with_scores returns dicts with required keys, score > 0, descending order, len <= k.
    Validates: Requirements 4.1, 4.6, 4.7
    """
    s = _make_store_for_pbt(tmp_path)

    with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
        for i in range(n):
            s.add(f"document {i}", {"user_id": "u1"}, f"rec_{i}")

        results = s.search_with_scores("query", k=k)

    assert len(results) <= k
    for r in results:
        assert set(r.keys()) >= {"text", "metadata", "id", "score"}
        assert r["score"] > 0.0

    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


@given(
    records=st.lists(
        st.fixed_dictionaries({
            "text": _text_st,
            "meta": _meta_st,
            "id": _rid_st,
        }),
        min_size=0,
        max_size=8,
        unique_by=lambda r: r["id"],
    ),
)
@settings(max_examples=50)
def test_property_6_persistence_roundtrip(records, tmp_path):
    """
    # Feature: turbovec-vector-store-integration, Property 6: Persistence round-trip
    save() then load() in a fresh instance recovers identical _texts, _metas, count().
    Validates: Requirements 5.1, 5.2, 5.3
    """
    idx_path = str(tmp_path / "tv_persist_idx")
    _inject_turbovec()

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    from backend.turbovec_store import TurboVecVectorStore

    fixed_vec = [1.0] * 768
    with patch("backend.rag.core_ai.embed_text", return_value=fixed_vec):
        s1 = TurboVecVectorStore()
        s1._index_path = idx_path
        s1._meta_path = idx_path + ".meta.json"
        import turbovec
        s1._index = turbovec.IdMapIndex(bits=4)

        for r in records:
            s1.add(r["text"], r["meta"], r["id"])
        s1.save()

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    from backend.turbovec_store import TurboVecVectorStore as TV2

    s2 = TV2()
    s2._index_path = idx_path
    s2._meta_path = idx_path + ".meta.json"
    s2.load()

    assert s2.count() == len(records)
    for r in records:
        assert s2._texts[r["id"]] == r["text"]
        assert s2._metas[r["id"]] == r["meta"]

    assert os.path.exists(idx_path + ".meta.json")


@given(
    valid_ids=st.lists(_rid_st, min_size=0, max_size=5, unique=True),
    malformed_ids=st.lists(_rid_st, min_size=0, max_size=3, unique=True),
)
@settings(max_examples=50)
def test_property_7_migration_correctness(valid_ids, malformed_ids, tmp_path):
    """
    # Feature: turbovec-vector-store-integration, Property 7: JSON migration correctness
    All valid records are imported; malformed vectors are skipped.
    Validates: Requirements 6.1, 6.4
    """
    # Ensure no ID overlap between valid and malformed
    all_ids = list(dict.fromkeys(valid_ids + malformed_ids))
    v_ids = all_ids[:len(valid_ids)]
    m_ids = all_ids[len(valid_ids):len(valid_ids) + len(malformed_ids)]

    json_path = str(tmp_path / "vector_store.json")
    idx_path = str(tmp_path / "tv_migrate_idx")

    ids = v_ids + m_ids
    documents = [f"doc_{i}" for i in range(len(ids))]
    vectors = [[1.0] * 768] * len(v_ids) + ["BAD_VECTOR"] * len(m_ids)
    metadatas = [{"user_id": "u1"}] * len(ids)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "documents": documents,
            "vectors": vectors,
            "metadatas": metadatas,
            "ids": ids,
        }, f)

    _inject_turbovec()
    import backend.turbovec_store as ts_mod
    importlib.reload(ts_mod)

    with patch.object(ts_mod, "_DEFAULT_JSON_PATH", json_path):
        s = ts_mod.TurboVecVectorStore()
        s._index_path = idx_path
        s._meta_path = idx_path + ".meta.json"
        import turbovec
        s._index = turbovec.IdMapIndex(bits=4)
        s._texts = {}
        s._metas = {}
        s._migrate_from_json(json_path)

    assert s.count() == len(v_ids)
    for rid in v_ids:
        assert rid in s._texts
    for rid in m_ids:
        assert rid not in s._texts


@given(n_calls=st.integers(min_value=2, max_value=10))
@settings(max_examples=50)
def test_property_8_singleton_idempotence(n_calls, tmp_path, monkeypatch):
    """
    # Feature: turbovec-vector-store-integration, Property 8: Singleton idempotence
    get_vector_store() returns the identical object on all calls.
    Validates: Requirement 7.3
    """
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "idx_singleton"))
    _inject_turbovec()
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    import backend.rag as rag_mod
    rag_mod._store = None

    with patch("backend.rag.core_ai.embed_text", return_value=[1.0] * 768):
        first = rag_mod.get_vector_store()
        for _ in range(n_calls - 1):
            subsequent = rag_mod.get_vector_store()
            assert subsequent is first

    rag_mod._store = None


@given(
    quant=st.text(min_size=1, max_size=5).filter(lambda s: s not in {"2", "4"}),
)
@settings(max_examples=100)
def test_property_9_invalid_quantization_fallback(quant, tmp_path, monkeypatch, caplog):
    """
    # Feature: turbovec-vector-store-integration, Property 9: Invalid quantization falls back to 4-bit
    Any TURBOVEC_QUANTIZATION value outside {"2","4"} → _quantization == 4, WARNING logged.
    Validates: Requirement 1.3
    """
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "idx_q"))
    monkeypatch.setenv("TURBOVEC_QUANTIZATION", quant)
    _inject_turbovec()
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    from backend.turbovec_store import TurboVecVectorStore

    import logging
    with caplog.at_level(logging.WARNING, logger="backend.turbovec_store"):
        s = TurboVecVectorStore()

    assert s._quantization == 4
    assert len(caplog.records) > 0
