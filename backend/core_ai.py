"""
AI Healthcare System — Multi-Tier AI Inference Engine

All AI inference MUST go through this module. Never call provider APIs directly.

Supports three tiers with automatic fallback:
  Tier A: Ollama (local, zero-cost, HIPAA-friendly — data never leaves the machine)
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

import os
import json
import logging
import asyncio
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# ── Configuration ─────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

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
    except Exception as e:
        logger.warning("Ollama error: %s", e)
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
    except Exception as e:
        logger.warning("Ollama stream error: %s", e)
        yield f"**SYSTEM ERROR:** {str(e)}"


# ═══════════════════════════════════════════════════════════════════════
# TIER B: GEMINI (Google Cloud)
# ═══════════════════════════════════════════════════════════════════════

_gemini_configured = False
_gemini_model = None


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
    except Exception as e:
        logger.warning("Failed to initialize Gemini: %s", e)
        return None


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
            logger.warning("Gemini error: %s", e)
        return ""


async def _chat_gemini(messages: list[dict], system: str = "") -> str:
    """Chat using Gemini (converts messages to single prompt)."""
    model = _get_gemini_model()
    if not model:
        return ""
    parts = []
    if system:
        parts.append(f"System: {system}\n")
    for msg in messages:
        role = msg.get("role", "user").capitalize()
        parts.append(f"{role}: {msg.get('content', '')}\n")
    full_prompt = "\n".join(parts)
    try:
        response = await asyncio.to_thread(model.generate_content, full_prompt)
        return response.text.strip() if response.text else ""
    except Exception as e:
        logger.warning("Gemini chat error: %s", e)
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
                logger.warning("%s error: %d %s", api_provider, r.status_code, r.text[:200])

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
                logger.warning("Anthropic error: %d %s", r.status_code, r.text[:200])

    except Exception as e:
        logger.warning("Cloud AI Error (%s): %s", api_provider, e)
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

    except Exception as e:
        logger.warning("Cloud AI Error (%s): %s", api_provider, e)
        raise


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
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "dummy":
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

    Fallback chain: explicit cloud provider → Ollama → Gemini → empty string.
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
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "dummy":
        result = await _generate_gemini(prompt, system)
        if result:
            return result

    logger.warning("All AI backends unavailable for generate()")
    return ""


async def chat(
    messages: list[dict],
    system: str = "",
    model: Optional[str] = None,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Multi-turn chat using the best available AI backend.

    Fallback chain: explicit cloud provider → Ollama → Gemini → raises Exception.
    """
    # Explicit cloud provider override
    if api_provider and api_key and api_provider.lower() not in ("ollama", "gemini"):
        return await _chat_cloud(messages, system, model, api_provider, api_key)

    # Tier A: Ollama
    ollama_models = await get_ollama_models()
    if ollama_models:
        try:
            return await _chat_ollama(messages, system, model)
        except Exception as e:
            logger.warning("Ollama chat failed, trying Gemini: %s", e)

    # Tier B: Gemini
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "dummy":
        result = await _chat_gemini(messages, system)
        if result:
            return result

    raise Exception("No AI backends available for chat()")


async def chat_stream(
    messages: list[dict],
    system: str = "",
    model: Optional[str] = None,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Streaming multi-turn chat. Yields text chunks as they arrive.

    Fallback: explicit cloud → Ollama → Gemini (single-chunk).
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
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "dummy":
        async for chunk in _stream_gemini(messages, system):
            yield chunk
        return

    yield "**SYSTEM ERROR:** No AI backends are available. Please configure Ollama or set GOOGLE_API_KEY."
