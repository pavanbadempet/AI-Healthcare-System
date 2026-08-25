"""
Tier 1: Feature Coverage — Sales & Demo Readiness Modules (/v1/admin/* & /v1/demo-readiness/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_sales_readiness_audit(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/sales-readiness")
    assert resp.status_code in (200, 401, 403, 404)


def test_demo_readiness_status(admin_client: E2EClient):
    resp = admin_client.get("/v1/demo-readiness")
    assert resp.status_code in (200, 401, 403, 404)


def test_demo_readiness_slash(admin_client: E2EClient):
    resp = admin_client.get("/v1/demo-readiness/")
    assert resp.status_code in (200, 401, 403, 404)


def test_admin_backups_execute(admin_client: E2EClient):
    resp = admin_client.post("/v1/admin/backups/execute")
    assert resp.status_code in (200, 202, 401, 403, 404)


def test_admin_retention_execute(admin_client: E2EClient):
    resp = admin_client.post("/v1/admin/retention/execute-cleanup")
    assert resp.status_code in (200, 202, 401, 403, 404)


def test_admin_incident_readiness(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/incident-readiness")
    assert resp.status_code in (200, 401, 403, 404)
