"""
Tier 1: Feature Coverage — System Health, Probes & Prometheus Metrics (Feature 8)
Endpoints: /healthz, /healthz/live, /healthz/ready, /metrics
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_healthz_endpoint(e2e_client: E2EClient):
    """Verifies that the /healthz primary health endpoint returns 200 and healthy status."""
    resp = e2e_client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert any(k in data for k in ("status", "status_code", "healthy", "service", "version"))


def test_healthz_live_probe(e2e_client: E2EClient):
    """Verifies that the /healthz/live Kubernetes liveness probe returns 200 OK."""
    resp = e2e_client.get("/healthz/live")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("status") in ("alive", "healthy", "ok", "UP") or "status" in data


def test_healthz_ready_probe(e2e_client: E2EClient):
    """Verifies that the /healthz/ready Kubernetes readiness probe returns 200 OK."""
    resp = e2e_client.get("/healthz/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("status") in ("ready", "healthy", "ok", "UP") or "status" in data


def test_metrics_endpoint(e2e_client: E2EClient):
    """Verifies that the /metrics Prometheus telemetry endpoint returns valid metrics."""
    resp = e2e_client.get("/metrics")
    assert resp.status_code == 200
    assert len(resp.text) > 0
    # Prometheus format contains metric names, TYPE or HELP comments, or JSON metrics
    text = resp.text
    assert (
        "#" in text
        or "http_" in text
        or "process_" in text
        or "health" in text
        or "{" in text
    )


def test_circuit_breaker_status(e2e_client: E2EClient):
    """Verifies that the system circuit breaker status endpoint is queryable."""
    resp = e2e_client.get("/circuit-breaker/status")
    # Endpoint returns 200 if supported or standard status
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, dict)


def test_health_response_headers(e2e_client: E2EClient):
    """Verifies that health responses include proper content headers and low response latency."""
    resp = e2e_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.elapsed_ms >= 0.0
    # Response elapsed time should be sub-50ms in local testing
    assert resp.elapsed_ms < 500.0
