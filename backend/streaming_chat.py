"""
AI Healthcare System — SSE Streaming Chat Endpoint

Provides real-time streaming chat with RAG-powered medical context.
Adapted from Universe Dex chat_routes.py SSE architecture.

Endpoints:
  POST /chat/stream   — SSE streaming chat with heartbeat keepalive
  GET  /chat/context   — Returns assembled RAG context (for debugging)
  GET  /chat/suggestions — Dynamic starter questions

Features:
  - Server-Sent Events (SSE) with heartbeat keepalive
  - Multi-tier AI inference via core_ai.py
  - RAG context from chat_context.py
  - Cloud provider override via x-ai-provider / x-ai-api-key headers
"""

import asyncio
import json
import logging
import time
from typing import Optional, AsyncGenerator, List

from pydantic import BaseModel
from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from . import models, database, auth
from . import core_ai
from .chat_context import build_chat_context, get_suggested_questions
from .prompt_registry import get_prompt

logger = logging.getLogger(__name__)

# SSE Heartbeat interval (keeps connection alive through proxies)
SSE_HEARTBEAT_INTERVAL = 15.0

router = APIRouter(prefix="/chat", tags=["Streaming Chat"])


class StreamChatMessage(BaseModel):
    role: str
    content: str


class StreamChatRequest(BaseModel):
    message: str
    history: List[StreamChatMessage] = []
    model: Optional[str] = None


# ── SSE Streaming Chat ────────────────────────────────────────────────

@router.post("/stream")
async def stream_chat(
    req: StreamChatRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_ai_provider: Optional[str] = Header(None, alias="x-ai-provider"),
    x_ai_api_key: Optional[str] = Header(None, alias="x-ai-api-key"),
):
    """
    SSE streaming chat endpoint.

    Streams AI responses token-by-token with heartbeat keepalive.
    Uses RAG context from the patient's medical records.
    """
    question = req.message.strip()
    if not question:
        async def empty_gen():
            yield f"data: {json.dumps({'reply': 'How can I help you with your health today?', 'status': 'complete'})}\n\n"
        return StreamingResponse(empty_gen(), media_type="text/event-stream")

    ai_available = await core_ai.is_available() or (x_ai_provider and x_ai_api_key)

    if ai_available:
        # Build RAG context
        context, context_sources = build_chat_context(db, question, current_user)

        sources = []
        if context:
            sources.append({"title": "Medical Records", "content": context[:200] + "..."})
        for s in context_sources:
            sources.append({"title": s.get("name", "Source"), "content": f"Type: {s.get('type')}"})

        # Build chat history
        final_model = req.model or core_ai.OLLAMA_MODEL
        chat_history = [{"role": m.role, "content": m.content} for m in req.history]
        chat_history.append({"role": "user", "content": question})

        # Get system prompt from registry
        system_prompt = get_prompt("streaming_system").format(
            context=context[:2500] if len(context) > 2500 else context
        )

        async def stream_generator() -> AsyncGenerator[str, None]:
            """Robust streaming generator with heartbeat and error handling."""
            last_activity = time.time()

            try:
                # 1. Send sources immediately
                yield f"data: {json.dumps({'sources': sources, 'model': final_model, 'status': 'starting'})}\n\n"
                last_activity = time.time()

                # 2. Stream AI response with heartbeat
                chunk_queue: asyncio.Queue = asyncio.Queue()

                async def ai_stream_consumer():
                    """Consume AI stream and put chunks into queue."""
                    try:
                        async for chunk in core_ai.chat_stream(
                            chat_history[-4:],  # Keep context tight
                            system=system_prompt,
                            model=final_model,
                            api_provider=x_ai_provider,
                            api_key=x_ai_api_key,
                        ):
                            if chunk:
                                await chunk_queue.put(("chunk", chunk))
                        await chunk_queue.put(("done", None))
                    except Exception as e:
                        await chunk_queue.put(("error", str(e)))

                stream_task = asyncio.create_task(ai_stream_consumer())

                # Consume chunks with heartbeat
                while True:
                    try:
                        msg_type, data = await asyncio.wait_for(
                            chunk_queue.get(),
                            timeout=SSE_HEARTBEAT_INTERVAL,
                        )

                        if msg_type == "chunk":
                            yield f"data: {json.dumps({'reply': data})}\n\n"
                            last_activity = time.time()
                        elif msg_type == "error":
                            logger.error("AI stream error: %s", data)
                            yield f"data: {json.dumps({'error': data, 'status': 'error'})}\n\n"
                            break
                        elif msg_type == "done":
                            yield f"data: {json.dumps({'status': 'complete'})}\n\n"
                            break

                    except asyncio.TimeoutError:
                        elapsed = time.time() - last_activity
                        if elapsed >= SSE_HEARTBEAT_INTERVAL:
                            yield ":heartbeat (keepalive)\n\n"
                            last_activity = time.time()

            except Exception as e:
                logger.error("Chat streaming error: %s", e)
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    error_msg = "The AI is taking too long. Please try again or use a cloud provider."
                yield f"data: {json.dumps({'error': error_msg, 'status': 'error'})}\n\n"
            finally:
                if stream_task and not stream_task.done():
                    stream_task.cancel()

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Fallback mode (no AI available)
    context, _ = build_chat_context(db, question, current_user)
    fallback_msg = (
        f"I found the following from your records:\n\n{context}\n\n"
        "(AI response unavailable; showing raw data fallback)"
        if context
        else "I don't have enough data to answer that yet. Please complete a health checkup first."
    )

    async def fallback_generator():
        yield f"data: {json.dumps({'sources': [], 'model': 'fallback'})}\n\n"
        yield f"data: {json.dumps({'reply': fallback_msg})}\n\n"
        yield f"data: {json.dumps({'status': 'complete'})}\n\n"

    return StreamingResponse(
        fallback_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Context Endpoint (for debugging/transparency) ────────────────────

@router.get("/context")
def chat_context_endpoint(
    q: str = "",
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return assembled RAG context for a question (useful for debugging)."""
    question = q.strip()
    if not question:
        return {"context": "", "sources": []}

    context, sources = build_chat_context(db, question, current_user)
    return {
        "context": context[:2500] if len(context) > 2500 else context,
        "sources": sources,
    }


# ── Suggestions Endpoint ──────────────────────────────────────────────

@router.get("/suggestions")
def chat_suggestions(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return dynamic starter questions based on the patient's health data."""
    suggestions = get_suggested_questions(db, current_user)
    return {"suggestions": suggestions}
