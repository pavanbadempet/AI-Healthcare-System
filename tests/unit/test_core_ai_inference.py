"""
Tests for core_ai.py inference paths.

Covers: model resolution, fallback chain, public API (generate/chat/chat_stream),
Gemini multi-turn via start_chat, embed_text_async, generate_vision_content_async,
is_available, Ollama management helpers, and the model list TTL cache.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend import core_ai

# ── helpers ──────────────────────────────────────────────────────────────────


def _make_ollama_response(content: str, status: int = 200):
    """Return a fake httpx Response-like object for Ollama chat/generate."""
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {"message": {"content": content}}
    mock.text = content
    return mock


def _make_generate_response(text: str, status: int = 200):
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {"response": text, "done_reason": "stop"}
    mock.text = text
    return mock


# ── Model list cache ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_ollama_models_returns_list():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "llama3.2"}, {"name": "mistral"}]}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    # Clear the cache first
    core_ai._model_cache.clear()

    with patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client):
        models = await core_ai.get_ollama_models()

    assert "llama3.2" in models
    assert "mistral" in models


@pytest.mark.asyncio
async def test_get_ollama_models_returns_empty_on_failure():
    core_ai._model_cache.clear()

    with patch(
        "backend.core_ai.httpx.AsyncClient",
        side_effect=Exception("connection refused"),
    ):
        models = await core_ai.get_ollama_models()

    assert models == []


@pytest.mark.asyncio
async def test_get_ollama_models_uses_cache():
    """Second call within TTL should not hit the network."""
    core_ai._model_cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "llama3.2"}]}

    call_count = 0

    class CountingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url):
            nonlocal call_count
            call_count += 1
            return mock_resp

    with patch("backend.core_ai.httpx.AsyncClient", return_value=CountingClient()):
        await core_ai.get_ollama_models()
        await core_ai.get_ollama_models()  # Should use cache

    assert call_count == 1


# ── Model resolution ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_ollama_model_exact_match():
    with patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=["llama3.2", "mistral"])):
        result = await core_ai._resolve_ollama_model("llama3.2")
    assert result == "llama3.2"


@pytest.mark.asyncio
async def test_resolve_ollama_model_fuzzy_match():
    with patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=["llama3.2:3b", "mistral"])):
        result = await core_ai._resolve_ollama_model("llama3.2")
    assert result == "llama3.2:3b"


@pytest.mark.asyncio
async def test_resolve_ollama_model_fallback_to_first():
    with patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=["mistral", "phi3"])):
        result = await core_ai._resolve_ollama_model("nonexistent-model")
    assert result == "mistral"


@pytest.mark.asyncio
async def test_resolve_ollama_model_no_models():
    with patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=[])):
        result = await core_ai._resolve_ollama_model("llama3.2")
    assert result is None


# ── is_available ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_is_available_true_when_ollama_has_models():
    with patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=["llama3.2"])):
        assert await core_ai.is_available() is True


@pytest.mark.asyncio
async def test_is_available_true_when_gemini_key_set():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=[])),
        patch("backend.core_ai.has_gemini_api_key", return_value=True),
    ):
        assert await core_ai.is_available() is True


@pytest.mark.asyncio
async def test_is_available_false_when_neither():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=[])),
        patch("backend.core_ai.has_gemini_api_key", return_value=False),
    ):
        assert await core_ai.is_available() is False


# ── has_gemini_api_key guard ──────────────────────────────────────────────────


def test_has_gemini_api_key_rejects_placeholder_values():
    for bad in ("", "dummy", "your_gemini_api_key_here", "placeholder", "your_key"):
        with patch("backend.core_ai.GOOGLE_API_KEY", bad):
            assert core_ai.has_gemini_api_key() is False


def test_has_gemini_api_key_accepts_real_key():
    with patch("backend.core_ai.GOOGLE_API_KEY", "AIzaSyRealKey12345"):
        assert core_ai.has_gemini_api_key() is True


# ── Ollama generate ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_ollama_returns_text():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_make_generate_response("Diabetes info"))

    with (
        patch("backend.core_ai._resolve_ollama_model", AsyncMock(return_value="llama3.2")),
        patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client),
    ):
        result = await core_ai._generate_ollama("What is diabetes?", system="You are a doctor.")

    assert result == "Diabetes info"


@pytest.mark.asyncio
async def test_generate_ollama_falls_back_to_chat_api_when_response_empty():
    # /api/generate returns empty response (no text, done_reason not "load")
    empty_resp = MagicMock()
    empty_resp.status_code = 200
    empty_resp.json.return_value = {"response": "", "done_reason": "stop"}

    # /api/chat fallback returns actual content
    chat_resp = _make_ollama_response("Chat fallback response")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    # First call is /api/generate (empty), second is /api/chat (content)
    mock_client.post = AsyncMock(side_effect=[empty_resp, chat_resp])

    with (
        patch("backend.core_ai._resolve_ollama_model", AsyncMock(return_value="llama3.2")),
        patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client),
    ):
        result = await core_ai._generate_ollama("prompt")

    assert result == "Chat fallback response"


# ── Ollama chat ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_ollama_returns_text():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_make_ollama_response("I am fine, thank you."))

    with (
        patch("backend.core_ai._resolve_ollama_model", AsyncMock(return_value="llama3.2")),
        patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client),
    ):
        result = await core_ai._chat_ollama([{"role": "user", "content": "How are you?"}])

    assert result == "I am fine, thank you."


@pytest.mark.asyncio
async def test_chat_ollama_raises_when_no_models():
    with patch("backend.core_ai._resolve_ollama_model", AsyncMock(return_value=None)):
        with pytest.raises(Exception, match="No Ollama models"):
            await core_ai._chat_ollama([{"role": "user", "content": "hi"}])


# ── Ollama stream ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_ollama_yields_chunks():
    lines = [
        b'{"message":{"content":"Hello"},"done":false}\n',
        b'{"message":{"content":" world"},"done":true}\n',
    ]

    async def fake_aiter_lines():
        for line in lines:
            yield line.decode().strip()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = fake_aiter_lines

    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.stream = MagicMock(return_value=mock_stream)

    with (
        patch("backend.core_ai._resolve_ollama_model", AsyncMock(return_value="llama3.2")),
        patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client),
    ):
        chunks = [c async for c in core_ai._stream_ollama([{"role": "user", "content": "hi"}])]

    assert chunks == ["Hello", " world"]


@pytest.mark.asyncio
async def test_stream_ollama_yields_error_when_no_model():
    with patch("backend.core_ai._resolve_ollama_model", AsyncMock(return_value=None)):
        chunks = [c async for c in core_ai._stream_ollama([{"role": "user", "content": "hi"}])]
    assert len(chunks) == 1
    assert "No Ollama models" in chunks[0]


# ── Gemini chat (multi-turn) ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_gemini_uses_start_chat_and_returns_text():
    mock_response = MagicMock()
    mock_response.text = "Gemini multi-turn reply"

    mock_session = MagicMock()
    mock_session.send_message = MagicMock(return_value=mock_response)

    mock_model = MagicMock()
    mock_model.start_chat = MagicMock(return_value=mock_session)

    with (
        patch("backend.core_ai._get_gemini_model", return_value=mock_model),
        patch("asyncio.to_thread", new=lambda fn, *args, **kwargs: asyncio.coroutine(lambda: fn(*args, **kwargs))()),
    ):
        # Use side_effect to properly await
        pass

    # Simpler approach: patch asyncio.to_thread to call sync directly
    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with (
        patch("backend.core_ai._get_gemini_model", return_value=mock_model),
        patch("backend.core_ai.asyncio.to_thread", new=fake_to_thread),
    ):
        result = await core_ai._chat_gemini(
            [{"role": "user", "content": "What is hypertension?"}], system="You are a medical assistant."
        )

    assert result == "Gemini multi-turn reply"
    # Verify start_chat was called (not generate_content with flattened string)
    mock_model.start_chat.assert_called_once()


@pytest.mark.asyncio
async def test_chat_gemini_injects_system_as_history():
    """System prompt should appear as a user/model exchange in the history, not a flat string."""
    captured_history = []

    mock_response = MagicMock()
    mock_response.text = "ok"

    mock_session = MagicMock()
    mock_session.send_message = MagicMock(return_value=mock_response)

    def capture_start_chat(history):
        captured_history.extend(history)
        return mock_session

    mock_model = MagicMock()
    mock_model.start_chat = capture_start_chat

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with (
        patch("backend.core_ai._get_gemini_model", return_value=mock_model),
        patch("backend.core_ai.asyncio.to_thread", new=fake_to_thread),
    ):
        await core_ai._chat_gemini([{"role": "user", "content": "hello"}], system="You are a doctor.")

    # System should be first history entry as user role
    assert captured_history[0]["role"] == "user"
    assert "You are a doctor." in captured_history[0]["parts"][0]


@pytest.mark.asyncio
async def test_chat_gemini_maps_assistant_role_to_model():
    """Messages with role='assistant' should be mapped to Gemini's 'model' role."""
    captured_history = []

    mock_response = MagicMock()
    mock_response.text = "ok"

    mock_session = MagicMock()
    mock_session.send_message = MagicMock(return_value=mock_response)

    def capture_start_chat(history):
        captured_history.extend(history)
        return mock_session

    mock_model = MagicMock()
    mock_model.start_chat = capture_start_chat

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    messages = [
        {"role": "user", "content": "What is my risk?"},
        {"role": "assistant", "content": "Your risk is low."},
        {"role": "user", "content": "How can I improve?"},
    ]

    with (
        patch("backend.core_ai._get_gemini_model", return_value=mock_model),
        patch("backend.core_ai.asyncio.to_thread", new=fake_to_thread),
    ):
        await core_ai._chat_gemini(messages)

    # The second message (assistant) should map to "model"
    roles_in_history = [entry["role"] for entry in captured_history]
    assert "model" in roles_in_history


