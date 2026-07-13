"""
tests/unit/test_turbovec_store.py
=================================

Unit, edge-case, and property-based tests for TurboVecVectorStore.

All tests mock ``turbovec.IdMapIndex`` with the ``DictIdMapIndex`` stub
defined below — turbovec is never required to be installed.

Test organisation
-----------------
- DictIdMapIndex      — in-memory dict stub that mimics turbovec.IdMapIndex
- Fixtures            — ``store`` (shared)
- Task 5.2 tests      — example / interface tests (added in task 5.2)
- Task 5.3 tests      — edge-case / error-path tests (added in task 5.3)
- Task 6.x tests      — property-based tests via Hypothesis (added in task 6.x)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import types
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# DictIdMapIndex — dict-backed stub that mimics turbovec.IdMapIndex
#
# Updated to match the real turbovec API used by turbovec_store.py:
#   - __init__(bit_width=N)
#   - add_with_ids(vectors_ndarray, ids_ndarray)   ids are uint64 ints
#   - remove(uint64_id)
#   - write(path)
#   - IdMapIndex.load(path)  — classmethod
#   - search(q_array, k=k)  → (scores_arr, ids_arr) both shape (1, k)
# ---------------------------------------------------------------------------


class DictIdMapIndex:
    """Lightweight in-memory substitute for ``turbovec.IdMapIndex``.

    Stores ``{uint64_id: List[float]}`` as a plain Python dict.

    Parameters
    ----------
    bit_width:
        Ignored; accepted so the constructor signature matches turbovec.
    """

    def __init__(self, bit_width: int = 4) -> None:
        self._data: Dict[int, List[float]] = {}  # uint64_id -> vector

    # ------------------------------------------------------------------
    # Mutation API
    # ------------------------------------------------------------------

    def add_with_ids(self, vectors: "np.ndarray", ids: "np.ndarray") -> None:
        """Insert entries. vectors shape (N, dim), ids shape (N,) uint64."""
        for uid, vec in zip(ids.tolist(), vectors.tolist()):
            self._data[int(uid)] = list(vec)

    def remove(self, uint64_id: int) -> None:
        """Remove an entry by integer ID (silently ignore if absent)."""
        self._data.pop(int(uint64_id), None)

    # ------------------------------------------------------------------
    # Search — returns (scores_arr, ids_arr) each shape (1, k)
    # ------------------------------------------------------------------

    def _dot(self, a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def search(
        self,
        query_arr: "np.ndarray",
        k: int = 5,
        allowlist: Optional["np.ndarray"] = None,
    ) -> Tuple["np.ndarray", "np.ndarray"]:
        query_vec = (
            query_arr[0].tolist()
            if hasattr(query_arr[0], "tolist")
            else list(query_arr[0])
        )
        candidates = self._data
        if allowlist is not None:
            allow_set = set(
                int(x)
                for x in (
                    allowlist.tolist() if hasattr(allowlist, "tolist") else allowlist
                )
            )
            candidates = {uid: vec for uid, vec in self._data.items() if uid in allow_set}

        scored = [(uid, self._dot(query_vec, vec)) for uid, vec in candidates.items()]
        scored.sort(key=lambda t: t[1], reverse=True)
        top = scored[:k]

        if top:
            scores = np.array([[s for _, s in top]], dtype="float32")
            ids = np.array([[uid for uid, _ in top]], dtype="uint64")
        else:
            scores = np.zeros((1, 0), dtype="float32")
            ids = np.zeros((1, 0), dtype="uint64")
        return scores, ids

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def write(self, path: str) -> None:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        # Write the stub data file
        with open(path + ".stub.json", "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in self._data.items()}, f)
        # Create a sentinel at the bare path so os.path.exists(path) returns True
        # (mirrors turbovec's native index which is a file/directory at `path`)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("turbovec-stub-sentinel")

    @classmethod
    def load(cls, path: str) -> "DictIdMapIndex":
        instance = cls()
        stub_path = path + ".stub.json"
        if os.path.exists(stub_path):
            with open(stub_path, "r", encoding="utf-8") as f:
                instance._data = {int(k): v for k, v in json.load(f).items()}
        return instance

    # ------------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return len(self._data) > 0


# ---------------------------------------------------------------------------
# Helper — build a fake ``turbovec`` module
# ---------------------------------------------------------------------------


def _make_turbovec_module() -> types.ModuleType:
    mod = types.ModuleType("turbovec")
    mod.IdMapIndex = DictIdMapIndex  # type: ignore[attr-defined]
    return mod


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _patch_turbovec_store_embeddings(monkeypatch, fn=None):
    """Patch get_embedding/get_query_embedding in the turbovec_store module."""
    if fn is None:
        fn = lambda text, **kw: [1.0] * 768  # noqa: E731
    import backend.turbovec_store as tvs_mod
    monkeypatch.setattr(tvs_mod, "get_embedding", fn)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", fn)


def _fresh_store(monkeypatch, tmp_path, quant="4"):
    """Create a patched TurboVecVectorStore with DictIdMapIndex stub and no I/O side effects."""
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / "tvec_idx")

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    if quant != "4":
        monkeypatch.setenv("TURBOVEC_QUANTIZATION", quant)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    from backend.turbovec_store import TurboVecVectorStore
    _patch_turbovec_store_embeddings(monkeypatch)

    tvs = TurboVecVectorStore()
    tvs.load()
    return tvs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Fresh ``TurboVecVectorStore`` backed by a temp directory.

    - ``sys.modules["turbovec"]`` → DictIdMapIndex stub
    - ``TURBOVEC_INDEX_PATH``     → tmp_path / "tvec_idx"
    - ``backend.rag._store``      → reset to None before/after
    - ``backend.rag.core_ai.embed_text`` → deterministic [1.0]*768
    - ``backend.turbovec_store.get_embedding/get_query_embedding`` → same stub
    """
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / "tvec_idx")

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)

    original_store = rag_module._store
    rag_module._store = None

    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    # Patch get_embedding/get_query_embedding inside the turbovec_store module
    # (they are imported from .rag; turbovec_store.py calls get_embedding with
    # task_type kwarg which the raw wrapper doesn't accept)
    import backend.turbovec_store as tvs_mod
    from backend.turbovec_store import TurboVecVectorStore
    monkeypatch.setattr(tvs_mod, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", lambda text, **kw: [1.0] * 768)

    tvs = TurboVecVectorStore()
    tvs.load()

    yield tvs

    rag_module._store = None
    if original_store is not None:
        rag_module._store = original_store


# ===========================================================================
# Task 5.2 — Example / interface tests
# ===========================================================================


def test_turbovec_store_is_vector_store_backend(store):
    """Req 1.1 — TurboVecVectorStore must implement VectorStoreBackend."""
    from backend.vector_store_base import VectorStoreBackend

    assert isinstance(store, VectorStoreBackend)


def test_load_no_index_creates_empty_store(store):
    """Req 1.2 — Loading with no persisted files yields count() == 0."""
    assert store.count() == 0


def test_load_existing_index_calls_idmapindex_load(tmp_path, monkeypatch):
    """Req 1.2, 5.3 — A fresh store loaded from an existing path has records."""
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / "existing_idx")

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    import backend.turbovec_store as tvs_mod
    from backend.turbovec_store import TurboVecVectorStore
    monkeypatch.setattr(tvs_mod, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", lambda text, **kw: [1.0] * 768)

    # Build and persist a store with one record
    s1 = TurboVecVectorStore()
    s1.load()
    s1.add("hello world", {"user_id": "u1"}, "rec_load_test")

    assert os.path.exists(index_path + ".meta.json"), ".meta.json sidecar must exist after save"

    # Load a fresh store from the same path
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    import backend.turbovec_store as tvs_mod2
    from backend.turbovec_store import TurboVecVectorStore as TVS2
    monkeypatch.setattr(tvs_mod2, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod2, "get_query_embedding", lambda text, **kw: [1.0] * 768)

    s2 = TVS2()
    s2.load()

    assert s2.count() > 0, "Fresh store loaded from existing index must have records"
    assert "rec_load_test" in s2._texts

    rag_module._store = None


def test_add_uses_retrieval_document_task_type(store, monkeypatch):
    """Req 2.3 — add() must use task_type='retrieval_document' for document embedding.

    ``get_embedding()`` in rag.py always calls ``core_ai.embed_text`` with
    ``task_type="retrieval_document"``.  We verify this by patching core_ai.embed_text
    and checking the kwarg it receives via the call chain.
    """
    import backend.rag as rag_module

    captured: Dict[str, Any] = {}

    def capture_embed(text, **kw):
        captured.update(kw)
        return [1.0] * 768

    # Patch at the core_ai boundary where task_type is actually passed
    monkeypatch.setattr(rag_module.core_ai, "embed_text", capture_embed)
    # Also re-patch the turbovec_store module-level references to use the real rag wrappers
    import backend.turbovec_store as tvs_mod
    from backend.rag import get_embedding as real_get_embedding
    monkeypatch.setattr(tvs_mod, "get_embedding", real_get_embedding)

    store.add("some medical text", {"user_id": "u1"}, "rec_task_type")

    assert "task_type" in captured, "task_type kwarg must be forwarded to core_ai.embed_text"
    assert captured["task_type"] == "retrieval_document"


def test_get_vector_store_returns_turbovec_when_importable(tmp_path, monkeypatch):
    """Req 7.1 — When turbovec is importable, get_vector_store() returns TurboVecVectorStore."""
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / "gvs_turbo_idx")

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    for mod_name in list(sys.modules.keys()):
        if "turbovec_store" in mod_name:
            del sys.modules[mod_name]

    import backend.turbovec_store as tvs_mod
    from backend.turbovec_store import TurboVecVectorStore
    monkeypatch.setattr(tvs_mod, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", lambda text, **kw: [1.0] * 768)

    from backend.rag import get_vector_store
    result = get_vector_store()

    assert isinstance(result, TurboVecVectorStore)

    rag_module._store = None


def test_get_vector_store_returns_simple_on_import_error(tmp_path, monkeypatch):
    """Req 7.2 — When turbovec backend is unavailable, get_vector_store() returns SimpleVectorStore."""
    import backend.rag as rag_module
    from backend.rag import SimpleVectorStore

    db_file = str(tmp_path / "vs_simple.json")
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / "unused"))
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    # Remove turbovec and turbovec_store from sys.modules so next import is fresh
    monkeypatch.delitem(sys.modules, "turbovec", raising=False)
    for mod_name in list(sys.modules.keys()):
        if "turbovec_store" in mod_name:
            del sys.modules[mod_name]

    # Patch the import inside rag.py's get_vector_store() to raise ImportError.
    # We do this by making the turbovec_store module itself raise ImportError when imported.
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "backend.turbovec_store" or (
            name == "turbovec_store" and args and "backend" in str(args)
        ):
            raise ImportError("turbovec not installed (test mock)")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        with patch("backend.rag.DB_FILE", db_file):
            result = rag_module.get_vector_store()

    assert isinstance(result, SimpleVectorStore)

    rag_module._store = None
    # Restore stub so later tests aren't affected
    monkeypatch.setitem(sys.modules, "turbovec", _make_turbovec_module())


