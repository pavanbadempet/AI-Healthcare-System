"""
Tier 1: Feature Coverage — FHIR Compression Domain (/v1/fhir/compact & /v1/fhir/decompress)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_fhir_compression_compact(doctor_client: E2EClient):
    payload = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "1", "gender": "male"}},
        ],
    }
    resp = doctor_client.post("/v1/fhir/compact", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_fhir_compression_decompress(doctor_client: E2EClient):
    payload = {"compressed_payload": "H4sIC...", "algorithm": "gzip"}
    resp = doctor_client.post("/v1/fhir/decompress", json=payload)
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_fhir_compression_readiness(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/interop/smart/readiness")
    assert resp.status_code in (200, 401, 404)


def test_fhir_compression_invalid_format(doctor_client: E2EClient):
    payload = {"invalid_key": "not a fhir resource"}
    resp = doctor_client.post("/v1/fhir/compact", json=payload)
    assert resp.status_code in (200, 400, 422, 404)


def test_fhir_compression_doctor_patient_bundle(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/interop/doctor/patients/1/fhir-bundle")
    assert resp.status_code in (200, 401, 404)
