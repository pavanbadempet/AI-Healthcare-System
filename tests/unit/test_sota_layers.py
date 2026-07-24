"""
Unit tests for SOTA Layered Architecture Registry (backend/sota_layers.py).
"""

from backend.sota_layers import sota_layer_registry


def test_sota_layer_registry():
    status = sota_layer_registry.get_layer_status()
    assert status["status"] == "healthy"
    assert status["total_layers"] == 5
    assert "Layer_1_Transport" in status["layer_topology"]
    assert "Layer_3_SIMD_Analytics" in status["layer_topology"]
    assert "Layer_5_TEE_Security" in status["layer_topology"]
