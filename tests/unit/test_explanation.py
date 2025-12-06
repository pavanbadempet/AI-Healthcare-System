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
    
    # Patch the global 'model' object in backend.explanation
    with patch("backend.explanation.model") as mock_model_instance:
        mock_resp = MagicMock()
        mock_resp.text = "EXPLANATION: Valid Explanation\nTIPS:\n- Tip 1"
        
        # FIX: The code uses synchronous generate_content, NOT async
        # We Mock the synchronous method
        mock_model_instance.generate_content.return_value = mock_resp
        
        # No json.loads patching needed as per code inspection (custom text parsing)
        
        res = await explain_prediction(req)
         
        assert res.explanation == "Valid Explanation"
        assert len(res.lifestyle_tips) == 1
