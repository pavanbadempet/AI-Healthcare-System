"""
Unit tests for SOTA Cache Locality Engine (backend/sota_cache_locality_layer.py).
"""

from backend.sota_cache_locality_layer import SOTACacheLocalityLayerEngine


def test_aos_to_soa_memory_conversion():
    engine = SOTACacheLocalityLayerEngine()

    aos = [
        {"ts": 100.0, "hr": 72.0, "bp": 120.0},
        {"ts": 101.0, "hr": 74.0, "bp": 122.0},
    ]

    soa = engine.convert_aos_to_soa(aos)

    assert soa.total_samples == 2
    assert soa.heart_rates == [72.0, 74.0]
    assert soa.is_soa_layout
    assert soa.layout_conversion_time_us >= 0.0
