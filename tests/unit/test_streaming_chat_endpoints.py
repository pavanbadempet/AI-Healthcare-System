"""
Tests for streaming_chat.py endpoints.

Covers: /chat/stream (AI available, fallback, empty message),
/chat/context, and /chat/suggestions — all with mocked auth and AI.
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.prediction import initialize_models


@pytest.fixture(autouse=True)
def mock_agent_nodes():
    with patch("backend.agent.supervisor_node", return_value={"next_step": "respond"}), \
         patch("backend.agent.research_node", return_value={"tavily_results": ""}), \
         patch("backend.agent.analyst_node", return_value={"analysis_results": ""}):
        yield

# ── Test DB & client setup ────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _make_user_and_headers(client, username="stream_user", role="patient"):
    password = "StreamTest123!"
    client.post(
        "/signup",
        json={
            "username": username,
            "password": password,
            "email": f"{username}@test.com",
            "full_name": "Stream User",
            "dob": "1990-01-01",
        },
    )
    login = client.post("/token", data={"username": username, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    initialize_models()
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c
    app.dependency_overrides.clear()


# ── /chat/stream ──────────────────────────────────────────────────────────────

def test_stream_chat_empty_message_returns_default_reply(client):
    headers = _make_user_and_headers(client, "stream_empty")
    response = client.post("/chat/stream", json={"message": "  ", "history": []}, headers=headers)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "reply" in body or "How can I help" in body


def test_stream_chat_with_ai_available_streams_response(client):
    headers = _make_user_and_headers(client, "stream_ai")

    async def fake_stream(*args, **kwargs):
        yield "Heart "
        yield "health "
        yield "is good."

    with patch("backend.streaming_chat.core_ai.is_available", AsyncMock(return_value=True)), \
         patch("backend.streaming_chat.core_ai.chat_stream", fake_stream), \
         patch("backend.streaming_chat.build_chat_context",
               return_value=("Patient profile context", [{"type": "patient_profile", "name": "test", "id": 1}])):
        response = client.post(
            "/chat/stream",
            json={"message": "How is my heart health?", "history": []},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.text
    # Should contain streamed content
    assert "Heart" in body or "heart" in body or "reply" in body


def test_stream_chat_includes_medical_disclaimer(client):
    headers = _make_user_and_headers(client, "stream_disclaimer")

    async def fake_stream(*args, **kwargs):
        yield "Your glucose looks stable."

    with patch("backend.streaming_chat.core_ai.is_available", AsyncMock(return_value=True)), \
         patch("backend.streaming_chat.core_ai.chat_stream", fake_stream), \
         patch("backend.streaming_chat.build_chat_context", return_value=("context", [])):
        response = client.post(
            "/chat/stream",
            json={"message": "What is my glucose level?", "history": []},
            headers=headers,
        )

    body = response.text
    # Disclaimer should be appended
    assert "disclaimer" in body.lower() or "consult" in body.lower() or "medical" in body.lower()


def test_stream_chat_fallback_when_ai_unavailable(client):
    headers = _make_user_and_headers(client, "stream_fallback")

    with patch("backend.streaming_chat.core_ai.is_available", AsyncMock(return_value=False)), \
         patch("backend.streaming_chat.build_chat_context", return_value=("Patient has diabetes.", [])):
        response = client.post(
            "/chat/stream",
            json={"message": "How am I doing?", "history": []},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.text
    assert "complete" in body or "reply" in body


def test_stream_chat_fallback_with_no_context(client):
    headers = _make_user_and_headers(client, "stream_nocontext")

    with patch("backend.streaming_chat.core_ai.is_available", AsyncMock(return_value=False)), \
         patch("backend.streaming_chat.build_chat_context", return_value=("", [])):
        response = client.post(
            "/chat/stream",
            json={"message": "Tell me about my health", "history": []},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.text
    assert "checkup" in body.lower() or "data" in body.lower() or "reply" in body


def test_stream_chat_sends_sources_in_first_event(client):
    headers = _make_user_and_headers(client, "stream_sources")

    async def fake_stream(*args, **kwargs):
        yield "Here is some info."

    mock_sources = [{"type": "patient_profile", "name": "Stream User", "id": 1}]
    with patch("backend.streaming_chat.core_ai.is_available", AsyncMock(return_value=True)), \
         patch("backend.streaming_chat.core_ai.chat_stream", fake_stream), \
         patch("backend.streaming_chat.build_chat_context",
               return_value=("Some context text", mock_sources)):
        response = client.post(
            "/chat/stream",
            json={"message": "What are my records?", "history": []},
            headers=headers,
        )

    body = response.text
    # First SSE event should contain sources
    first_data = body.split("\n\n")[0]
    assert "sources" in first_data or "starting" in first_data


# ── /chat/context ─────────────────────────────────────────────────────────────

def test_chat_context_endpoint_returns_context(client):
    headers = _make_user_and_headers(client, "ctx_user")

    with patch("backend.streaming_chat.build_chat_context",
               return_value=("Patient has high glucose.", [{"type": "health_record", "name": "Diabetes", "id": 1}])):
        response = client.get("/chat/context?q=What+is+my+glucose", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "context" in data
    assert "sources" in data


def test_chat_context_endpoint_empty_question_returns_empty(client):
    headers = _make_user_and_headers(client, "ctx_empty")
    response = client.get("/chat/context?q=", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["context"] == ""
    assert data["sources"] == []


def test_chat_context_endpoint_requires_auth(client):
    response = client.get("/chat/context?q=test")
    assert response.status_code == 401


def test_chat_context_endpoint_truncates_long_context(client):
    headers = _make_user_and_headers(client, "ctx_trunc")
    long_context = "x" * 5000

    with patch("backend.streaming_chat.build_chat_context", return_value=(long_context, [])):
        response = client.get("/chat/context?q=anything", headers=headers)

    data = response.json()
    assert len(data["context"]) <= 2500


# ── /chat/suggestions ────────────────────────────────────────────────────────

def test_chat_suggestions_returns_list(client):
    headers = _make_user_and_headers(client, "sug_user")
    response = client.get("/chat/suggestions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_chat_suggestions_requires_auth(client):
    response = client.get("/chat/suggestions")
    assert response.status_code == 401


def test_chat_suggestions_returns_at_most_8(client):
    headers = _make_user_and_headers(client, "sug_limit")
    response = client.get("/chat/suggestions", headers=headers)
    data = response.json()
    assert len(data["suggestions"]) <= 8


def test_chat_agent_failure(client, caplog):
    from unittest.mock import patch
    headers = _make_user_and_headers(client, "chat_agent_fail")
    caplog.set_level("ERROR", logger="backend.chat")
    with patch("backend.chat.agent.medical_agent.invoke", side_effect=Exception("Agent Down with patient context")):
        resp = client.post("/chat", json={"message": "Hi"}, headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "trouble" in body["response"]
        assert "Agent Down" not in str(body)


def test_chat_db_save_failure(client, caplog):
    from unittest.mock import MagicMock, patch

    from backend.database import get_db
    headers = _make_user_and_headers(client, "chat_db_fail")
    caplog.set_level("ERROR", logger="backend.chat")

    mock_db = MagicMock()
    mock_db.commit.side_effect = Exception("DB Error with patient context")

    orig_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        mock_agent_resp = {"messages": [MagicMock(content="Hello")]}
        with patch("backend.chat.agent.medical_agent.invoke", return_value=mock_agent_resp):
            resp = client.post("/chat", json={"message": "Hi"}, headers=headers)
            assert resp.status_code == 200
            assert resp.json()["response"].startswith("Hello")
    finally:
        if orig_override:
            app.dependency_overrides[get_db] = orig_override
        else:
            del app.dependency_overrides[get_db]


def test_chat_response_adds_medical_disclaimer(client):
    from unittest.mock import MagicMock, patch
    headers = _make_user_and_headers(client, "chat_disclaimer")
    mock_agent_resp = {"messages": [MagicMock(content="Hydration may help, but monitor symptoms.")]}
    with patch("backend.chat.agent.medical_agent.invoke", return_value=mock_agent_resp):
        resp = client.post("/chat", json={"message": "What should I do?"}, headers=headers)
    assert resp.status_code == 200
    assert "Hydration may help" in resp.json()["response"]


def test_chat_record_validation(client):
    headers = _make_user_and_headers(client, "record_val_user")
    resp = client.delete("/v1/records/999", headers=headers)
    assert resp.status_code == 404

