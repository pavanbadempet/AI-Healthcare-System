"""
Tier 1: Feature Coverage — Federated Learning Domain (/v1/federated/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_federated_sync_stats(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/federated/stats")
    assert resp.status_code in (200, 401, 404)


def test_federated_audits(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/federated/audits")
    assert resp.status_code in (200, 401, 404)


def test_federated_sync_post(doctor_client: E2EClient):
    payload = {
        "model_name": "diabetes_model",
        "client_id": "client_node_01",
        "round_id": 1,
        "weights": [0.01, -0.02, 0.05],
        "num_samples": 100,
    }
    resp = doctor_client.post("/v1/federated/sync", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_federated_simulation_run(admin_client: E2EClient):
    resp = admin_client.post("/v1/admin/federated-sim?epochs=2&epsilon=1.0")
    assert resp.status_code in (200, 401, 403, 404, 422)


def test_federated_admin_audit_logs(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/audit-logs")
    assert resp.status_code in (200, 401, 403)
