"""
AI Healthcare System — Multi-Tier AI Inference Engine

All AI inference MUST go through this module. Never call provider APIs directly.

Supports three tiers with automatic fallback:
  Tier A: Ollama (local-first; no cloud provider when OLLAMA_BASE_URL is local)
  Tier B: Gemini (Google API, free tier available)
  Tier C: OpenAI / Anthropic / OpenRouter (optional, via env vars or request headers)

Usage:
    from backend.core_ai import generate, chat, chat_stream, is_available

    text = await generate("Summarize the patient's history", system="You are a medical assistant.")
    text = await chat([{"role": "user", "content": "What causes diabetes?"}], system="...")
    async for chunk in chat_stream(messages, system="..."):
        print(chunk, end="")

Ported from Universe Dex Singularity AI Engine, adapted for healthcare domain.
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

OLLAMA_PULL_FAILURE_DETAIL = "Failed to pull model"
OLLAMA_DELETE_FAILURE_DETAIL = "Failed to delete model"
AI_STREAM_FAILURE_CHUNK = "**SYSTEM ERROR:** AI stream failed. Please try again later."
CLOUD_AI_FAILURE_DETAIL = "Cloud AI request failed"


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# ── Configuration ─────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", GEMINI_MODEL)

# ── Model list TTL cache (avoids redundant /api/tags calls) ──────────
_model_cache: dict[str, tuple[float, list[str]]] = {}
_MODEL_CACHE_TTL = 30  # seconds


# ═══════════════════════════════════════════════════════════════════════
# TIER A: OLLAMA (Local Inference)
# ═══════════════════════════════════════════════════════════════════════

async def get_ollama_models() -> list[str]:
    """List available Ollama models (cached with TTL)."""
    import time as _time
    cache_key = OLLAMA_BASE_URL
    now = _time.monotonic()
    if cache_key in _model_cache:
        ts, cached = _model_cache[cache_key]
        if now - ts < _MODEL_CACHE_TTL:
            return cached
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                _model_cache[cache_key] = (now, models)
                return models
    except Exception:
        pass
    _model_cache[cache_key] = (now, [])
    return []


async def list_ollama_model_details() -> list[dict]:
    """List downloaded Ollama model metadata."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                return r.json().get("models", [])
    except Exception:
        logger.warning("Ollama not available")
    return []


async def is_ollama_running() -> bool:
    """Check whether the Ollama API is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


async def stream_ollama_model_pull(name: str):
    """Yield Ollama model pull progress events as dictionaries."""
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/pull", json={"name": name}) as response:
                if response.status_code != 200:
                    await response.aread()
                    logger.warning("Ollama model pull failed with status %s", response.status_code)
                    yield {"error": OLLAMA_PULL_FAILURE_DETAIL}
                    return

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            total = data.get("total", 0)
                            completed = data.get("completed", 0)
                            progress = (completed / total * 100) if total > 0 else 0
                            yield {"status": data.get("status", ""), "progress": progress}
                        except Exception:
                            continue
    except Exception:
        logger.warning("Ollama model pull failed")
        yield {"error": OLLAMA_PULL_FAILURE_DETAIL}


async def delete_ollama_model(name: str) -> tuple[bool, int, str]:
    """Delete an Ollama model and return success, status code, and error text."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.request("DELETE", f"{OLLAMA_BASE_URL}/api/delete", json={"name": name})
            return r.status_code == 200, r.status_code, r.text
    except Exception:
        return False, 500, OLLAMA_DELETE_FAILURE_DETAIL


async def _resolve_ollama_model(target_model: str) -> Optional[str]:
    """Resolve an Ollama model name, falling back to best available match."""
    available = await get_ollama_models()
    if not available:
        return None
    if target_model in available:
        return target_model
    # Fuzzy match: e.g. "llama3.2" matches "llama3.2:3b"
    fallback = next(
        (m for m in available if target_model in m or m in target_model),
        available[0],
    )
    logger.debug("Ollama model '%s' not found, falling back to '%s'", target_model, fallback)
    return fallback


