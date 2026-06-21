"""
Tests for security.py, report.py, vision_service.py, explanation.py,
and explainability.py.
"""
import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import explainability, security, vision_service
from backend.database import Base, get_db
from backend.main import app
from backend.prediction import initialize_models

# ── Test DB & client ──────────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _auth_headers(client, username="sec_report_user"):
    password = "SecurePass123!"
    client.post("/signup", json={
        "username": username, "password": password,
        "email": f"{username}@test.com", "full_name": "Test", "dob": "1990-01-01",
    })
    r = client.post("/token", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    initialize_models()
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c
    app.dependency_overrides.clear()


# ── RateLimiter ───────────────────────────────────────────────────────────────

def test_rate_limiter_allows_requests_under_limit():
    limiter = security.RateLimiter(requests_per_minute=5)
    limiter.redis_available = False
    mock_req = MagicMock()
    # Should not raise for first 5 requests
    for _ in range(5):
        limiter.check(mock_req, "user:test")


def test_rate_limiter_raises_429_when_limit_exceeded():
    limiter = security.RateLimiter(requests_per_minute=3)
    limiter.redis_available = False
    mock_req = MagicMock()
    for _ in range(3):
        limiter.check(mock_req, "user:test2")
    with pytest.raises(HTTPException) as exc:
        limiter.check(mock_req, "user:test2")
    assert exc.value.status_code == 429


def test_rate_limiter_tracks_separate_identifiers_independently():
    limiter = security.RateLimiter(requests_per_minute=2)
    limiter.redis_available = False
    mock_req = MagicMock()
    limiter.check(mock_req, "user:a")
    limiter.check(mock_req, "user:a")
    # user:b should still be allowed
    limiter.check(mock_req, "user:b")


def test_rate_limiter_cleans_up_old_entries():
    import time
    limiter = security.RateLimiter(requests_per_minute=10)
    limiter.redis_available = False
    mock_req = MagicMock()
    # Fill storage above threshold to trigger cleanup
    for i in range(1010):
        limiter.storage[f"old_user_{i}"] = [time.time() - 120]  # 2 min ago = expired

    # This check should trigger _cleanup
    limiter.check(mock_req, "new_user")
    # Old expired entries should be pruned
    assert len(limiter.storage) < 1010


def test_rate_limiter_sliding_window_resets_after_60s():
    import time
    limiter = security.RateLimiter(requests_per_minute=2)
    limiter.redis_available = False
    mock_req = MagicMock()
    # Pre-populate with timestamps older than 60 seconds
    limiter.storage["user:old"] = [time.time() - 61, time.time() - 62]
    # Should now be allowed since old entries are expired
    limiter.check(mock_req, "user:old")


def test_load_rate_limit_raises_on_non_integer(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "not_a_number")
    with pytest.raises(RuntimeError, match="integer"):
        security._load_rate_limit_requests_per_minute()


def test_load_rate_limit_raises_on_zero(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "0")
    with pytest.raises(RuntimeError, match="positive"):
        security._load_rate_limit_requests_per_minute()


def test_load_rate_limit_raises_on_negative(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "-5")
    with pytest.raises(RuntimeError, match="positive"):
        security._load_rate_limit_requests_per_minute()


def test_load_rate_limit_returns_valid_value(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "120")
    assert security._load_rate_limit_requests_per_minute() == 120


# ── log_audit_event ───────────────────────────────────────────────────────────

def test_log_audit_event_writes_to_db(db_session):
    from backend import models as m
    security.log_audit_event(
        db_session,
        action="TEST_ACTION",
        target_user_id=99,
        admin_id=1,
        details="test details",
    )
    log = db_session.query(m.AuditLog).filter_by(action="TEST_ACTION").first()
    assert log is not None
    assert log.target_user_id == 99


def test_log_audit_event_handles_db_error(db_session):
    """Should not raise — DB errors are caught and logged."""
    with patch.object(db_session, "add", side_effect=Exception("DB error")):
        # Should not raise
        security.log_audit_event(db_session, action="FAIL", target_user_id=1)


# ── vision_service ────────────────────────────────────────────────────────────

def test_analyze_lab_report_raises_503_when_no_api_key():
    from PIL import Image
    img = Image.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=False):
        with pytest.raises(HTTPException) as exc:
            vision_service.analyze_lab_report(image_bytes)
    assert exc.value.status_code == 503


def test_analyze_lab_report_raises_503_when_vision_returns_empty():
    from PIL import Image
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.core_ai.generate_vision_content", return_value=""):
        with pytest.raises(HTTPException) as exc:
            vision_service.analyze_lab_report(image_bytes)
    assert exc.value.status_code == 503


def test_analyze_lab_report_returns_parsed_json():
    from PIL import Image
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    mock_response = json.dumps({
        "extracted_data": {"glucose": 140.0, "hba1c": 6.5},
        "summary": "Glucose slightly elevated."
    })

    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.core_ai.generate_vision_content", return_value=mock_response):
        result = vision_service.analyze_lab_report(image_bytes)

    assert result["extracted_data"]["glucose"] == 140.0
    assert "summary" in result


def test_analyze_lab_report_handles_json_parse_error():
    from PIL import Image
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.core_ai.generate_vision_content", return_value="NOT JSON"):
        result = vision_service.analyze_lab_report(image_bytes)

    # Should return graceful fallback
    assert "extracted_data" in result
    assert "summary" in result


