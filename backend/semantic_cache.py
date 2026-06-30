import logging
import sys
from types import ModuleType
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import clinical_rag_cache.semantic_cache as _pkg_cache
except ImportError:
    _pkg_cache = None


class _CacheModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if _pkg_cache is not None and hasattr(_pkg_cache, name):
            return getattr(_pkg_cache, name)
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if _pkg_cache is not None and hasattr(_pkg_cache, name):
            setattr(_pkg_cache, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CacheModule

# Populate globals with package attributes to make mock/patch happy
if _pkg_cache is not None:
    for _name in dir(_pkg_cache):
        if not _name.startswith("__"):
            globals()[_name] = getattr(_pkg_cache, _name)

if _pkg_cache is None:
    logger.warning("clinical-rag-cache package not installed. Running in mock/fallback mode.")

    class SemanticCache:
        def __init__(self, filename: Optional[str] = None, threshold: float = 0.95):
            self.filename = filename
            self.threshold = threshold

        def load(self) -> None:
            pass

        def save(self) -> None:
            pass

        def lookup(self, query_text: str, query_embedding: List[float]) -> Optional[str]:
            return None

        def add(self, query_text: str, query_embedding: List[float], response: str) -> None:
            pass

        def clear(self) -> None:
            pass

        def get_stats(self) -> Dict[str, Any]:
            return {"hits": 0, "misses": 0, "size": 0}
