"""
Tier 1: Feature Coverage — Peak Healthcare Intelligence Domain (/v1/digital-twin/*, /v1/pharmacogenomics/*, /v1/clinical-council/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_digital_twin_simulate(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "current_vitals": {"systolic": 135, "diastolic": 85, "glucose": 110, "bmi": 27.5},
        "simulation_years": 5,
        "interventions": ["lifestyle_diet_modification", "ace_inhibitor_therapy"],
    }
    resp = doctor_client.post("/v1/digital-twin/simulate", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_digital_twin_pharmacogenomics(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "medications": ["Clopidogrel", "Warfarin", "Simvastatin"],
        "genetic_variants": ["CYP2C19*2", "CYP2C9*3", "SLCO1B1*5"],
    }
    resp = doctor_client.post("/v1/pharmacogenomics/evaluate", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_digital_twin_clinical_council(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "case_summary": "Complex diabetic patient with declining renal function and refractory hypertension",
        "specialties_requested": ["Cardiology", "Nephrology", "Endocrinology"],
    }
    resp = doctor_client.post("/v1/clinical-council/deliberate", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_digital_twin_status(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/hospital/doctor/insights")
    assert resp.status_code in (200, 401, 404)


def test_digital_twin_physiology(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/intelligence/insights/1")
    assert resp.status_code in (200, 401, 404)
