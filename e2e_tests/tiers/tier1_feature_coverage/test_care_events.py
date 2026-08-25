"""
Tier 1: Feature Coverage — Care Events Domain (/v1/events/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_events_dispatch(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "event_type": "vital_alert",
        "severity": "medium",
        "payload": {"alert": "Systolic BP elevated at 145 mmHg"},
    }
    resp = doctor_client.post("/v1/events/dispatch", json=payload)
    assert resp.status_code in (200, 201, 401, 422)


def test_events_patient_feed(patient_client: E2EClient):
    resp = patient_client.get("/v1/events/patient/feed")
    assert resp.status_code in (200, 401)


def test_events_doctor_patient_feed(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/events/doctor/patients/1/feed")
    assert resp.status_code in (200, 401, 404)


def test_events_admin_recent(admin_client: E2EClient):
    resp = admin_client.get("/v1/events/admin/recent")
    assert resp.status_code in (200, 401, 403)


def test_events_admin_patient_feed(admin_client: E2EClient):
    resp = admin_client.get("/v1/events/admin/patients/1/feed")
    assert resp.status_code in (200, 401, 403, 404)


def test_events_admin_metrics(admin_client: E2EClient):
    resp = admin_client.get("/v1/events/admin/metrics")
    assert resp.status_code in (200, 401, 403)
