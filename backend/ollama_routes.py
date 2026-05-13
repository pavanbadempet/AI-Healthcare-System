import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/models", tags=["Ollama Models"])

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

class PullModelRequest(BaseModel):
    name: str

class DeleteModelRequest(BaseModel):
    name: str

@router.get("")
async def list_models():
    """List downloaded Ollama models."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                return {"available": True, "models": r.json().get("models", [])}
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")
    return {"available": False, "models": []}

@router.post("/pull")
async def pull_model(req: PullModelRequest):
    """Pull an Ollama model with streaming progress."""
    try:
        # Check if Ollama is running first
        async with httpx.AsyncClient(timeout=5) as client:
            await client.get(f"{OLLAMA_BASE_URL}/api/tags")
    except Exception:
        raise HTTPException(status_code=503, detail="Ollama is not running. Please start Ollama first.")

    async def stream_pull():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/pull", json={"name": req.name}) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield f"data: {json.dumps({'error': f'Ollama error {response.status_code}: {error_text.decode()}'})}\n\n"
                        return

                    # Parse the streaming JSON chunks
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if not line.strip():
                                continue
                            try:
                                data = json.loads(line)
                                status = data.get("status", "")
                                total = data.get("total", 0)
                                completed = data.get("completed", 0)
                                progress = (completed / total * 100) if total > 0 else 0
                                
                                yield f"data: {json.dumps({'status': status, 'progress': progress})}\n\n"
                            except Exception as e:
                                pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(stream_pull(), media_type="text/event-stream")

@router.delete("")
async def delete_model(req: DeleteModelRequest):
    """Delete an Ollama model."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.request("DELETE", f"{OLLAMA_BASE_URL}/api/delete", json={"name": req.name})
            if r.status_code == 200:
                return {"success": True}
            raise HTTPException(status_code=r.status_code, detail=r.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/library")
async def get_library():
    """Mock library of available models."""
    return {"catalog": [
        {"name": "llama3.2:1b", "label": "Llama 3.2 (1B)", "size": "1.3GB", "speed": "fastest", "quality": "good", "description": "Extremely fast, lightweight model perfect for low-end hardware."},
        {"name": "llama3.2", "label": "Llama 3.2 (3B)", "size": "2.0GB", "speed": "fast", "quality": "great", "description": "Highly capable 3B model for general chat and reasoning."},
        {"name": "llama3.1", "label": "Llama 3.1 (8B)", "size": "4.7GB", "speed": "medium", "quality": "excellent", "description": "Powerful 8B model with excellent reasoning capabilities."},
        {"name": "phi3:mini", "label": "Phi-3 Mini", "size": "2.3GB", "speed": "fast", "quality": "great", "description": "Microsoft's efficient 3.8B model."},
        {"name": "qwen2.5:0.5b", "label": "Qwen 2.5 (0.5B)", "size": "350MB", "speed": "fastest", "quality": "good", "description": "Ultra lightweight and fast."},
        {"name": "gemma2:2b", "label": "Gemma 2 (2B)", "size": "1.6GB", "speed": "fast", "quality": "great", "description": "Google's lightweight model."},
    ]}
