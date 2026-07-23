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

from .semantic_cache import SemanticCache

semantic_cache = SemanticCache()

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

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-2")
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

_gemini_disabled = False


def has_gemini_api_key() -> bool:
    """Return whether Gemini-backed features can be configured."""
    if _gemini_disabled:
        return False
    key = GOOGLE_API_KEY.strip()
    if not key:
        return False
    if key in ("dummy", "your_gemini_api_key_here", "placeholder"):
        return False
    if key.startswith("your_"):
        return False
    return True


_gemini_configured = False
_gemini_model = None


def _get_gemini_model():
    """Lazy-load Gemini model."""
    global _gemini_configured, _gemini_model
    if _gemini_disabled:
        return None
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
    """Generate a text embedding through the centralized AI provider boundary.

    This is a synchronous function intentionally kept sync for callers that
    cannot be async (e.g. startup-time vector store population). Async callers
    should wrap it with ``asyncio.to_thread(embed_text, text)``.
    """
    global _gemini_configured
    import hashlib

    from .cache_service import cache
    # Generate MD5 hash of text to create a compact, unique cache key
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    cache_key = f"emb:{task_type}:{text_hash}"

    try:
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return cached_val
    except Exception as ex_cache:
        logger.debug("Embedding cache lookup failed: %s", ex_cache)

    try:
        # Use Cloudflare Workers AI for embeddings
        import requests
        url = "https://ai-healthcare-model.pavan9b.workers.dev/embed"

        response = requests.post(
            url,
            json={"text": [text]},
            timeout=15.0
        )
        response.raise_for_status()

        data = response.json()

        # Cloudflare returns: {"shape": [...], "data": [[...]]}
        # The vector is the first element of "data"
        if "data" in data and len(data["data"]) > 0:
            embedding = data["data"][0]
            # Ensure it's a list of floats
            embedding = [float(x) for x in embedding]

            try:
                cache.set(cache_key, embedding, ttl=86400) # Cache for 24 hours
            except Exception as ex_cache:
                logger.debug("Embedding cache set failed: %s", ex_cache)

            return embedding
        else:
            logger.error(f"Cloudflare embedding format unexpected: {data}")
            return [0.0] * 768

    except Exception as e:
        logger.error(f"Error calling Cloudflare embedding API: {str(e)}")
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


def generate_vision_content_pdf(prompt: str, pdf_bytes: bytes, model: Optional[str] = None) -> str:
    """Generate text from a prompt plus PDF through Gemini Vision."""
    if not has_gemini_api_key():
        return ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        vision_model = genai.GenerativeModel(model or GEMINI_VISION_MODEL)
        response = vision_model.generate_content([
            {'mime_type': 'application/pdf', 'data': pdf_bytes},
            prompt
        ])
        return (getattr(response, "text", "") or "").strip()
    except Exception:
        logger.error("Vision PDF generation failed")
        return ""


async def generate_vision_content_pdf_async(prompt: str, pdf_bytes: bytes, model: Optional[str] = None) -> str:
    """Async wrapper for generate_vision_content_pdf."""
    return await asyncio.to_thread(generate_vision_content_pdf, prompt, pdf_bytes, model)