def test_analyze_lab_report_strips_markdown_code_fences():
    from PIL import Image
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    mock_response = '```json\n{"extracted_data": {"glucose": 110.0}, "summary": "Normal"}\n```'

    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.core_ai.generate_vision_content", return_value=mock_response):
        result = vision_service.analyze_lab_report(image_bytes)

    assert result["extracted_data"]["glucose"] == 110.0


# ── explainability ────────────────────────────────────────────────────────────

def test_get_shap_values_returns_not_available_when_shap_missing():
    import numpy as np
    with patch("backend.explainability.SHAP_AVAILABLE", False):
        result = explainability.get_shap_values(
            MagicMock(), np.array([[1.0, 2.0]]), ["feature1", "feature2"]
        )
    assert "error" in result
    assert "SHAP library not installed" in result["error"]


def test_get_shap_values_returns_none_on_exception():
    import numpy as np
    mock_model = MagicMock()
    mock_model.estimators_ = [MagicMock()]

    with patch("backend.explainability.SHAP_AVAILABLE", True), \
         patch("backend.explainability.shap") as mock_shap:
        mock_shap.TreeExplainer.side_effect = Exception("SHAP error")
        result = explainability.get_shap_values(
            mock_model, np.array([[1.0, 2.0]]), ["f1", "f2"]
        )
    assert result is None


# ── /explain/ endpoint ────────────────────────────────────────────────────────

def test_explain_prediction_returns_explanation(client):
    headers = _auth_headers(client, "explain_user")
    payload = {
        "prediction_type": "Diabetes",
        "input_data": {"glucose": 140, "bmi": 30.5},
        "prediction_result": "High Risk",
    }

    mock_text = (
        "EXPLANATION: Your glucose of 140 is above normal range.\n"
        "TIPS:\n- Reduce sugar intake\n- Exercise 30 mins daily\n- Monitor blood pressure"
    )

    with patch("backend.explanation.core_ai.generate", new=AsyncMock(return_value=mock_text)):
        response = client.post("/explain/", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "lifestyle_tips" in data
    assert len(data["lifestyle_tips"]) > 0


def test_explain_prediction_fallback_when_no_explanation_section(client):
    headers = _auth_headers(client, "explain_user2")
    payload = {
        "prediction_type": "Heart Disease",
        "input_data": {"cholesterol": 240},
        "prediction_result": "Detected",
    }

    with patch("backend.explanation.core_ai.generate",
               new=AsyncMock(return_value="Your cholesterol is high. Please consult a doctor.")):
        response = client.post("/explain/", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["explanation"]) > 0


def test_explain_prediction_returns_503_when_ai_unavailable(client):
    headers = _auth_headers(client, "explain_user3")
    payload = {
        "prediction_type": "Liver",
        "input_data": {},
        "prediction_result": "Healthy",
    }

    with patch("backend.explanation.core_ai.generate", new=AsyncMock(return_value="")):
        response = client.post("/explain/", json=payload, headers=headers)

    assert response.status_code == 503


def test_explain_prediction_requires_auth(client):
    payload = {
        "prediction_type": "Diabetes",
        "input_data": {"glucose": 100},
        "prediction_result": "Low Risk",
    }
    response = client.post("/explain/", json=payload)
    assert response.status_code == 401


# ── /analyze/report endpoint ─────────────────────────────────────────────────

def test_analyze_report_rejects_non_image_files(client):
    headers = _auth_headers(client, "report_user1")
    response = client.post(
        "/analyze/report",
        files={"file": ("test.pdf", b"PDF content", "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 400


def test_analyze_report_requires_auth(client):
    response = client.post(
        "/analyze/report",
        files={"file": ("test.png", b"fake image", "image/png")},
    )
    assert response.status_code == 401


def test_analyze_report_returns_result_with_disclaimer(client):
    headers = _auth_headers(client, "report_user2")

    from PIL import Image
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    mock_result = {"extracted_data": {"glucose": 120.0}, "summary": "Normal range."}

    with patch("backend.report.vision_service.analyze_lab_report", return_value=mock_result):
        response = client.post(
            "/analyze/report",
            files={"file": ("lab.png", image_bytes, "image/png")},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "disclaimer" in data
    assert "extracted_data" in data


def test_analyze_report_propagates_503_from_vision_service(client):
    headers = _auth_headers(client, "report_user3")

    from PIL import Image
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    with patch("backend.report.vision_service.analyze_lab_report",
               side_effect=HTTPException(status_code=503, detail="Vision API Key not configured")):
        response = client.post(
            "/analyze/report",
            files={"file": ("lab.png", image_bytes, "image/png")},
            headers=headers,
        )

    assert response.status_code == 503


# ── /reports/download/health-report ──────────────────────────────────────────

def test_download_health_report_returns_pdf(client):
    headers = _auth_headers(client, "pdf_user1")

    mock_pdf = b"%PDF-1.4 test content"
    with patch("backend.report.pdf_service.generate_medical_report", return_value=mock_pdf):
        response = client.get("/reports/download/health-report", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert b"%PDF" in response.content


def test_download_health_report_requires_auth(client):
    response = client.get("/reports/download/health-report")
    assert response.status_code == 401


def test_download_health_report_returns_500_on_pdf_failure(client):
    headers = _auth_headers(client, "pdf_user2")

    with patch("backend.report.pdf_service.generate_medical_report",
               side_effect=Exception("PDF generation error")):
        response = client.get("/reports/download/health-report", headers=headers)

    assert response.status_code == 500
