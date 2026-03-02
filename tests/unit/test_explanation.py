"""
Test for backend/explanation.py — core_ai-backed explanation service.
"""
import pytest
from unittest.mock import patch, AsyncMock
from backend.explanation import explain_prediction, ExplanationRequest


@pytest.mark.asyncio(loop_scope="session")
async def test_explain_prediction():
    req = ExplanationRequest(
        prediction_type="Diabetes",
        input_data={"glucose": 200},
        prediction_result="High Risk"
    )

    # Mock core_ai.generate to return a structured response
    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "EXPLANATION: Valid Explanation\nTIPS:\n- Tip 1"
        res = await explain_prediction(req)

    assert res.explanation == "Valid Explanation"
    assert len(res.lifestyle_tips) == 1

