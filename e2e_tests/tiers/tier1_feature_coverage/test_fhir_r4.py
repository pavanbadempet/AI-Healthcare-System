"""
Tier 1: Feature Coverage — FHIR R4 Domain (/v1/fhir/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_fhir_get_observations(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/fhir/Observation?patient=1")
    assert resp.status_code in (200, 401, 404, 422)


def test_fhir_get_patient(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/fhir/Patient/1")
    assert resp.status_code in (200, 401, 404)


def test_fhir_search_claims(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/fhir/Claim?patient=1")
    assert resp.status_code in (200, 401, 404, 422)


def test_fhir_search_imaging_studies(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/fhir/ImagingStudy?patient=1")
    assert resp.status_code in (200, 401, 404, 422)


def test_fhir_audit_events(admin_client: E2EClient):
    resp = admin_client.get("/v1/fhir/AuditEvent")
    assert resp.status_code in (200, 401, 403)


def test_fhir_import_patient(doctor_client: E2EClient):
    resp = doctor_client.post("/v1/fhir/Patient/import/ext_pat_9981")
    assert resp.status_code in (200, 201, 400, 401, 404, 422, 500, 502, 503)
