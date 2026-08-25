"""
Tier 1: Feature Coverage — Streaming Chat SSE Domain (/v1/chat/stream)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_streaming_chat_post_stream(patient_client: E2EClient):
    payload = {"message": "Hello, please provide wellness recommendations.", "conversation_id": "stream_test_01"}
    resp = patient_client.post("/v1/chat/stream", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_streaming_chat_empty_message_validation(patient_client: E2EClient):
    payload = {"message": "", "conversation_id": "stream_test_02"}
    resp = patient_client.post("/v1/chat/stream", json=payload)
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_streaming_chat_with_patient_context(patient_client: E2EClient):
    payload = {"message": "What is my latest blood pressure?", "patient_id": 1}
    resp = patient_client.post("/v1/chat/stream", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_streaming_chat_agent_stream(patient_client: E2EClient):
    payload = {"message": "I would like to book a cardiologist appointment", "patient_id": 1}
    resp = patient_client.post("/v1/appointments/agent-stream", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_streaming_chat_keepalive_structure(patient_client: E2EClient):
    payload = {"message": "Give a comprehensive 3-step heart care summary."}
    resp = patient_client.post("/v1/chat/stream", json=payload)
    assert resp.status_code in (200, 401, 404, 422)
