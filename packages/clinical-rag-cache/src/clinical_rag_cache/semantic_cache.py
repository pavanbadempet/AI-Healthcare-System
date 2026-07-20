import json
import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

class SemanticCache:
    """
    Semantic Cache for LLM responses using cosine similarity over embeddings.
    Persists cached entries to backend/models/semantic_cache.json.
    """
    def __init__(self, filename: Optional[str] = None, threshold: float = 0.95):
        if filename is None:
            filename = os.path.join(os.path.dirname(__file__), "models", "semantic_cache.json")
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
        if not self.cache or not query_embedding:
            self.misses += 1
            return None

        q_vec = np.array(query_embedding)
        norm_q = np.linalg.norm(q_vec)
        if norm_q == 0:
            self.misses += 1
            return None

        best_score = -1.0
        best_response = None

        for entry in self.cache:
            c_vec = np.array(entry["embedding"])
            norm_c = np.linalg.norm(c_vec)
            if norm_c == 0:
                continue

            score = np.dot(q_vec, c_vec) / (norm_q * norm_c)
            if score > best_score:
                best_score = score
                best_response = entry["response"]

        if best_score >= self.threshold:
            logger.info("Semantic cache HIT (score: %.4f) for query: '%s'", best_score, query_text[:50])
            self.hits += 1
            return best_response

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