def test_turbovec_index_path_env_var(tmp_path, monkeypatch):
    """Req 8.1 — TURBOVEC_INDEX_PATH env var sets _index_path at construction time."""
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    custom_path = str(tmp_path / "custom" / "path")

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", custom_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    from backend.turbovec_store import TurboVecVectorStore

    s = TurboVecVectorStore()
    assert s._index_path == custom_path

    rag_module._store = None


def test_turbovec_quantization_env_var(tmp_path, monkeypatch):
    """Req 8.2 — TURBOVEC_QUANTIZATION=2 sets _quantization == 2."""
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / "quant_idx")

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setenv("TURBOVEC_QUANTIZATION", "2")
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    from backend.turbovec_store import TurboVecVectorStore

    s = TurboVecVectorStore()
    assert s._quantization == 2

    rag_module._store = None


def test_save_creates_missing_directory(tmp_path, monkeypatch):
    """Req 8.3 — save() creates missing parent directories for _index_path."""
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    deep_path = str(tmp_path / "a" / "b" / "c" / "tvec_idx")

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", deep_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    import backend.turbovec_store as tvs_mod
    from backend.turbovec_store import TurboVecVectorStore
    monkeypatch.setattr(tvs_mod, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", lambda text, **kw: [1.0] * 768)

    s = TurboVecVectorStore()
    s.load()
    s.add("test doc", {"user_id": "u1"}, "rec_mkdir")

    meta_path = deep_path + ".meta.json"
    assert os.path.exists(meta_path), ".meta.json must exist after save in new directory"

    rag_module._store = None


def test_migration_calls_save_and_logs_info(tmp_path, monkeypatch):
    """Req 6.2, 6.3 — Loading with only vector_store.json triggers migration,
    persists the result, and logs an INFO message with migrated count.
    """
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / "migrated_idx")

    # Write a legacy vector_store.json with one valid record
    legacy_data = {
        "ids": ["old_rec_1"],
        "vectors": [[0.5] * 768],
        "documents": ["Legacy document text"],
        "metadatas": [{"user_id": "u42"}],
    }
    json_path = str(tmp_path / "vector_store.json")
    with open(json_path, "w") as f:
        json.dump(legacy_data, f)

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    import backend.turbovec_store as tvs_module
    monkeypatch.setattr(tvs_module, "_DEFAULT_JSON_PATH", json_path)
    monkeypatch.setattr(tvs_module, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_module, "get_query_embedding", lambda text, **kw: [1.0] * 768)

    from backend.turbovec_store import TurboVecVectorStore

    with patch("backend.turbovec_store.logger.info") as mock_info:
        s = TurboVecVectorStore()
        s.load()

    # The legacy record should have been migrated
    assert s.count() > 0, "Migrated store must have records"
    assert "old_rec_1" in s._texts

    # .meta.json sidecar must have been written (save() was called)
    assert os.path.exists(index_path + ".meta.json"), ".meta.json must exist after migration save"

    # INFO log with migrated count must have been emitted
    assert mock_info.called, "Expected INFO log about migration to be called"
    called_args = mock_info.call_args[0]
    assert "Migrated" in called_args[0]
    assert called_args[1] == 1  # migrated count

    rag_module._store = None


