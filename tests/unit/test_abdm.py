"""
Unit tests for ABDM Health ID & Consent Manager Sandbox.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_abdm_health_id_generation_and_lookup():
    # 1. Generate ABHA Health ID
    payload = {
        "name": "Dr Ananya Sen",
        "gender": "F",
        "year_of_birth": 1988,
        "mobile": "9988776655",
        "aadhaar_last4": "5678"
    }
    response = client.post("/v1/abdm/abha/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "abha_number" in data
    assert data["name"] == "Dr Ananya Sen"
    assert data["status"] == "ACTIVE"

    # 2. Retrieve ABHA record
    abha_num = data["abha_number"]
    get_res = client.get(f"/v1/abdm/abha/{abha_num}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Dr Ananya Sen"

def test_abdm_consent_artifact_creation():
    payload = {
        "patient_abha": "91-9988-7766-5544@sbx",
        "purpose": "CLINICAL_DIAGNOSIS",
        "hi_types": ["DiagnosticReport", "Prescription"],
        "valid_until": "2027-12-31T23:59:59Z"
    }
    response = client.post("/v1/abdm/consent/request", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "GRANTED"
    assert data["patient_abha"] == "91-9988-7766-5544@sbx"

    # Lookup consent status
    consent_id = data["consent_id"]
    lookup_res = client.get(f"/v1/abdm/consent/{consent_id}")
    assert lookup_res.status_code == 200
    assert lookup_res.json()["consent_id"] == consent_id
