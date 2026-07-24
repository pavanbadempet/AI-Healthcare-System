import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock qdrant_client before importing qdrant_store to prevent ImportError in test runner
mock_qdrant = MagicMock()
mock_qdrant_client_class = MagicMock()
mock_qdrant.QdrantClient = mock_qdrant_client_class
sys.modules["qdrant_client"] = mock_qdrant
sys.modules["qdrant_client.models"] = MagicMock()

from backend.qdrant_store import QdrantVectorStore


@pytest.fixture
def mock_embedding():
    with patch("backend.qdrant_store.get_embedding", return_value=[0.1, 0.2, 0.3]) as mock_emb:
        yield mock_emb


def test_qdrant_store_local_load(mock_embedding):
    """Test Qdrant local initialization when QDRANT_HOST is default."""
    env_patch = {"QDRANT_MODE": "local"}
    with patch.dict(os.environ, env_patch):
        store = QdrantVectorStore()

        # Mock get_collections and get_collections().collections
        mock_collections_res = MagicMock()
        mock_collections_res.collections = []
        store.client = MagicMock()
        store.client.get_collections.return_value = mock_collections_res

        # Force load with mocked QdrantClient
        with patch("backend.qdrant_store.QdrantClient", return_value=store.client):
            store.load()

            assert store.dimension == 3
            store.client.get_collections.assert_called_once()
            store.client.create_collection.assert_called_once()


def test_qdrant_store_server_load(mock_embedding):
    """Test Qdrant server mode initialization when custom host is set."""
    env_patch = {"QDRANT_HOST": "qdrant-server"}
    with patch.dict(os.environ, env_patch):
        store = QdrantVectorStore()

        mock_collections_res = MagicMock()
        mock_collections_res.collections = []
        store.client = MagicMock()
        store.client.get_collections.return_value = mock_collections_res

        with patch("backend.qdrant_store.QdrantClient", return_value=store.client) as mock_client_init:
            store.load()

            mock_client_init.assert_called_with(host="qdrant-server", port=6333, api_key=None, timeout=5.0)


def test_qdrant_store_ops(mock_embedding):
    """Test Qdrant collection CRUD operations."""
    store = QdrantVectorStore()
    store.client = MagicMock()

    # Mock add
    store.add("clinical note", {"patient_id": "42"}, "rec-1")
    store.client.upsert.assert_called_once()

    # Mock delete
    store.client.delete.return_value = MagicMock()
    res = store.delete("rec-1")
    assert res is True
    store.client.delete.assert_called_once()

    # Mock search
    mock_search_res = [
        MagicMock(id="rec-1", payload={"text": "clinical note", "patient_id": "42"}, score=0.85)
    ]
    store.client.search.return_value = mock_search_res
    results = store.search("note", filter_meta={"patient_id": "42"}, k=1)

    assert len(results) == 1
    assert results[0] == "clinical note"

    # Mock search with scores
    results_with_scores = store.search_with_scores("note", filter_meta={"patient_id": "42"}, k=1)
    assert len(results_with_scores) == 1
    assert results_with_scores[0]["text"] == "clinical note"
    assert results_with_scores[0]["score"] == 0.85
