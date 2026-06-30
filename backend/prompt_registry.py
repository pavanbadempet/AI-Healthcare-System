import logging
import sys
from types import ModuleType
from typing import Any

logger = logging.getLogger(__name__)

try:
    import clinical_rag_cache.prompt_registry as _pkg_prompts
except ImportError:
    _pkg_prompts = None


import os
import requests

def _call_get_prompt(name: str) -> str:
    service_url = os.environ.get("RAG_SERVICE_URL", "http://127.0.0.1:8002")
    res = requests.get(f"{service_url}/prompt/get", params={"name": name}, timeout=10)
    res.raise_for_status()
    return res.json()["prompt"]


class _PromptModule(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if os.environ.get("MICROSERVICES_MODE") == "true":
            if name == "get_prompt":
                return _call_get_prompt

        if _pkg_prompts is not None and hasattr(_pkg_prompts, name):
            return getattr(_pkg_prompts, name)
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if _pkg_prompts is not None and hasattr(_pkg_prompts, name):
            setattr(_pkg_prompts, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _PromptModule

# Populate globals with package attributes to make mock/patch happy
if _pkg_prompts is not None:
    for _name in dir(_pkg_prompts):
        if not _name.startswith("__"):
            globals()[_name] = getattr(_pkg_prompts, _name)

if _pkg_prompts is None:
    logger.warning("clinical-rag-cache package not installed. Running in mock/fallback mode.")

    SYSTEM_PROMPTS = {"chat": "You are a clinical AI assistant...", "summary": "Summarize the clinical note..."}

    CLINICAL_GUIDELINES = "Mock clinical guidelines. Always consult a qualified clinician."

    def get_prompt(name: str) -> str:
        return SYSTEM_PROMPTS.get(name, "You are a clinical AI assistant.")
