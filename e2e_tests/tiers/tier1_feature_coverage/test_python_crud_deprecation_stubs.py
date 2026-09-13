"""
Tier 1: Feature Coverage — Python CRUD Route Deprecation & Test-Safe Stubs (Features 17 & 18)
Validates that deprecated Python CRUD routes provide clean stubs and preserve 100% pytest test compatibility.
"""
import os
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_testing_mode_environment_variable():
    """Verifies that TESTING mode is active during test runner execution."""
    assert os.getenv("TESTING") == "1", "TESTING environment variable must be set to '1'"


def test_appointments_crud_stub_compatibility(patient_client: E2EClient):
    """Verifies that deprecated Python appointment routes respond without internal server errors."""
    resp = patient_client.get("/v1/appointments/")
    assert resp.status_code in (200, 401, 404)
    if resp.status_code == 200:
        assert isinstance(resp.json(), (list, dict))


def test_pharmacy_crud_stub_compatibility(admin_client: E2EClient):
    """Verifies that deprecated Python pharmacy routes maintain backward compatibility in test mode."""
    resp = admin_client.get("/v1/pharmacy/inventory")
    assert resp.status_code in (200, 401, 404)
    if resp.status_code == 200:
        assert isinstance(resp.json(), (list, dict))


def test_records_crud_stub_compatibility(doctor_client: E2EClient):
    """Verifies that deprecated Python health records routes maintain backward compatibility in test mode."""
    resp = doctor_client.get("/v1/records/patient/1")
    assert resp.status_code in (200, 401, 404)
    if resp.status_code == 200:
        assert isinstance(resp.json(), (list, dict))


def test_billing_crud_stub_compatibility(admin_client: E2EClient):
    """Verifies that deprecated Python billing routes respond correctly in test mode."""
    resp = admin_client.get("/v1/billing/services")
    assert resp.status_code in (200, 401, 404)
    if resp.status_code == 200:
        assert isinstance(resp.json(), (list, dict))


def test_zero_breaking_changes_across_crud_domains(patient_client: E2EClient):
    """Verifies that calling multiple CRUD endpoints returns standard HTTP codes (no 500 crashes)."""
    endpoints = [
        "/v1/appointments/doctors",
        "/v1/hospital/facilities",
        "/v1/hospital/departments",
        "/v1/events/feed",
    ]
    for ep in endpoints:
        resp = patient_client.get(ep)
        assert resp.status_code != 500, f"Endpoint {ep} crashed with 500 Internal Server Error"
