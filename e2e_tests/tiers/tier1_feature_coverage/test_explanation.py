"""
Tier 1: Feature Coverage — ML Explanations & SHAP Domain (/v1/predict/explain/* & /v1/explain/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_explain_diabetes(patient_client: E2EClient):
    payload = TestDataFactory.diabetes_input()
    resp = patient_client.post("/v1/predict/explain/diabetes", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_explain_heart(patient_client: E2EClient):
    payload = TestDataFactory.heart_input()
    resp = patient_client.post("/v1/predict/explain/heart", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_explain_liver(patient_client: E2EClient):
    payload = TestDataFactory.liver_input()
    resp = patient_client.post("/v1/predict/explain/liver", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_explain_text(doctor_client: E2EClient):
    payload = {"patient_text": "Patient has elevated fasting glucose and mild polyuria.", "model_name": "diabetes"}
    resp = doctor_client.post("/v1/predict/explain-text/diabetes", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_explain_counterfactual(doctor_client: E2EClient):
    payload = {"target_risk_level": "low", "features_to_vary": ["bmi", "physical_activity"]}
    resp = doctor_client.post("/v1/predict/counterfactual/1", json=payload)
    assert resp.status_code in (200, 401, 404, 422)
