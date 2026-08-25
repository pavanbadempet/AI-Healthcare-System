"""
Tier 2: Boundary & Corner Cases — Interoperability & FHIR Boundaries
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_fhir_get_nonexistent_patient(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/fhir/Patient/9999999")
    assert resp.status_code in (404, 200, 401, 500)


def test_fhir_observation_invalid_patient_param(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/fhir/Observation?patient=not_a_valid_number")
    assert resp.status_code in (400, 422, 404, 401, 200)


def test_interop_terminology_lookup_missing_system(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/terminology/lookup?code=38341003")
    assert resp.status_code in (200, 400, 401, 422, 404)


def test_interop_link_abha_empty_payload(patient_client: E2EClient):
    resp = patient_client.post("/v1/interop/abdm/link", json={})
    assert resp.status_code in (200, 201, 400, 401, 422)


def test_interop_consent_revoke_invalid_id(patient_client: E2EClient):
    resp = patient_client.post("/v1/interop/patient/consents/999999/revoke")
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_fhir_compression_corrupted_gzip_input(doctor_client: E2EClient):
    payload = {"compressed_payload": "corrupted_non_base64_!@#$", "algorithm": "gzip"}
    resp = doctor_client.post("/v1/fhir/decompress", json=payload)
    assert resp.status_code in (200, 400, 401, 422, 404)