def test_save_and_load_sidecar_atomic_write(store):
    """Req 5.2 — After add(), .meta.json exists and no leftover .tmp file remains."""
    store.add("atomic write test", {"user_id": "u99"}, "rec_atomic")

    meta_path = store._index_path + ".meta.json"
    tmp_leftover = meta_path + ".tmp"

    assert os.path.exists(meta_path), ".meta.json sidecar must exist after save"
    assert not os.path.exists(tmp_leftover), ".tmp file must not remain after atomic replace"


# ===========================================================================
# Task 5.3 — Edge-case / error-path tests
# ===========================================================================


def test_add_reraises_embedding_exception_without_modifying_store(store, monkeypatch):
    """Req 1.6, 2.4 — Embedding failure re-raises; store state is unchanged."""
    import backend.turbovec_store as tvs_mod

    monkeypatch.setattr(
        tvs_mod,
        "get_embedding",
        lambda text, **kw: (_ for _ in ()).throw(RuntimeError("embed failed")),
    )

    with pytest.raises(RuntimeError, match="embed failed"):
        store.add("some text", {"user_id": "u1"}, "rec_fail")

    assert store.count() == 0
    assert "rec_fail" not in store._texts
    assert "rec_fail" not in store._metas


def test_delete_nonexistent_returns_false(store):
    """Req 3.2 — Deleting an absent record_id returns False without side-effects."""
    assert store.delete("nonexistent_id") is False
    assert store.count() == 0


