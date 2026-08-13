"""
FastAPI Routes for Multi-Cloud Healthcare Pipeline Mesh Orchestrator.
Exposes endpoints for auditing, monitoring, and triggering full-stack runs across
Doppler, Cloudflare Workers AI, Neon PostgreSQL, Databricks Free Edition, Kaggle GPU, and Hugging Face.
"""

from fastapi import APIRouter
from backend.pipeline_mesh_orchestrator import (
    pipeline_mesh_orchestrator,
    MeshPipelineRunRequest,
    MeshPipelineRunResult,
    DopplerSecretsBridge,
    CloudflareAIBridge,
    NeonPostgresBridge,
    DatabricksLakehouseBridge,
    KaggleGPUBridge,
    HuggingFaceSpacesBridge
)

router = APIRouter(prefix="/v1/mesh", tags=["Multi-Cloud Pipeline Mesh"])


@router.get("/status")
def get_mesh_status():
    """Returns the live connectivity status across all multi-cloud infrastructure nodes."""
    return {
        "doppler_secrets": DopplerSecretsBridge.resolve_secrets(),
        "cloudflare_ai": CloudflareAIBridge.check_health_and_warmup().model_dump(),
        "neon_postgres": NeonPostgresBridge.check_health_and_sync().model_dump(),
        "databricks_lakehouse": DatabricksLakehouseBridge.trigger_and_monitor("COHORT-AUDIT", 10).model_dump(),
        "kaggle_gpu": KaggleGPUBridge.dispatch_gpu_job("COHORT-AUDIT").model_dump(),
        "huggingface_spaces": HuggingFaceSpacesBridge.sync_and_verify_space().model_dump()
    }


@router.post("/run", response_model=MeshPipelineRunResult)
def trigger_mesh_pipeline_run(request: MeshPipelineRunRequest):
    """
    Triggers an end-to-end execution across the entire healthcare ecosystem:
    - Doppler Secret validation
    - Cloudflare Workers AI warm-up & inference check
    - Neon PostgreSQL database pooling check
    - Databricks Free Edition OMOP CDM & Quality Gates execution
    - Kaggle GPU deep inference acceleration
    - Hugging Face Spaces synchronization & deployment verification
    """
    return pipeline_mesh_orchestrator.execute_mesh_pipeline(request)
