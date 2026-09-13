"""
Tier 2: Boundary & Corner Cases — System Health & Telemetry Probes
Tests probe divergence, rapid sequential querying, trailing slash handling, and header acceptance.
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_healthz_trailing_slash_normalization(e2e_client: E2EClient):
    """Verifies that both /healthz and /healthz/ respond consistently without redirection errors."""
    resp1 = e2e_client.get("/healthz")
    resp2 = e2e_client.get("/healthz/")
    assert resp1.status_code == 200
    assert resp2.status_code in (200, 307, 308)


def test_healthz_rapid_consecutive_probes(e2e_client: E2EClient):
    """Verifies that rapid successive health probes do not trigger thread starvation or socket leaks."""
    for _ in range(10):
        resp = e2e_client.get("/healthz/live")
        assert resp.status_code == 200


def test_metrics_accept_headers(e2e_client: E2EClient):
    """Verifies that /metrics responds appropriately with text/plain or default content types."""
    resp = e2e_client.get("/metrics", headers={"Accept": "text/plain"})
    assert resp.status_code == 200
    assert len(resp.text) > 0


def test_health_query_parameters_ignored(e2e_client: E2EClient):
    """Verifies that unrecognized query parameters on health checks do not cause exceptions."""
    resp = e2e_client.get("/healthz", params={"check_all": "true", "timeout": "999"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


def test_readiness_probe_response_time(e2e_client: E2EClient):
    """Verifies that readiness probes execute promptly within the SLA threshold."""
    resp = e2e_client.get("/healthz/ready")
    assert resp.status_code == 200
    assert resp.elapsed_ms < 1000.0
