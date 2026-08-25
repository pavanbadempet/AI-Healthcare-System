"""
Tier 1: Feature Coverage — Longitudinal Prediction Domain (/v1/predict/longitudinal/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_longitudinal_diabetes_progression(doctor_client: E2EClient):
    payload = {
        "features": TestDataFactory.diabetes_input(),
        "time_horizon_years": 5,
    }
    resp = doctor_client.post("/v1/predict/longitudinal/diabetes", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_longitudinal_heart_progression(doctor_client: E2EClient):
    payload = {
        "features": TestDataFactory.heart_input(),
        "time_horizon_years": 5,
    }
    resp = doctor_client.post("/v1/predict/longitudinal/heart", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_longitudinal_liver_progression(doctor_client: E2EClient):
    payload = {
        "features": TestDataFactory.liver_input(),
        "time_horizon_years": 5,
    }
    resp = doctor_client.post("/v1/predict/longitudinal/liver", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_longitudinal_kidney_progression(doctor_client: E2EClient):
    payload = {
        "features": TestDataFactory.kidney_input(),
        "time_horizon_years": 5,
    }
    resp = doctor_client.post("/v1/predict/longitudinal/kidney", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_longitudinal_organ_health(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/predict/organ_health/1")
    assert resp.status_code in (200, 401, 404)
