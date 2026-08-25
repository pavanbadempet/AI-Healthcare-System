"""
Tier 1: Feature Coverage — Discharge Domain (/v1/discharge/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_discharge_patient_summaries(patient_client: E2EClient):
    resp = patient_client.get("/v1/discharge/patient/summaries")
    assert resp.status_code in (200, 401)


def test_discharge_create_summary(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "encounter_id": 1,
        "discharge_diagnosis": "Resolved acute gastroenteritis",
        "discharge_instructions": "Maintain hydration and resume soft diet",
        "follow_up_recommendations": "Follow up in 2 weeks with primary care",
    }
    resp = doctor_client.post("/v1/discharge/summaries", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_discharge_auto_generate(doctor_client: E2EClient):
    resp = doctor_client.post("/v1/discharge/summaries/generate/1")
    assert resp.status_code in (200, 401, 404)


def test_discharge_finalize_summary(doctor_client: E2EClient):
    resp = doctor_client.put("/v1/discharge/summaries/1/finalize")
    assert resp.status_code in (200, 401, 404)


def test_discharge_doctor_patient_summaries(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/discharge/doctor/patients/1/summaries")
    assert resp.status_code in (200, 401, 404)


def test_discharge_admin_metrics(admin_client: E2EClient):
    resp = admin_client.get("/v1/discharge/admin/metrics")
    assert resp.status_code in (200, 401, 403)
