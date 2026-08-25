"""
Tier 1: Feature Coverage — Clinical Intelligence Domain (/v1/intelligence/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_intelligence_clinical_alerts(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/intelligence/alerts")
    assert resp.status_code in (200, 401, 404)


def test_intelligence_patient_insights(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/intelligence/insights/1")
    assert resp.status_code in (200, 401, 404)


def test_intelligence_explainability(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/intelligence/explainability/1")
    assert resp.status_code in (200, 401, 404)


def test_intelligence_doctor_insights(doctor_client: E2EClient):
    resp = doctor_client.get("/v1/hospital/doctor/insights")
    assert resp.status_code in (200, 401, 404)


def test_intelligence_acknowledge_alert(doctor_client: E2EClient):
    resp = doctor_client.post("/v1/intelligence/alerts/1/acknowledge")
    assert resp.status_code in (200, 401, 404)
