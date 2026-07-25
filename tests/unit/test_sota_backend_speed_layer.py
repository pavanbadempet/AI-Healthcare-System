"""
Unit tests for SOTA Backend Speed Engine (backend/sota_backend_speed_layer.py).
"""

from backend.sota_backend_speed_layer import SOTABackendSpeedLayerEngine


def test_fast_json_serialization_and_response_wrapping():
    engine = SOTABackendSpeedLayerEngine()

    data = {"patient_id": "PAT_880", "status": "STABLE", "vitals": {"hr": 74}}
    json_str = engine.serialize_fast_json(data)

    assert '"patient_id":"PAT_880"' in json_str
    assert '"status":"STABLE"' in json_str

    response = engine.build_accelerated_response(data, start_time_us=100.0, end_time_us=185.5)

    assert response.status_code == 200
    assert response.execution_time_us == 85.5
    assert response.data["patient_id"] == "PAT_880"
