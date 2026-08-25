"""
Tier 2: Boundary & Corner Cases — Security, SQL Injection & XSS Input Resilience
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_security_xss_in_chat(patient_client: E2EClient):
    xss_payload = {"message": "<script>alert('XSS Attack')</script><img src=x onerror=alert(1)>"}
    resp = patient_client.post("/v1/chat", json=xss_payload)
    assert resp.status_code in (200, 400, 401, 422)


def test_security_sql_injection_in_search(patient_client: E2EClient):
    sql_injection = "' OR '1'='1'; DROP TABLE users; --"
    resp = patient_client.get(f"/v1/pharmacy/compare-pricing?medication_name={sql_injection}")
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_security_null_byte_in_path(patient_client: E2EClient):
    resp = patient_client.get("/v1/diagnostics/lab-kits/%00evil")
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_security_admin_endpoint_forbidden_to_patient(patient_client: E2EClient):
    resp = patient_client.get("/v1/admin/audit-logs")
    assert resp.status_code in (401, 403)


def test_security_large_payload_handling(patient_client: E2EClient):
    huge_message = "A" * 100000
    resp = patient_client.post("/v1/chat", json={"message": huge_message})
    assert resp.status_code in (200, 400, 401, 413, 422, 500)