async def _generate_ollama(prompt: str, system: str = "", model: Optional[str] = None) -> str:
    """Generate text using Ollama /api/generate endpoint."""
    target_model = await _resolve_ollama_model(model or OLLAMA_MODEL)
    if not target_model:
        return ""

    payload = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 1024},
    }
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            for attempt in range(3):
                r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
                if r.status_code != 200:
                    logger.warning("Ollama returned %d: %s", r.status_code, r.text[:200])
                    return ""
                try:
                    data = r.json() or {}
                except Exception:
                    data = {}
                text = (data.get("response") or "").strip()
                if text:
                    return text
                # Retry on warmup
                done_reason = str((data or {}).get("done_reason") or "").lower()
                if attempt < 2 and done_reason in {"load", "loading"}:
                    await asyncio.sleep(2.0)
                    continue
                break

            # Fallback: /api/chat sometimes works better
            chat_payload = {
                "model": target_model,
                "stream": False,
                "messages": (
                    ([{"role": "system", "content": system}] if system else [])
                    + [{"role": "user", "content": prompt}]
                ),
                "options": payload.get("options") or {},
            }
            r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=chat_payload)
            if r.status_code == 200:
                data = r.json() or {}
                return ((data.get("message") or {}).get("content") or "").strip()
    except httpx.TimeoutException:
        logger.warning("Ollama request timed out after %ds", OLLAMA_TIMEOUT)
    except Exception:
        logger.warning("Ollama generation failed")
    return ""


async def _chat_ollama(messages: list[dict], system: str = "", model: Optional[str] = None) -> str:
    """Chat using Ollama native messages array."""
    target_model = await _resolve_ollama_model(model or OLLAMA_MODEL)
    if not target_model:
        raise Exception(f"No Ollama models available at {OLLAMA_BASE_URL}")

    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    chat_payload = {
        "model": target_model,
        "stream": False,
        "messages": payload_messages,
        "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 1024},
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=chat_payload)
            if r.status_code == 200:
                data = r.json() or {}
                return ((data.get("message") or {}).get("content") or "").strip()
            else:
                raise Exception(f"Ollama returned {r.status_code}: {r.text[:200]}")
    except httpx.TimeoutException:
        raise Exception(f"Ollama request timed out after {OLLAMA_TIMEOUT}s")


async def _stream_ollama(messages: list[dict], system: str = "", model: Optional[str] = None):
    """Stream chat responses chunk-by-chunk from Ollama."""
    target_model = await _resolve_ollama_model(model or OLLAMA_MODEL)
    if not target_model:
        yield "**SYSTEM ERROR:** No Ollama models available. Please start Ollama and pull a model."
        return

    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    chat_payload = {
        "model": target_model,
        "stream": True,
        "messages": payload_messages,
        "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 1024},
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/chat", json=chat_payload) as r:
                if r.status_code != 200:
                    yield f"**SYSTEM ERROR:** Ollama returned {r.status_code}."
                    return
                async for line in r.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = (data.get("message") or {}).get("content")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            pass
    except httpx.TimeoutException:
        yield "**SYSTEM TIMEOUT:** The LLM took too long to respond."
    except Exception:
        logger.warning("Ollama stream error")
        yield AI_STREAM_FAILURE_CHUNK


# ═══════════════════════════════════════════════════════════════════════
# TIER B: GEMINI (Google Cloud)
# ═══════════════════════════════════════════════════════════════════════

_gemini_configured = False
_gemini_model = None


def has_gemini_api_key() -> bool:
    """Return whether Gemini-backed features can be configured."""
    key = GOOGLE_API_KEY.strip()
    if not key:
        return False
    if key in ("dummy", "your_gemini_api_key_here", "placeholder"):
        return False
    if key.startswith("your_"):
        return False
    return True


def _get_gemini_model():
    """Lazy-load Gemini model."""
    global _gemini_configured, _gemini_model
    if _gemini_model:
        return _gemini_model
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "dummy":
        return None
    try:
        import google.generativeai as genai
        if not _gemini_configured:
            genai.configure(api_key=GOOGLE_API_KEY)
            _gemini_configured = True
        _gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        return _gemini_model
    except Exception:
        logger.warning("Failed to initialize Gemini")
        return None


def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    """Generate a text embedding through the canonical AI provider boundary.

    This is a synchronous function intentionally kept sync for callers that
    cannot be async (e.g. startup-time vector store population). Async callers
    should wrap it with ``asyncio.to_thread(embed_text, text)``.
    """
    global _gemini_configured
    if not has_gemini_api_key():
        logger.warning("GOOGLE_API_KEY not found, using zero vector")
        return [0.0] * 768

    try:
        import google.generativeai as genai
        if not _gemini_configured:
            genai.configure(api_key=GOOGLE_API_KEY)
            _gemini_configured = True
        result = genai.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            content=text,
            task_type=task_type,
        )
        return result.get("embedding") or [0.0] * 768
    except Exception:
        logger.error("Embedding failed")
        return [0.0] * 768


async def embed_text_async(text: str, task_type: str = "retrieval_document") -> list[float]:
    """Async wrapper for embed_text — use this from async route handlers."""
    return await asyncio.to_thread(embed_text, text, task_type)


