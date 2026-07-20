"""
VectorStore Abstraction — Interface for pluggable vector backends
=================================================================

Defines the abstract interface that all vector store backends must implement.
The current SimpleVectorStore (JSON-backed) implements this interface.
Future backends (Qdrant, Pinecone, pgvector) can be swapped in without
changing any caller code.

Usage:
    from backend.vector_store_base import VectorStoreBackend
    from backend.rag import SimpleVectorStore  # implements VectorStoreBackend
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class VectorStoreBackend(ABC):
    """
    Abstract base class for vector store backends.

    All methods that the RAG pipeline depends on are defined here.
    Concrete implementations must override every abstract method.
    """

    @abstractmethod
    def add(self, text: str, metadata: Dict[str, Any], record_id: str) -> None:
        """Add or update a document in the store."""
        ...

    @abstractmethod
    def delete(self, record_id: str) -> bool:
        """Delete a document by ID. Returns True if found and deleted."""
        ...

    @abstractmethod
    def search(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[str]:
        """Semantic search returning matching document texts."""
        ...

    @abstractmethod
    def search_with_scores(
        self,
        query: str,
        filter_meta: Optional[Dict[str, Any]] = None,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Semantic search returning documents with similarity scores and metadata."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return the total number of documents in the store."""
        ...

    @abstractmethod
    def load(self) -> None:
        """Load or initialize the store from persistent storage."""
        ...

    @abstractmethod
    def save(self) -> None:
        """Persist the store to durable storage."""
        ...