def test_delete_save_exception_returns_false(store, monkeypatch):
    """Req 3.3 — When save() raises after deletion, delete() returns False and logs error."""
    store.add("hello", {"user_id": "u1"}, "rec_to_delete")
    assert store.count() == 1

    def _raising_save():
        raise OSError("disk full")

    monkeypatch.setattr(store, "save", _raising_save)

    with patch("backend.turbovec_store.logger") as mock_logger:
        result = store.delete("rec_to_delete")

    assert result is False
    mock_logger.error.assert_called()


def test_search_empty_index_returns_empty_list(store):
    """Req 4.5 — search() on an empty store returns []."""
    assert store.search("anything") == []


def test_search_embedding_exception_returns_empty_list(store, monkeypatch):
    """Req 4.8 — When query embedding fails, search() returns []."""
    import backend.turbovec_store as tvs_mod

    store.add("document text", {"user_id": "u1"}, "rec1")
    assert store.count() == 1

    monkeypatch.setattr(
        tvs_mod,
        "get_query_embedding",
        lambda text, **kw: (_ for _ in ()).throw(RuntimeError("embed down")),
    )

    assert store.search("failing query") == []


def test_save_exception_silently_swallowed(store, monkeypatch):
    """Req 5.5 — save() logs but does NOT propagate exceptions."""
    def _raising_write(path):
        raise OSError("disk error")

    monkeypatch.setattr(store._index, "write", _raising_write)

    with patch("backend.turbovec_store.logger") as mock_logger:
        store.save()  # must not raise

    mock_logger.error.assert_called()


