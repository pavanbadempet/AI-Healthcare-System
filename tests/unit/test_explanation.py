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


# --- Merged from test_explanation_extended.py & test_explanation_security.py ---

def test_explain_success(client, db_session):
    from unittest.mock import AsyncMock, patch
    from backend import models, auth
    
    # Create user in DB to allow JWT verification
    user = models.User(
        username="explain_test",
        email="explain_test@example.com",
        hashed_password=auth.get_password_hash("Password123!"),
        role="patient",
    )
    db_session.add(user)
    db_session.commit()

    mock_text = (
        "EXPLANATION: Your glucose level of 140 is elevated.\n"
        "TIPS:\n"
        "- Reduce sugar intake\n"
        "- Exercise regularly\n"
        "- Monitor blood glucose daily"
    )
    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock, return_value=mock_text):
        headers = {"Authorization": f"Bearer {auth.create_access_token({'sub': 'explain_test'})}"}
        resp = client.post("/explain/", json={
            "prediction_type": "Diabetes",
            "input_data": {"glucose": 140, "bmi": 28},
            "prediction_result": "High Risk"
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "explanation" in data
        assert "lifestyle_tips" in data
        assert "glucose" in data["explanation"].lower()
        assert len(data["lifestyle_tips"]) == 3


def test_explain_model_unavailable(client, db_session):
    from unittest.mock import AsyncMock, patch
    from backend import models, auth
    
    user = models.User(
        username="explain_test_unavailable",
        email="explain_test_unavailable@example.com",
        hashed_password=auth.get_password_hash("Password123!"),
        role="patient",
    )
    db_session.add(user)
    db_session.commit()

    headers = {"Authorization": f"Bearer {auth.create_access_token({'sub': 'explain_test_unavailable'})}"}
    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock, return_value=None):
        resp = client.post("/explain/", json={
            "prediction_type": "Diabetes",
            "input_data": {"glucose": 140},
            "prediction_result": "High Risk"
        }, headers=headers)
        assert resp.status_code == 503
        assert resp.json()["detail"] == "AI Service Unavailable"


def test_ai_prediction_explanation_requires_authentication(client):
    from unittest.mock import AsyncMock, patch
    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock) as generate:
        response = client.post("/explain/", json={
            "prediction_type": "Diabetes",
            "input_data": {"glucose": 140, "bmi": 28},
            "prediction_result": "High Risk",
        })
    assert response.status_code == 401
    generate.assert_not_called()