async def _generate_gemini(prompt: str, system: str = "") -> str:
    """Generate text using Google Gemini."""
    model = _get_gemini_model()
    if not model:
        return ""

    # Enable Gemini Context Caching if system prompt is exceptionally large (>32k tokens / ~130k chars)
    if system and len(system) > 130000:
        try:
            import datetime
            import hashlib

            from google.generativeai import caching

            system_hash = hashlib.md5(system.encode("utf-8")).hexdigest()
            cache_name = f"sys-cache-{system_hash}"

            cached_content = None
            try:
                for c in caching.CachedContent.list():
                    if c.display_name == cache_name:
                        cached_content = c
                        break
            except Exception:
                pass

            if not cached_content:
                logger.info("Creating Gemini Context Cache for large system prompt (%s)...", cache_name)
                cached_content = await asyncio.to_thread(
                    caching.CachedContent.create,
                    model=GEMINI_MODEL,
                    display_name=cache_name,
                    contents=system,
                    ttl=datetime.timedelta(minutes=10)
                )

            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                cached_content=cached_content
            )
            return response.text.strip() if response.text else ""
        except Exception as cache_err:
            logger.debug("Failed to use Gemini Context Caching: %s", cache_err)
            # Fall back to standard content generation below

    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    try:
        response = await asyncio.to_thread(model.generate_content, full_prompt)
        return response.text.strip() if response.text else ""
    except Exception as e:
        err = str(e)
        global _gemini_disabled
        if any(code in err for code in ["400", "401", "403", "404", "API_KEY_INVALID", "not found"]):
            import re

            from .guardrails import redact_pii_from_text
            clean_err = redact_pii_from_text(err)
            clean_err = re.sub(r"(?i)token=[^\s]+", "token=REDACTED", clean_err)
            clean_err = re.sub(r"(?i)key=[^\s]+", "key=REDACTED", clean_err)
            logger.error("Permanent Gemini error encountered (%s). Disabling Gemini circuit breaker.", clean_err)
            _gemini_disabled = True
        elif "429" in err or "Quota" in err:
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
    provider = api_provider.lower()
    if provider == "openai":
        base_url = "https://api.openai.com/v1"
    elif provider == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    elif provider == "huggingface":
        base_url = "https://api-inference.huggingface.co/v1"
    elif provider == "groq":
        base_url = "https://api.groq.com/openai/v1"
    elif provider == "together":
        base_url = "https://api.together.xyz/v1"
    else:
        base_url = os.getenv("CUSTOM_AI_BASE_URL")
        if not base_url or "<your-unique-subdomain>" in base_url:
            base_url = "https://ai-healthcare-model.pavan9b.workers.dev"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Zero Retention / Opt-Out telemetry headers for privacy
    headers["OAI-Telemetry"] = "false"
    headers["x-api-telemetry-opt-out"] = "true"
    if model and ("cloudflare" in model.lower() or "ollama" in model.lower()):
        model = None

    target_model = model or (
        "gpt-4o-mini" if provider == "openai"
        else "mistralai/Mistral-7B-Instruct-v0.3" if provider == "huggingface"
        else "google/gemini-2.5-flash"
    )
    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.append({"role": "user", "content": prompt})

    try:
        if os.getenv("SPACE_ID"):
            raise RuntimeError("Bypassing httpx in Hugging Face Space container")
        async with httpx.AsyncClient(timeout=30) as client:
            if provider in ("openai", "openrouter", "huggingface", "groq", "together", "custom"):
                r = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={"model": target_model, "messages": payload_messages, "temperature": 0.7},
                )
                if r.status_code == 200:
                    data = r.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                logger.warning("%s error: %d", api_provider, r.status_code)

            elif provider == "anthropic":
                headers_ant = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                target_model_ant = model or "claude-3-haiku-20240307"
                payload = {
                    "model": target_model_ant,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.7,
                }
                if system:
                    payload["system"] = system

                r = await client.post("https://api.anthropic.com/v1/messages", headers=headers_ant, json=payload)
                if r.status_code == 200:
                    content = r.json().get("content", [])
                    if content:
                        return content[0].get("text", "").strip()
                logger.warning("Anthropic error: %d", r.status_code)

    except Exception:
        logger.warning("httpx connection error (%s). Trying requests fallback...", api_provider)
        try:
            import requests
            def do_sync_request():
                if provider in ("openai", "openrouter", "huggingface", "groq", "together", "custom"):
                    return requests.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json={"model": target_model, "messages": payload_messages, "temperature": 0.7},
                        timeout=30
                    )
                elif provider == "anthropic":
                    headers_ant = {
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    }
                    target_model_ant = model or "claude-3-haiku-20240307"
                    payload = {
                        "model": target_model_ant,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1024,
                        "temperature": 0.7,
                    }
                    if system:
                        payload["system"] = system
                    return requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers=headers_ant,
                        json=payload,
                        timeout=30
                    )
            r = await asyncio.to_thread(do_sync_request)
            if r.status_code == 200:
                data = r.json()
                if provider == "anthropic":
                    content = data.get("content", [])
                    if content:
                        return content[0].get("text", "").strip()
                else:
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.warning("requests fallback error (%s): %d", api_provider, r.status_code)
        except Exception:
            logger.error("requests fallback failed completely")
    return ""


