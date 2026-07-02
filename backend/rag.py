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

        if name in globals():
            return globals()[name]

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

    class SimpleVectorStore:
        def __init__(self):
            self.documents = []
            self.vectors = []
            self.metadatas = []
            self.ids = []
            self.db_file = None

        def save(self):
            pass

        def add(self, text, metadata, record_id):
            self.documents.append(text)
            self.metadatas.append(metadata)
            self.ids.append(record_id)

        def delete(self, record_id):
            if record_id in self.ids:
                idx = self.ids.index(record_id)
                self.ids.pop(idx)
                self.documents.pop(idx)
                self.metadatas.pop(idx)
                return True
            return False

        def search(self, query, filter_meta=None, k=3):
            results = []
            for doc, meta in zip(self.documents, self.metadatas):
                if filter_meta:
                    match = True
                    for kk, vv in filter_meta.items():
                        if meta.get(kk) != vv:
                            match = False
                            break
                    if not match:
                        continue
                results.append(doc)
            return results[:k]

    class FallbackCoreAI:
        def embed_text(self, text, *args, **kwargs):
            return [1.0] * 768

    core_ai = FallbackCoreAI()
    _store = None

    def add_checkup_to_db(user_id: Any, record_id: str, record_type: str, data: Any, prediction: str, timestamp: str, facility_id: Optional[str] = None) -> None:
        global _store
        if _store is not None:
            text = f"User: {user_id}\nCheckup: {record_type}\nData: {data}\nPrediction: {prediction}"
            meta = {
                "user_id": str(user_id),
                "record_id": str(record_id),
                "type": record_type,
                "timestamp": timestamp,
                "facility_id": facility_id
            }
            _store.add(text, meta, record_id)

    def add_interaction_to_db(user_id: Any, interaction_id: str, role: str, content: str, timestamp: str, facility_id: Optional[str] = None) -> None:
        global _store
        if _store is not None:
            text = f"User: {user_id}\nInteraction: {role}: {content}"
            meta = {
                "user_id": str(user_id),
                "interaction_id": str(interaction_id),
                "role": role,
                "timestamp": timestamp,
                "facility_id": facility_id
            }
            _store.add(text, meta, interaction_id)

    def search_similar_records(user_id: Any, query: str, n_results: int = 3, facility_id: Optional[str] = None) -> List[Any]:
        global _store
        if _store is not None:
            raw_results = []
            for doc, meta in zip(_store.documents, _store.metadatas):
                if meta.get("user_id") != str(user_id):
                    continue
                if facility_id and meta.get("facility_id") != facility_id:
                    continue
                raw_results.append(RetrievedChunk(
                    record_type=meta.get("type", "chat_log"),
                    record_id=meta.get("record_id", meta.get("interaction_id")),
                    text=doc
                ))
            return raw_results[:n_results]
        return []

    def delete_record_from_db(record_id: str) -> bool:
        global _store
        if _store is not None:
            return _store.delete(record_id)
        return True

    def _metadata_matches_filter(meta: Dict[str, Any], filter_meta: Dict[str, Any]) -> bool:
        for k, v in filter_meta.items():
            if meta.get(k) != v:
                return False
        return True
