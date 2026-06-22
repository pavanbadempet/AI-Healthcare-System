from unittest.mock import patch

import numpy as np
import pytest

from backend import rag


@pytest.fixture
def temp_vector_db(monkeypatch, tmp_path):
    # Redirect DB file to a temporary directory
    d = tmp_path / "test_lsh_store.json"
    monkeypatch.setattr(rag, "DB_FILE", str(d))

    # Initialize store
    store = rag.SimpleVectorStore()
    store.documents = []
    store.metadatas = []
    store.vectors = []
    store.ids = []
    store.lsh.clear()
    store.save()
    return store

def test_lsh_direct_projection_and_indexing():
    # Test LSH with a small dimensional space (10-D)
    lsh = rag.LocalitySensitiveHash(num_tables=3, hash_size=4)

    # 10-D vectors
    v1 = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    v2 = np.array([0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) # v2 is close to v1
    v3 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]) # v3 is orthogonal/far

    lsh.index("doc_1", v1)
    lsh.index("doc_2", v2)
    lsh.index("doc_3", v3)

    # Query with v1
    candidates = lsh.query(v1)

    # doc_1 must be a candidate
    assert "doc_1" in candidates

    # Clear index
    lsh.clear()
    assert lsh.dim is None
    assert len(lsh.tables) == 0

def test_simple_vector_store_lsh_search(temp_vector_db):
    # Add 12 documents to exceed the LSH threshold of 10
    # Create 12 distinct vectors. Document i will have a high value at index i.
    embeddings = {}
    for i in range(12):
        vec = [0.0] * 768
        vec[i] = 1.0
        embeddings[f"doc_{i}"] = vec

    def mock_get_embedding(text):
        return embeddings.get(text, [0.0] * 768)

    with (
        patch("backend.rag.get_embedding", side_effect=mock_get_embedding),
        patch("backend.rag.get_query_embedding", side_effect=lambda q: mock_get_embedding(q))
    ):
        # Insert 12 documents
        for i in range(12):
            temp_vector_db.add(
                text=f"doc_{i}",
                metadata={"facility_id": "fac_1", "user_id": "user_1"},
                record_id=f"rec_{i}"
            )

        assert len(temp_vector_db.ids) == 12
        assert temp_vector_db.lsh.dim == 768

        # Run search for doc_3
        # Should return doc_3 as first result
        results = temp_vector_db.search("doc_3", k=3)
        assert len(results) > 0
        assert results[0] == "doc_3"

        # Run search_with_scores for doc_5
        scored_results = temp_vector_db.search_with_scores("doc_5", k=3)
        assert len(scored_results) > 0
        assert scored_results[0]["text"] == "doc_5"
        assert scored_results[0]["id"] == "rec_5"
        assert scored_results[0]["score"] > 0.9

def test_simple_vector_store_lsh_deletion(temp_vector_db):
    embeddings = {}
    for i in range(12):
        vec = [0.0] * 768
        vec[i] = 1.0
        embeddings[f"doc_{i}"] = vec

    def mock_get_embedding(text):
        return embeddings.get(text, [0.0] * 768)

    with (
        patch("backend.rag.get_embedding", side_effect=mock_get_embedding),
        patch("backend.rag.get_query_embedding", side_effect=lambda q: mock_get_embedding(q))
    ):
        # Insert 12 documents
        for i in range(12):
            temp_vector_db.add(
                text=f"doc_{i}",
                metadata={"facility_id": "fac_1"},
                record_id=f"rec_{i}"
            )

        # Confirm retrieval
        assert "doc_4" in temp_vector_db.search("doc_4", k=1)

        # Delete document 4
        deleted = temp_vector_db.delete("rec_4")
        assert deleted is True
        assert len(temp_vector_db.ids) == 11

        # Search for doc_4 again
        # Should not be returned
        results = temp_vector_db.search("doc_4", k=1)
        if results:
            assert results[0] != "doc_4"
