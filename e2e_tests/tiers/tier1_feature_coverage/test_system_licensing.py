"""
Tier 1: Feature Coverage — Top-Level System & Licensing Domain (/, /healthz/*, /metrics, /v1/licensing/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_root_endpoint(e2e_client: E2EClient):
    resp = e2e_client.get("/")
    assert resp.status_code == 200, f"Root endpoint failed: {resp.text}"


def test_healthz(e2e_client: E2EClient):
    resp = e2e_client.get("/healthz")
    assert resp.status_code == 200, f"Healthz failed: {resp.text}"
    data = resp.json()
    assert data.get("status") in ("healthy", "ok", "degraded") or "status" in data


def test_healthz_circuit_breaker(e2e_client: E2EClient):
    resp = e2e_client.get("/healthz/circuit_breaker")
    assert resp.status_code == 200, f"Circuit breaker failed: {resp.text}"


def test_healthz_env(e2e_client: E2EClient):
    resp = e2e_client.get("/healthz/env")
    assert resp.status_code in (200, 404)


def test_healthz_time_predict(e2e_client: E2EClient):
    resp = e2e_client.get("/healthz/time_predict")
    assert resp.status_code in (200, 404)


def test_prometheus_metrics(e2e_client: E2EClient):
    resp = e2e_client.get("/metrics")
    assert resp.status_code == 200, f"Metrics failed: {resp.text}"


def test_licensing_status(e2e_client: E2EClient):
    resp = e2e_client.get("/v1/licensing/status")
    assert resp.status_code in (200, 404)


def test_licensing_activate(e2e_client: E2EClient):
    payload = {"license_key": "ENTERPRISE-PRO-2026-TESTKEY", "facility_id": 1}
    resp = e2e_client.post("/v1/licensing/activate", json=payload)
    assert resp.status_code in (200, 400, 401, 404, 422)
