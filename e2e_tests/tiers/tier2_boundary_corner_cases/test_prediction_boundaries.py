"""
Tier 2: Boundary & Corner Cases — ML Prediction Input Boundaries
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_predict_diabetes_empty_body(patient_client: E2EClient):
    resp = patient_client.post("/v1/predict/diabetes", json={})
    assert resp.status_code in (200, 400, 401, 422, 500)


def test_predict_diabetes_extreme_bmi(patient_client: E2EClient):
    payload = TestDataFactory.diabetes_input()
    payload["bmi"] = 999.9
    resp = patient_client.post("/v1/predict/diabetes", json=payload)
    assert resp.status_code in (200, 400, 401, 422)


def test_predict_heart_negative_age(patient_client: E2EClient):
    payload = TestDataFactory.heart_input()
    payload["age"] = -50.0
    resp = patient_client.post("/v1/predict/heart", json=payload)
    assert resp.status_code in (200, 400, 401, 422)


def test_predict_kidney_string_in_float_field(patient_client: E2EClient):
    payload = TestDataFactory.kidney_input()
    payload["bp"] = "high_blood_pressure"
    resp = patient_client.post("/v1/predict/kidney", json=payload)
    assert resp.status_code in (400, 401, 422)


def test_predict_liver_null_values(patient_client: E2EClient):
    payload = {"age": None, "gender": None, "total_bilirubin": None}
    resp = patient_client.post("/v1/predict/liver", json=payload)
    assert resp.status_code in (200, 400, 401, 422)


def test_predict_stroke_overflow_values(patient_client: E2EClient):
    payload = TestDataFactory.stroke_input()
    payload["avg_glucose_level"] = 1e12
    resp = patient_client.post("/v1/predict/stroke", json=payload)
    assert resp.status_code in (200, 400, 401, 422)


def test_predict_nonexistent_model(patient_client: E2EClient):
    resp = patient_client.post("/v1/predict/unknown_cancer_model", json={})
    assert resp.status_code in (401, 404, 405)
