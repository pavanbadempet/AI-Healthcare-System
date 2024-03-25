"""
Extended tests for backend/vision_service.py to increase coverage.
Tests lazy model loading and analyze_lab_report function.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import io
from PIL import Image

from backend import vision_service
from backend.vision_service import get_vision_model, analyze_lab_report


class TestGetVisionModel:
    """Tests for the get_vision_model lazy loading function."""
    
    def test_get_vision_model_cached(self):
        """Test that model is cached after first load."""
        vision_service._vision_model = None
        
        mock_model = MagicMock()
        with patch("backend.vision_service.GOOGLE_API_KEY", "test-key"), \
             patch("backend.vision_service.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            
            result1 = get_vision_model()
            result2 = get_vision_model()
            
            assert result1 == result2
            # Should only create model once
            assert mock_genai.GenerativeModel.call_count == 1
    
    def test_get_vision_model_no_api_key(self):
        """Test returns None when API key missing."""
        vision_service._vision_model = None
        
        with patch("backend.vision_service.GOOGLE_API_KEY", None):
            result = get_vision_model()
            assert result is None
    
    def test_get_vision_model_init_failure(self):
        """Test graceful handling of initialization errors."""
        vision_service._vision_model = None
        
        with patch("backend.vision_service.GOOGLE_API_KEY", "test-key"), \
             patch("backend.vision_service.genai") as mock_genai:
            mock_genai.configure.side_effect = Exception("API Error")
            
            result = get_vision_model()
            assert result is None


class TestAnalyzeLabReport:
    """Tests for the analyze_lab_report function."""
    
    def create_test_image(self):
        """Create a simple test image."""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def test_analyze_no_api_key(self):
        """Test error when API key missing."""
        with patch("backend.vision_service.GOOGLE_API_KEY", None):
            with pytest.raises(HTTPException) as exc_info:
                analyze_lab_report(self.create_test_image())
            assert exc_info.value.status_code == 503
    
    def test_analyze_model_unavailable(self):
        """Test error when model unavailable."""
        with patch("backend.vision_service.GOOGLE_API_KEY", "test-key"), \
             patch("backend.vision_service.get_vision_model", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                analyze_lab_report(self.create_test_image())
            assert exc_info.value.status_code == 503
    
    def test_analyze_success(self):
        """Test successful image analysis."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"extracted_data": {"glucose": 120}, "summary": "Normal"}'
        mock_model.generate_content.return_value = mock_response
        
        with patch("backend.vision_service.GOOGLE_API_KEY", "test-key"), \
             patch("backend.vision_service.get_vision_model", return_value=mock_model):
            
            result = analyze_lab_report(self.create_test_image())
            
            assert "extracted_data" in result
            assert result["extracted_data"]["glucose"] == 120
    
    def test_analyze_strips_markdown(self):
        """Test that markdown formatting is stripped from response."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '```json\n{"extracted_data": {}, "summary": "Test"}\n```'
        mock_model.generate_content.return_value = mock_response
        
        with patch("backend.vision_service.GOOGLE_API_KEY", "test-key"), \
             patch("backend.vision_service.get_vision_model", return_value=mock_model):
            
            result = analyze_lab_report(self.create_test_image())
            
            assert "extracted_data" in result
    
    def test_analyze_exception_handling(self):
        """Test graceful handling of analysis errors."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API timeout")
        
        with patch("backend.vision_service.GOOGLE_API_KEY", "test-key"), \
             patch("backend.vision_service.get_vision_model", return_value=mock_model):
            
            result = analyze_lab_report(self.create_test_image())
            
            # Should return fallback response, not raise
            assert result["extracted_data"] == {}
            assert "Could not analyze" in result["summary"]
    
    def test_analyze_invalid_json(self):
        """Test handling of invalid JSON response."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Not valid JSON"
        mock_model.generate_content.return_value = mock_response
        
        with patch("backend.vision_service.GOOGLE_API_KEY", "test-key"), \
             patch("backend.vision_service.get_vision_model", return_value=mock_model):
            
            result = analyze_lab_report(self.create_test_image())
            
            # Should return fallback
            assert "Could not analyze" in result["summary"]
