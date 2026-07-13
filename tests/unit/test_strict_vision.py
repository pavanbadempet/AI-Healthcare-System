from unittest.mock import patch

import pytest
from fastapi import HTTPException

from backend.vision_service import analyze_lab_report


def test_analyze_report_success():
    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.core_ai.generate_vision_content", return_value='{"extracted_data": {"glucose": 100}, "summary": "Healthy"}'), \
         patch("backend.vision_service.Image.open"):

        result = analyze_lab_report(b"fake_image_data")

        assert result["extracted_data"]["glucose"] == 100
        assert "Healthy" in result["summary"]

def test_analyze_report_api_failure():
    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.core_ai.generate_vision_content", side_effect=Exception("API Error")):

        # Expect generic success dict with empty data (as per service logic)
        result = analyze_lab_report(b"data")
        assert result["extracted_data"] == {}
        assert "Could not analyze" in result["summary"]

def test_analyze_report_api_failure_hides_error_details(caplog):
    sensitive_error = "vision provider failed patient_name=Sensitive User token=vision-secret"
    caplog.set_level("ERROR", logger="backend.vision_service")

    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.Image.open"), \
         patch("backend.vision_service.core_ai.generate_vision_content", side_effect=Exception(sensitive_error)):
        result = analyze_lab_report(b"data")

    assert result["extracted_data"] == {}
    assert "Could not analyze" in result["summary"]
    assert sensitive_error not in caplog.text
    assert "Sensitive User" not in caplog.text
    assert "vision-secret" not in caplog.text

def test_analyze_image_malformed_json():
    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.core_ai.generate_vision_content", return_value="Not JSON"):
        result = analyze_lab_report(b"bytes")
        # Should fall into exception block (json.loads fails)
        assert result["extracted_data"] == {}

def test_missing_api_key():
    # Patch GOOGLE_API_KEY to be None/Empty
    with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=False):
        with pytest.raises(HTTPException) as excinfo:
            analyze_lab_report(b"fake_image_bytes")

        assert excinfo.value.status_code == 503
        assert "Vision API Key not configured" in excinfo.value.detail