@pytest.mark.asyncio
async def test_chat_gemini_returns_empty_when_no_model():
    with patch("backend.core_ai._get_gemini_model", return_value=None):
        result = await core_ai._chat_gemini([{"role": "user", "content": "hi"}])
    assert result == ""


# ── Public API: generate() ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_uses_ollama_when_available():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=["llama3.2"])),
        patch("backend.core_ai._generate_ollama", AsyncMock(return_value="Ollama says: glucose is sugar")),
    ):
        result = await core_ai.generate("What is glucose?")
    assert result == "Ollama says: glucose is sugar"


@pytest.mark.asyncio
async def test_generate_falls_back_to_gemini_when_ollama_empty():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=[])),
        patch("backend.core_ai.has_gemini_api_key", return_value=True),
        patch("backend.core_ai._generate_gemini", AsyncMock(return_value="Gemini says: glucose is sugar")),
    ):
        result = await core_ai.generate("What is glucose?")
    assert result == "Gemini says: glucose is sugar"


@pytest.mark.asyncio
async def test_generate_uses_explicit_cloud_provider():
    with patch("backend.core_ai._generate_cloud", AsyncMock(return_value="OpenAI answer")):
        result = await core_ai.generate("prompt", api_provider="openai", api_key="sk-test")
    assert result == "OpenAI answer"


