import threading
from unittest.mock import MagicMock

from backend.cache_service import SystemCache


def _redis_backed_cache():
    cache = object.__new__(SystemCache)
    cache.redis_client = MagicMock()
    cache._store_lock = threading.Lock()
    cache._in_memory_store = {}
    return cache


def test_redis_set_uses_supported_ttl_api():
    cache = _redis_backed_cache()

    cache.set("patient-summary", {"status": "ready"}, ttl=30)

    cache.redis_client.set.assert_called_once()
    args, kwargs = cache.redis_client.set.call_args
    assert args[0] == "patient-summary"
    assert kwargs == {"ex": 30}
    cache.redis_client.setex.assert_not_called()


def test_redis_safe_set_uses_supported_ttl_api():
    cache = _redis_backed_cache()

    cache.safe_set("clinical-cache", {"status": "ready"}, ttl=45)

    cache.redis_client.set.assert_called_once()
    args, kwargs = cache.redis_client.set.call_args
    assert args[0] == "clinical-cache"
    assert kwargs == {"ex": 45}
    cache.redis_client.setex.assert_not_called()
