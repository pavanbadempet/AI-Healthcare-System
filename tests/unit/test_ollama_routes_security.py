from unittest.mock import AsyncMock, patch

from backend import auth, models


def _auth_headers(db_session, username: str, role: str) -> dict[str, str]:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()

    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}


def test_ollama_delete_model_requires_authentication(client):
    with patch(
        "backend.ollama_routes.core_ai.delete_ollama_model",
        new_callable=AsyncMock,
        return_value=(True, 200, ""),
    ) as delete_model:
        response = client.request("DELETE", "/ai/models", json={"name": "llama3.2"})

    assert response.status_code == 401
    delete_model.assert_not_awaited()


def test_ollama_list_models_requires_authentication(client):
    with patch("backend.ollama_routes.core_ai.is_ollama_running", new_callable=AsyncMock, return_value=False) as is_running:
        response = client.get("/ai/models")

    assert response.status_code == 401
    is_running.assert_not_awaited()


def test_ollama_library_requires_authentication(client):
    response = client.get("/ai/models/library")

    assert response.status_code == 401


def test_ollama_list_models_requires_admin_role(client, db_session):
    headers = _auth_headers(db_session, "model_list_patient", "patient")

    with patch("backend.ollama_routes.core_ai.is_ollama_running", new_callable=AsyncMock, return_value=False) as is_running:
        response = client.get("/ai/models", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
    is_running.assert_not_awaited()


def test_ollama_library_requires_admin_role(client, db_session):
    headers = _auth_headers(db_session, "model_library_patient", "patient")

    response = client.get("/ai/models/library", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_ollama_delete_model_requires_admin_role(client, db_session):
    headers = _auth_headers(db_session, "model_patient", "patient")

    with patch(
        "backend.ollama_routes.core_ai.delete_ollama_model",
        new_callable=AsyncMock,
        return_value=(True, 200, ""),
    ) as delete_model:
        response = client.request("DELETE", "/ai/models", json={"name": "llama3.2"}, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
    delete_model.assert_not_awaited()


def test_ollama_delete_model_allows_admin(client, db_session):
    headers = _auth_headers(db_session, "model_admin", "admin")

    with patch(
        "backend.ollama_routes.core_ai.delete_ollama_model",
        new_callable=AsyncMock,
        return_value=(True, 200, ""),
    ) as delete_model:
        response = client.request("DELETE", "/ai/models", json={"name": "llama3.2"}, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"success": True}
    delete_model.assert_awaited_once_with("llama3.2")


def test_ollama_delete_model_hides_backend_error_details(client, db_session):
    headers = _auth_headers(db_session, "model_error_admin", "admin")
    sensitive_error = "delete failed api_key=ollama-secret path=C:/Users/pavan/model"

    with patch(
        "backend.ollama_routes.core_ai.delete_ollama_model",
        new_callable=AsyncMock,
        return_value=(False, 500, sensitive_error),
    ) as delete_model:
        response = client.request("DELETE", "/ai/models", json={"name": "llama3.2"}, headers=headers)

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to delete model"
    assert sensitive_error not in response.text
    assert "ollama-secret" not in response.text
    assert "C:/Users/pavan/model" not in response.text
    delete_model.assert_awaited_once_with("llama3.2")


def test_ollama_pull_model_requires_admin_role(client, db_session):
    headers = _auth_headers(db_session, "pull_patient", "patient")

    with patch("backend.ollama_routes.core_ai.is_ollama_running", new_callable=AsyncMock, return_value=True), \
         patch("backend.ollama_routes.core_ai.stream_ollama_model_pull") as stream_pull:
        response = client.post("/ai/models/pull", json={"name": "llama3.2"}, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
    stream_pull.assert_not_called()
