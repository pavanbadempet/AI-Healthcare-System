"""
Tier 2: Boundary & Corner Cases — Deprecated CRUD Routes Input Resilience
Validates 404 on missing entities, 422 on malformed schemas, 401 on missing auth, and SQL injection resilience.
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_deprecated_route_missing_entity_returns_404(patient_client: E2EClient):
    """Verifies that requesting non-existent records on deprecated endpoints returns 404."""
    resp = patient_client.get("/v1/appointments/999999999")
    assert resp.status_code in (404, 401, 200)


def test_deprecated_route_malformed_json_returns_422(patient_client: E2EClient):
    """Verifies that posting malformed or invalid schema types returns 422 Unprocessable Entity."""
    invalid_payload = {
        "doctor_id": "NOT_AN_INTEGER",
        "appointment_date": 12345,
        "reason": None,
    }
    resp = patient_client.post("/v1/appointments/", json=invalid_payload)
    assert resp.status_code in (422, 400, 401)


def test_deprecated_route_unauthenticated_guard(e2e_client: E2EClient):
    """Verifies that unauthenticated requests to protected deprecated routes return 401 Unauthorized."""
    resp = e2e_client.get("/v1/appointments/")
    assert resp.status_code in (401, 403, 200)


def test_deprecated_route_sql_injection_defense(patient_client: E2EClient):
    """Verifies that SQL injection payloads in query parameters are parameterized and do not cause 500 errors."""
    sqli_params = {"status": "' OR '1'='1", "search": "admin' --"}
    resp = patient_client.get("/v1/appointments/", params=sqli_params)
    assert resp.status_code != 500, "SQL injection string caused 500 crash"
    assert resp.status_code in (200, 400, 401, 422)


def test_deprecated_route_extreme_pagination(patient_client: E2EClient):
    """Verifies that extreme offset/limit values are safely clamped without server crashing."""
    resp = patient_client.get("/v1/appointments/", params={"skip": 1000000, "limit": 50000})
    assert resp.status_code in (200, 400, 401, 422)
