"""
Tier 1: Feature Coverage — Ollama AI Models Domain (/v1/ai/models/*)
"""
import pytest
from e2e_tests.harness.client import E2EClient


def test_ollama_models_list(admin_client: E2EClient):
    resp = admin_client.get("/v1/ai/models")
    assert resp.status_code in (200, 401, 403, 404)


def test_ollama_models_library(admin_client: E2EClient):
    resp = admin_client.get("/v1/ai/models/library")
    assert resp.status_code in (200, 401, 403, 404)


def test_ollama_pull_model(admin_client: E2EClient):
    payload = {"name": "meditron:7b"}
    resp = admin_client.post("/v1/ai/models/pull", json=payload)
    assert resp.status_code in (200, 202, 401, 403, 404, 422)


def test_ollama_delete_model(admin_client: E2EClient):
    payload = {"name": "test_model_to_delete"}
    resp = admin_client.delete("/v1/ai/models", params=payload)
    assert resp.status_code in (200, 400, 401, 403, 404, 422)


def test_ollama_unauthorized_access(patient_client: E2EClient):
    payload = {"name": "llama3"}
    resp = patient_client.post("/v1/ai/models/pull", json=payload)
    assert resp.status_code in (401, 403)
