"""
RAG Module - Semantic Memory for Personalized Healthcare AI
============================================================
Uses centralized core_ai embeddings (no local embedding model needed = saves ~200MB)

Enhanced with citation tracking, token budget management, and
RAGResult return types from the Singularity AI Engine architecture.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from . import core_ai
from .vector_store_base import VectorStoreBackend

# --- Logging ---
logger = logging.getLogger(__name__)

# ── Token Budget Constants ──
DEFAULT_CONTEXT_TOKEN_BUDGET = 3000
DEFAULT_MAX_CHUNKS = 10


# ── RAG Pipeline Dataclasses (from Singularity AI Engine) ──

@dataclass
class RetrievedChunk:
    """A single retrieved context chunk from the vector store."""
    record_type: str
    record_id: str
    text: str
    similarity: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def citation_key(self) -> str:
        return f"{self.record_type}:{self.record_id}"

    def estimated_tokens(self) -> int:
        """Rough token estimate (4 chars ≈ 1 token for English text)."""
        return max(1, len(self.text) // 4)


@dataclass
class Citation:
    """A citation linking generated text back to source records."""
    record_type: str
    record_id: str
    record_name: str
    relevance: float
    excerpt: str = ""


@dataclass
class RAGResult:
    """Result of a RAG pipeline execution with citations."""
    answer: str
    citations: List[Citation] = field(default_factory=list)
    context_chunks_used: int = 0
    total_context_tokens: int = 0
    model_used: str = ""
    grounded: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [
                {
                    "record_type": c.record_type,
                    "record_id": c.record_id,
                    "record_name": c.record_name,
                    "relevance": round(c.relevance, 3),
                    "excerpt": c.excerpt,
                }
                for c in self.citations
            ],
            "metadata": {
                "context_chunks_used": self.context_chunks_used,
                "total_context_tokens": self.total_context_tokens,
                "model_used": self.model_used,
                "grounded": self.grounded,
            },
        }


def assemble_context(
    chunks: List[RetrievedChunk],
    token_budget: int = DEFAULT_CONTEXT_TOKEN_BUDGET,
    max_chunks: int = DEFAULT_MAX_CHUNKS,
) -> tuple:
    """
    Assemble retrieved chunks into a context string within the token budget.

    Returns (context_string, total_tokens_used, selected_chunks).
    """
    selected = []
    total_tokens = 0

    for chunk in chunks[:max_chunks]:
        chunk_tokens = chunk.estimated_tokens()
        if total_tokens + chunk_tokens > token_budget:
            break
        selected.append(chunk)
        total_tokens += chunk_tokens

    context_parts = []
    for i, chunk in enumerate(selected, 1):
        source = f"[{chunk.record_type.title()} #{chunk.record_id}]"
        context_parts.append(f"{i}. {source} {chunk.text}")

    return "\n".join(context_parts), total_tokens, selected

# --- Constants ---
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "models", "vector_store.json")

def get_embedding(text: str) -> List[float]:
    """
    Generate an embedding through the centralized AI provider boundary.
    """
    return core_ai.embed_text(text, task_type="retrieval_document")

def get_query_embedding(text: str) -> List[float]:
    """Generate embedding for search query."""
    return core_ai.embed_text(text, task_type="retrieval_query")


def _normalize_acl_value(value: Any) -> str:
    return str(value).strip()


def _build_acl_filter(user_id: str, facility_id: Optional[str] = None) -> Dict[str, str]:
    acl_filter = {"user_id": _normalize_acl_value(user_id)}
    if facility_id is not None and _normalize_acl_value(facility_id):
        acl_filter["facility_id"] = _normalize_acl_value(facility_id)
    return acl_filter


def _metadata_matches_filter(metadata: Dict[str, Any], filter_meta: Dict[str, Any]) -> bool:
    for key, expected in filter_meta.items():
        if key not in metadata:
            return False
        if _normalize_acl_value(metadata[key]) != _normalize_acl_value(expected):
            return False
    return True


class LocalitySensitiveHash:
    """
    Locality-Sensitive Hashing (LSH) for fast Approximate Nearest Neighbor (ANN) search.
    Partitions high-dimensional spaces using random projection hyperplanes.
    """
    def __init__(self, num_tables: int = 5, hash_size: int = 6):
        self.num_tables = num_tables
        self.hash_size = hash_size
        self.dim: Optional[int] = None
        self.tables: List[Dict[str, Any]] = []

    def _init_tables(self, dim: int) -> None:
        self.dim = dim
        self.tables = []
        from collections import defaultdict
        rng = np.random.RandomState(42)
        for _ in range(self.num_tables):
            planes = rng.normal(0, 1, (self.hash_size, dim))
            self.tables.append({
                "planes": planes,
                "buckets": defaultdict(list)
            })

    def _hash(self, planes: np.ndarray, vector: np.ndarray) -> int:
        projection = np.dot(planes, vector)
        bits = projection > 0
        val = 0
        for b in bits:
            val = (val << 1) | int(b)
        return val

    def index(self, record_id: str, vector: np.ndarray) -> None:
        if self.dim is None:
            self._init_tables(len(vector))
        for table in self.tables:
            hash_val = self._hash(table["planes"], vector)
            if record_id not in table["buckets"][hash_val]:
                table["buckets"][hash_val].append(record_id)

    def query(self, query_vector: np.ndarray) -> set[str]:
        if self.dim is None:
            return set()
        candidates = set()
        for table in self.tables:
            hash_val = self._hash(table["planes"], query_vector)
            candidates.update(table["buckets"][hash_val])
        return candidates

    def clear(self) -> None:
        self.dim = None
        self.tables = []


class SimpleVectorStore(VectorStoreBackend):
    """
    Persistent vector store using JSON + Scikit-Learn cosine similarity.
    Embeddings are generated through core_ai.
    Implements the VectorStoreBackend interface for future pluggable backends.
    """

    def __init__(self):
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.vectors: List[List[float]] = []
        self.ids: List[str] = []
        self.id_to_idx: Dict[str, int] = {}
        self.lsh = LocalitySensitiveHash()
        self.load()

    def load(self) -> None:
        """Load from JSON file (avoids pickle deserialization risks)."""
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                self.documents = data.get("documents", []) or []
                self.metadatas = data.get("metadatas", []) or []
                self.vectors = data.get("vectors", []) or []
                self.ids = data.get("ids", []) or []
                self.id_to_idx = {rid: i for i, rid in enumerate(self.ids)}

                # Re-index LSH
                self.lsh.clear()
                for record_id, vec in zip(self.ids, self.vectors):
                    self.lsh.index(record_id, np.array(vec))

                logger.info(f"Loaded Vector Store: {len(self.ids)} records and indexed LSH.")
                return
            except Exception:
                logger.error("Failed to load vector store JSON")

        # Optional one-time migration path from legacy pickle store.
        legacy_pkl = os.path.splitext(DB_FILE)[0] + ".pkl"
        if os.path.exists(legacy_pkl) and os.getenv("ALLOW_PICKLE_MIGRATION", "").strip().lower() in {"1", "true", "yes", "on"}:
            try:
                import pickle  # local import; only used when explicitly enabled
                with open(legacy_pkl, "rb") as f:
                    data = pickle.load(f) or {}
                self.documents = data.get("documents", []) or []
                self.metadatas = data.get("metadatas", []) or []
                self.vectors = data.get("vectors", []) or []
                self.ids = data.get("ids", []) or []
                self.id_to_idx = {rid: i for i, rid in enumerate(self.ids)}
                self.save()

                # Re-index LSH
                self.lsh.clear()
                for record_id, vec in zip(self.ids, self.vectors):
                    self.lsh.index(record_id, np.array(vec))

                logger.warning("Migrated legacy pickle vector store to JSON. Disable ALLOW_PICKLE_MIGRATION after first run.")
            except Exception:
                logger.error("Failed to migrate legacy pickle vector store")

    def save(self) -> None:
        """Persist to JSON file (atomic write)."""
        try:
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
            tmp_path = DB_FILE + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "documents": self.documents,
                        "metadatas": self.metadatas,
                        "vectors": self.vectors,
                        "ids": self.ids,
                    },
                    f,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            os.replace(tmp_path, DB_FILE)
        except Exception:
            logger.error("Failed to save vector store")

    def add(self, text: str, metadata: Dict[str, Any], record_id: str) -> None:
        """Add or update a document."""
        vector = get_embedding(text)

        if record_id in self.id_to_idx:
            idx = self.id_to_idx[record_id]
            self.documents[idx] = text
            self.metadatas[idx] = metadata
            self.vectors[idx] = vector
        else:
            idx = len(self.ids)
            self.documents.append(text)
            self.metadatas.append(metadata)
            self.vectors.append(vector)
            self.ids.append(record_id)
            self.id_to_idx[record_id] = idx

        # Index in LSH
        self.lsh.index(record_id, np.array(vector))
        self.save()

    def delete(self, record_id: str) -> bool:
        """Delete by ID."""
        if record_id in self.id_to_idx:
            idx = self.id_to_idx[record_id]
            self.documents.pop(idx)
            self.metadatas.pop(idx)
            self.vectors.pop(idx)
            self.ids.pop(idx)

            # Rebuild index map because indices shifted
            self.id_to_idx = {rid: i for i, rid in enumerate(self.ids)}

            # Re-index LSH
            self.lsh.clear()
            for rid, vec in zip(self.ids, self.vectors):
                self.lsh.index(rid, np.array(vec))

            self.save()
            return True
        return False

    def _hybrid_score(self, query: str, document_text: str, similarity_score: float) -> float:
        """Calculate hybrid relevance score combining vector similarity and exact keyword match."""
        query_words = set(query.lower().split())
        doc_text_lower = document_text.lower()

        # Exclude common stop words and short query terms
        stop_words = {"a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "to", "of", "in", "on", "at", "for"}
        filtered_query = {w for w in query_words if w not in stop_words and len(w) > 2}
        if not filtered_query:
            return similarity_score

        # Exact substring or word match check
        matches = 0
        for word in filtered_query:
            if f" {word} " in f" {doc_text_lower} " or doc_text_lower.startswith(f"{word} ") or doc_text_lower.endswith(f" {word}"):
                matches += 1

        # Boost score by 0.05 per keyword match, up to a maximum boost of 0.20
        boost = min(0.05 * matches, 0.20)
        return similarity_score + boost

    def search(self, query: str, filter_meta: Optional[Dict[str, Any]] = None, k: int = 3) -> List[str]:
        """Semantic search with user filtering and hybrid keyword boosting."""
        if not self.vectors:
            return []

        if len(self.ids) != len(self.vectors):
            self.ids = [f"auto_id_{i}" for i in range(len(self.vectors))]
            self.id_to_idx = {rid: i for i, rid in enumerate(self.ids)}
            self.lsh.clear()
            for record_id, vec in zip(self.ids, self.vectors):
                self.lsh.index(record_id, np.array(vec))

        query_vector = get_query_embedding(query)
        q_vec = np.array([query_vector])

        # Hashing and Candidate Pruning (LSH ANN search)
        use_lsh = len(self.ids) > 10
        candidates = set()
        if use_lsh:
            candidates = self.lsh.query(np.array(query_vector))

        id_to_idx = self.id_to_idx
        if use_lsh and candidates:
            indices_to_scan = [id_to_idx[cid] for cid in candidates if cid in id_to_idx]
        else:
            indices_to_scan = list(range(len(self.ids)))

        if not indices_to_scan:
            return []

        candidate_vectors = [self.vectors[idx] for idx in indices_to_scan]
        vec_matrix = np.array(candidate_vectors)

        # Cosine similarity on subset
        sim_scores = cosine_similarity(q_vec, vec_matrix)[0]

        # Apply hybrid keyword boost
        hybrid_scores = []
        for idx, score in enumerate(sim_scores):
            orig_idx = indices_to_scan[idx]
            h_score = self._hybrid_score(query, self.documents[orig_idx], score)
            hybrid_scores.append(h_score)
        hybrid_scores = np.array(hybrid_scores)

        sorted_indices = hybrid_scores.argsort()[::-1]

        results = []
        count = 0

        for idx in sorted_indices:
            original_idx = indices_to_scan[idx]
            if hybrid_scores[idx] <= 0.0:
                break

            # Apply metadata filter
            match = True
            if filter_meta and not _metadata_matches_filter(self.metadatas[original_idx], filter_meta):
                match = False

            if match:
                results.append(self.documents[original_idx])
                count += 1
                if count >= k:
                    break

        return results

    def search_with_scores(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Semantic search returning documents with hybrid similarity scores and metadata."""
        if not self.vectors:
            return []

        if len(self.ids) != len(self.vectors):
            self.ids = [f"auto_id_{i}" for i in range(len(self.vectors))]
            self.id_to_idx = {rid: i for i, rid in enumerate(self.ids)}
            self.lsh.clear()
            for record_id, vec in zip(self.ids, self.vectors):
                self.lsh.index(record_id, np.array(vec))

        query_vector = get_query_embedding(query)
        q_vec = np.array([query_vector])

        # Hashing and Candidate Pruning (LSH ANN search)
        use_lsh = len(self.ids) > 10
        candidates = set()
        if use_lsh:
            candidates = self.lsh.query(np.array(query_vector))

        id_to_idx = self.id_to_idx
        if use_lsh and candidates:
            indices_to_scan = [id_to_idx[cid] for cid in candidates if cid in id_to_idx]
        else:
            indices_to_scan = list(range(len(self.ids)))

        if not indices_to_scan:
            return []

        candidate_vectors = [self.vectors[idx] for idx in indices_to_scan]
        vec_matrix = np.array(candidate_vectors)

        sim_scores = cosine_similarity(q_vec, vec_matrix)[0]

        # Apply hybrid keyword boost
        hybrid_scores = []
        for idx, score in enumerate(sim_scores):
            orig_idx = indices_to_scan[idx]
            h_score = self._hybrid_score(query, self.documents[orig_idx], score)
            hybrid_scores.append(h_score)
        hybrid_scores = np.array(hybrid_scores)

        sorted_indices = hybrid_scores.argsort()[::-1]

        results = []
        count = 0

        for idx in sorted_indices:
            original_idx = indices_to_scan[idx]
            if hybrid_scores[idx] <= 0.0:
                break
            if filter_meta and not _metadata_matches_filter(self.metadatas[original_idx], filter_meta):
                continue
            results.append({
                "text": self.documents[original_idx],
                "metadata": self.metadatas[original_idx],
                "id": self.ids[original_idx],
                "score": float(hybrid_scores[idx]),
            })
            count += 1
            if count >= k:
                break

        return results


    def count(self) -> int:
        """Return the total number of documents in the store."""
        return len(self.ids)


