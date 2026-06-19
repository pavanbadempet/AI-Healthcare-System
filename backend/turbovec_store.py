"""
TurboVecVectorStore — turbovec-backed vector store backend
==========================================================

Implements ``VectorStoreBackend`` using turbovec's ``IdMapIndex``, a
Rust-powered SIMD-accelerated ANN index with 2-bit/4-bit quantization.

``turbovec`` is an *optional* dependency.  The top-level import is deferred
to :meth:`TurboVecVectorStore.__init__` so this module can be imported even
when turbovec is not installed.  When it is absent, ``get_vector_store()`` in
``rag.py`` catches the ``ImportError`` and falls back to ``SimpleVectorStore``.

Environment variables
---------------------
TURBOVEC_INDEX_PATH   Path for the native turbovec binary index (default:
                      ``models/turbovec_index``)
TURBOVEC_QUANTIZATION Quantization bits – ``"2"`` or ``"4"`` (default: ``"4"``)

turbovec API notes
------------------
``IdMapIndex`` uses uint64 integer IDs internally.  This class maintains a
bidirectional mapping between string ``record_id`` values (used by the
``VectorStoreBackend`` interface) and uint64 integers stored in the index.
The mapping is persisted in the ``.meta.json`` sidecar alongside texts and
metadata.

Key API differences from the design-doc assumptions:
- Constructor: ``IdMapIndex(dim=None, bit_width=4)``  (not ``bits=``)
- Add:  ``add_with_ids(vectors: ndarray, ids: ndarray[uint64])``
- Remove: ``remove(uint64_id)``
- Save: ``write(path)``
- Load: ``IdMapIndex.load(path)``
- Search returns ``(scores_ndarray, ids_ndarray)`` each shape ``(1, k)``
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np

from .rag import _metadata_matches_filter, get_embedding, get_query_embedding
from .vector_store_base import VectorStoreBackend

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

TURBOVEC_INDEX_PATH: str = os.environ.get(
    "TURBOVEC_INDEX_PATH", "models/turbovec_index"
)
TURBOVEC_QUANTIZATION: str = os.environ.get("TURBOVEC_QUANTIZATION", "4")

# Valid quantization levels supported by turbovec.
_VALID_QUANTIZATIONS = {"2", "4"}

# Default path to the legacy JSON vector store for one-time migration.
# Tests can patch this module-level constant to redirect migration reads.
_DEFAULT_JSON_PATH: str = "vector_store.json"


# ---------------------------------------------------------------------------
# TurboVecVectorStore
# ---------------------------------------------------------------------------


class TurboVecVectorStore(VectorStoreBackend):
    """turbovec-backed vector store.  Implements :class:`VectorStoreBackend`.

    The turbovec ``IdMapIndex`` is loaded lazily inside :meth:`load`.
    ``__init__`` performs only env-var resolution, quantization validation,
    and in-memory state initialisation so that constructing the class never
    performs I/O or requires turbovec to be installed.

    Because ``IdMapIndex`` uses uint64 integer IDs internally, this class
    maintains:
      - ``_str_to_int: Dict[str, int]``  — string record_id → uint64 int
      - ``_int_to_str: Dict[int, str]``  — uint64 int → string record_id
      - ``_next_id: int``                — next available uint64 integer slot

    These mappings are persisted in the ``.meta.json`` sidecar.
    """

    def __init__(self) -> None:
        # Read configuration from environment at construction time so that
        # tests can monkeypatch env vars before instantiation.
        self._index_path: str = os.environ.get(
            "TURBOVEC_INDEX_PATH", "models/turbovec_index"
        )

        raw_quant: str = os.environ.get("TURBOVEC_QUANTIZATION", "4")
        if raw_quant not in _VALID_QUANTIZATIONS:
            logger.warning(
                "TURBOVEC_QUANTIZATION=%r is not valid (expected '2' or '4'). "
                "Falling back to 4-bit quantization.",
                raw_quant,
            )
            self._quantization: int = 4
        else:
            self._quantization = int(raw_quant)

        # In-memory state — populated by load() / add()
        self._index = None                          # turbovec.IdMapIndex, set by load()
        self._texts: Dict[str, str] = {}            # record_id -> document text
        self._metas: Dict[str, Dict[str, Any]] = {} # record_id -> metadata dict

        # Integer ID mapping (string record_id ↔ uint64 int for turbovec)
        self._str_to_int: Dict[str, int] = {}       # string record_id -> uint64 int
        self._int_to_str: Dict[int, str] = {}       # uint64 int -> string record_id
        self._next_id: int = 0                      # next available integer slot

    # ------------------------------------------------------------------
    # VectorStoreBackend abstract methods — stubbed until later tasks
    # ------------------------------------------------------------------

    def add(self, text: str, metadata: Dict[str, Any], record_id: str) -> None:
        """Add or update a document in the turbovec index.

        Obtains an embedding via ``get_embedding(text, task_type="retrieval_document")``.
        If the record already exists, removes and re-inserts; otherwise inserts a new entry.
        Calls ``save()`` after a successful index operation.

        Raises:
            Any exception raised by ``get_embedding()`` is logged and re-raised
            without modifying ``_index``, ``_texts``, or ``_metas``.
        """
        # Step 1 — obtain the embedding; re-raise (without modifying state) on failure.
        try:
            vector = get_embedding(text)
        except Exception:
            logger.error(
                "TurboVecVectorStore.add() failed to get embedding for record_id=%r",
                record_id,
                exc_info=True,
            )
            raise

        # Step 2 — resolve or allocate the uint64 integer ID.
        if record_id in self._str_to_int:
            # Record already exists — remove the old vector from the index.
            uint_id = self._str_to_int[record_id]
            self._index.remove(uint_id)
        else:
            # New record — assign a fresh integer ID.
            uint_id = self._next_id
            self._next_id += 1
            self._str_to_int[record_id] = uint_id
            self._int_to_str[uint_id] = record_id

        # Step 3 — insert into the turbovec index using numpy arrays.
        vec_array = np.array([vector], dtype="float32")
        id_array = np.array([uint_id], dtype="uint64")
        self._index.add_with_ids(vec_array, id_array)
        self._texts[record_id] = text
        self._metas[record_id] = metadata

        # Step 4 — persist.  save() silently swallows its own exceptions internally.
        self.save()

    def delete(self, record_id: str) -> bool:
        """Delete a document by ``record_id``.  Returns ``True`` on success.

        Returns ``False`` immediately if the record does not exist, without
        touching the index or calling ``save()``.

        If ``save()`` raises after the in-memory state has already been
        modified, the error is logged and ``False`` is returned; the
        in-memory state remains modified (consistent with the design spec).
        """
        # Step 1 — short-circuit for unknown record IDs (Req 3.2).
        if record_id not in self._texts:
            return False

        # Step 2 — remove from the turbovec index and in-memory dicts (Req 3.1).
        uint_id = self._str_to_int.pop(record_id, None)
        if uint_id is not None:
            self._index.remove(uint_id)
            self._int_to_str.pop(uint_id, None)
        del self._texts[record_id]
        del self._metas[record_id]

        # Step 3 — persist; on failure log and return False (Req 3.3).
        try:
            self.save()
        except Exception:
            logger.error(
                "TurboVecVectorStore.delete() failed to save after removing record_id=%r",
                record_id,
                exc_info=True,
            )
            return False

        return True

    def search(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[str]:
        """Return up to *k* matching document texts.

        Excludes results with ``score <= 0.0``.  Returns ``[]`` immediately on
        an empty index or if the query embedding fails.
        """
        results = self._do_search_with_scores(query, filter_meta=filter_meta, k=k)
        return [r["text"] for r in results]

    def search_with_scores(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Return up to *k* results with ``text``, ``metadata``, ``id``, ``score``.

        Results are ordered descending by score.  Results with ``score <= 0.0``
        are excluded.
        """
        return self._do_search_with_scores(query, filter_meta=filter_meta, k=k)

    def _do_search_with_scores(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Shared implementation for :meth:`search` and :meth:`search_with_scores`.

        Returns a list of dicts with ``"text"``, ``"metadata"``, ``"id"``, and
        ``"score"`` keys, ordered descending by ``"score"``, with zero/negative
        scores excluded.

        ``turbovec.IdMapIndex.search`` returns ``(scores_ndarray, ids_ndarray)``
        both of shape ``(1, k)``.  The ids are uint64 integers that must be
        mapped back to string record IDs via ``_int_to_str``.
        """
        # Short-circuit on empty index (Req 4.5)
        if self.count() == 0:
            return []

        # Obtain query embedding (Req 4.8)
        try:
            query_vec = get_query_embedding(query)
        except Exception:
            logger.error(
                "TurboVecVectorStore.search() failed to get query embedding.",
                exc_info=True,
            )
            return []

        # Build allowlist of uint64 IDs when a metadata filter is provided (Req 4.2, 4.3)
        allowlist_uint: Optional[np.ndarray] = None
        if filter_meta is not None:
            str_allowlist = self._build_allowlist(filter_meta)
            if not str_allowlist:
                return []
            allowlist_uint = np.array(
                [self._str_to_int[rid] for rid in str_allowlist if rid in self._str_to_int],
                dtype="uint64",
            )
            if len(allowlist_uint) == 0:
                return []

        # Run ANN search.  turbovec returns (scores, ids) each shaped (1, k).
        q_array = np.array([query_vec], dtype="float32")
        try:
            if allowlist_uint is not None:
                try:
                    scores_arr, ids_arr = self._index.search(q_array, k=k, allowlist=allowlist_uint)
                except TypeError:
                    # turbovec version does not support allowlist parameter — post-filter
                    scores_arr, ids_arr = self._index.search(q_array, k=k)
            else:
                scores_arr, ids_arr = self._index.search(q_array, k=k)
        except Exception:
            logger.error(
                "TurboVecVectorStore.search() failed during index search.",
                exc_info=True,
            )
            return []

        # scores_arr and ids_arr are shape (1, k) — take first row.
        scores_row = scores_arr[0].tolist() if len(scores_arr) > 0 else []
        ids_row = ids_arr[0].tolist() if len(ids_arr) > 0 else []

        # Build output, exclude non-positive scores, apply post-filter if needed.
        output: List[Dict[str, Any]] = []
        for uint_id, score in zip(ids_row, scores_row):
            if score <= 0.0:
                continue
            record_id = self._int_to_str.get(int(uint_id))
            if record_id is None:
                continue
            if filter_meta is not None and not _metadata_matches_filter(
                self._metas.get(record_id, {}), filter_meta
            ):
                continue
            output.append(
                {
                    "text": self._texts.get(record_id, ""),
                    "metadata": self._metas.get(record_id, {}),
                    "id": record_id,
                    "score": float(score),
                }
            )

        # Ensure descending order by score
        output.sort(key=lambda r: r["score"], reverse=True)
        return output

    def count(self) -> int:
        """Return the number of documents currently in the store."""
        return len(self._texts)

    def load(self) -> None:
        """Load (or initialise) the turbovec index from ``_index_path``."""
        try:
            import turbovec
            if os.path.exists(self._index_path):
                # Load existing native index
                self._index = turbovec.IdMapIndex.load(self._index_path)
                # Load companion sidecar for texts, metas, and ID maps
                meta_path = self._index_path + ".meta.json"
                if os.path.exists(meta_path):
                    with open(meta_path, "r", encoding="utf-8") as f:
                        sidecar = json.load(f)
                    self._texts = sidecar.get("texts", {})
                    self._metas = sidecar.get("metas", {})
                    # Restore integer ID mappings (JSON keys are strings)
                    self._str_to_int = {
                        k: int(v) for k, v in sidecar.get("str_to_int", {}).items()
                    }
                    self._int_to_str = {
                        int(k): v for k, v in sidecar.get("int_to_str", {}).items()
                    }
                    self._next_id = int(sidecar.get("next_id", 0))
                else:
                    self._texts = {}
                    self._metas = {}
                    self._str_to_int = {}
                    self._int_to_str = {}
                    self._next_id = 0
            else:
                # No persisted index — initialise empty
                self._index = turbovec.IdMapIndex(bit_width=self._quantization)
                self._texts = {}
                self._metas = {}
                self._str_to_int = {}
                self._int_to_str = {}
                self._next_id = 0
                # Trigger JSON migration if legacy file exists.
                if os.path.exists(_DEFAULT_JSON_PATH):
                    self._migrate_from_json(_DEFAULT_JSON_PATH)
        except Exception:
            logger.error(
                "Failed to load turbovec index from %r — initialising empty index.",
                self._index_path,
                exc_info=True,
            )
            import turbovec
            self._index = turbovec.IdMapIndex(bit_width=self._quantization)
            self._texts = {}
            self._metas = {}
            self._str_to_int = {}
            self._int_to_str = {}
            self._next_id = 0

    def save(self) -> None:
        """Persist the turbovec index and companion sidecar atomically."""
        try:
            # Create the directory if it doesn't exist (only when dirname is non-empty)
            dir_name = os.path.dirname(self._index_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            # Persist the native turbovec index (turbovec uses write(), not save())
            self._index.write(self._index_path)

            # Write companion sidecar atomically: write to .tmp, then os.replace.
            # The sidecar stores texts, metas, and the integer ID mappings.
            meta_path = self._index_path + ".meta.json"
            tmp_path = meta_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "texts": self._texts,
                        "metas": self._metas,
                        "str_to_int": self._str_to_int,
                        # JSON requires string keys
                        "int_to_str": {str(k): v for k, v in self._int_to_str.items()},
                        "next_id": self._next_id,
                    },
                    f,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            os.replace(tmp_path, meta_path)
        except Exception:
            logger.error(
                "TurboVecVectorStore.save() failed for index path %r",
                self._index_path,
                exc_info=True,
            )

    # ------------------------------------------------------------------
    # Internal helpers — stubbed until later tasks
    # ------------------------------------------------------------------

    def _build_allowlist(
        self, filter_meta: Dict[str, Any]
    ) -> List[str]:
        """Return record IDs whose metadata satisfies ``filter_meta``.

        Iterates :attr:`_metas` and collects every ``record_id`` for which
        :func:`_metadata_matches_filter` returns ``True``.
        """
        return [
            record_id
            for record_id, meta in self._metas.items()
            if _metadata_matches_filter(meta, filter_meta)
        ]

    def _migrate_from_json(self, json_path: str) -> None:
        """Migrate records from a legacy ``vector_store.json`` file."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ids = data.get("ids", [])
        vectors = data.get("vectors", [])
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])

        migrated = 0
        for record_id, vector, text, meta in zip(ids, vectors, documents, metadatas):
            if not isinstance(vector, list):
                logger.warning(
                    "Skipping record %r during migration: vector is missing or not a list.",
                    record_id,
                )
                continue
            # Assign an integer ID and insert directly without re-embedding
            uint_id = self._next_id
            self._next_id += 1
            self._str_to_int[record_id] = uint_id
            self._int_to_str[uint_id] = record_id

            vec_array = np.array([vector], dtype="float32")
            id_array = np.array([uint_id], dtype="uint64")
            self._index.add_with_ids(vec_array, id_array)
            self._texts[record_id] = text
            self._metas[record_id] = meta if meta is not None else {}
            migrated += 1

        self.save()
        logger.info("Migrated %d records from %r into turbovec index.", migrated, json_path)
