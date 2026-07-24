"""Unit tests for the backend FHIR Compression module."""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_fhir_compression_roundtrip():
    # Large mock FHIR-like resource
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "12345",
                    "active": True,
                    "name": [{"use": "official", "family": "Doe", "given": ["John", "M"]}],
                    "gender": "male",
                    "birthDate": "1980-01-01"
                }
            }
        ]
    }

    # 1. Compress
    resp = client.post("/v1/fhir/compact", json={"fhir_bundle": bundle})
    assert resp.status_code == 200
    res_data = resp.json()
    assert "payload" in res_data
    assert res_data["compressed_size"] < res_data["original_size"]

    # 2. Decompress
    resp_decomp = client.post("/v1/fhir/decompress", json={"compressed_data": res_data["payload"]})
    assert resp_decomp.status_code == 200
    decomp_bundle = resp_decomp.json()
    assert decomp_bundle["resourceType"] == "Bundle"
    assert decomp_bundle["entry"][0]["resource"]["id"] == "12345"

def test_decompress_invalid_data():
    resp = client.post("/v1/fhir/decompress", json={"compressed_data": "invalid_base85_or_zlib_data"})
    assert resp.status_code == 400
    assert "Decompression failed" in resp.json()["detail"]