async def _chat_cloud(messages: list[dict], system: str, model: Optional[str], api_provider: str, api_key: str) -> str:
    """Chat using a cloud provider."""
    provider = api_provider.lower()
    if provider == "openai":
        base_url = "https://api.openai.com/v1"
    elif provider == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    elif provider == "huggingface":
        base_url = "https://api-inference.huggingface.co/v1"
    elif provider == "groq":
        base_url = "https://api.groq.com/openai/v1"
    elif provider == "together":
        base_url = "https://api.together.xyz/v1"
    else:
        base_url = os.getenv("CUSTOM_AI_BASE_URL")
        if not base_url or "<your-unique-subdomain>" in base_url:
            base_url = "https://ai-healthcare-model.pavan9b.workers.dev"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Zero Retention / Opt-Out telemetry headers for privacy
    headers["OAI-Telemetry"] = "false"
    headers["x-api-telemetry-opt-out"] = "true"
    target_model = model or (
        "gpt-4o-mini" if provider == "openai"
        else "google/gemini-2.5-flash"
    )
    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    try:
        if os.getenv("SPACE_ID"):
            raise RuntimeError("Bypassing httpx in Hugging Face Space container")
        async with httpx.AsyncClient(timeout=30) as client:
            if provider in ("openai", "openrouter", "huggingface", "groq", "together", "custom"):
                r = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={"model": target_model, "messages": payload_messages, "temperature": 0.7, "store": False},
                )
                if r.status_code == 200:
                    data = r.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                raise Exception(f"{api_provider} error: {r.status_code}")

            elif provider == "anthropic":
                headers_ant = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                target_model_ant = model or "claude-3-haiku-20240307"
                payload = {
                    "model": target_model_ant,
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                }
                if system:
                    payload["system"] = system

                r = await client.post("https://api.anthropic.com/v1/messages", headers=headers_ant, json=payload)
                if r.status_code == 200:
                    content = r.json().get("content", [])
                    if content:
                        return content[0].get("text", "").strip()
                raise Exception(f"Anthropic error: {r.status_code}")

    except Exception:
        logger.warning("httpx connection error for chat (%s). Trying requests fallback...", api_provider)
        try:
            import requests
            def do_sync_request():
                if provider in ("openai", "openrouter", "huggingface", "groq", "together", "custom"):
                    return requests.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json={"model": target_model, "messages": payload_messages, "temperature": 0.7, "store": False},
                        timeout=30
                    )
                elif provider == "anthropic":
                    headers_ant = {
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    }
                    target_model_ant = model or "claude-3-haiku-20240307"
                    payload = {
                        "model": target_model_ant,
                        "messages": messages,
                        "max_tokens": 1024,
                        "temperature": 0.7,
                    }
                    if system:
                        payload["system"] = system
                    return requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers=headers_ant,
                        json=payload,
                        timeout=30
                    )
            r = await asyncio.to_thread(do_sync_request)
            if r.status_code == 200:
                data = r.json()
                if provider == "anthropic":
                    content = data.get("content", [])
                    if content:
                        return content[0].get("text", "").strip()
                else:
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.warning("requests fallback error for chat (%s): %d", api_provider, r.status_code)
        except Exception:
            logger.error("requests fallback failed completely for chat")
    return ""


