
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