# --- Singleton ---
_store = None


def get_vector_store() -> VectorStoreBackend:
    """
    Return the active vector store backend (singleton, chosen once per process).

    Preference order:
      1. QdrantVectorStore   — Rust-powered Qdrant vector database (if configured)
      2. TurboVecVectorStore — turbovec Rust/SIMD ANN backend (if installed)
      3. SimpleVectorStore   — JSON + scikit-learn cosine fallback
    """
    global _store
    if _store is None:
        # Check local-first compliance mode (EU AI Act 2026 requirement)
        local_safety = os.environ.get("LOCAL_FIRST_SAFETY", "").strip().lower() in {"1", "true", "yes", "on"}
        if local_safety:
            logger.info("LOCAL_FIRST_SAFETY mode enabled. Forcing SimpleVectorStore local backend.")
            _store = SimpleVectorStore()
            return _store

        # 1. Try Qdrant if host is set or library is present
        qdrant_enabled = os.environ.get("QDRANT_HOST") is not None
        if qdrant_enabled:
            try:
                from .qdrant_store import QdrantVectorStore  # noqa: PLC0415
                _store = QdrantVectorStore()
                _store.load()
                logger.info("Vector store backend: QdrantVectorStore (Qdrant)")
                return _store
            except Exception as e:
                logger.warning("Failed to initialize Qdrant (falling back): %s", e)

        # 2. Try TurboVec
        try:
            from .turbovec_store import TurboVecVectorStore  # noqa: PLC0415
            _store = TurboVecVectorStore()
            _store.load()
            logger.info("Vector store backend: TurboVecVectorStore (turbovec)")
        except ImportError:
            logger.warning(
                "turbovec is not installed — falling back to SimpleVectorStore. "
                "Install turbovec>=0.5.0 for SIMD-accelerated ANN search."
            )
            _store = SimpleVectorStore()
    return _store