@pytest.mark.asyncio
async def test_generate_returns_mock_fallback_when_all_unavailable():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=[])),
        patch("backend.core_ai.has_gemini_api_key", return_value=False),
    ):
        result = await core_ai.generate("prompt")
    assert "offline mode" in result.lower() or "mock" in result.lower()


# ── Public API: chat() ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_uses_ollama_when_available():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=["llama3.2"])),
        patch("backend.core_ai._chat_ollama", AsyncMock(return_value="Ollama chat reply")),
    ):
        result = await core_ai.chat([{"role": "user", "content": "hi"}])
    assert result == "Ollama chat reply"


@pytest.mark.asyncio
async def test_chat_falls_back_to_gemini_on_ollama_failure():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=["llama3.2"])),
        patch("backend.core_ai._chat_ollama", AsyncMock(side_effect=Exception("timeout"))),
        patch("backend.core_ai.has_gemini_api_key", return_value=True),
        patch("backend.core_ai._chat_gemini", AsyncMock(return_value="Gemini fallback")),
    ):
        result = await core_ai.chat([{"role": "user", "content": "hi"}])
    assert result == "Gemini fallback"


@pytest.mark.asyncio
async def test_chat_returns_mock_when_all_unavailable():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=[])),
        patch("backend.core_ai.has_gemini_api_key", return_value=False),
    ):
        result = await core_ai.chat([{"role": "user", "content": "hi"}])
    assert "offline mode" in result.lower()


