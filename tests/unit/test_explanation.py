import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from backend.explanation import explain_prediction, ExplanationRequest

@pytest.fixture
def mock_genai():
    # Only useful if we patch the class, but we patch the instance now.
    pass

@pytest.mark.asyncio
async def test_explain_prediction():
    req = ExplanationRequest(
        prediction_type="Diabetes",
        input_data={"glucose": 200},
        prediction_result="High Risk"
    )
    
    # Create a MagicMock for the model
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "EXPLANATION: Valid Explanation\nTIPS:\n- Tip 1"
    
    # Mock synchronous generate_content
    mock_model.generate_content.return_value = mock_resp
    
    # Inject the mock model directly
    res = await explain_prediction(req, injected_model=mock_model)
     
    assert res.explanation == "Valid Explanation"
    assert len(res.lifestyle_tips) == 1
