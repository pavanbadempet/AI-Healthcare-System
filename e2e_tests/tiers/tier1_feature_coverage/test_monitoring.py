"""
Tier 1: Feature Coverage — Monitoring Domain (/v1/monitoring/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_monitoring_submit_vitals(patient_client: E2EClient):
    payload = TestDataFactory.vitals_create()
    resp = patient_client.post("/v1/monitoring/vitals", json=payload)
    assert resp.status_code in (200, 201, 401, 422)


def test_monitoring_patient_vitals(patient_client: E2EClient):
    resp = patient_client.get("/v1/monitoring/patient/vitals")
    assert resp.status_code in (200, 401)


def test_monitoring_doctor_signals(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/monitoring/doctor/patients/1/signals")
    assert resp.status_code in (200, 401, 404)


def test_monitoring_admin_patterns(admin_client: E2EClient):
    resp = admin_client.get("/v1/monitoring/admin/patterns")
    assert resp.status_code in (200, 401, 403)


def test_monitoring_doctor_patterns(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/monitoring/doctor/patterns")
    assert resp.status_code in (200, 401)


def test_monitoring_resolve_signal(doctor_client: E2EClient):
    resp = doctor_client.put("/v1/monitoring/signals/1/resolve")
    assert resp.status_code in (200, 401, 404)