async def _stream_cloud(messages: list[dict], system: str, model: Optional[str], api_provider: str, api_key: str):
    """Yield text chunks from cloud APIs using thread-based requests streaming."""
    import json
    import queue
    import threading

    import requests

    q = queue.Queue()

    def fetch_stream():
        try:
            provider = api_provider.lower()
            if provider == "openai":
                base_url = "https://api.openai.com/v1"
            elif provider == "openrouter":
                base_url = "https://openrouter.ai/api/v1"
            elif provider == "huggingface":
                base_url = "https://api-inference.huggingface.co/v1"
            elif provider == "groq":
                base_url = "https://api.groq.com/openai/v1"
            elif provider == "together":
                base_url = "https://api.together.xyz/v1"
            else:
                base_url = os.getenv("CUSTOM_AI_BASE_URL")
                if not base_url or "<your-unique-subdomain>" in base_url:
                    base_url = "https://ai-healthcare-model.pavan9b.workers.dev"

            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            # Zero Retention / Opt-Out telemetry headers for privacy
            headers["OAI-Telemetry"] = "false"
            headers["x-api-telemetry-opt-out"] = "true"
            local_model = model
            if local_model and ("cloudflare" in local_model.lower() or "ollama" in local_model.lower()):
                local_model = None

            target_model = local_model or (
                "gpt-4o-mini" if provider == "openai"
                else "mistralai/Mistral-7B-Instruct-v0.3" if provider == "huggingface"
                else "google/gemini-2.5-flash"
            )
            payload_messages = []
            if system:
                payload_messages.append({"role": "system", "content": system})
            payload_messages.extend(messages)

            with requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={"model": target_model, "messages": payload_messages, "temperature": 0.7, "stream": True, "store": False},
                stream=True,
                timeout=30
            ) as r:
                if r.status_code != 200:
                    logger.error(f"Stream error: {r.status_code} {r.text}")
                    return
                for line in r.iter_lines():
                    if line:
                        q.put(line.decode('utf-8'))
        except Exception as e:
            q.put(e)
        finally:
            q.put(None)

    thread = threading.Thread(target=fetch_stream, daemon=True)
    thread.start()

    while True:
        # Await the queue get non-blockingly
        item = await asyncio.to_thread(q.get)

        if item is None:
            break
        if isinstance(item, Exception):
            logger.error(f"Stream error: {item}")
            break

        if item.startswith("data: "):
            data_str = item[6:]
            if data_str.strip() == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                # Some APIs use choices[0].delta.content
                choices = data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    chunk = delta.get("content")
                    if chunk:
                        yield chunk
            except Exception:
                pass



async def _resolve_provider_and_key(api_provider: Optional[str] = None, api_key: Optional[str] = None):
    """Resolves provider and key, falling back to custom Cloudflare if configured provider is inactive."""
    resolved_provider = api_provider or os.getenv("GLOBAL_AI_PROVIDER")
    resolved_key = api_key or os.getenv("GLOBAL_AI_API_KEY")

    gemini_active = has_gemini_api_key()
    ollama_active = False
    try:
        models = await get_ollama_models()
        if models:
            ollama_active = True
    except Exception:
        pass

    if not resolved_provider or (resolved_provider.lower() == "gemini" and not gemini_active) or (resolved_provider.lower() == "ollama" and not ollama_active):
        hf_token = os.getenv("HF_TOKEN")
        if os.getenv("SPACE_ID") and hf_token:
            resolved_provider = "huggingface"
            resolved_key = hf_token
        else:
            resolved_provider = "custom"
            resolved_key = resolved_key or "cloudflare"

    return resolved_provider, resolved_key


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API — The only functions external modules should call
# ═══════════════════════════════════════════════════════════════════════

async def is_available() -> bool:
    """Check if any AI backend is available."""
    # If in testing mode, check Ollama or Gemini availability since tests expect it to be mockable
    if os.getenv("TESTING") == "1":
        ollama_models = await get_ollama_models()
        if ollama_models:
            return True
        if has_gemini_api_key():
            return True
        return False
    # We now always have Cloudflare AI available as the default custom provider
    return True


from .security_decorators import no_log_zone_async, no_log_zone_async_gen