def generate_vision_content(prompt: str, image: Any, model: Optional[str] = None) -> str:
    """Generate text from a prompt plus image through Gemini Vision.

    Synchronous. Async callers should use ``asyncio.to_thread(generate_vision_content, ...)``.
    """
    if not has_gemini_api_key():
        return ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        vision_model = genai.GenerativeModel(model or GEMINI_VISION_MODEL)
        response = vision_model.generate_content([prompt, image])
        return (getattr(response, "text", "") or "").strip()
    except Exception:
        logger.error("Vision generation failed")
        return ""


async def generate_vision_content_async(prompt: str, image: Any, model: Optional[str] = None) -> str:
    """Async wrapper for generate_vision_content — use this from async route handlers."""
    return await asyncio.to_thread(generate_vision_content, prompt, image, model)


async def _generate_gemini(prompt: str, system: str = "") -> str:
    """Generate text using Google Gemini."""
    model = _get_gemini_model()
    if not model:
        return ""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    try:
        response = await asyncio.to_thread(model.generate_content, full_prompt)
        return response.text.strip() if response.text else ""
    except Exception as e:
        err = str(e)
        if "429" in err or "Quota" in err:
            logger.warning("Gemini quota exceeded")
        else:
            logger.warning("Gemini generation failed")
        return ""


async def _chat_gemini(messages: list[dict], system: str = "") -> str:
    """Chat using Gemini native multi-turn via start_chat()."""
    model = _get_gemini_model()
    if not model:
        return ""

    try:
        import google.generativeai as genai
        from google.generativeai.types import ContentDict

        # Build history for all but the final user message
        history: list[ContentDict] = []
        if system:
            # Gemini doesn't have a dedicated system role in start_chat history;
            # inject it as the first user/model exchange so it anchors the conversation.
            history.append({"role": "user", "parts": [system]})
            history.append({"role": "model", "parts": ["Understood. I will follow those instructions."]})

        # All messages except the last become history
        for msg in messages[:-1]:
            gemini_role = "model" if msg.get("role") == "assistant" else "user"
            history.append({"role": gemini_role, "parts": [msg.get("content", "")]})

        chat_session = await asyncio.to_thread(model.start_chat, history=history)

        # Send the last message
        last_msg = messages[-1].get("content", "") if messages else ""
        response = await asyncio.to_thread(chat_session.send_message, last_msg)
        return response.text.strip() if response.text else ""
    except Exception:
        logger.warning("Gemini chat failed")
        return ""


async def _stream_gemini(messages: list[dict], system: str = ""):
    """Pseudo-stream from Gemini (single-chunk yield — Gemini SDK doesn't support true SSE)."""
    result = await _chat_gemini(messages, system)
    if result:
        yield result


# ═══════════════════════════════════════════════════════════════════════
# TIER C: CLOUD APIs (OpenAI / Anthropic / OpenRouter)
# ═══════════════════════════════════════════════════════════════════════

async def _generate_cloud(prompt: str, system: str, model: Optional[str], api_provider: str, api_key: str) -> str:
    """Generate text using a cloud provider."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if api_provider.lower() in ("openai", "openrouter"):
                base_url = (
                    "https://api.openai.com/v1" if api_provider.lower() == "openai"
                    else "https://openrouter.ai/api/v1"
                )
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                target_model = model or (
                    "gpt-4o-mini" if api_provider.lower() == "openai"
                    else "google/gemini-2.5-flash"
                )
                payload_messages = []
                if system:
                    payload_messages.append({"role": "system", "content": system})
                payload_messages.append({"role": "user", "content": prompt})

                r = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={"model": target_model, "messages": payload_messages, "temperature": 0.7},
                )
                if r.status_code == 200:
                    data = r.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                logger.warning("%s error: %d", api_provider, r.status_code)

            elif api_provider.lower() == "anthropic":
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                target_model = model or "claude-3-haiku-20240307"
                payload = {
                    "model": target_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.7,
                }
                if system:
                    payload["system"] = system

                r = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                if r.status_code == 200:
                    content = r.json().get("content", [])
                    if content:
                        return content[0].get("text", "").strip()
                logger.warning("Anthropic error: %d", r.status_code)

    except Exception:
        logger.warning("Cloud AI error (%s)", api_provider)
    return ""


async def _chat_cloud(messages: list[dict], system: str, model: Optional[str], api_provider: str, api_key: str) -> str:
    """Chat using a cloud provider."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if api_provider.lower() in ("openai", "openrouter"):
                base_url = (
                    "https://api.openai.com/v1" if api_provider.lower() == "openai"
                    else "https://openrouter.ai/api/v1"
                )
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                target_model = model or (
                    "gpt-4o-mini" if api_provider.lower() == "openai"
                    else "google/gemini-2.5-flash"
                )
                payload_messages = []
                if system:
                    payload_messages.append({"role": "system", "content": system})
                payload_messages.extend(messages)

                r = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={"model": target_model, "messages": payload_messages, "temperature": 0.7},
                )
                if r.status_code == 200:
                    data = r.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                raise Exception(f"{api_provider} error: {r.status_code}")

            elif api_provider.lower() == "anthropic":
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                target_model = model or "claude-3-haiku-20240307"
                payload = {
                    "model": target_model,
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                }
                if system:
                    payload["system"] = system

                r = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                if r.status_code == 200:
                    content = r.json().get("content", [])
                    if content:
                        return content[0].get("text", "").strip()
                raise Exception(f"Anthropic error: {r.status_code}")

    except Exception as exc:
        if isinstance(exc, RuntimeError) and str(exc) == CLOUD_AI_FAILURE_DETAIL:
            raise
        logger.warning("Cloud AI error (%s)", api_provider)
        raise RuntimeError(CLOUD_AI_FAILURE_DETAIL) from None


