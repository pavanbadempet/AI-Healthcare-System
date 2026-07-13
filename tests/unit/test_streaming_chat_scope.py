from unittest.mock import AsyncMock, patch

from backend import auth, models


def _create_user(db_session, username: str, role: str) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}


def _create_health_record(
    db_session,
    user: models.User,
    prediction: str,
    record_type: str = "diabetes",
) -> models.HealthRecord:
    record = models.HealthRecord(
        user_id=user.id,
        record_type=record_type,
        data="{}",
        prediction=prediction,
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


def test_stream_chat_all_scope_is_patient_scoped_for_patient(client, db_session):
    patient = _create_user(db_session, "stream_scope_patient", "patient")
    other_patient = _create_user(db_session, "stream_scope_other", "patient")
    _create_health_record(db_session, patient, "Own stream diabetes record")
    _create_health_record(db_session, other_patient, "Other stream diabetes record")

    with patch("backend.streaming_chat.core_ai.is_available", new_callable=AsyncMock, return_value=False):
        response = client.post(
            "/chat/stream",
            json={"message": "diabetes cases", "rag_scope": "all"},
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert "Global Hospital Database" not in response.text
    assert "Own stream diabetes record" in response.text
    assert "Other stream diabetes record" not in response.text


def test_stream_chat_all_scope_allows_doctor_global_context(client, db_session):
    doctor = _create_user(db_session, "stream_scope_doctor", "doctor")
    patient = _create_user(db_session, "stream_scope_global_patient", "patient")
    _create_health_record(db_session, patient, "Global stream diabetes record")

    with patch("backend.streaming_chat.core_ai.is_available", new_callable=AsyncMock, return_value=False):
        response = client.post(
            "/chat/stream",
            json={"message": "diabetes cases", "rag_scope": "all"},
            headers=_auth_headers(doctor.username),
        )

    assert response.status_code == 200
    assert "Global Hospital Database" in response.text
    assert "Global stream diabetes record" in response.text


def test_stream_chat_hides_ai_stream_error_details(client, db_session, caplog):
    patient = _create_user(db_session, "stream_error_patient", "patient")
    sensitive_error = "stream failed api_key=stream-secret patient_name=Sensitive User"
    caplog.set_level("ERROR", logger="backend.streaming_chat")

    async def failing_chat_stream(*args, **kwargs):
        raise Exception(sensitive_error)
        yield ""

    with patch("backend.streaming_chat.core_ai.is_available", new_callable=AsyncMock, return_value=True), \
         patch("backend.streaming_chat.core_ai.chat_stream", failing_chat_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "What should I do?"},
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert "AI stream failed. Please try again later." in response.text
    assert sensitive_error not in response.text
    assert "stream-secret" not in response.text
    assert "Sensitive User" not in response.text
    assert sensitive_error not in caplog.text
    assert "stream-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_stream_chat_appends_medical_disclaimer(client, db_session):
    patient = _create_user(db_session, "stream_disclaimer_patient", "patient")

    async def chat_stream(*args, **kwargs):
        yield "Drink water and monitor your symptoms."

    with patch("backend.streaming_chat.core_ai.is_available", new_callable=AsyncMock, return_value=True), \
         patch("backend.streaming_chat.core_ai.chat_stream", chat_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "What should I do?"},
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert "Drink water and monitor your symptoms." in response.text
    assert "This is AI-generated information and is not a medical diagnosis." in response.text
    assert "qualified healthcare professional" in response.text


def test_stream_chat_fallback_includes_medical_disclaimer(client, db_session):
    patient = _create_user(db_session, "stream_fallback_disclaimer_patient", "patient")
    _create_health_record(db_session, patient, "Fallback diabetes record")

    with patch("backend.streaming_chat.core_ai.is_available", new_callable=AsyncMock, return_value=False):
        response = client.post(
            "/chat/stream",
            json={"message": "diabetes advice"},
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert "Fallback diabetes record" in response.text
    assert "This is AI-generated information and is not a medical diagnosis." in response.text
    assert "qualified healthcare professional" in response.text


def test_patient_stream_chat_ignores_cloud_provider_override(client, db_session):
    patient = _create_user(db_session, "stream_cloud_override_patient", "patient")
    _create_health_record(db_session, patient, "Local fallback record")
    chat_stream_calls = []

    async def chat_stream(*args, **kwargs):
        chat_stream_calls.append(kwargs)
        yield "cloud provider response"

    with patch("backend.streaming_chat.core_ai.is_available", new_callable=AsyncMock, return_value=False), \
         patch("backend.streaming_chat.core_ai.chat_stream", chat_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "diabetes advice"},
            headers={
                **_auth_headers(patient.username),
                "x-ai-provider": "openai",
                "x-ai-api-key": "patient-cloud-secret",
            },
        )

    assert response.status_code == 200
    assert chat_stream_calls == []
    assert "Local fallback record" in response.text
    assert "cloud provider response" not in response.text
    assert "patient-cloud-secret" not in response.text
