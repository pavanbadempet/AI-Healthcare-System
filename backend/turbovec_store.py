"""
TurboVecVectorStore — turbovec-backed vector store backend
==========================================================
Implements VectorStoreBackend using turbovec's IdMapIndex:
  - Rust-based SIMD-accelerated ANN search (TurboQuant 2-bit/4-bit)
  - Stable external string IDs with O(1) deletes
  - Filtered search via allowlists (ACL-based per-user/per-facility isolation)
  - Index persistence: native binary + companion JSON sidecar (atomic write)
  - One-time migration from existing vector_store.json on first load

Environment variables:
  TURBOVEC_INDEX_PATH   Path for native index (default: models/turbovec_index)
  TURBOVEC_QUANTIZATION Quantization bits: "2" or "4" (default: "4")

Falls back to SimpleVectorStore (in rag.py) when turbovec is not installed.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import turbovec  # noqa: F401 — ImportError caught by get_vector_store() in rag.py

from .vector_store_base import VectorStoreBackend

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths (resolved relative to the project root, one level up from
# this file's directory — i.e. backend/../models/)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_DEFAULT_INDEX_PATH = os.path.join(_PROJECT_ROOT, "models", "turbovec_index")
_DEFAULT_JSON_PATH = os.path.join(_PROJECT_ROOT, "models", "vector_store.json")


def _resolve_index_path() -> str:
    raw = os.getenv("TURBOVEC_INDEX_PATH", "").strip()
    if raw:
        return raw if os.path.isabs(raw) else os.path.join(_PROJECT_ROOT, raw)
    return _DEFAULT_INDEX_PATH


def _resolve_quantization() -> int:
    raw = os.getenv("TURBOVEC_QUANTIZATION", "4").strip()
    if raw not in {"2", "4"}:
        logger.warning(
            "TURBOVEC_QUANTIZATION='%s' is invalid (must be '2' or '4'). "
            "Falling back to 4-bit quantization.",
            raw,
        )
        return 4
    return int(raw)


class TurboVecVectorStore(VectorStoreBackend):
    """
    turbovec-backed implementation of VectorStoreBackend.

    Uses turbovec.IdMapIndex for SIMD-accelerated ANN search with 2-bit/4-bit
    TurboQuant compression.  Metadata and raw document text are kept in
    in-memory dicts keyed by record_id and persisted alongside the native
    index as a JSON sidecar file.
    """

    def __init__(self) -> None:
        self._index_path: str = _resolve_index_path()
        self._quantization: int = _resolve_quantization()
        self._meta_path: str = self._index_path + ".meta.json"
        # In-memory stores — populated by load()
        self._texts: Dict[str, str] = {}
        self._metas: Dict[str, Dict[str, Any]] = {}
        self._index: Optional[turbovec.IdMapIndex] = None  # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # VectorStoreBackend: load / save
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load index from disk, or initialise fresh + migrate from JSON."""
        try:
            if os.path.exists(self._index_path):
                self._index = turbovec.IdMapIndex.load(self._index_path)  # type: ignore[attr-defined]
                if os.path.exists(self._meta_path):
                    with open(self._meta_path, "r", encoding="utf-8") as f:
                        sidecar = json.load(f) or {}
                    self._texts = sidecar.get("texts", {}) or {}
                    self._metas = sidecar.get("metas", {}) or {}
                logger.info(
                    "TurboVecVectorStore loaded: %d records from %s",
                    len(self._texts),
                    self._index_path,
                )
            else:
                # No existing index — start fresh
                self._index = turbovec.IdMapIndex(bits=self._quantization)  # type: ignore[attr-defined]
                self._texts = {}
                self._metas = {}
                # One-time migration from legacy vector_store.json
                if os.path.exists(_DEFAULT_JSON_PATH):
                    self._migrate_from_json(_DEFAULT_JSON_PATH)
                else:
                    logger.info("TurboVecVectorStore initialised as empty index.")
        except Exception:
            logger.error(
                "TurboVecVectorStore.load() failed — initialising empty index.",
                exc_info=True,
            )
            self._index = turbovec.IdMapIndex(bits=self._quantization)  # type: ignore[attr-defined]
            self._texts = {}
            self._metas = {}

    def save(self) -> None:
        """Persist native index and companion sidecar to disk (atomic write)."""
        try:
            index_dir = os.path.dirname(self._index_path)
            if index_dir:
                os.makedirs(index_dir, exist_ok=True)
            # Native turbovec index
            self._index.save(self._index_path)  # type: ignore[union-attr]
            # Companion sidecar (atomic)
            tmp_path = self._meta_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"texts": self._texts, "metas": self._metas},
                    f,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            os.replace(tmp_path, self._meta_path)
        except Exception:
            logger.error("TurboVecVectorStore.save() failed.", exc_info=True)

    # ------------------------------------------------------------------
    # VectorStoreBackend: add / delete / count
    # ------------------------------------------------------------------

    def add(self, text: str, metadata: Dict[str, Any], record_id: str) -> None:
        """Insert or update a document in the index."""
        # Import here to keep the embedding call consistent with rag.py
        from .rag import get_embedding  # noqa: PLC0415

        try:
            vector = get_embedding(text)
        except Exception:
            logger.error(
                "TurboVecVectorStore.add(): embedding failed for record_id=%r",
                record_id,
                exc_info=True,
            )
            raise

        try:
            if record_id in self._texts:
                # Update: delete old slot then re-add
                self._index.delete(record_id)  # type: ignore[union-attr]
            self._index.add(record_id, vector)  # type: ignore[union-attr]
            self._texts[record_id] = text
            self._metas[record_id] = metadata
            self.save()
        except Exception:
            logger.error(
                "TurboVecVectorStore.add(): index update failed for record_id=%r",
                record_id,
                exc_info=True,
            )
            raise

    def delete(self, record_id: str) -> bool:
        """Delete a document by ID. Returns True if found and deleted."""
        if record_id not in self._texts:
            return False
        try:
            self._index.delete(record_id)  # type: ignore[union-attr]
            del self._texts[record_id]
            del self._metas[record_id]
            self.save()
            return True
        except Exception:
            logger.error(
                "TurboVecVectorStore.delete(): failed for record_id=%r",
                record_id,
                exc_info=True,
            )
            return False

    def count(self) -> int:
        """Return the total number of indexed documents."""
        return len(self._texts)

    # ------------------------------------------------------------------
    # VectorStoreBackend: search / search_with_scores
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[str]:
        """Semantic search returning document texts."""
        if not self._texts:
            return []

        from .rag import get_query_embedding  # noqa: PLC0415

        try:
            query_vector = get_query_embedding(query)
        except Exception:
            logger.error("TurboVecVectorStore.search(): embedding failed.", exc_info=True)
            return []

        results = self._run_search(query_vector, filter_meta=filter_meta, k=k)
        return [r["text"] for r in results]

    def search_with_scores(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Semantic search returning dicts with text, metadata, id, score."""
        if not self._texts:
            return []

        from .rag import get_query_embedding  # noqa: PLC0415

        try:
            query_vector = get_query_embedding(query)
        except Exception:
            logger.error(
                "TurboVecVectorStore.search_with_scores(): embedding failed.",
                exc_info=True,
            )
            return []

        return self._run_search(query_vector, filter_meta=filter_meta, k=k)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_search(
        self,
        query_vector: List[float],
        filter_meta: Optional[Dict[str, Any]],
        k: int,
    ) -> List[Dict[str, Any]]:
        """
        Core search logic.  Uses allowlist-based pre-filtering when
        filter_meta is provided (turbovec IdMapIndex allowlist param), with
        post-filter fallback if the API is unavailable.
        Returns list of result dicts ordered descending by score, score > 0.
        """
        from .rag import _metadata_matches_filter  # noqa: PLC0415

        allowlist: Optional[List[str]] = None
        if filter_meta:
            allowlist = self._build_allowlist(filter_meta)
            if not allowlist:
                return []

        # Attempt allowlist-based pre-filter (turbovec >= 0.5 supports this)
        try:
            if allowlist is not None:
                raw = self._index.search(query_vector, k=k, allowlist=allowlist)  # type: ignore[union-attr]
            else:
                raw = self._index.search(query_vector, k=k)  # type: ignore[union-attr]
            # raw is expected to be List[Tuple[str, float]] — (record_id, score)
            results = []
            for record_id, score in raw:
                if score <= 0.0:
                    continue
                if record_id not in self._texts:
                    continue
                meta = self._metas.get(record_id, {})
                # Post-filter fallback (covers case where allowlist was not used)
                if filter_meta and not _metadata_matches_filter(meta, filter_meta):
                    continue
                results.append({
                    "text": self._texts[record_id],
                    "metadata": meta,
                    "id": record_id,
                    "score": float(score),
                })
                if len(results) >= k:
                    break
            # Ensure descending order by score
            results.sort(key=lambda x: x["score"], reverse=True)
            return results
        except TypeError:
            # turbovec version doesn't support allowlist param — fall back to
            # searching without it and applying post-retrieval filter
            logger.debug(
                "TurboVecVectorStore: allowlist param not supported, "
                "falling back to post-retrieval filtering."
            )
            raw = self._index.search(query_vector, k=len(self._texts) or k)  # type: ignore[union-attr]
            results = []
            for record_id, score in raw:
                if score <= 0.0:
                    continue
                if record_id not in self._texts:
                    continue
                meta = self._metas.get(record_id, {})
                if filter_meta and not _metadata_matches_filter(meta, filter_meta):
                    continue
                results.append({
                    "text": self._texts[record_id],
                    "metadata": meta,
                    "id": record_id,
                    "score": float(score),
                })
                if len(results) >= k:
                    break
            results.sort(key=lambda x: x["score"], reverse=True)
            return results

    def _build_allowlist(self, filter_meta: Dict[str, Any]) -> List[str]:
        """Return record IDs whose metadata matches filter_meta."""
        from .rag import _metadata_matches_filter  # noqa: PLC0415

        return [
            rid
            for rid, meta in self._metas.items()
            if _metadata_matches_filter(meta, filter_meta)
        ]

    def _migrate_from_json(self, json_path: str) -> None:
        """
        One-time migration: import all valid records from vector_store.json
        into this turbovec index without re-embedding.
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception:
            logger.error(
                "TurboVecVectorStore: failed to read migration source %s",
                json_path,
                exc_info=True,
            )
            return

        documents = data.get("documents", []) or []
        vectors = data.get("vectors", []) or []
        metadatas = data.get("metadatas", []) or []
        ids = data.get("ids", []) or []

        migrated = 0
        for i, record_id in enumerate(ids):
            vector = vectors[i] if i < len(vectors) else None
            text = documents[i] if i < len(documents) else ""
            meta = metadatas[i] if i < len(metadatas) else {}

            if not isinstance(vector, list) or len(vector) == 0:
                logger.warning(
                    "TurboVecVectorStore migration: skipping record_id=%r "
                    "(missing or malformed vector)",
                    record_id,
                )
                continue

            try:
                self._index.add(record_id, vector)  # type: ignore[union-attr]
                self._texts[record_id] = text
                self._metas[record_id] = meta
                migrated += 1
            except Exception:
                logger.warning(
                    "TurboVecVectorStore migration: failed to insert record_id=%r",
                    record_id,
                    exc_info=True,
                )

        logger.info(
            "TurboVecVectorStore: migrated %d records from %s",
            migrated,
            json_path,
        )
        self.save()
