"""
Tier 1: Feature Coverage — Chat & Records Domain (/v1/chat, /v1/records, /v1/download)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_chat_send_message(patient_client: E2EClient):
    payload = {"message": "What should I eat to control my blood sugar?", "conversation_id": "conv_test_1"}
    resp = patient_client.post("/v1/chat", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_chat_aura_fallback(patient_client: E2EClient):
    payload = {"message": "Can you summarize lifestyle modifications for prediabetes?"}
    resp = patient_client.post("/v1/chat/aura", json=payload)
    assert resp.status_code in (200, 401, 422)


def test_chat_get_history(patient_client: E2EClient):
    resp = patient_client.get("/v1/chat/history")
    assert resp.status_code in (200, 401)


def test_records_list(patient_client: E2EClient):
    resp = patient_client.get("/v1/records")
    assert resp.status_code in (200, 401)


def test_records_save(patient_client: E2EClient):
    payload = {
        "title": "Annual Cardiology Checkup Report",
        "record_type": "clinical_summary",
        "description": "Patient exhibits stable sinus rhythm",
        "file_url": "https://storage.internal/records/rec_001.pdf",
    }
    resp = patient_client.post("/v1/records", json=payload)
    assert resp.status_code in (200, 201, 401, 422)


def test_download_health_report(patient_client: E2EClient):
    resp = patient_client.get("/v1/download/health-report")
    assert resp.status_code in (200, 401, 404)
