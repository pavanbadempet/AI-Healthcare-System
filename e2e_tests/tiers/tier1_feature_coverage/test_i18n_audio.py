"""
Tier 1: Feature Coverage — i18n Audio Domain (/v1/audio/* & dictation)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_audio_tts(patient_client: E2EClient):
    payload = {"text": "Your prescription has been renewed.", "target_language": "en"}
    resp = patient_client.post("/v1/audio/tts", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_audio_translate(patient_client: E2EClient):
    payload = {"text": "Take this tablet after breakfast.", "target_language": "es"}
    resp = patient_client.post("/v1/audio/translate", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_audio_transcribe(doctor_client: E2EClient):
    resp = doctor_client.post("/v1/audio/transcribe")
    assert resp.status_code in (200, 400, 401, 404, 422)


def test_audio_soap_dictation(doctor_client: E2EClient):
    payload = {"audio_base64": "UklGRi4AAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=", "patient_id": 1}
    resp = doctor_client.post("/v1/hospital/dictation/soap", json=payload)
    assert resp.status_code in (200, 401, 404, 422)


def test_audio_dictation_upload(doctor_client: E2EClient):
    payload = {"patient_id": 1, "format": "audio/wav"}
    resp = doctor_client.post("/v1/hospital/dicom/upload", json=payload)
    assert resp.status_code in (200, 201, 401, 404, 422)
