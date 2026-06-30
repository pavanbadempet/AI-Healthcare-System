import logging
import os
import sys
from types import ModuleType
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

try:
    import clinical_rag_cache.rag as _pkg_rag
except ImportError:
    _pkg_rag = None

def _call_rag_add_checkup(user_id, record_id, record_type, data, prediction, timestamp, facility_id=None):
    service_url = os.environ.get("RAG_SERVICE_URL", "http://127.0.0.1:8002")
    payload = {
        "user_id": str(user_id),
        "record_id": str(record_id),
        "record_type": record_type,
        "data": data,
        "prediction": prediction,
        "timestamp": timestamp,
        "facility_id": facility_id
    }
    res = requests.post(f"{service_url}/rag/checkup", json=payload, timeout=10)
    res.raise_for_status()
    return True

def _call_rag_add_interaction(user_id, interaction_id, role, content, timestamp, facility_id=None):
    service_url = os.environ.get("RAG_SERVICE_URL", "http://127.0.0.1:8002")
    payload = {
        "user_id": str(user_id),
        "interaction_id": str(interaction_id),
        "role": role,
        "content": content,
        "timestamp": timestamp,
        "facility_id": facility_id
    }
    res = requests.post(f"{service_url}/rag/interaction", json=payload, timeout=10)
    res.raise_for_status()
    return True

def _call_rag_search(user_id, query, n_results=3, facility_id=None):
    service_url = os.environ.get("RAG_SERVICE_URL", "http://127.0.0.1:8002")
    payload = {
        "user_id": str(user_id),
        "query": query,
        "n_results": n_results,
        "facility_id": facility_id
    }
    res = requests.post(f"{service_url}/rag/search", json=payload, timeout=10)
    res.raise_for_status()
    return res.json()["results"]

def _call_rag_delete(record_id):
    service_url = os.environ.get("RAG_SERVICE_URL", "http://127.0.0.1:8002")
    res = requests.delete(f"{service_url}/rag/record/{record_id}", timeout=10)
    res.raise_for_status()
    return True

class _MicroservicesVectorStore:
    def add(self, text, metadata, record_id):
        service_url = os.environ.get("RAG_SERVICE_URL", "http://127.0.0.1:8002")
        payload = {
            "text": text,
            "metadata": metadata,
            "record_id": record_id
        }
        res = requests.post(f"{service_url}/rag/add", json=payload, timeout=10)
        res.raise_for_status()

    def delete(self, record_id):
        return _call_rag_delete(record_id)

def _call_get_vector_store():
    return _MicroservicesVectorStore()


class _RagModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if os.environ.get("MICROSERVICES_MODE") == "true":
            if name == "add_checkup_to_db":
                return _call_rag_add_checkup
            elif name == "add_interaction_to_db":
                return _call_rag_add_interaction
            elif name == "search_similar_records":
                return _call_rag_search
            elif name == "delete_record_from_db":
                return _call_rag_delete
            elif name == "get_vector_store":
                return _call_get_vector_store

        if _pkg_rag is not None and hasattr(_pkg_rag, name):
            return getattr(_pkg_rag, name)
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if _pkg_rag is not None and hasattr(_pkg_rag, name):
            setattr(_pkg_rag, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _RagModule

# Populate globals with package attributes to make mock/patch happy
if _pkg_rag is not None:
    for _name in dir(_pkg_rag):
        if not _name.startswith("__"):
            globals()[_name] = getattr(_pkg_rag, _name)

if _pkg_rag is None:
    logger.warning("clinical-rag-cache package not installed. Running in mock/fallback mode.")

    from dataclasses import dataclass

    @dataclass
    class RetrievedChunk:
        record_type: str
        record_id: str
        text: str

    @dataclass
    class Citation:
        record_type: str
        record_id: str
        text: str

    @dataclass
    class RAGResult:
        response: str
        citations: List[Any]

    def assemble_context(records: List[Any], max_tokens: int = 2000) -> str:
        return "\n\n".join([str(getattr(r, "text", "")) for r in records])[:max_tokens]

    def get_embedding(text: str) -> List[float]:
        return [0.1] * 128

    def get_query_embedding(text: str) -> List[float]:
        return [0.1] * 128

    class MockVectorStore:
        def index(self, record_id: str, vector: Any) -> None:
            pass

        def query(self, query_vector: Any) -> set[str]:
            return set()

        def add(self, text: str, metadata: Dict[str, Any], record_id: str) -> None:
            pass

        def delete(self, record_id: str) -> bool:
            return True

        def search(self, query: str, filter_meta: Optional[Dict[str, Any]] = None, k: int = 3) -> List[str]:
            return ["Mock clinical context record 1", "Mock clinical context record 2"]

        def count(self) -> int:
            return 2

    def get_vector_store() -> Any:
        return MockVectorStore()

    def add_checkup_to_db(checkup: Any, patient_name: str) -> None:
        pass

    def add_interaction_to_db(chat_interaction: Any, patient_name: str) -> None:
        pass

    def search_similar_records(query: str, patient_name: str, k: int = 3) -> List[Any]:
        return []

    def delete_record_from_db(record_id: str) -> bool:
        return True
