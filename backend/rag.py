import logging
import sys
from types import ModuleType
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import clinical_rag_cache.rag as _pkg_rag
except ImportError:
    _pkg_rag = None


class _RagModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
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
