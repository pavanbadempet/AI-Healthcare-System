"""
QdrantVectorStore — Pluggable Vector Store Backend
===================================================
Implements ``VectorStoreBackend`` using Qdrant client.
Qdrant is a high-performance vector search engine written in Rust.
"""

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointStruct,
        ScalarQuantization,
        ScalarType,
        VectorParams,
    )
except ImportError:
    QdrantClient = None

from .rag import get_embedding, get_query_embedding
from .vector_store_base import VectorStoreBackend

logger = logging.getLogger(__name__)

# Environment variable configurations
QDRANT_HOST = os.environ.get("QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", None)
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "healthcare_rag")

class QdrantVectorStore(VectorStoreBackend):
    """Qdrant-backed vector store implementing VectorStoreBackend."""

    def __init__(self) -> None:
        if QdrantClient is None:
            raise ImportError("qdrant-client is not installed. Run 'pip install qdrant-client'")

        self.client: Optional[QdrantClient] = None
        self.collection_name = QDRANT_COLLECTION
        self.dimension = None

    def load(self) -> None:
        """Connect to Qdrant and initialize the collection."""
        try:
            # Connect via HTTP
            self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, api_key=QDRANT_API_KEY, timeout=5.0)

            # Determine embedding dimension dynamically
            test_emb = get_embedding("test")
            self.dimension = len(test_emb)

            # Create collection if it doesn't exist
            collections = [col.name for col in self.client.get_collections().collections]
            if self.collection_name not in collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
                    quantization_config=ScalarQuantization(
                        scalar=ScalarType.INT8,
                        always_ram=True,
                        quantile=0.99
                    )
                )
                logger.info("Created Qdrant collection: %s", self.collection_name)
            else:
                logger.info("Connected to existing Qdrant collection: %s", self.collection_name)
        except Exception as e:
            logger.error("Failed to connect to Qdrant: %s", e)
            raise RuntimeError(f"Qdrant connection failed: {e}") from e

    def _get_uuid(self, record_id: str) -> str:
        """Generate a deterministic UUID from a string record_id for Qdrant compatibility."""
        # Qdrant accepts 64-bit unsigned integers or UUID strings
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, record_id))

    def add(self, text: str, metadata: Dict[str, Any], record_id: str) -> None:
        """Add or update a document embedding in Qdrant."""
        if not self.client:
            raise RuntimeError("Qdrant store is not loaded.")

        vector = get_embedding(text)
        point_id = self._get_uuid(record_id)

        payload = {
            "text": text,
            "record_id": record_id,
            **metadata
        }

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        logger.debug("Successfully upserted point %s to Qdrant", record_id)

    def delete(self, record_id: str) -> bool:
        """Delete a document by ID. Returns True if successful."""
        if not self.client:
            raise RuntimeError("Qdrant store is not loaded.")

        point_id = self._get_uuid(record_id)
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            return True
        except Exception as e:
            logger.error("Failed to delete point %s from Qdrant: %s", record_id, e)
            return False

    def _build_filter(self, filter_meta: Optional[Dict[str, Any]]) -> Optional[Any]:
        if not filter_meta:
            return None

        must_conditions = []
        for key, val in filter_meta.items():
            must_conditions.append(
                FieldCondition(
                    key=key,
                    match=MatchValue(value=val)
                )
            )
        return Filter(must=must_conditions) if must_conditions else None

    def search(self, query: str, filter_meta: Optional[Dict[str, Any]] = None, k: int = 3) -> List[str]:
        """Semantic search returning matching document texts."""
        results = self.search_with_scores(query, filter_meta, k)
        return [res["text"] for res in results]

    def search_with_scores(self, query: str, filter_meta: Optional[Dict[str, Any]] = None, k: int = 3) -> List[Dict[str, Any]]:
        """Semantic search returning documents with similarity scores and metadata."""
        if not self.client:
            raise RuntimeError("Qdrant store is not loaded.")

        query_vector = get_query_embedding(query)
        qdrant_filter = self._build_filter(filter_meta)

        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=k,
            with_payload=True
        )

        output = []
        for res in search_results:
            payload = res.payload or {}
            text = payload.get("text", "")
            record_id = payload.get("record_id", "")

            # Reconstruct metadata (all fields except text and record_id)
            metadata = {k: v for k, v in payload.items() if k not in ("text", "record_id")}

            output.append({
                "text": text,
                "score": float(res.score),
                "record_id": record_id,
                "metadata": metadata
            })
        return output

    def count(self) -> int:
        """Return the total number of documents in the collection."""
        if not self.client:
            return 0
        try:
            return self.client.get_collection(self.collection_name).points_count
        except Exception:
            return 0

    def save(self) -> None:
        """No-op as Qdrant is persistent server-side."""
        pass
