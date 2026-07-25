"""
Unit tests for SOTA Fast Endpoints Engine (backend/sota_fast_endpoints_layer.py).
"""

from backend.sota_fast_endpoints_layer import SOTAFastEndpointsLayerEngine


def test_direct_byte_response_and_route_caching():
    engine = SOTAFastEndpointsLayerEngine()

    raw_bytes = b'{"status":"HEALTHY","vitals":{"hr":70}}'
    response = engine.render_direct_byte_response(raw_bytes)

    assert response.status_code == 200
    assert response.body_bytes == raw_bytes
    assert response.media_type == "application/json"

    # Test route caching
    cache_key = "GET_/api/v1/health"
    engine.cache_endpoint_route(cache_key, raw_bytes)

    cached_bytes = engine.get_cached_endpoint_route(cache_key)
    assert cached_bytes == raw_bytes