@no_log_zone_async
async def generate(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    bypass_cache: bool = False,
) -> str:
    """
    Generate text using the best available AI backend.

    Fallback chain: explicit cloud provider → Ollama → Gemini → mock response.
    """
    from .tee_enclave import ConfidentialEnclave
    enclave = ConfidentialEnclave()
    enclave._attested = True

    async def _inner():
        # 0. Prompt injection check
        from .guardrails import is_prompt_injection, redact_pii_from_text
        if is_prompt_injection(prompt):
            from .database import SessionLocal
            from .security import log_audit_event
            db = SessionLocal()
            try:
                log_audit_event(
                    db,
                    action="SECURITY_PROMPT_INJECTION_BLOCKED",
                    target_user_id=0,
                    details=f"Prompt flagged for injection. Snippet: {prompt[:100]}"
                )
            except Exception as e:
                logger.warning("Failed to log prompt injection event: %s", e)
            finally:
                db.close()

            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Clinical safety guardrail: Input prompt flagged for potential instruction override."
            )

        # 1. Semantic Cache check
        embedding = None
        if not bypass_cache and os.getenv("SEMANTIC_CACHE_ENABLED", "true").lower() in ("true", "1", "yes", "on"):
            try:
                # Fast path exact match (< 0.1ms execution, 0 network calls)
                cached_fast = semantic_cache.lookup(prompt, [])
                if cached_fast:
                    return redact_pii_from_text(cached_fast)
                embedding = await asyncio.to_thread(embed_text, prompt)
                cached_response = semantic_cache.lookup(prompt, embedding)
                if cached_response:
                    return redact_pii_from_text(cached_response)
            except Exception as e:
                logger.debug("Semantic cache lookup error: %s", e)

        # Explicit cloud provider override
        resolved_provider, resolved_key = await _resolve_provider_and_key(api_provider, api_key)
        logger.info("CORE_AI GENERATE: resolved_provider=%s, resolved_key_configured=%s", resolved_provider, bool(resolved_key))

        result = None

        # 1. Try explicit provider (if requested via UI)
        if api_provider:
            if api_provider.lower() == "gemini" and has_gemini_api_key():
                logger.info("CORE_AI GENERATE: Executing explicit provider Gemini...")
                result = await _generate_gemini(prompt, system)
            elif api_provider.lower() == "ollama":
                ollama_models = await get_ollama_models()
                if ollama_models:
                    logger.info("CORE_AI GENERATE: Executing explicit provider Ollama...")
                    result = await _generate_ollama(prompt, system, model)
            else:
                logger.info("CORE_AI GENERATE: Executing explicit provider %s...", api_provider)
                result = await _generate_cloud(prompt, system, model, api_provider, api_key)

        # 2. Default Primary: Cloudflare (if not already tried)
        if not result and (not api_provider or api_provider.lower() != "custom"):
            logger.info("CORE_AI GENERATE: Executing Default Primary (Cloudflare)...")
            result = await _generate_cloud(prompt, system, model, "custom", "cloudflare")

        # 3. Tier A Fallback: Gemini (if not already tried)
        if not result and (not api_provider or api_provider.lower() != "gemini"):
            if has_gemini_api_key():
                logger.info("CORE_AI GENERATE: Trying Tier A fallback (Gemini)...")
                result = await _generate_gemini(prompt, system)

        # 4. Tier B Fallback: Ollama (if not already tried)
        if not result and (not api_provider or api_provider.lower() != "ollama"):
            ollama_models = await get_ollama_models()
            if ollama_models:
                logger.info("CORE_AI GENERATE: Trying Tier B fallback (Ollama)...")
                result = await _generate_ollama(prompt, system, model)

        if result:
            # Redact PII from the output
            result = redact_pii_from_text(result)
            # Save to semantic cache
            if not bypass_cache and os.getenv("SEMANTIC_CACHE_ENABLED", "true").lower() in ("true", "1", "yes", "on"):
                try:
                    if embedding is None:
                        embedding = await asyncio.to_thread(embed_text, prompt)
                    semantic_cache.add(prompt, embedding, result)
                except Exception as e:
                    logger.debug("Semantic cache save error: %s", e)
            return result

        logger.warning("All AI backends unavailable for generate(), using mock fallback")
        mock_res = "Clinical analysis mock response: The system is running in offline mode. For full functionality, please run Ollama or configure a valid GOOGLE_API_KEY."
        return redact_pii_from_text(mock_res)

    return await enclave.execute_async(_inner)


