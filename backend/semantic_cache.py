import logging
import sys
from types import ModuleType
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import clinical_rag_cache.semantic_cache as _pkg_cache
except ImportError:
    _pkg_cache = None


class _CacheModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if _pkg_cache is not None and hasattr(_pkg_cache, name):
            return getattr(_pkg_cache, name)
        if name in globals():
            return globals()[name]
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if _pkg_cache is not None and hasattr(_pkg_cache, name):
            setattr(_pkg_cache, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CacheModule

# Populate globals with package attributes to make mock/patch happy
if _pkg_cache is not None:
    for _name in dir(_pkg_cache):
        if not _name.startswith("__"):
            globals()[_name] = getattr(_pkg_cache, _name)

if _pkg_cache is None:
    logger.warning("clinical-rag-cache package not installed. Running in mock/fallback mode.")

    import json
    import os

    import numpy as np

    class SemanticCache:
        """
        Semantic Cache for LLM responses using cosine similarity over embeddings.
        Persists cached entries to models/semantic_cache.json.
        """
        def __init__(self, filename: Optional[str] = None, threshold: float = 0.95):
            if filename is None:
                filename = os.path.join(os.path.dirname(__file__), "..", "models", "semantic_cache.json")
            self.filename = os.path.abspath(filename)
            self.threshold = threshold
            self.cache: List[Dict[str, Any]] = []
            self.hits = 0
            self.misses = 0
            self.load()

        def load(self) -> None:
            if os.path.exists(self.filename):
                try:
                    with open(self.filename, "r", encoding="utf-8") as f:
                        self.cache = json.load(f)
                    logger.info("Loaded %d entries into semantic cache.", len(self.cache))
                except Exception as e:
                    logger.warning("Failed to load semantic cache: %s. Starting fresh.", e)
                    self.cache = []

        def save(self) -> None:
            try:
                os.makedirs(os.path.dirname(self.filename), exist_ok=True)
                with open(self.filename, "w", encoding="utf-8") as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning("Failed to save semantic cache: %s", e)

        def lookup(self, query_text: str, query_embedding: List[float]) -> Optional[str]:
            if not self.cache:
                self.misses += 1
                return None

            # Direct exact match fast path (< 0.1ms)
            for entry in self.cache:
                if entry.get("query") == query_text:
                    logger.info("Semantic cache EXACT HIT for query: '%s'", query_text[:50])
                    self.hits += 1
                    return entry["response"]

            if not query_embedding:
                self.misses += 1
                return None

            q_vec = np.array(query_embedding, dtype=np.float32)
            norm_q = np.linalg.norm(q_vec)
            if norm_q == 0:
                self.misses += 1
                return None

            # Vectorized Matrix Cosine Similarity for ultra-fast lookup
            try:
                embeddings = np.array([e["embedding"] for e in self.cache], dtype=np.float32)
                norms = np.linalg.norm(embeddings, axis=1)
                valid_mask = norms > 0
                if not np.any(valid_mask):
                    self.misses += 1
                    return None

                dots = np.dot(embeddings, q_vec)
                scores = np.zeros(len(self.cache), dtype=np.float32)
                scores[valid_mask] = dots[valid_mask] / (norms[valid_mask] * norm_q)
                best_idx = int(np.argmax(scores))
                best_score = float(scores[best_idx])

                if best_score >= self.threshold:
                    logger.info("Semantic cache HIT (score: %.4f) for query: '%s'", best_score, query_text[:50])
                    self.hits += 1
                    return self.cache[best_idx]["response"]
            except Exception as e:
                logger.warning("Vectorized lookup fallback: %s", e)

            self.misses += 1
            return None

        def add(self, query_text: str, query_embedding: List[float], response: str) -> None:
            if not query_embedding or not response:
                return

            # Avoid caching error messages, offline warnings or blank responses
            response_lower = response.lower()
            if any(w in response_lower for w in ["mock response", "offline mode", "unavailable", "failed"]):
                return

            # Avoid duplicates in cache
            for entry in self.cache:
                if entry["query"] == query_text:
                    return

            self.cache.append({
                "query": query_text,
                "embedding": query_embedding,
                "response": response
            })
            # LRU Pruning: Evict oldest entries if capacity exceeds 500 items
            if len(self.cache) > 500:
                self.cache = self.cache[-500:]
            self.save()

        def clear(self) -> None:
            self.cache = []
            self.hits = 0
            self.misses = 0
            if os.path.exists(self.filename):
                try:
                    os.remove(self.filename)
                except Exception:
                    pass

        def get_stats(self) -> Dict[str, Any]:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "size": len(self.cache),
                "entries": [{"query": e["query"][:100], "response_length": len(e["response"])} for e in self.cache]
            }
