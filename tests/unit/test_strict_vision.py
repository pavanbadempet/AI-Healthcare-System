import pytest
from unittest.mock import MagicMock, patch
import os
import importlib
import backend.vision_service
from backend.vision_service import analyze_lab_report
from fastapi import HTTPException

def test_analyze_image_success():
    # Mock genai model response
    mock_resp = MagicMock()
    # Return strict JSON string
    mock_resp.text = '{"extracted_data": {"glucose": 100}, "summary": "Healthy"}'
    
    with patch("backend.vision_service.model.generate_content", return_value=mock_resp) as mock_gen, \
         patch("backend.vision_service.Image.open") as mock_open, \
         patch("backend.vision_service.GOOGLE_API_KEY", "dummy_key"):
         
        result = analyze_lab_report(b"fake_image_bytes")
        
        # DEBUG: Check if assertion failure was Key Error
        print(f"DEBUG RESULT: {result}")
        
        assert "extracted_data" in result
        assert "summary" in result
        assert result["extracted_data"]["glucose"] == 100
        assert result["summary"] == "Healthy"
        assert mock_gen.called

def test_analyze_image_exception():
    # Force exception
    # Force exception
    with patch("backend.vision_service.model.generate_content", side_effect=Exception("API Error")), \
         patch("backend.vision_service.GOOGLE_API_KEY", "dummy_key"):
        result = analyze_lab_report(b"bytes")
        # Should return error stricture
        assert result["extracted_data"] == {}
        assert "Could not analyze" in result["summary"]

def test_analyze_image_malformed_json():
    mock_resp = MagicMock()
    mock_resp.text = "Not JSON"
    
    with patch("backend.vision_service.model.generate_content", return_value=mock_resp), \
         patch("backend.vision_service.GOOGLE_API_KEY", "dummy_key"):
        result = analyze_lab_report(b"bytes")
        # Should fall into exception block (json.loads fails)
        assert result["extracted_data"] == {}

def test_missing_api_key():
    # Patch GOOGLE_API_KEY to be None/Empty
    with patch("backend.vision_service.GOOGLE_API_KEY", None):
        with pytest.raises(HTTPException) as excinfo:
            analyze_lab_report(b"fake_image_bytes")
        
        assert excinfo.value.status_code == 503
        assert "Vision API Key not configured" in excinfo.value.detail
