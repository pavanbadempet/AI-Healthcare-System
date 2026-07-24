"""
Unit tests for SOTA Enterprise Infrastructure Adapters.
"""

from backend.database import apply_postgres_rls_policy, set_session_tenant_context
from backend.qdrant_vector_store import QdrantVectorStore
from backend.smart_fhir import verify_smart_launch_jwt


def test_qdrant_vector_store_fallback():
    store = QdrantVectorStore(collection_name="test_clinical_docs")
    assert store.collection_name == "test_clinical_docs"
    assert store.qdrant_url != ""


def test_postgres_rls_helpers():
    class DummySession:
        pass

    session = DummySession()
    # In SQLite local dev testing, returns False safely without error
    res = apply_postgres_rls_policy(session, "clinical_events")
    assert res is False

    set_session_tenant_context(session, "facility_alpha")


def test_smart_fhir_jwt_verification():
    invalid_res = verify_smart_launch_jwt("invalid_token")
    assert invalid_res["valid"] is False

    valid_res = verify_smart_launch_jwt("smt_launch_token_99182")
    assert valid_res["valid"] is True
    assert "launch/patient" in valid_res["scopes"]
