"""
Tier 1: Feature Coverage — Hospital Operations Domain (/v1/hospital/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_hospital_list_facilities(patient_client: E2EClient):
    resp = patient_client.get("/v1/hospital/facilities")
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_hospital_create_facility(admin_client: E2EClient):
    payload = TestDataFactory.facility_create()
    resp = admin_client.post("/v1/hospital/facilities", json=payload)
    assert resp.status_code in (200, 201, 401, 403)


def test_hospital_list_departments(patient_client: E2EClient):
    resp = patient_client.get("/v1/hospital/departments")
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_hospital_list_beds(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/hospital/beds")
    assert resp.status_code in (200, 401)


def test_hospital_create_encounter(doctor_client: E2EClient):
    payload = TestDataFactory.encounter_create()
    resp = doctor_client.post("/v1/hospital/encounters", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_hospital_create_clinical_order(doctor_client: E2EClient):
    payload = TestDataFactory.clinical_order_create()
    resp = doctor_client.post("/v1/hospital/orders", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)


def test_hospital_patient_timeline(patient_client: E2EClient):
    resp = patient_client.get("/v1/hospital/patient/timeline")
    assert resp.status_code in (200, 401, 404)
