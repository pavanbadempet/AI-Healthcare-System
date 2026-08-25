"""
Tier 1: Feature Coverage — Admin Dashboard Domain (/v1/admin/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_admin_stats(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/stats")
    assert resp.status_code in (200, 401, 403)


def test_admin_users(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/users")
    assert resp.status_code in (200, 401, 403)


def test_admin_audit_logs(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/audit-logs")
    assert resp.status_code in (200, 401, 403)


def test_admin_backup_readiness(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/backup-readiness")
    assert resp.status_code in (200, 401, 403)


def test_admin_compliance_hipaa(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/compliance/hipaa")
    assert resp.status_code in (200, 401, 403)


def test_admin_model_cards(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/model-cards")
    assert resp.status_code in (200, 401, 403)


def test_admin_semantic_cache_stats(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/semantic-cache")
    assert resp.status_code in (200, 401, 403)


def test_admin_operational_health(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/operational-health")
    assert resp.status_code in (200, 401, 403)
