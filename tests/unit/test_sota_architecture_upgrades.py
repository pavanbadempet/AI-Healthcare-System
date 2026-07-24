"""
Unit tests for SOTA Architecture Upgrades:
- SIMD Analytics Engine (sota_analytics.py)
- SIMD Vector Engine (sota_vector_engine.py)
- MessagePack Binary Transport (binary_transport.py)
- ONNX C++ Inference Compiler (onnx_compiler.py)
"""

import pytest
from backend.sota_analytics import simd_analytics
from backend.sota_vector_engine import SOTAVectorEngine
from backend.binary_transport import pack_binary_payload, unpack_binary_payload, MessagePackResponse
from backend.onnx_compiler import onnx_compiler


def test_simd_analytics_bed_occupancy():
    beds = [
        {"id": 1, "status": "occupied"},
        {"id": 2, "status": "occupied"},
        {"id": 3, "status": "available"},
        {"id": 4, "status": "available"}
    ]
    res = simd_analytics.aggregate_bed_occupancy(beds)
    assert res["total_beds"] == 4
    assert res["occupied_beds"] == 2
    assert res["available_beds"] == 2
    assert res["occupancy_rate"] == 50.0
    assert "execution_ms" in res


def test_simd_analytics_empty_beds():
    res = simd_analytics.aggregate_bed_occupancy([])
    assert res["total_beds"] == 0
    assert res["occupancy_rate"] == 0.0


def test_sota_vector_engine_search():
    engine = SOTAVectorEngine(vector_dim=3)
    engine.add_vector("doc1", [1.0, 0.0, 0.0], {"title": "Cardiology"})
    engine.add_vector("doc2", [0.0, 1.0, 0.0], {"title": "Neurology"})

    results = engine.search_similar([0.9, 0.1, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "doc1"
    assert results[0]["payload"]["title"] == "Cardiology"


def test_binary_transport_pack_unpack():
    sample_data = {"patient_id": 42, "vitals": [120, 80, 72], "status": "stable"}
    packed = pack_binary_payload(sample_data)
    assert isinstance(packed, bytes)

    unpacked = unpack_binary_payload(packed)
    assert unpacked == sample_data


def test_messagepack_response_rendering():
    resp = MessagePackResponse(content={"status": "ok"})
    rendered = resp.render({"status": "ok"})
    assert isinstance(rendered, bytes)


def test_onnx_compiler_graceful_missing_model():
    res = onnx_compiler.predict_onnx_fast("nonexistent_model", [1.0, 2.0, 3.0])
    assert res is None
