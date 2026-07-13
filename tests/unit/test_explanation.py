"""
Test for backend/explanation.py — core_ai-backed explanation service.
"""
from unittest.mock import AsyncMock, patch

import pytest

from backend.explanation import ExplanationRequest, explain_prediction


@pytest.mark.asyncio(loop_scope="session")
async def test_explain_prediction():
    req = ExplanationRequest(
        prediction_type="Diabetes",
        input_data={"glucose": 200},
        prediction_result="High Risk"
    )

    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "EXPLANATION: Valid Explanation\nTIPS:\n- Tip 1"
        res = await explain_prediction(req)

    assert res.explanation == "Valid Explanation"
    assert len(res.lifestyle_tips) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_explain_prediction_heart():
    """Test explanation for heart disease prediction."""
    req = ExplanationRequest(
        prediction_type="Heart",
        input_data={"age": 55, "cholesterol": 280},
        prediction_result="Heart Disease Detected"
    )

    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "EXPLANATION: Heart risk factors identified\nTIPS:\n- Exercise\n- Diet"
        res = await explain_prediction(req)

    assert res.explanation == "Heart risk factors identified"
    assert len(res.lifestyle_tips) == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_explain_prediction_empty_tips():
    """Test explanation when AI returns no tips."""
    req = ExplanationRequest(
        prediction_type="Liver",
        input_data={"bilirubin": 3.5},
        prediction_result="Liver Disease Detected"
    )

    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "EXPLANATION: Liver markers elevated"
        res = await explain_prediction(req)

    assert res.explanation == "Liver markers elevated"
    assert res.lifestyle_tips == []


@pytest.mark.asyncio(loop_scope="session")
async def test_explain_prediction_ai_failure():
    """Test explanation when AI generation fails."""
    req = ExplanationRequest(
        prediction_type="Kidney",
        input_data={"creatinine": 2.5},
        prediction_result="CKD Detected"
    )

    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ""  # Empty response from AI
        res = await explain_prediction(req)

    # Should handle gracefully
    assert res.explanation == "" or res.explanation is not None