async def _stream_cloud(messages: list[dict], system: str, model: Optional[str], api_provider: str, api_key: str):
    """Single-chunk yield for cloud APIs."""
    res = await _chat_cloud(messages, system, model, api_provider, api_key)
    if res:
        yield res


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API — The only functions external modules should call
# ═══════════════════════════════════════════════════════════════════════

async def is_available() -> bool:
    """Check if any AI backend is available (Ollama or Gemini)."""
    ollama_models = await get_ollama_models()
    if ollama_models:
        return True
    if has_gemini_api_key():
        return True
    return False


async def generate(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Generate text using the best available AI backend.

    Fallback chain: explicit cloud provider → Ollama → Gemini → mock response.
    """
    # Explicit cloud provider override
    if api_provider and api_key and api_provider.lower() not in ("ollama", "gemini"):
        result = await _generate_cloud(prompt, system, model, api_provider, api_key)
        if result:
            return result

    # Tier A: Ollama
    ollama_models = await get_ollama_models()
    if ollama_models:
        result = await _generate_ollama(prompt, system, model)
        if result:
            return result

    # Tier B: Gemini
    if has_gemini_api_key():
        result = await _generate_gemini(prompt, system)
        if result:
            return result

    logger.warning("All AI backends unavailable for generate(), using mock fallback")
    return "Clinical analysis mock response: The system is running in offline mode. For full functionality, please run Ollama or configure a valid GOOGLE_API_KEY."


async def chat(
    messages: list[dict],
    system: str = "",
    model: Optional[str] = None,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Multi-turn chat using the best available AI backend.

    Fallback chain: explicit cloud provider → Ollama → Gemini → mock response.
    """
    # Explicit cloud provider override
    if api_provider and api_key and api_provider.lower() not in ("ollama", "gemini"):
        return await _chat_cloud(messages, system, model, api_provider, api_key)

    # Tier A: Ollama
    ollama_models = await get_ollama_models()
    if ollama_models:
        try:
            return await _chat_ollama(messages, system, model)
        except Exception:
            logger.warning("Ollama chat failed, trying Gemini")

    # Tier B: Gemini
    if has_gemini_api_key():
        result = await _chat_gemini(messages, system)
        if result:
            return result

    logger.warning("All AI backends unavailable for chat(), using mock response")
    return "Hello! I am your AI Copilot. Currently, the system is running in offline mode (Ollama and Gemini API are unavailable). I can answer simple queries or show patient data mockups."


async def chat_stream(
    messages: list[dict],
    system: str = "",
    model: Optional[str] = None,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Streaming multi-turn chat. Yields text chunks as they arrive.

    Fallback: explicit cloud → Ollama → Gemini → mock stream response.
    """
    # Explicit cloud provider override
    if api_provider and api_key and api_provider.lower() not in ("ollama", "gemini"):
        async for chunk in _stream_cloud(messages, system, model, api_provider, api_key):
            yield chunk
        return

    # Tier A: Ollama
    ollama_models = await get_ollama_models()
    if ollama_models:
        async for chunk in _stream_ollama(messages, system, model):
            yield chunk
        return

    # Tier B: Gemini (pseudo-stream)
    if has_gemini_api_key():
        try:
            has_yielded = False
            async for chunk in _stream_gemini(messages, system):
                if chunk:
                    has_yielded = True
                    yield chunk
            if has_yielded:
                return
        except Exception as e:
            logger.warning(f"Gemini stream error: {e}")

    # Fallback to mock response to prevent the UI from hanging
    yield "Hello! I am your AI Copilot. Currently, the system is running in offline mode because local Ollama models are not active and a valid Google Gemini API key is not configured.\n\n"
    yield "I can assist you with simulated clinical summaries, guide you through the EHR interface, or answer general workflow questions. How can I help you today?"
