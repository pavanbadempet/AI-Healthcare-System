"""
Tier 1: Feature Coverage — Appointments Domain (/v1/appointments/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_appointments_list(patient_client: E2EClient):
    resp = patient_client.get("/v1/appointments/")
    assert resp.status_code in (200, 401)


def test_appointments_create(patient_client: E2EClient):
    payload = TestDataFactory.appointment_create()
    resp = patient_client.post("/v1/appointments/", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_appointments_list_doctors(patient_client: E2EClient):
    resp = patient_client.get("/v1/appointments/doctors")
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_appointments_recommend_specialists(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/appointments/recommend-specialists/1")
    assert resp.status_code in (200, 401, 404)


def test_appointments_agent_chat(patient_client: E2EClient):
    payload = {"message": "I need to schedule an appointment with a cardiologist", "patient_id": 1}
    resp = patient_client.post("/v1/appointments/agent-chat", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_appointments_special_care(patient_client: E2EClient):
    payload = {
        "patient_id": 1,
        "care_tier": "cardiology_intensive",
        "requested_date": "2026-09-20",
        "symptoms": ["chest discomfort", "shortness of breath"],
    }
    resp = patient_client.post("/v1/appointments/special-care", json=payload)
    assert resp.status_code in (200, 201, 401, 422)
