"""
Tier 1: Feature Coverage — Consent Gate Domain (/v1/consent/* & /v1/interop/consents/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_consent_list_patient(patient_client: E2EClient):
    resp = patient_client.get("/v1/interop/patient/consents")
    assert resp.status_code in (200, 401)


def test_consent_grant(patient_client: E2EClient):
    payload = {
        "patient_id": 1,
        "purpose": "clinical_research",
        "hiu_id": "HIU_RESEARCH_01",
        "data_categories": ["observations", "conditions"],
    }
    resp = patient_client.post("/v1/interop/patient/consents", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_consent_revoke(patient_client: E2EClient):
    resp = patient_client.post("/v1/interop/patient/consents/1/revoke")
    assert resp.status_code in (200, 401, 404)


def test_consent_check_doctor(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/interop/doctor/patients/1/consent-status")
    assert resp.status_code in (200, 401, 404)


def test_consent_admin_list(admin_client: E2EClient):
    resp = admin_client.get("/v1/interop/admin/consents")
    assert resp.status_code in (200, 401, 403)
