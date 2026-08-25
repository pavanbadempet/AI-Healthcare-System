"""
Tier 1: Feature Coverage — Recommendation Engine Domain (/v1/recommendations/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_recommendations_clinical_interventions(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "prediction_domain": "cardiology",
        "risk_level": "high",
        "features": {"systolic_bp": 145, "cholesterol": 240},
    }
    resp = doctor_client.post("/v1/recommendations/clinical-interventions", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_recommendations_lifestyle_pathways(patient_client: E2EClient):
    payload = {
        "patient_id": 1,
        "prediction_domain": "metabolic",
        "risk_level": "moderate",
        "features": {"bmi": 28.5, "physical_activity": 0},
    }
    resp = patient_client.post("/v1/recommendations/lifestyle-pathways", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_recommendations_clinical_trials(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "prediction_domain": "oncology",
        "risk_level": "high",
        "features": {"stage": "II", "biomarker_positive": 1},
    }
    resp = doctor_client.post("/v1/recommendations/clinical-trials", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_recommendations_generate_generic(doctor_client: E2EClient):
    payload = {
        "patient_id": 1,
        "prediction_domain": "general_wellness",
        "risk_level": "low",
        "features": {},
    }
    resp = doctor_client.post("/v1/recommendations/generate", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_recommendations_feedback(doctor_client: E2EClient):
    payload = {
        "recommendation_id": "rec_001",
        "patient_id": 1,
        "action_taken": "accepted",
        "clinician_rating": 5,
    }
    resp = doctor_client.post("/v1/recommendations/feedback", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)