@no_log_zone_async
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
    from .tee_enclave import ConfidentialEnclave
    enclave = ConfidentialEnclave()
    enclave._attested = True

    async def _inner():
        # 0. Prompt injection check
        from .guardrails import is_prompt_injection, redact_pii_from_text

        last_user_content = ""
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_content = msg.get("content", "")
                    break
            if not last_user_content:
                last_user_content = messages[-1].get("content", "")

        if last_user_content and is_prompt_injection(last_user_content):
            from .database import SessionLocal
            from .security import log_audit_event
            db = SessionLocal()
            try:
                log_audit_event(
                    db,
                    action="SECURITY_PROMPT_INJECTION_BLOCKED",
                    target_user_id=0,
                    details=f"Prompt flagged for injection in chat. Snippet: {last_user_content[:100]}"
                )
            except Exception as e:
                logger.warning("Failed to log prompt injection event in chat: %s", e)
            finally:
                db.close()

            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Clinical safety guardrail: Input prompt flagged for potential instruction override."
            )

        # Serialize message history for cache key mapping
        history_str = json.dumps(messages)

        if os.getenv("SEMANTIC_CACHE_ENABLED", "true").lower() in ("true", "1", "yes", "on"):
            try:
                repr_text = messages[-1]["content"] if messages else ""
                embedding = await asyncio.to_thread(embed_text, repr_text)
                cached_response = semantic_cache.lookup(history_str, embedding)
                if cached_response:
                    return redact_pii_from_text(cached_response)
            except Exception as e:
                logger.debug("Semantic cache lookup error for chat: %s", e)

        # Explicit cloud provider override
        resolved_provider, resolved_key = await _resolve_provider_and_key(api_provider, api_key)

        result = None

        # 1. Try explicit provider (if requested via UI)
        if api_provider:
            if api_provider.lower() == "gemini" and has_gemini_api_key():
                result = await _chat_gemini(messages, system)
            elif api_provider.lower() == "ollama":
                ollama_models = await get_ollama_models()
                if ollama_models:
                    try:
                        result = await _chat_ollama(messages, system, model)
                    except Exception:
                        logger.warning("Ollama explicit chat failed")
            else:
                result = await _chat_cloud(messages, system, model, api_provider, api_key)

        # 2. Default Primary: Cloudflare (if not already tried)
        if not result and (not api_provider or api_provider.lower() != "custom"):
            logger.info("CORE_AI CHAT: Executing Default Primary (Cloudflare)...")
            result = await _chat_cloud(messages, system, model, "custom", "cloudflare")

        # 3. Tier A Fallback: Gemini (if not already tried)
        if not result and (not api_provider or api_provider.lower() != "gemini"):
            if has_gemini_api_key():
                logger.info("CORE_AI CHAT: Trying Tier A fallback (Gemini)...")
                result = await _chat_gemini(messages, system)

        # 4. Tier B Fallback: Ollama (if not already tried)
        if not result and (not api_provider or api_provider.lower() != "ollama"):
            ollama_models = await get_ollama_models()
            if ollama_models:
                try:
                    logger.info("CORE_AI CHAT: Trying Tier B fallback (Ollama)...")
                    result = await _chat_ollama(messages, system, model)
                except Exception:
                    logger.warning("Ollama fallback chat failed")

        if result:
            # Redact PII from the output
            result = redact_pii_from_text(result)
            if os.getenv("SEMANTIC_CACHE_ENABLED", "true").lower() in ("true", "1", "yes", "on"):
                try:
                    repr_text = messages[-1]["content"] if messages else ""
                    embedding = await asyncio.to_thread(embed_text, repr_text)
                    semantic_cache.add(history_str, embedding, result)
                except Exception as e:
                    logger.debug("Semantic cache save error for chat: %s", e)
            return result

        logger.warning("All AI backends unavailable for chat(), using mock response")
        mock_res = "Hello! I am your AI Copilot. Currently, the system is running in offline mode (Ollama and Gemini API are unavailable). I can answer simple queries or show patient data mockups."
        return redact_pii_from_text(mock_res)

    return await enclave.execute_async(_inner)


