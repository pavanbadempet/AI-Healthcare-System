def _without_demo_readiness_env(monkeypatch):
    keys = [
        "ABDM_DEMO_MODE",
        "SECRET_KEY",
        "DATABASE_URL",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OLLAMA_BASE_URL",
        "ABDM_CLIENT_ID",
        "ABDM_CLIENT_SECRET",
        "DICOMWEB_BASE_URL",
        "SMART_CLIENT_ID",
        "SMART_ISSUER_URL",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_demo_mode_ready_without_external_keys(client, monkeypatch):
    _without_demo_readiness_env(monkeypatch)
    monkeypatch.setenv("ABDM_DEMO_MODE", "true")

    response = client.get("/demo-readiness/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "demo-ready"
    assert payload["demo_mode"] is True
    assert payload["missing_required"] == []
    assert payload["required"]["SECRET_KEY"]["configured"] is False
    assert payload["required"]["DATABASE_URL"]["configured"] is False
    assert payload["optional"]["Gemini"]["configured"] is False
    assert payload["optional"]["ABDM"]["configured"] is False
    assert "operational metadata only" in payload["clinical_safety_note"]
    assert "does not certify clinical/legal/regulatory/production readiness" in payload["clinical_safety_note"]
    assert "does not expose patient data, PHI, or secret values" in payload["privacy_note"]
    assert payload["source"] == "backend.demo_readiness"


def test_production_blocked_when_required_runtime_env_missing(client, monkeypatch):
    _without_demo_readiness_env(monkeypatch)

    response = client.get("/demo-readiness/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "production-blocked"
    assert payload["demo_mode"] is False
    assert payload["missing_required"] == ["SECRET_KEY", "DATABASE_URL"]
    assert payload["required"]["SECRET_KEY"]["configured"] is False
    assert payload["required"]["DATABASE_URL"]["configured"] is False


def test_response_does_not_expose_secret_values(client, monkeypatch):
    _without_demo_readiness_env(monkeypatch)
    secret_value = "super-secret-runtime-value"
    database_value = "postgresql://user:password@db.example/healthcare"
    monkeypatch.setenv("SECRET_KEY", secret_value)
    monkeypatch.setenv("DATABASE_URL", database_value)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret")
    monkeypatch.setenv("ABDM_CLIENT_SECRET", "abdm-secret")

    response = client.get("/demo-readiness/")

    assert response.status_code == 200
    payload_text = response.text
    assert response.json()["status"] == "pilot-ready"
    assert secret_value not in payload_text
    assert database_value not in payload_text
    assert "gemini-secret" not in payload_text
    assert "abdm-secret" not in payload_text
