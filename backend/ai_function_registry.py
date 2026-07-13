"""Static AI function governance inventory for backend clinical safety review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


class AIRegistryError(ValueError):
    """Raised when the AI function registry is internally inconsistent."""


GOVERNANCE_ANCHORS = [
    "WHO AI governance",
    "FDA clinical decision support transparency",
    "EU AI Act human oversight",
]


@dataclass(frozen=True)
class AIFunction:
    id: str
    name: str
    module: str
    endpoints: tuple[str, ...]
    audience: tuple[str, ...]
    risk_category: str
    clinical_safety_required: bool
    medical_disclaimer_required: bool
    human_review_required: bool
    basis_transparency_required: bool
    uses_ai_provider: bool
    provider_boundary: str
    prompt_keys: tuple[str, ...]
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "module": self.module,
            "endpoints": list(self.endpoints),
            "audience": list(self.audience),
            "risk_category": self.risk_category,
            "clinical_safety_required": self.clinical_safety_required,
            "medical_disclaimer_required": self.medical_disclaimer_required,
            "human_review_required": self.human_review_required,
            "basis_transparency_required": self.basis_transparency_required,
            "uses_ai_provider": self.uses_ai_provider,
            "provider_boundary": self.provider_boundary,
            "prompt_keys": list(self.prompt_keys),
            "notes": self.notes,
        }


AI_FUNCTIONS: tuple[AIFunction, ...] = (
    AIFunction(
        id="clinical_chat",
        name="Clinical chat assistant",
        module="backend.chat",
        endpoints=("/chat",),
        audience=("patient", "doctor", "admin"),
        risk_category="clinical_support",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=True,
        provider_boundary="backend.core_ai",
        prompt_keys=(),
        notes="Patient-facing advice is appended with a clinician-consult disclaimer.",
    ),
    AIFunction(
        id="streaming_clinical_chat",
        name="Streaming clinical chat assistant",
        module="backend.streaming_chat",
        endpoints=("/chat/stream",),
        audience=("patient", "doctor", "admin"),
        risk_category="clinical_support",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=True,
        provider_boundary="backend.core_ai",
        prompt_keys=(),
        notes="SSE responses append the same medical disclaimer after generated content.",
    ),
    AIFunction(
        id="risk_prediction",
        name="Disease risk prediction",
        module="backend.prediction",
        endpoints=(
            "/predict/diabetes",
            "/predict/heart",
            "/predict/kidney",
            "/predict/liver",
            "/predict/lungs",
        ),
        audience=("patient", "doctor", "admin"),
        risk_category="clinical_prediction",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=False,
        provider_boundary="backend.prediction.initialize_models",
        prompt_keys=(),
        notes="Local ML models return confidence, risk level, raw output, and disclaimer.",
    ),
    AIFunction(
        id="prediction_explanation",
        name="Prediction explanation",
        module="backend.explanation",
        endpoints=("/explain/", "/predict/explain/diabetes", "/predict/explain/heart", "/predict/explain/liver"),
        audience=("patient", "doctor", "admin"),
        risk_category="clinical_explanation",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=True,
        provider_boundary="backend.core_ai",
        prompt_keys=(),
        notes="Generated explanation text must remain supportive and clinician-reviewed.",
    ),
    AIFunction(
        id="lab_report_analysis",
        name="Lab report vision analysis",
        module="backend.report",
        endpoints=("/analyze/report",),
        audience=("patient", "doctor", "admin"),
        risk_category="clinical_document_ai",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=True,
        provider_boundary="backend.core_ai",
        prompt_keys=("lab_report_vision",),
        notes="Vision analysis uses the registered lab report prompt and adds a disclaimer.",
    ),
    AIFunction(
        id="health_report_generation",
        name="Health report generation",
        module="backend.main",
        endpoints=("/generate_report", "/reports/download/health-report"),
        audience=("patient", "doctor", "admin"),
        risk_category="clinical_document_generation",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=False,
        provider_boundary="backend.pdf_service",
        prompt_keys=(),
        notes="Report artifacts must remain advisory and clinician-reviewable.",
    ),
    AIFunction(
        id="clinical_rag_retrieval",
        name="Clinical RAG retrieval",
        module="backend.rag",
        endpoints=(),
        audience=("system",),
        risk_category="clinical_context_retrieval",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=True,
        provider_boundary="backend.core_ai",
        prompt_keys=(),
        notes="Embeddings must be delegated through core_ai and scoped to authorized user context.",
    ),
    AIFunction(
        id="agentic_scheduling",
        name="Agentic scheduling assistant",
        module="backend.appointments",
        endpoints=("/appointments/agent-chat", "/appointments/agent-stream"),
        audience=("patient", "doctor", "admin"),
        risk_category="clinical_triage_scheduling",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=True,
        provider_boundary="backend.core_ai",
        prompt_keys=("scheduling_system",),
        notes="Conversational assistant with symptom pre-screening warnings and SQLite booking write-back.",
    ),
)


def validate_ai_registry(registry: Iterable[AIFunction] = AI_FUNCTIONS) -> bool:
    seen_ids: set[str] = set()
    for function in registry:
        if function.id in seen_ids:
            raise AIRegistryError(f"Duplicate AI function id: {function.id}")
        seen_ids.add(function.id)
        if function.clinical_safety_required:
            if not function.medical_disclaimer_required:
                raise AIRegistryError(f"Medical disclaimer required for clinical AI function: {function.id}")
            if not function.human_review_required:
                raise AIRegistryError(f"Human review required for clinical AI function: {function.id}")
            if not function.basis_transparency_required:
                raise AIRegistryError(f"Basis transparency required for clinical AI function: {function.id}")
        if function.uses_ai_provider and function.provider_boundary != "backend.core_ai":
            raise AIRegistryError(f"AI provider boundary must be backend.core_ai for: {function.id}")
    return True


def list_ai_functions() -> list[dict[str, Any]]:
    validate_ai_registry()
    return [function.to_dict() for function in AI_FUNCTIONS]


def get_ai_function(function_id: str) -> dict[str, Any] | None:
    validate_ai_registry()
    for function in AI_FUNCTIONS:
        if function.id == function_id:
            return function.to_dict()
    return None


def contains_medical_disclaimer(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    has_consult = "consult" in normalized
    has_qualified_clinician = (
        "qualified healthcare professional" in normalized
        or "qualified clinician" in normalized
        or "doctor" in normalized
    )
    has_clinical_scope = (
        "medical decisions" in normalized
        or "diagnosis" in normalized
        or "treatment" in normalized
        or "emergencies" in normalized
    )
    return has_consult and has_qualified_clinician and has_clinical_scope


def registry_response() -> dict[str, Any]:
    return {
        "source": "backend.ai_function_registry",
        "governance_anchors": GOVERNANCE_ANCHORS,
        "functions": list_ai_functions(),
    }
