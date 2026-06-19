import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import auth, core_ai, models

router = APIRouter(prefix="/ai/models", tags=["Ollama Models"])
DELETE_MODEL_FAILURE_DETAIL = "Failed to delete model"

class PullModelRequest(BaseModel):
    name: str

class DeleteModelRequest(BaseModel):
    name: str


def require_admin_user(current_user: models.User = Depends(auth.get_current_user)) -> models.User:
    """Require admin privileges for mutating local model state."""
    if not auth.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


@router.get("")
async def list_models(
    _current_user: models.User = Depends(require_admin_user),
):
    """List downloaded Ollama models."""
    available = await core_ai.is_ollama_running()
    models = await core_ai.list_ollama_model_details() if available else []
    return {"available": available, "models": models}

@router.post("/pull")
async def pull_model(
    req: PullModelRequest,
    current_user: models.User = Depends(require_admin_user),
):
    """Pull an Ollama model with streaming progress."""
    if not await core_ai.is_ollama_running():
        raise HTTPException(status_code=503, detail="Ollama is not running. Please start Ollama first.")

    async def stream_pull():
        async for event in core_ai.stream_ollama_model_pull(req.name):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(stream_pull(), media_type="text/event-stream")

@router.delete("")
async def delete_model(
    req: DeleteModelRequest,
    current_user: models.User = Depends(require_admin_user),
):
    """Delete an Ollama model."""
    success, status_code, detail = await core_ai.delete_ollama_model(req.name)
    if success:
        return {"success": True}
    raise HTTPException(status_code=status_code, detail=DELETE_MODEL_FAILURE_DETAIL)

@router.get("/library")
async def get_library(
    _current_user: models.User = Depends(require_admin_user),
):
    """Mock library of available models."""
    return {"catalog": [
        {"name": "llama3.2:1b", "label": "Llama 3.2 (1B)", "size": "1.3GB", "speed": "fastest", "quality": "good", "description": "Extremely fast, lightweight model perfect for low-end hardware."},
        {"name": "llama3.2", "label": "Llama 3.2 (3B)", "size": "2.0GB", "speed": "fast", "quality": "great", "description": "Highly capable 3B model for general chat and reasoning."},
        {"name": "llama3.1", "label": "Llama 3.1 (8B)", "size": "4.7GB", "speed": "medium", "quality": "excellent", "description": "Powerful 8B model with excellent reasoning capabilities."},
        {"name": "phi3:mini", "label": "Phi-3 Mini", "size": "2.3GB", "speed": "fast", "quality": "great", "description": "Microsoft's efficient 3.8B model."},
        {"name": "qwen2.5:0.5b", "label": "Qwen 2.5 (0.5B)", "size": "350MB", "speed": "fastest", "quality": "good", "description": "Ultra lightweight and fast."},
        {"name": "gemma2:2b", "label": "Gemma 2 (2B)", "size": "1.6GB", "speed": "fast", "quality": "great", "description": "Google's lightweight model."},
    ]}