def test_load_exception_initialises_empty_store(tmp_path, monkeypatch):
    """Req 5.6 — When IdMapIndex.load() raises, load() recovers with an empty store."""

    class BrokenLoadIndex(DictIdMapIndex):
        @classmethod
        def load(cls, path: str) -> "BrokenLoadIndex":
            raise RuntimeError("corrupt index")

    broken_mod = types.ModuleType("turbovec")
    broken_mod.IdMapIndex = BrokenLoadIndex  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "turbovec", broken_mod)

    index_path = str(tmp_path / "broken_idx")
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)

    # Create a fake file so load() tries IdMapIndex.load()
    open(index_path, "w").close()

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    import backend.rag as rag_module
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    from backend.turbovec_store import TurboVecVectorStore

    with patch("backend.turbovec_store.logger") as mock_logger:
        tvs = TurboVecVectorStore()
        tvs.load()

    assert tvs.count() == 0
    mock_logger.error.assert_called()

    rag_module._store = None


def test_load_no_json_no_index_is_empty(tmp_path, monkeypatch):
    """Req 6.5 — Neither turbovec index nor vector_store.json → empty store, no crash."""
    turbovec_mod = _make_turbovec_module()
    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)

    index_path = str(tmp_path / "fresh_idx")
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    assert not os.path.exists(index_path)

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    import backend.rag as rag_module
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    import backend.turbovec_store as tvs_mod
    # Ensure no JSON migration file is found
    monkeypatch.setattr(tvs_mod, "_DEFAULT_JSON_PATH", str(tmp_path / "no_such_file.json"))

    from backend.turbovec_store import TurboVecVectorStore

    tvs = TurboVecVectorStore()
    tvs.load()

    assert tvs.count() == 0

    rag_module._store = None


def test_migration_skips_malformed_records_and_logs_warning(tmp_path, monkeypatch):
    """Req 6.4 — Migration skips records with non-list vectors and logs a WARNING."""
    turbovec_mod = _make_turbovec_module()
    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)

    json_path = tmp_path / "vector_store.json"
    valid_vector = [0.1] * 768
    legacy_data = {
        "ids": ["valid_rec", "bad_rec"],
        "vectors": [valid_vector, "not_a_list"],
        "documents": ["valid doc", "bad doc"],
        "metadatas": [{"user_id": "u1"}, {"user_id": "u2"}],
    }
    json_path.write_text(json.dumps(legacy_data), encoding="utf-8")

    index_path = str(tmp_path / "mig_idx")
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)

    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    import backend.rag as rag_module
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None

    import backend.turbovec_store as tvs_mod
    monkeypatch.setattr(tvs_mod, "_DEFAULT_JSON_PATH", str(json_path))

    from backend.turbovec_store import TurboVecVectorStore

    with patch("backend.turbovec_store.logger") as mock_logger:
        tvs = TurboVecVectorStore()
        tvs.load()

    assert tvs.count() == 1
    assert "valid_rec" in tvs._texts
    assert "bad_rec" not in tvs._texts

    # At least one warning must have been logged for the malformed record
    assert mock_logger.warning.called

    rag_module._store = None


