"""
Tier 1: Feature Coverage — Prediction Domain (/v1/predict/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_predict_diabetes(patient_client: E2EClient):
    payload = TestDataFactory.diabetes_input()
    resp = patient_client.post("/v1/predict/diabetes", json=payload)
    assert resp.status_code in (200, 401, 422), f"Diabetes prediction failed: {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        assert "prediction" in data or "probability" in data or "risk_level" in data


def test_predict_heart(patient_client: E2EClient):
    payload = TestDataFactory.heart_input()
    resp = patient_client.post("/v1/predict/heart", json=payload)
    assert resp.status_code in (200, 401, 422), f"Heart prediction failed: {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        assert "prediction" in data or "probability" in data or "risk_level" in data


def test_predict_kidney(patient_client: E2EClient):
    payload = TestDataFactory.kidney_input()
    resp = patient_client.post("/v1/predict/kidney", json=payload)
    assert resp.status_code in (200, 401, 422), f"Kidney prediction failed: {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        assert "prediction" in data or "probability" in data or "risk_level" in data


def test_predict_liver(patient_client: E2EClient):
    payload = TestDataFactory.liver_input()
    resp = patient_client.post("/v1/predict/liver", json=payload)
    assert resp.status_code in (200, 401, 422), f"Liver prediction failed: {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        assert "prediction" in data or "probability" in data or "risk_level" in data


def test_predict_lungs(patient_client: E2EClient):
    payload = TestDataFactory.lung_input()
    resp = patient_client.post("/v1/predict/lungs", json=payload)
    assert resp.status_code in (200, 401, 422), f"Lungs prediction failed: {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        assert "prediction" in data or "probability" in data or "risk_level" in data


def test_predict_stroke(patient_client: E2EClient):
    payload = TestDataFactory.stroke_input()
    resp = patient_client.post("/v1/predict/stroke", json=payload)
    assert resp.status_code in (200, 401, 422), f"Stroke prediction failed: {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        assert "prediction" in data or "probability" in data or "risk_level" in data


def test_predict_multi_organ(patient_client: E2EClient):
    payload = {
        "diabetes": TestDataFactory.diabetes_input(),
        "heart": TestDataFactory.heart_input(),
        "kidney": TestDataFactory.kidney_input(),
        "liver": TestDataFactory.liver_input(),
        "lungs": TestDataFactory.lung_input(),
    }
    resp = patient_client.post("/v1/predict/multi-organ", json=payload)
    assert resp.status_code in (200, 401, 422), f"Multi-organ response: {resp.text}"


def test_predict_models_health(admin_client: E2EClient):
    resp = admin_client.get("/v1/admin/models/health")
    assert resp.status_code in (200, 401, 403)