# --- Public API ---

def add_checkup_to_db(
    user_id: str,
    record_id: str,
    record_type: str,
    data: dict,
    prediction: str,
    timestamp: str,
    facility_id: Optional[str] = None,
) -> bool:
    """Index a health checkup record."""
    try:
        data_str = ", ".join([f"{k}: {v}" for k, v in data.items()])
        document_text = (
            f"User: {user_id}\n"
            f"Date: {timestamp}\n"
            f"Checkup Type: {record_type}\n"
            f"Result: {prediction}\n"
            f"Clinical Data: {data_str}"
        )

        metadata = {
            "user_id": str(user_id),
            "record_id": str(record_id),
            "type": record_type,
            "timestamp": timestamp,
            "prediction": prediction
        }
        if facility_id is not None and _normalize_acl_value(facility_id):
            metadata["facility_id"] = _normalize_acl_value(facility_id)

        get_vector_store().add(document_text, metadata, str(record_id))
        return True
    except Exception:
        logger.error("Error saving checkup to RAG")
        return False

def add_interaction_to_db(
    user_id: str,
    interaction_id: str,
    role: str,
    content: str,
    timestamp: str,
    facility_id: Optional[str] = None,
) -> bool:
    """Index a chat interaction."""
    try:
        document_text = (
            f"Date: {timestamp}. "
            f"Interaction: {role.upper()}: {content}"
        )

        metadata = {
            "user_id": str(user_id),
            "interaction_id": str(interaction_id),
            "type": "chat_log",
            "timestamp": timestamp,
            "role": role
        }
        if facility_id is not None and _normalize_acl_value(facility_id):
            metadata["facility_id"] = _normalize_acl_value(facility_id)

        get_vector_store().add(document_text, metadata, f"chat_{interaction_id}")
        return True
    except Exception:
        logger.error("Error saving interaction to RAG")
        return False

def search_similar_records(
    user_id: str,
    query: str,
    n_results: int = 3,
    facility_id: Optional[str] = None,
) -> List[str]:
    """Retrieve relevant context for a user."""
    try:
        return get_vector_store().search(
            query,
            filter_meta=_build_acl_filter(user_id, facility_id),
            k=n_results,
        )
    except Exception:
        logger.error("Error querying RAG")
        return []

def delete_record_from_db(record_id: str) -> bool:
    """Delete from vector index."""
    return get_vector_store().delete(str(record_id))
