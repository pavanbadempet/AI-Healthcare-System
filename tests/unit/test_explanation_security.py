from unittest.mock import AsyncMock, patch

from backend import auth, models


def _auth_headers(db_session, username: str = "explain_user") -> dict[str, str]:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
    )
    db_session.add(user)
    db_session.commit()

    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}


def _payload() -> dict:
    return {
        "prediction_type": "Diabetes",
        "input_data": {"glucose": 140, "bmi": 28},
        "prediction_result": "High Risk",
    }


def test_ai_prediction_explanation_requires_authentication(client):
    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock) as generate:
        response = client.post("/explain/", json=_payload())

    assert response.status_code == 401
    generate.assert_not_awaited()


def test_ai_prediction_explanation_allows_authenticated_user(client, db_session):
    headers = _auth_headers(db_session)
    mock_text = (
        "EXPLANATION: Your glucose level is elevated.\n"
        "TIPS:\n"
        "- Reduce sugar intake\n"
        "- Exercise regularly"
    )

    with patch("backend.explanation.core_ai.generate", new_callable=AsyncMock, return_value=mock_text) as generate:
        response = client.post("/explain/", json=_payload(), headers=headers)

    assert response.status_code == 200
    assert response.json()["explanation"] == "Your glucose level is elevated."
    assert response.json()["lifestyle_tips"] == ["Reduce sugar intake", "Exercise regularly"]
    generate.assert_awaited_once()


def test_ai_prediction_explanation_hides_provider_error_details(client, db_session, caplog):
    headers = _auth_headers(db_session, username="explain_error_user")
    sensitive_error = "Provider failure with synthetic patient context"
    caplog.set_level("ERROR", logger="backend.explanation")

    with patch(
        "backend.explanation.core_ai.generate",
        new_callable=AsyncMock,
        side_effect=Exception(sensitive_error),
    ) as generate:
        response = client.post("/explain/", json=_payload(), headers=headers)

    body_text = str(response.json())
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to generate explanation"
    assert sensitive_error not in body_text
    assert "synthetic patient context" not in body_text
    assert sensitive_error not in caplog.text
    assert "synthetic patient context" not in caplog.text
    generate.assert_awaited_once()
