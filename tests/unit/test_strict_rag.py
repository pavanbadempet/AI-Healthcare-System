import pytest
from unittest.mock import MagicMock, patch, mock_open
import numpy as np
import pickle
import backend.rag
from backend.rag import SimpleVectorStore, add_checkup_to_db, add_interaction_to_db, search_similar_records

# FIXTURE: Mock Embedding Model GLOBAL to prevent download
@pytest.fixture(autouse=True)
def mock_embedding_model():
    with patch("backend.rag.HuggingFaceEmbeddings") as mock_cls:
        mock_instance = MagicMock()
        # embed_query returns a vector of valid shape (e.g. 384 dim)
        mock_instance.embed_query.return_value = [0.1] * 5 
        mock_cls.return_value = mock_instance
        
        # Reset global
        backend.rag._embedding_model = None
        yield mock_instance

# --- SimpleVectorStore Tests ---

def test_store_load_failure():
    # Patch exists=True, but open/pickle fails
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", side_effect=Exception("Corrupt File")):
        
        store = SimpleVectorStore()
        # Should initialize empty
        assert len(store.documents) == 0

def test_store_save_failure():
    store = SimpleVectorStore()
    store.documents = ["doc1"]
    
    with patch("builtins.open", side_effect=Exception("Disk Full")):
        store.save()
        # Should just log error and not crash

def test_store_search_empty():
    # Ensure it doesn't load from disk
    with patch("os.path.exists", return_value=False):
        store = SimpleVectorStore()
        # No vectors
        results = store.search("query")
        assert results == []

def test_store_search_logic():
    # Setup store with vectors
    store = SimpleVectorStore()
    store.vectors = [[1.0, 0.0], [0.0, 1.0]]
    store.documents = ["Doc A", "Doc B"]
    store.metadatas = [{"id": 1}, {"id": 2}]
    
    # Mock cosine_similarity
    # query vs [[1,0], [0,1]]
    # if query is [1,0], sim is [1.0, 0.0] -> index 0 first
    with patch("backend.rag.cosine_similarity", return_value=np.array([[0.9, 0.1]])):
        results = store.search("query")
        assert results == ["Doc A", "Doc B"]

def test_store_search_filter():
    store = SimpleVectorStore()
    store.vectors = [[1,0], [1,0]]
    store.documents = ["User1 Doc", "User2 Doc"]
    store.metadatas = [{"user_id": "1"}, {"user_id": "2"}]
    
    with patch("backend.rag.cosine_similarity", return_value=np.array([[0.9, 0.9]])):
        results = store.search("q", filter_meta={"user_id": "1"})
        assert results == ["User1 Doc"]

# --- High Level Function Tests (Exception Handling) ---

def test_add_checkup_exception():
    mock_store = MagicMock()
    mock_store.add.side_effect = Exception("Store Error")
    with patch("backend.rag.get_vector_store", return_value=mock_store):
        res = add_checkup_to_db("1", "1", "type", {}, "pred", "date")
        assert res is False

def test_add_interaction_exception():
    mock_store = MagicMock()
    mock_store.add.side_effect = Exception("Store Error")
    with patch("backend.rag.get_vector_store", return_value=mock_store):
        res = add_interaction_to_db("1", "int1", "user", "msg", "date")
        assert res is False

def test_search_similar_records_exception():
    mock_store = MagicMock()
    mock_store.search.side_effect = Exception("Search Fail")
    with patch("backend.rag.get_vector_store", return_value=mock_store):
        res = search_similar_records("1", "q")
        assert res == []