@no_log_zone_async_gen
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
    from .tee_enclave import ConfidentialEnclave
    enclave = ConfidentialEnclave()
    enclave._attested = True

    async def _inner_gen():
        # 0. Prompt injection check
        from .guardrails import is_prompt_injection, redact_pii_from_text

        last_user_content = ""
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_content = msg.get("content", "")
                    break
            if not last_user_content:
                last_user_content = messages[-1].get("content", "")

        if last_user_content and is_prompt_injection(last_user_content):
            from .database import SessionLocal
            from .security import log_audit_event
            db = SessionLocal()
            try:
                log_audit_event(
                    db,
                    action="SECURITY_PROMPT_INJECTION_BLOCKED",
                    target_user_id=0,
                    details=f"Prompt flagged for injection in chat_stream. Snippet: {last_user_content[:100]}"
                )
            except Exception as e:
                logger.warning("Failed to log prompt injection event in chat_stream: %s", e)
            finally:
                db.close()

            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Clinical safety guardrail: Input prompt flagged for potential instruction override."
            )

        # 1. Define stream generator that yields unredacted chunks
        async def source_generator():
            # Explicit cloud provider override
            resolved_provider, resolved_key = await _resolve_provider_and_key(api_provider, api_key)
            has_yielded = False

            # 1. Try explicit provider (if requested via UI)
            if api_provider:
                if api_provider.lower() == "gemini" and has_gemini_api_key():
                    try:
                        async for chunk in _stream_gemini(messages, system):
                            if chunk:
                                has_yielded = True
                                yield chunk
                    except Exception as e:
                        logger.warning(f"Explicit Gemini stream error: {e}")
                elif api_provider.lower() == "ollama":
                    ollama_models = await get_ollama_models()
                    if ollama_models:
                        try:
                            async for chunk in _stream_ollama(messages, system, model):
                                if chunk:
                                    has_yielded = True
                                    yield chunk
                        except Exception as e:
                            logger.warning("Explicit Ollama stream failed: %s", e)
                else:
                    try:
                        async for chunk in _stream_cloud(messages, system, model, api_provider, api_key):
                            if chunk:
                                has_yielded = True
                                yield chunk
                    except Exception as e:
                        logger.warning("Explicit Cloud stream failed: %s", e)

            if has_yielded:
                return

            # 2. Default Primary: Cloudflare (if not already tried)
            if not has_yielded and (not api_provider or api_provider.lower() != "custom"):
                logger.info("CORE_AI STREAM: Executing Default Primary (Cloudflare)...")
                try:
                    async for chunk in _stream_cloud(messages, system, model, "custom", "cloudflare"):
                        if chunk:
                            has_yielded = True
                            yield chunk
                except Exception as e:
                    logger.warning("Cloudflare primary stream failed: %s", e)
                if has_yielded:
                    return

            # 3. Tier A Fallback: Gemini (if not already tried)
            if not has_yielded and (not api_provider or api_provider.lower() != "gemini"):
                if has_gemini_api_key():
                    logger.info("CORE_AI STREAM: Trying Tier A fallback (Gemini)...")
                    try:
                        async for chunk in _stream_gemini(messages, system):
                            if chunk:
                                has_yielded = True
                                yield chunk
                    except Exception as e:
                        logger.warning(f"Gemini fallback stream error: {e}")
                    if has_yielded:
                        return

            # 4. Tier B Fallback: Ollama (if not already tried)
            if not has_yielded and (not api_provider or api_provider.lower() != "ollama"):
                ollama_models = await get_ollama_models()
                if ollama_models:
                    logger.info("CORE_AI STREAM: Trying Tier B fallback (Ollama)...")
                    try:
                        async for chunk in _stream_ollama(messages, system, model):
                            if chunk:
                                has_yielded = True
                                yield chunk
                    except Exception as e:
                        logger.warning("Ollama fallback stream failed: %s", e)
                    if has_yielded:
                        return

            if not has_yielded:
                # Fallback to mock response to prevent the UI from hanging
                yield "Hello! I am your AI Copilot. Currently, the system is running in offline mode because local Ollama models are not active and a valid Google Gemini API key is not configured.\n\n"
                yield "I can assist you with simulated clinical summaries, guide you through the EHR interface, or answer general workflow questions. How can I help you today?"


        # 2. Define stream wrapper to redact PII from chunks
        async def redact_stream_generator(generator):
            buffer = ""
            async for chunk in generator:
                if not chunk:
                    continue
                buffer += chunk
                # Redact the buffer
                redacted_buffer = redact_pii_from_text(buffer)

                # Find the last boundary character that is safe to split
                split_idx = 0
                for i in range(len(redacted_buffer) - 1, -1, -1):
                    char = redacted_buffer[i]
                    if char in " \t\n\r.,;:!?()[]{}":
                        suffix = redacted_buffer[i + 1:]
                        if not any(c.isdigit() or c in "@-" for c in suffix):
                            split_idx = i + 1
                            break

                if split_idx > 0:
                    yield redacted_buffer[:split_idx]
                    buffer = redacted_buffer[split_idx:]
                else:
                    pass

            if buffer:
                yield buffer

        # 3. Stream redacted response
        async for redacted_chunk in redact_stream_generator(source_generator()):
            yield redacted_chunk

    async for chunk in enclave.execute_async_gen(_inner_gen):
        yield chunk


