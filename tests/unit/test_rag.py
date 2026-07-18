
import pytest

from backend import rag

# Since RAG uses a file-based pickle, we want to mock it or use a separate test file.
# But rag.py defines DB_FILE global.
# We should probably patch DB_FILE for tests to avoid nuking prod DB.

@pytest.fixture
def mock_vector_db(monkeypatch, tmp_path):
    # Mock core AI embeddings so tests never call an external provider.
    monkeypatch.setattr(rag.core_ai, "embed_text", lambda text, task_type: [1.0] * 768)

    # Create temp DB file
    d = tmp_path / "test_vector_store.pkl"
    monkeypatch.setattr(rag, "DB_FILE", str(d))

    # Reset store
    # Since _store singleton might be initialized, we should force it to None or re-create
    rag._store = rag.SimpleVectorStore()
    rag._store.documents = []
    rag._store.vectors = []
    rag._store.metadatas = []
    rag._store.ids = []
    rag._store.save() # Create file

    return rag._store

def test_rag_tenant_isolation(mock_vector_db):
    user_a = "user_100"
    user_b = "user_200"

    # 1. Add Record for A
    rag.add_checkup_to_db(user_a, "rec_1", "TestType", {"val": 1}, "High Risk", "2024-01-01")

    # 2. Search as A
    results_a = rag.search_similar_records(user_a, "Risk")
    assert len(results_a) == 1

    # 3. Search as B (Should be empty)
    results_b = rag.search_similar_records(user_b, "Risk")
    assert len(results_b) == 0

def test_rag_deletion(mock_vector_db):
    user_id = "user_del"
    rec_id = "rec_del_1"

    rag.add_checkup_to_db(user_id, rec_id, "Diabetes", {}, "Pred", "2024-01-01")

    # Confirm Added
    assert len(rag.search_similar_records(user_id, "Diabetes")) == 1

    # Delete
    rag.delete_record_from_db(rec_id)

    # Confirm Gone
    assert len(rag.search_similar_records(user_id, "Diabetes")) == 0


def test_rag_facility_scoped_search_blocks_same_user_cross_facility(mock_vector_db):
    user_id = "user_facility"

    rag.add_checkup_to_db(
        user_id,
        "rec_north",
        "Diabetes",
        {"site": "north"},
        "North facility result",
        "2024-01-01",
        facility_id="facility_north",
    )
    rag.add_checkup_to_db(
        user_id,
        "rec_south",
        "Diabetes",
        {"site": "south"},
        "South facility result",
        "2024-01-01",
        facility_id="facility_south",
    )

    results = rag.search_similar_records(
        user_id,
        "show me the South facility result",
        n_results=5,
        facility_id="facility_north",
    )

    assert any("North facility result" in result for result in results)
    assert all("South facility result" not in result for result in results)


def test_rag_facility_scoped_search_excludes_unscoped_legacy_documents(mock_vector_db):
    user_id = "user_legacy"

    rag.add_checkup_to_db(
        user_id,
        "rec_legacy",
        "Diabetes",
        {"site": "legacy"},
        "Legacy unscoped result",
        "2024-01-01",
    )

    assert rag.search_similar_records(user_id, "Legacy", facility_id="facility_north") == []
    assert len(rag.search_similar_records(user_id, "Legacy")) == 1


# --- Merged from test_strict_rag.py ---

def test_store_load_failure():
    from unittest.mock import patch
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", side_effect=Exception("Corrupt File")):
        store = rag.SimpleVectorStore()
        assert len(store.documents) == 0


def test_store_save_failure():
    from unittest.mock import patch
    store = rag.SimpleVectorStore()
    store.documents = ["doc1"]
    with patch("builtins.open", side_effect=Exception("Disk Full")):
        store.save()


def test_store_search_empty():
    from unittest.mock import patch
    with patch("os.path.exists", return_value=False):
        store = rag.SimpleVectorStore()
        results = store.search("query")
        assert results == []


def test_store_search_logic():
    from unittest.mock import patch
    import numpy as np
    store = rag.SimpleVectorStore()
    store.vectors = [[1.0, 0.0], [0.0, 1.0]]
    store.documents = ["Doc A", "Doc B"]
    store.metadatas = [{"id": 1}, {"id": 2}]
    with patch("backend.rag.cosine_similarity", return_value=np.array([[0.9, 0.1]])):
        results = store.search("query")
        assert results == ["Doc A", "Doc B"]


def test_store_search_filter():
    from unittest.mock import patch
    import numpy as np
    store = rag.SimpleVectorStore()
    store.vectors = [[1,0], [1,0]]
    store.documents = ["User1 Doc", "User2 Doc"]
    store.metadatas = [{"user_id": "1"}, {"user_id": "2"}]
    with patch("backend.rag.cosine_similarity", return_value=np.array([[0.9, 0.9]])):
        results = store.search("q", filter_meta={"user_id": "1"})
        assert results == ["User1 Doc"]


def test_add_checkup_exception(caplog):
    from unittest.mock import MagicMock, patch
    mock_store = MagicMock()
    sensitive_error = "Store error token=rag-secret patient_name=Sensitive User"
    mock_store.add.side_effect = Exception(sensitive_error)
    caplog.set_level("ERROR", logger="backend.rag")
    with patch("backend.rag.get_vector_store", return_value=mock_store):
        res = rag.add_checkup_to_db("1", "1", "type", {}, "pred", "date")
        assert res is False
    assert sensitive_error not in caplog.text
    assert "rag-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_add_interaction_exception(caplog):
    from unittest.mock import MagicMock, patch
    mock_store = MagicMock()
    sensitive_error = "Store error token=rag-secret patient_name=Sensitive User"
    mock_store.add.side_effect = Exception(sensitive_error)
    caplog.set_level("ERROR", logger="backend.rag")
    with patch("backend.rag.get_vector_store", return_value=mock_store):
        res = rag.add_interaction_to_db("1", "int1", "user", "msg", "date")
        assert res is False
    assert sensitive_error not in caplog.text
    assert "rag-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_search_similar_records_exception(caplog):
    from unittest.mock import MagicMock, patch
    mock_store = MagicMock()
    sensitive_error = "Search fail token=rag-secret patient_name=Sensitive User"
    mock_store.search.side_effect = Exception(sensitive_error)
    caplog.set_level("ERROR", logger="backend.rag")
    with patch("backend.rag.get_vector_store", return_value=mock_store):
        res = rag.search_similar_records("1", "q")
        assert res == []
    assert sensitive_error not in caplog.text
    assert "rag-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text

