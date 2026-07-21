import pytest
from backend.database_pool_manager import EnterpriseDatabasePoolManager, get_db_pool_status


def test_enterprise_db_pool_manager():
    manager = EnterpriseDatabasePoolManager()
    res = manager.get_pooled_engine()
    assert res["status"] == "active"
    assert res["max_concurrency_req_sec"] >= 5000


def test_get_db_pool_status_helper():
    info = get_db_pool_status()
    assert info["status"] == "active"
    assert "pool_type" in info