# ===========================================================================
# Helpers for property-based tests
# ===========================================================================

import uuid as _uuid


def _make_pbt_store(tmp_path, monkeypatch):
    """Set up a fresh TurboVecVectorStore for use inside @given test bodies.

    Uses a unique sub-directory under tmp_path on every call so that Hypothesis
    iterations (which reuse the same tmp_path fixture) do not see a stale index
    written by a previous iteration.
    """
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    # Each call gets its own unique sub-path so previous iterations' saved
    # indexes are not visible to the current iteration.
    index_path = str(tmp_path / f"pbt_idx_{_uuid.uuid4().hex}")
    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    import backend.turbovec_store as tvs_mod
    from backend.turbovec_store import TurboVecVectorStore
    monkeypatch.setattr(tvs_mod, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", lambda text, **kw: [1.0] * 768)
    s = TurboVecVectorStore()
    s.load()
    return s


def _cleanup_pbt_store(monkeypatch):
    """Reset the RAG singleton after a property test."""
    import backend.rag as rag_module
    rag_module._store = None


# ===========================================================================
# Task 6.x — Property-based tests (Hypothesis)
# ===========================================================================


# Feature: turbovec-vector-store-integration, Property 1: Add round-trip
@given(
    text=st.text(min_size=1),
    metadata=st.fixed_dictionaries({"user_id": st.text(min_size=1)}),
    record_id=st.text(min_size=1),
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_add_round_trip(text, metadata, record_id, tmp_path, monkeypatch):
    """Req 1.4, 1.5, 2.1, 10.1, 10.2 — Added records are stored and retrievable.

    **Validates: Requirements 1.4, 1.5, 2.1, 10.1, 10.2**
    """
    store = _make_pbt_store(tmp_path, monkeypatch)
    store.add(text, metadata, record_id)
    assert store._texts[record_id] == text
    assert store._metas[record_id] == metadata
    results = store.search_with_scores("query")
    ids_in_results = [r["id"] for r in results]
    assert record_id in ids_in_results
    matching = [r for r in results if r["id"] == record_id]
    assert matching[0]["text"] == text
    assert matching[0]["metadata"] == metadata
    assert matching[0]["score"] > 0.0
    _cleanup_pbt_store(monkeypatch)


# Feature: turbovec-vector-store-integration, Property 2: Update idempotence
@given(
    record_id=st.text(min_size=1),
    text1=st.text(min_size=1),
    meta1=st.fixed_dictionaries({"user_id": st.text(min_size=1)}),
    text2=st.text(min_size=1),
    meta2=st.fixed_dictionaries({"user_id": st.text(min_size=1)}),
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_update_idempotence(record_id, text1, meta1, text2, meta2, tmp_path, monkeypatch):
    """Req 2.2 — Calling add() twice with same record_id does not grow the store.

    **Validates: Requirements 2.2**
    """
    store = _make_pbt_store(tmp_path, monkeypatch)
    store.add(text1, meta1, record_id)
    assert store.count() == 1
    store.add(text2, meta2, record_id)
    assert store.count() == 1
    assert store._texts[record_id] == text2
    assert store._metas[record_id] == meta2
    _cleanup_pbt_store(monkeypatch)


# Feature: turbovec-vector-store-integration, Property 3: Delete isolation
@given(
    record_ids=st.lists(st.text(min_size=1), min_size=1, max_size=5, unique=True)
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_delete_isolation(record_ids, tmp_path, monkeypatch):
    """Req 3.1, 3.2, 10.3 — Deleted records never appear in search results.

    **Validates: Requirements 3.1, 3.2, 10.3**
    """
    store = _make_pbt_store(tmp_path, monkeypatch)
    for rid in record_ids:
        store.add(f"text for {rid}", {"user_id": "u1"}, rid)
    count_before = store.count()
    assert count_before == len(record_ids)
    for rid in record_ids:
        result = store.delete(rid)
        assert result is True
        assert store.count() == count_before - 1
        count_before -= 1
        search_ids = [r["id"] for r in store.search_with_scores("query", k=20)]
        assert rid not in search_ids
    # Deleting a missing ID returns False
    assert store.delete("never_existed_xyz") is False
    _cleanup_pbt_store(monkeypatch)


# Feature: turbovec-vector-store-integration, Property 4: ACL filter isolation
@given(
    records=st.lists(
        st.fixed_dictionaries({
            "user_id": st.text(min_size=1, max_size=5),
            "text": st.text(min_size=1),
            "id": st.text(min_size=1),
        }),
        min_size=2,
        max_size=6,
        unique_by=lambda r: r["id"],
    )
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_acl_filter_isolation(records, tmp_path, monkeypatch):
    """Req 4.2, 4.3, 4.4 — Search never leaks cross-user records.

    **Validates: Requirements 4.2, 4.3, 4.4**
    """
    store = _make_pbt_store(tmp_path, monkeypatch)
    for rec in records:
        store.add(rec["text"], {"user_id": rec["user_id"]}, rec["id"])
    for rec in records:
        uid = rec["user_id"]
        results = store.search("query", filter_meta={"user_id": uid}, k=20)
        # Build set of texts that belong to this user
        user_texts = {r["text"] for r in records if r["user_id"] == uid}
        for returned_text in results:
            assert returned_text in user_texts, (
                f"search leaked text '{returned_text}' not belonging to user '{uid}'"
            )
    _cleanup_pbt_store(monkeypatch)


# Feature: turbovec-vector-store-integration, Property 5: Search result shape and ordering
@given(
    k=st.integers(min_value=1, max_value=5),
    n=st.integers(min_value=1, max_value=8),
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_search_result_shape_and_ordering(k, n, tmp_path, monkeypatch):
    """Req 4.1, 4.6, 4.7 — Results have correct shape, positive scores, and are sorted.

    **Validates: Requirements 4.1, 4.6, 4.7**
    """
    store = _make_pbt_store(tmp_path, monkeypatch)
    for i in range(n):
        store.add(f"document {i}", {"user_id": "u1"}, f"rec_{i}")
    results = store.search_with_scores("query", k=k)
    assert len(results) <= k
    for r in results:
        assert set(r.keys()) >= {"text", "metadata", "id", "score"}
        assert r["score"] > 0.0
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    _cleanup_pbt_store(monkeypatch)


# Feature: turbovec-vector-store-integration, Property 6: Persistence round-trip
@given(
    records=st.lists(
        st.fixed_dictionaries({
            "text": st.text(min_size=1),
            "meta": st.fixed_dictionaries({"user_id": st.text(min_size=1)}),
            "id": st.text(min_size=1),
        }),
        min_size=0,
        max_size=5,
        unique_by=lambda r: r["id"],
    )
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_persistence_round_trip(records, tmp_path, monkeypatch):
    """Req 5.1, 5.2, 5.3 — save() + load() recovers identical state.

    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / f"persist_idx_{_uuid.uuid4().hex}")
    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    import backend.turbovec_store as tvs_mod
    from backend.turbovec_store import TurboVecVectorStore
    monkeypatch.setattr(tvs_mod, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", lambda text, **kw: [1.0] * 768)

    s1 = TurboVecVectorStore()
    s1.load()
    for rec in records:
        s1.add(rec["text"], rec["meta"], rec["id"])
    s1.save()

    assert os.path.exists(index_path + ".meta.json")

    # Load a fresh instance
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    import backend.turbovec_store as tvs_mod2
    from backend.turbovec_store import TurboVecVectorStore as TVS2
    monkeypatch.setattr(tvs_mod2, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod2, "get_query_embedding", lambda text, **kw: [1.0] * 768)

    s2 = TVS2()
    s2.load()

    assert s2._texts == s1._texts
    assert s2._metas == s1._metas
    assert s2.count() == s1.count()
    rag_module._store = None


# Feature: turbovec-vector-store-integration, Property 7: JSON migration correctness
@given(
    valid_count=st.integers(min_value=0, max_value=5),
    malformed_count=st.integers(min_value=0, max_value=3),
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_migration_correctness(valid_count, malformed_count, tmp_path, monkeypatch):
    """Req 6.1, 6.4 — All valid records imported; malformed records skipped.

    **Validates: Requirements 6.1, 6.4**
    """
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / f"mig_prop_idx_{_uuid.uuid4().hex}")
    json_path = str(tmp_path / f"vector_store_prop_{_uuid.uuid4().hex}.json")

    valid_ids = [f"valid_{i}" for i in range(valid_count)]
    malformed_ids = [f"malformed_{i}" for i in range(malformed_count)]
    all_ids = valid_ids + malformed_ids
    vectors = [[0.1] * 768] * valid_count + ["not_a_list"] * malformed_count
    documents = [f"doc {i}" for i in range(len(all_ids))]
    metadatas = [{"user_id": "u1"}] * len(all_ids)

    with open(json_path, "w") as f:
        json.dump(
            {"ids": all_ids, "vectors": vectors, "documents": documents, "metadatas": metadatas},
            f,
        )

    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    import backend.turbovec_store as tvs_mod
    monkeypatch.setattr(tvs_mod, "_DEFAULT_JSON_PATH", json_path)
    monkeypatch.setattr(tvs_mod, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", lambda text, **kw: [1.0] * 768)
    from backend.turbovec_store import TurboVecVectorStore

    s = TurboVecVectorStore()
    s.load()

    assert s.count() == valid_count
    for vid in valid_ids:
        assert vid in s._texts
    for mid in malformed_ids:
        assert mid not in s._texts

    rag_module._store = None


# Feature: turbovec-vector-store-integration, Property 8: Singleton idempotence
@given(n_calls=st.integers(min_value=2, max_value=10))
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_singleton_idempotence(n_calls, tmp_path, monkeypatch):
    """Req 7.3 — get_vector_store() always returns the same object.

    **Validates: Requirements 7.3**
    """
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    index_path = str(tmp_path / f"singleton_idx_{_uuid.uuid4().hex}")
    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", index_path)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]
    import backend.turbovec_store as tvs_mod
    monkeypatch.setattr(tvs_mod, "get_embedding", lambda text, **kw: [1.0] * 768)
    monkeypatch.setattr(tvs_mod, "get_query_embedding", lambda text, **kw: [1.0] * 768)
    from backend.rag import get_vector_store

    instances = [get_vector_store() for _ in range(n_calls)]
    first_id = id(instances[0])
    for inst in instances[1:]:
        assert id(inst) == first_id, "get_vector_store() must return the same cached object"

    rag_module._store = None


# Feature: turbovec-vector-store-integration, Property 9: Invalid quantization falls back to 4-bit
@given(quant=st.text(alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00")).filter(lambda s: s not in {"2", "4"}))
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_property_invalid_quantization_fallback(quant, tmp_path, monkeypatch):
    """Req 1.3 — Invalid TURBOVEC_QUANTIZATION always falls back to 4-bit with a WARNING.

    **Validates: Requirements 1.3**
    """
    import backend.rag as rag_module

    turbovec_mod = _make_turbovec_module()
    monkeypatch.setitem(sys.modules, "turbovec", turbovec_mod)
    monkeypatch.setenv("TURBOVEC_INDEX_PATH", str(tmp_path / f"quant_prop_idx_{_uuid.uuid4().hex}"))
    monkeypatch.setenv("TURBOVEC_QUANTIZATION", quant)
    monkeypatch.setattr(rag_module.core_ai, "embed_text", lambda text, **kw: [1.0] * 768)
    rag_module._store = None
    if "backend.turbovec_store" in sys.modules:
        del sys.modules["backend.turbovec_store"]

    # Import the module fresh so the module-level logger is bound, then patch it.

    with patch("backend.turbovec_store.logger") as mock_logger:
        from backend.turbovec_store import TurboVecVectorStore
        s = TurboVecVectorStore()

    assert s._quantization == 4, (
        f"Expected fallback to 4-bit, got {s._quantization} for quant={quant!r}"
    )
    mock_logger.warning.assert_called()

    rag_module._store = None
