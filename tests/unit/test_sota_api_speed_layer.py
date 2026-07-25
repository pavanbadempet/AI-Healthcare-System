"""
Unit tests for SOTA High-Speed API Engine (backend/sota_api_speed_layer.py).
"""

from backend.sota_api_speed_layer import SOTAAPISpeedLayerEngine


def test_etag_generation_and_304_conditional_responses():
    engine = SOTAAPISpeedLayerEngine()

    payload = {"patient_id": "PAT_123", "name": "John Doe", "hr": 72}
    etag = engine.generate_etag(payload)

    assert etag.startswith('W/"')

    # Test 304 Not Modified when ETag matches
    resp_304 = engine.evaluate_conditional_request(payload, if_none_match_header=etag)
    assert resp_304.status_code == 304
    assert not resp_304.is_modified
    assert resp_304.payload is None

    # Test sparse fieldset pruning
    pruned = engine.prune_sparse_fields(payload, ["patient_id", "hr"])
    assert "patient_id" in pruned
    assert "hr" in pruned
    assert "name" not in pruned
