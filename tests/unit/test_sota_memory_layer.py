"""
Unit tests for SOTA High-Performance Memory Cache Engine (backend/sota_memory_layer.py).
"""

import time

from backend.sota_memory_layer import SOTAMemoryLayerEngine


def test_tiny_lfu_memory_caching_and_eviction():
    engine = SOTAMemoryLayerEngine(capacity=2)

    engine.put("KEY_1", "PATIENT_DATA_1", ttl_seconds=60)
    engine.put("KEY_2", "PATIENT_DATA_2", ttl_seconds=60)

    # Increment frequency count for KEY_1
    assert engine.get("KEY_1") == "PATIENT_DATA_1"
    assert engine.get("KEY_1") == "PATIENT_DATA_1"

    # Insert KEY_3; KEY_2 should be evicted due to lower frequency count
    engine.put("KEY_3", "PATIENT_DATA_3", ttl_seconds=60)

    assert engine.get("KEY_1") == "PATIENT_DATA_1"
    assert engine.get("KEY_2") is None  # Evicted
    assert engine.get("KEY_3") == "PATIENT_DATA_3"

    # Test TTL expiration
    engine.put("KEY_EXP", "TEMP_DATA", ttl_seconds=0.01)
    time.sleep(0.02)
    assert engine.get("KEY_EXP") is None
