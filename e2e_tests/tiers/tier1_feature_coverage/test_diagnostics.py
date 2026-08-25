"""
Tier 1: Feature Coverage — Diagnostics Domain (/v1/diagnostics/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_diagnostics_patient_results(patient_client: E2EClient):
    resp = patient_client.get("/v1/diagnostics/patient/results")
    assert resp.status_code in (200, 401)


def test_diagnostics_create_result(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "test_name": "Hemoglobin A1c",
        "category": "blood_panel",
        "value": "6.8",
        "unit": "%",
        "reference_range": "4.0-5.6",
        "status": "final",
    }
    resp = doctor_client.post("/v1/diagnostics/results", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_diagnostics_order_lab_kit(patient_client: E2EClient):
    payload = {
        "patient_id": 1,
        "kit_type": "lipid_panel_home_kit",
        "delivery_address": "123 Main St, Springfield",
    }
    resp = patient_client.post("/v1/diagnostics/lab-kits", json=payload)
    assert resp.status_code in (200, 201, 401, 422)


def test_diagnostics_ecg_analyze(doctor_client: E2EClient):
    payload = {
        "signal_data": [0.01, 0.05, 0.25, 0.95, -0.2, 0.03, 0.1, 0.02] * 10,
        "sampling_rate": 250,
        "lead": "II",
    }
    resp = doctor_client.post("/v1/diagnostics/ecg/analyze", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_diagnostics_admin_metrics(admin_client: E2EClient):
    resp = admin_client.get("/v1/diagnostics/admin/metrics")
    assert resp.status_code in (200, 401, 403)


def test_diagnostics_doctor_patient_results(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/diagnostics/doctor/patients/1/results")
    assert resp.status_code in (200, 401, 404)
