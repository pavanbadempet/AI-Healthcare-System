"""
Extended tests for backend/explanation.py — core_ai-backed explanation service.
Tests response parsing, error handling, and edge cases.
"""
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import auth, explanation, models

# Create test app
app = FastAPI()
app.include_router(explanation.router)
app.dependency_overrides[auth.get_current_user] = lambda: models.User(id=1, username="explain_test")
client = TestClient(app)


class TestExplainPredictionEndpoint:
    """Tests for the /explain/ endpoint via core_ai."""

    def test_explain_success(self):
        """Test successful explanation generation."""
        mock_text = (
            "EXPLANATION: Your glucose level of 140 is elevated.\n"
            "TIPS:\n"
            "- Reduce sugar intake\n"
            "- Exercise regularly\n"
            "- Monitor blood glucose daily"
        )

        with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock, return_value=mock_text):
            resp = client.post("/explain/", json={
                "prediction_type": "Diabetes",
                "input_data": {"glucose": 140, "bmi": 28},
                "prediction_result": "High Risk"
            })

            assert resp.status_code == 200
            data = resp.json()
            assert "explanation" in data
            assert "lifestyle_tips" in data
            assert "glucose" in data["explanation"].lower()
            assert len(data["lifestyle_tips"]) == 3

    def test_explain_model_unavailable(self):
        """Test explanation when core_ai returns None (no AI available)."""
        with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock, return_value=None):
            resp = client.post("/explain/", json={
                "prediction_type": "Diabetes",
                "input_data": {"glucose": 140},
                "prediction_result": "High Risk"
            })
            assert resp.status_code == 503
            assert resp.json()["detail"] == "AI Service Unavailable"

    def test_explain_parsing_fallback(self):
        """Test fallback when response doesn't match expected format."""
        raw_text = "Some unstructured response about heart health risk factors"

        with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock, return_value=raw_text):
            resp = client.post("/explain/", json={
                "prediction_type": "Heart",
                "input_data": {"bp": 140},
                "prediction_result": "Low Risk"
            })

            assert resp.status_code == 200
            data = resp.json()
            # Should use fallback — the raw text becomes the explanation
            assert data["explanation"] == raw_text
            assert data["lifestyle_tips"] == ["Consult a doctor for personalized advice."]

    def test_explain_exception_handling(self):
        """Test exception handling during explanation generation."""
        with patch(
            "backend.explanation.core_ai.generate",
            new_callable=AsyncMock,
            side_effect=Exception("API timeout with synthetic patient context"),
        ):
            resp = client.post("/explain/", json={
                "prediction_type": "Liver",
                "input_data": {"bilirubin": 2.0},
                "prediction_result": "Normal"
            })
            assert resp.status_code == 500
            assert resp.json()["detail"] == "Failed to generate explanation"
            assert "API timeout" not in str(resp.json())
            assert "synthetic patient context" not in str(resp.json())

    def test_explain_empty_tips(self):
        """Test when TIPS section is present but empty."""
        mock_text = "EXPLANATION: All values normal.\nTIPS:\n"

        with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock, return_value=mock_text):
            resp = client.post("/explain/", json={
                "prediction_type": "Kidney",
                "input_data": {"creatinine": 0.9},
                "prediction_result": "Low Risk"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["explanation"] == "All values normal."