@pytest.mark.asyncio
async def test_chat_explicit_cloud_provider():
    with patch("backend.core_ai._chat_cloud", AsyncMock(return_value="Anthropic reply")):
        result = await core_ai.chat(
            [{"role": "user", "content": "hi"}], api_provider="anthropic", api_key="sk-ant-test"
        )
    assert result == "Anthropic reply"


# ── Public API: chat_stream() ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_stream_yields_ollama_chunks():
    async def fake_stream(*args, **kwargs):
        yield "chunk1"
        yield "chunk2"

    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=["llama3.2"])),
        patch("backend.core_ai._stream_ollama", fake_stream),
    ):
        chunks = [c async for c in core_ai.chat_stream([{"role": "user", "content": "hi"}])]

    assert "".join(chunks) == "chunk1chunk2"


@pytest.mark.asyncio
async def test_chat_stream_falls_back_to_gemini():
    async def fake_gemini_stream(*args, **kwargs):
        yield "Gemini chunk"

    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=[])),
        patch("backend.core_ai.has_gemini_api_key", return_value=True),
        patch("backend.core_ai._stream_gemini", fake_gemini_stream),
    ):
        chunks = [c async for c in core_ai.chat_stream([{"role": "user", "content": "hi"}])]

    assert "Gemini chunk" in "".join(chunks)


@pytest.mark.asyncio
async def test_chat_stream_yields_mock_when_all_unavailable():
    with (
        patch("backend.core_ai.get_ollama_models", AsyncMock(return_value=[])),
        patch("backend.core_ai.has_gemini_api_key", return_value=False),
    ):
        chunks = [c async for c in core_ai.chat_stream([{"role": "user", "content": "hi"}])]

    combined = "".join(chunks)
    assert "offline mode" in combined.lower()


# ── embed_text_async ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_embed_text_async_returns_vector():
    fake_vector = [0.1] * 768
    with patch("backend.core_ai.embed_text", return_value=fake_vector):
        result = await core_ai.embed_text_async("clinical note")
    assert result == fake_vector


@pytest.mark.asyncio
async def test_embed_text_async_returns_zero_vector_when_no_key():
    with patch("backend.core_ai.has_gemini_api_key", return_value=False):
        result = await core_ai.embed_text_async("note")
    assert result == [0.0] * 768
    assert len(result) == 768


# ── generate_vision_content_async ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_vision_content_async_returns_text():
    with patch("backend.core_ai.generate_vision_content", return_value="X-ray shows clear lungs"):
        result = await core_ai.generate_vision_content_async("Analyze this X-ray", object())
    assert result == "X-ray shows clear lungs"


@pytest.mark.asyncio
async def test_generate_vision_content_async_returns_empty_when_no_key():
    with patch("backend.core_ai.has_gemini_api_key", return_value=False):
        result = await core_ai.generate_vision_content_async("prompt", object())
    assert result == ""


# ── Ollama management helpers ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_is_ollama_running_true():
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client):
        result = await core_ai.is_ollama_running()
    assert result is True


@pytest.mark.asyncio
async def test_is_ollama_running_false_on_connection_error():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=Exception("refused"))

    with patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client):
        result = await core_ai.is_ollama_running()
    assert result is False


@pytest.mark.asyncio
async def test_delete_ollama_model_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = ""

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.request = AsyncMock(return_value=mock_resp)

    with patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client):
        success, status, text = await core_ai.delete_ollama_model("llama3.2")

    assert success is True
    assert status == 200


@pytest.mark.asyncio
async def test_delete_ollama_model_failure_on_exception():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.request = AsyncMock(side_effect=Exception("network error"))

    with patch("backend.core_ai.httpx.AsyncClient", return_value=mock_client):
        success, status, text = await core_ai.delete_ollama_model("llama3.2")

    assert success is False
    assert status == 500
    assert text == core_ai.OLLAMA_DELETE_FAILURE_DETAIL
