import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os
import importlib
import backend.vision_service
from backend.vision_service import analyze_lab_report
from fastapi import HTTPException, UploadFile

@pytest.mark.asyncio
async def test_analyze_report_success():
    # Mock the model object returned by get_vision_model
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = '{"extracted_data": {"glucose": 100}, "summary": "Healthy"}'
    mock_model.generate_content.return_value = mock_resp

    # Ensure get_vision_model returns our mock model
    with patch("backend.vision_service.get_vision_model", return_value=mock_model), \
         patch("backend.vision_service.Image.open"):
        
        result = analyze_lab_report(b"fake_image_data")
        
        assert result["extracted_data"]["glucose"] == 100
        assert "Healthy" in result["summary"]

@pytest.mark.asyncio
async def test_analyze_report_api_failure():
    mock_model = MagicMock()
    # Simulate API Error
    mock_model.generate_content.side_effect = Exception("API Error")

    with patch("backend.vision_service.get_vision_model", return_value=mock_model):
        
        # Expect generic success dict with empty data (as per service logic)
        result = analyze_lab_report(b"data")
        assert result["extracted_data"] == {}
        assert "Could not analyze" in result["summary"]

def test_analyze_image_malformed_json():
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Not JSON"
    mock_model.generate_content.return_value = mock_resp
    
    with patch("backend.vision_service.get_vision_model", return_value=mock_model), \
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
