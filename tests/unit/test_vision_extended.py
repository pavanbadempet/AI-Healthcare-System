"""
Extended tests for backend/vision_service.py to increase coverage.
Tests that lab report analysis delegates provider work to core_ai.
"""
import io
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from PIL import Image

from backend.vision_service import analyze_lab_report


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
        with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                analyze_lab_report(self.create_test_image())
            assert exc_info.value.status_code == 503

    def test_analyze_model_unavailable(self):
        """Test error when the core AI vision boundary returns no text."""
        with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
             patch("backend.vision_service.core_ai.generate_vision_content", return_value=""):
            with pytest.raises(HTTPException) as exc_info:
                analyze_lab_report(self.create_test_image())
            assert exc_info.value.status_code == 503

    def test_analyze_success(self):
        """Test successful image analysis."""
        response_text = '{"extracted_data": {"glucose": 120}, "summary": "Normal"}'

        with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
             patch("backend.vision_service.core_ai.generate_vision_content", return_value=response_text):

            result = analyze_lab_report(self.create_test_image())

            assert "extracted_data" in result
            assert result["extracted_data"]["glucose"] == 120

    def test_analyze_strips_markdown(self):
        """Test that markdown formatting is stripped from response."""
        response_text = '```json\n{"extracted_data": {}, "summary": "Test"}\n```'

        with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
             patch("backend.vision_service.core_ai.generate_vision_content", return_value=response_text):

            result = analyze_lab_report(self.create_test_image())

            assert "extracted_data" in result

    def test_analyze_exception_handling(self):
        """Test graceful handling of analysis errors."""
        with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
             patch("backend.vision_service.core_ai.generate_vision_content", side_effect=Exception("API timeout")):

            result = analyze_lab_report(self.create_test_image())

            assert result["extracted_data"] == {}
            assert "Could not analyze" in result["summary"]

    def test_analyze_invalid_json(self):
        """Test handling of invalid JSON response."""
        with patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
             patch("backend.vision_service.core_ai.generate_vision_content", return_value="Not valid JSON"):

            result = analyze_lab_report(self.create_test_image())

            assert "Could not analyze" in result["summary"]
