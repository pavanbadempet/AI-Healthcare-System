from unittest.mock import AsyncMock, patch

import pytest

from backend import core_ai


class FailingAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        raise Exception("connection failed token=core-ai-secret patient_name=Sensitive User")

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_ollama_pull_stream_hides_backend_error_details():
    with patch("backend.core_ai.httpx.AsyncClient", FailingAsyncClient):
        events = [event async for event in core_ai.stream_ollama_model_pull("llama3.2")]

    assert events == [{"error": "Failed to pull model"}]


@pytest.mark.asyncio
async def test_ollama_chat_stream_hides_backend_error_details(caplog):
    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai._resolve_ollama_model", return_value="llama3.2"), \
         patch("backend.core_ai.httpx.AsyncClient", FailingAsyncClient):
        chunks = [chunk async for chunk in core_ai._stream_ollama([{"role": "user", "content": "hi"}])]

    assert chunks == ["**SYSTEM ERROR:** AI stream failed. Please try again later."]
    assert "core-ai-secret" not in chunks[0]
    assert "Sensitive User" not in chunks[0]
    assert "core-ai-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


@pytest.mark.asyncio
async def test_ollama_model_details_hides_backend_error_details(caplog):
    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai.httpx.AsyncClient", FailingAsyncClient):
        result = await core_ai.list_ollama_model_details()

    assert result == []
    assert "core-ai-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


@pytest.mark.asyncio
async def test_generate_ollama_hides_backend_error_details(caplog):
    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai._resolve_ollama_model", new_callable=AsyncMock, return_value="llama3.2"), \
         patch("backend.core_ai.httpx.AsyncClient", FailingAsyncClient):
        result = await core_ai._generate_ollama("prompt")

    assert result == ""
    assert "core-ai-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


@pytest.mark.asyncio
async def test_generate_cloud_hides_backend_error_details(caplog):
    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai.httpx.AsyncClient", FailingAsyncClient):
        result = await core_ai._generate_cloud(
            "prompt",
            system="",
            model=None,
            api_provider="openai",
            api_key="secret-api-key",
        )

    assert result == ""
    assert "core-ai-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text
    assert "secret-api-key" not in caplog.text


@pytest.mark.asyncio
async def test_chat_cloud_raises_generic_error_and_hides_backend_error_details(caplog):
    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai.httpx.AsyncClient", FailingAsyncClient):
        with pytest.raises(RuntimeError) as exc_info:
            await core_ai._chat_cloud(
                [{"role": "user", "content": "hi"}],
                system="",
                model=None,
                api_provider="openai",
                api_key="secret-api-key",
            )

    assert str(exc_info.value) == "Cloud AI request failed"
    assert "core-ai-secret" not in str(exc_info.value)
    assert "Sensitive User" not in str(exc_info.value)
    assert "secret-api-key" not in str(exc_info.value)
    assert "core-ai-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text
    assert "secret-api-key" not in caplog.text


def test_embed_text_hides_backend_error_details(caplog):
    sensitive_error = "embedding failed token=embedding-secret patient_name=Sensitive User"
    caplog.set_level("ERROR", logger="backend.core_ai")

    with patch("backend.core_ai.GOOGLE_API_KEY", "real-key"), \
         patch("google.generativeai.configure"), \
         patch("google.generativeai.embed_content", side_effect=Exception(sensitive_error)):
        result = core_ai.embed_text("clinical note", task_type="retrieval_document")

    assert result == [0.0] * 768
    assert sensitive_error not in caplog.text
    assert "embedding-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_generate_vision_content_hides_backend_error_details(caplog):
    sensitive_error = "vision failed token=vision-secret patient_name=Sensitive User"
    caplog.set_level("ERROR", logger="backend.core_ai")

    with patch("backend.core_ai.GOOGLE_API_KEY", "real-key"), \
         patch("backend.core_ai.has_gemini_api_key", return_value=True), \
         patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel", side_effect=Exception(sensitive_error)):
        result = core_ai.generate_vision_content("prompt", object())

    assert result == ""
    assert sensitive_error not in caplog.text
    assert "vision-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_get_gemini_model_hides_initialization_error_details(caplog):
    sensitive_error = "gemini init failed token=gemini-secret patient_name=Sensitive User"
    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai.GOOGLE_API_KEY", "real-key"), \
         patch("backend.core_ai._gemini_model", None), \
         patch("backend.core_ai._gemini_configured", False), \
         patch("google.generativeai.configure", side_effect=Exception(sensitive_error)):
        result = core_ai._get_gemini_model()

    assert result is None
    assert sensitive_error not in caplog.text
    assert "gemini-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


@pytest.mark.asyncio
async def test_gemini_generate_hides_backend_error_details(caplog):
    sensitive_error = "gemini failed token=gemini-secret patient_name=Sensitive User"

    class FailingModel:
        def generate_content(self, prompt):
            raise Exception(sensitive_error)

    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai._get_gemini_model", return_value=FailingModel()):
        result = await core_ai._generate_gemini("prompt")

    assert result == ""
    assert sensitive_error not in caplog.text
    assert "gemini-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


@pytest.mark.asyncio
async def test_chat_fallback_hides_ollama_error_details(caplog):
    sensitive_error = "ollama failed token=ollama-secret patient_name=Sensitive User"
    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai.get_ollama_models", new_callable=AsyncMock, return_value=["llama3.2"]), \
         patch("backend.core_ai._chat_ollama", new_callable=AsyncMock, side_effect=Exception(sensitive_error)), \
         patch("backend.core_ai.GOOGLE_API_KEY", "real-key"), \
         patch("backend.core_ai._chat_gemini", new_callable=AsyncMock, return_value="Gemini fallback"):
        result = await core_ai.chat([{"role": "user", "content": "hi"}])

    assert result == "Gemini fallback"
    assert sensitive_error not in caplog.text
    assert "ollama-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


@pytest.mark.asyncio
async def test_gemini_chat_hides_backend_error_details(caplog):
    sensitive_error = "gemini chat failed token=gemini-secret patient_name=Sensitive User"

    class FailingModel:
        def generate_content(self, prompt):
            raise Exception(sensitive_error)

    caplog.set_level("WARNING", logger="backend.core_ai")

    with patch("backend.core_ai._get_gemini_model", return_value=FailingModel()):
        result = await core_ai._chat_gemini([{"role": "user", "content": "hi"}])

    assert result == ""
    assert sensitive_error not in caplog.text
    assert "gemini-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text
