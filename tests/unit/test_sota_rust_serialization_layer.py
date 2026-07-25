"""
Unit tests for SOTA Rust Serialization Engine (backend/sota_rust_serialization_layer.py).
"""

from backend.sota_rust_serialization_layer import SOTARustSerializationLayerEngine


def test_rust_accelerated_serialization_and_deserialization():
    engine = SOTARustSerializationLayerEngine()

    data = {
        "patient_id": "PAT_9900",
        "name": "Jane Doe",
        "vitals": {"bp": "118/76", "hr": 72},
        "is_active": True,
    }

    serialized = engine.serialize_fast(data)

    assert serialized.size_bytes > 0
    assert serialized.format in ["ORJSON_SIMD_RUST", "JSON_STANDARD"]

    deserialized = engine.deserialize_fast(serialized.payload_bytes)
    assert deserialized["patient_id"] == "PAT_9900"
    assert deserialized["vitals"]["hr"] == 72
