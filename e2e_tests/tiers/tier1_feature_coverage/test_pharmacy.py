"""
Tier 1: Feature Coverage — Pharmacy Domain (/v1/pharmacy/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_pharmacy_list_inventory(patient_client: E2EClient):
    resp = patient_client.get("/v1/pharmacy/inventory")
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_pharmacy_create_inventory(admin_client: E2EClient):
    payload = TestDataFactory.medication_inventory_create()
    resp = admin_client.post("/v1/pharmacy/inventory", json=payload)
    assert resp.status_code in (200, 201, 401, 403, 422)


def test_pharmacy_check_safety(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "new_medication": "Warfarin",
        "current_medications": ["Aspirin", "Metformin"],
    }
    resp = doctor_client.post("/v1/pharmacy/check-safety", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_pharmacy_compare_pricing(patient_client: E2EClient):
    resp = patient_client.get("/v1/pharmacy/compare-pricing?medication_name=Amoxicillin")
    assert resp.status_code in (200, 401, 422)


def test_pharmacy_generic_substitute(patient_client: E2EClient):
    resp = patient_client.get("/v1/pharmacy/generic-substitute?branded_name=Lipitor")
    assert resp.status_code in (200, 401, 422)


def test_pharmacy_patient_prescriptions(patient_client: E2EClient):
    resp = patient_client.get("/v1/pharmacy/patient/prescriptions")
    assert resp.status_code in (200, 401)
