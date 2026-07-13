from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from backend import ollama_routes, rag, vision_service
from backend.prompt_registry import get_prompt

ROOT = Path(__file__).resolve().parents[2]


def test_gemini_sdk_is_only_imported_by_core_ai():
    offenders = []
    for path in (ROOT / "backend").glob("*.py"):
        if path.name == "core_ai.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "google.generativeai" in text:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []


def test_ollama_routes_do_not_import_httpx_directly():
    text = (ROOT / "backend" / "ollama_routes.py").read_text(encoding="utf-8", errors="ignore")
    assert "import httpx" not in text


def test_rag_embeddings_use_core_ai_boundary():
    with patch("backend.rag.core_ai.embed_text", return_value=[0.2, 0.4]) as embed_text:
        assert rag.get_embedding("clinical note") == [0.2, 0.4]
        embed_text.assert_called_once_with("clinical note", task_type="retrieval_document")


def test_rag_query_embeddings_use_core_ai_boundary():
    with patch("backend.rag.core_ai.embed_text", return_value=[0.6, 0.8]) as embed_text:
        assert rag.get_query_embedding("clinical query") == [0.6, 0.8]
        embed_text.assert_called_once_with("clinical query", task_type="retrieval_query")


def test_vision_analysis_uses_core_ai_boundary():
    image = Image.new("RGB", (10, 10), color="white")
    response_text = '{"extracted_data": {"glucose": 99}, "summary": "Normal"}'

    with patch("backend.vision_service.Image.open", return_value=image), \
         patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.core_ai.generate_vision_content", return_value=response_text) as generate_vision:
        result = vision_service.analyze_lab_report(b"image-bytes")

    assert result["extracted_data"]["glucose"] == 99
    generate_vision.assert_called_once()
    prompt, passed_image = generate_vision.call_args.args
    assert "Analyze this lab report image" in prompt
    assert passed_image is image


def test_lab_report_vision_prompt_is_registered():
    prompt = get_prompt("lab_report_vision")

    assert "Analyze this lab report image" in prompt
    assert "Return ONLY valid JSON" in prompt


def test_vision_analysis_uses_registered_prompt():
    image = Image.new("RGB", (10, 10), color="white")
    response_text = '{"extracted_data": {"glucose": 99}, "summary": "Normal"}'

    with patch("backend.vision_service.Image.open", return_value=image), \
         patch("backend.vision_service.core_ai.has_gemini_api_key", return_value=True), \
         patch("backend.vision_service.get_prompt", return_value="registered vision prompt", create=True) as get_registered_prompt, \
         patch("backend.vision_service.core_ai.generate_vision_content", return_value=response_text) as generate_vision:
        result = vision_service.analyze_lab_report(b"image-bytes")

    assert result["summary"] == "Normal"
    get_registered_prompt.assert_called_once_with("lab_report_vision")
    generate_vision.assert_called_once_with("registered vision prompt", image)


@pytest.mark.asyncio
async def test_ollama_list_models_uses_core_ai_boundary():
    models = [{"name": "llama3.2"}]
    with patch("backend.ollama_routes.core_ai.is_ollama_running", new_callable=AsyncMock, return_value=True), \
         patch("backend.ollama_routes.core_ai.list_ollama_model_details", new_callable=AsyncMock, return_value=models) as list_models:
        result = await ollama_routes.list_models()

    assert result == {"available": True, "models": models}
    list_models.assert_awaited_once()


@pytest.mark.asyncio
async def test_ollama_list_models_reports_available_when_library_empty():
    with patch("backend.ollama_routes.core_ai.is_ollama_running", new_callable=AsyncMock, return_value=True), \
         patch("backend.ollama_routes.core_ai.list_ollama_model_details", new_callable=AsyncMock, return_value=[]):
        result = await ollama_routes.list_models()

    assert result == {"available": True, "models": []}


@pytest.mark.asyncio
async def test_ollama_delete_model_uses_core_ai_boundary():
    request = ollama_routes.DeleteModelRequest(name="llama3.2")
    with patch("backend.ollama_routes.core_ai.delete_ollama_model", new_callable=AsyncMock, return_value=(True, 200, "")) as delete_model:
        result = await ollama_routes.delete_model(request)

    assert result == {"success": True}
    delete_model.assert_awaited_once_with("llama3.2")