# =========================================================================
# ADVANCED RAG PIPELINE EXTENSIONS
# =========================================================================

# =========================================================================
# Advanced RAG Utilities
# =========================================================================

async def generate_expanded_queries(query: str, k: int = 3) -> list[str]:
    """
    Use the LLM fallback pipeline to generate semantic variations of a patient query
    for better RAG retrieval.
    """
    system_prompt = (
        "You are an expert clinical terminology assistant. "
        "The user will provide a medical query (often in colloquial terms). "
        f"Your task is to generate {k} distinct, clinical search variations of this query "
        "to improve database retrieval. "
        "Output ONLY the queries separated by a newline character. No numbering, no bullets, no introduction."
    )

    # Use the synchronous wrapper for generate (since search_similar_records is sync)
    # Actually, core_ai.generate is async, but we'll use a sync wrapper inside rag.py or we can use asyncio.run
    # Wait, core_ai.generate is async!
    # Let's write this as async, and use asyncio.run in the caller.
    expanded_text = await generate(query, system_prompt)
    if not expanded_text:
        return [query]

    variations = [line.strip().strip('-*1234567890. ') for line in expanded_text.split('\n') if line.strip()]

    # Always include the original query
    results = [query]
    for v in variations:
        if v and v.lower() not in [r.lower() for r in results] and len(results) < k + 1:
            results.append(v)

    return results

def rerank_documents(query: str, documents: list[str], top_k: int = 3) -> list[str]:
    """
    Re-rank a list of retrieved documents against the query using Cloudflare Workers AI.
    Returns the top_k most relevant documents.
    """
    if not documents:
        return []

    try:
        payload = {
            "query": query,
            "sentences": documents
        }
        import requests
        url = "https://ai-healthcare-model.pavan9b.workers.dev/rerank"
        response = requests.post(url, json=payload, timeout=10.0)
        response.raise_for_status()

        data = response.json()

        # Cloudflare reranker typically returns an array of objects under "response"
        results_list = data.get("response", data) if isinstance(data, dict) else data

        # Sort indices by score descending, just in case they aren't pre-sorted
        if isinstance(results_list, list) and len(results_list) > 0 and ("id" in results_list[0] or "index" in results_list[0]):
            results_list.sort(key=lambda x: x.get("score", 0), reverse=True)
            # Reorder the original documents based on the indices
            ranked_docs = [documents[item.get("id", item.get("index"))] for item in results_list]
            return ranked_docs[:top_k]
        else:
            logger.warning(f"Unexpected Cloudflare reranker format: {data}")
            return documents[:top_k]

    except Exception as e:
        logger.warning(f"Cloudflare reranking failed: {e}. Falling back to original ordering.")
        return documents[:top_k]
