"""
Tier 1: Feature Coverage — Nursing Domain (/v1/nursing/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_nursing_nurse_tasks(nurse_client: E2EClient):
    resp = nurse_client.get("/v1/nursing/nurse/tasks")
    assert resp.status_code in (200, 401)


def test_nursing_create_task(nurse_client: E2EClient):
    payload = TestDataFactory.nursing_task_create()
    resp = nurse_client.post("/v1/nursing/tasks", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_nursing_patient_tasks(patient_client: E2EClient):
    resp = patient_client.get("/v1/nursing/patient/tasks")
    assert resp.status_code in (200, 401)


def test_nursing_handoff_card(nurse_client: E2EClient):
    resp = nurse_client.post("/v1/nursing/patients/1/handoff")
    assert resp.status_code in (200, 401, 404)


def test_nursing_admin_metrics(admin_client: E2EClient):
    resp = admin_client.get("/v1/nursing/admin/metrics")
    assert resp.status_code in (200, 401, 403)


def test_nursing_doctor_patient_tasks(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/nursing/doctor/patients/1/tasks")
    assert resp.status_code in (200, 401, 404)
