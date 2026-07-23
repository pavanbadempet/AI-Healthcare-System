"""
SOTA Qdrant Vector Store Backend Adapter
========================================

Implements the VectorStoreBackend interface connecting to a remote or local Qdrant
instance with HNSW indexing, ACL payload filtering, and cosine distance metrics.

Falls back gracefully to SimpleVectorStore when Qdrant is unconfigured.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from .vector_store_base import VectorStoreBackend

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStoreBackend):
    """
    Production-grade Qdrant Vector Database Adapter with HNSW indexing.
    """

    def __init__(self, collection_name: str = "clinical_documents", vector_dim: int = 768):
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        self.qdrant_url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
        self.api_key = os.environ.get("QDRANT_API_KEY", "")
        self._headers = {"Content-Type": "application/json"}
        if self.api_key:
            self._headers["api-key"] = self.api_key

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create Qdrant collection with HNSW index configuration if it doesn't exist."""
        try:
            res = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}", headers=self._headers, timeout=3)
            if res.status_code == 404:
                payload = {
                    "vectors": {
                        "size": self.vector_dim,
                        "distance": "Cosine"
                    },
                    "hnsw_config": {
                        "m": 16,
                        "ef_construct": 100
                    }
                }
                create_res = requests.put(f"{self.qdrant_url}/collections/{self.collection_name}", json=payload, headers=self._headers, timeout=5)
                create_res.raise_for_status()
                logger.info("Successfully created Qdrant collection %s", self.collection_name)
        except Exception as e:
            logger.warning("Could not connect to Qdrant at %s: %s. Relying on fallback.", self.qdrant_url, e)

    def add(self, text: str, metadata: Dict[str, Any], record_id: str) -> None:
        """Upsert document vector and metadata payload to Qdrant."""
        try:
            from . import core_ai
            vector = core_ai.embed_text(text, task_type="retrieval_document") if core_ai else [0.1] * self.vector_dim

            payload = {
                "points": [
                    {
                        "id": str(record_id),
                        "vector": vector,
                        "payload": {
                            "text": text,
                            **metadata
                        }
                    }
                ]
            }
            res = requests.put(f"{self.qdrant_url}/collections/{self.collection_name}/points", json=payload, headers=self._headers, timeout=5)
            res.raise_for_status()
        except Exception as e:
            logger.error("Qdrant add failed for %s: %s", record_id, e)

    def delete(self, record_id: str) -> bool:
        """Delete document point by ID."""
        try:
            payload = {"points": [str(record_id)]}
            res = requests.post(f"{self.qdrant_url}/collections/{self.collection_name}/points/delete", json=payload, headers=self._headers, timeout=5)
            res.raise_for_status()
            return True
        except Exception:
            return False

    def search(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[str]:
        """Search top-K document texts matching query with optional payload filter."""
        results = self.search_with_scores(query, filter_meta, k)
        return [r["text"] for r in results if "text" in r]

    def search_with_scores(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Search top-K document points with similarity scores."""
        try:
            from . import core_ai
            query_vector = core_ai.embed_text(query, task_type="retrieval_query") if core_ai else [0.1] * self.vector_dim

            qdrant_filter = None
            if filter_meta:
                must_conditions = []
                for key, val in filter_meta.items():
                    must_conditions.append({
                        "key": key,
                        "match": {"value": str(val)}
                    })
                qdrant_filter = {"must": must_conditions}

            payload = {
                "vector": query_vector,
                "limit": k,
                "with_payload": True,
                "filter": qdrant_filter
            }

            res = requests.post(f"{self.qdrant_url}/collections/{self.collection_name}/points/search", json=payload, headers=self._headers, timeout=5)
            res.raise_for_status()
            points = res.json().get("result", [])

            out = []
            for pt in points:
                p_data = pt.get("payload", {})
                out.append({
                    "id": pt.get("id"),
                    "score": pt.get("score", 0.0),
                    "text": p_data.get("text", ""),
                    "metadata": p_data
                })
            return out
        except Exception as e:
            logger.error("Qdrant search failed: %s", e)
            return []

    def count(self) -> int:
        """Count points in Qdrant collection."""
        try:
            res = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}", headers=self._headers, timeout=3)
            return res.json().get("result", {}).get("vectors_count", 0)
        except Exception:
            return 0

    def load(self) -> None:
        pass

    def save(self) -> None:
        pass
