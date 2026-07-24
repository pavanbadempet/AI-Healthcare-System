"""Unit tests for the backend Text-to-Speech (TTS) module."""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_tts_english_success():
    resp = client.post("/v1/audio/tts", json={"text": "Hello world", "lang": "en"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert len(resp.content) > 10

def test_tts_spanish_success():
    resp = client.post("/v1/audio/tts", json={"text": "Hola mundo", "lang": "es"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"

def test_tts_unsupported_language():
    resp = client.post("/v1/audio/tts", json={"text": "Unsupported", "lang": "unknown"})
    assert resp.status_code == 400
    assert "Language" in resp.json()["detail"]

def test_tts_empty_text():
    resp = client.post("/v1/audio/tts", json={"text": "", "lang": "en"})
    assert resp.status_code == 400
    assert "Text" in resp.json()["detail"]
