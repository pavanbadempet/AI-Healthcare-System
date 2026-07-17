import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_prometheus_metrics_endpoint():
    client = TestClient(app)
    
    # Hit standard route first to trigger middleware
    res_home = client.get("/")
    assert res_home.status_code in (200, 404) # catchall frontend check might be 404 if not built, which is fine
    
    # Now scrape metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    
    body = response.text
    # Check that standard Prometheus metrics are in the body
    assert "http_requests_total" in body
    assert "system_cpu_percent" in body
    assert "system_memory_percent" in body
    assert "database_connections_active" in body
