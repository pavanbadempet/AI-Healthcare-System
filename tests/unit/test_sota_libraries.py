"""
Unit tests for SOTA Library Registry (backend/sota_libraries.py).
"""

from backend.sota_libraries import sota_library_registry


def test_sota_library_registry_summary():
    summary = sota_library_registry.get_summary()
    assert summary["total_sota_libraries"] >= 4
    assert "details" in summary
    assert "orjson" in summary["details"]
    assert "httpx" in summary["details"]
    assert "cryptography" in summary["details"]
    assert "polars" in summary["details"]
