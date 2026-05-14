"""
AI Healthcare System — Version-Controlled Prompt Registry

Every prompt used in the system is registered, versioned, and auditable.
This prevents silent prompt drift and enables A/B testing of prompts.

Usage:
    from backend.prompt_registry import get_prompt, register_prompt

    # Get the active prompt
    template = get_prompt("medical_qa")

    # Register a new version
    register_prompt("medical_qa", version="2.0", template="You are a medical expert...")

Ported from Universe Dex Singularity AI Engine, adapted for healthcare domain.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """A single version of a prompt template."""
    name: str
    version: str
    template: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    active: bool = True


class PromptRegistry:
    """
    Central registry for all prompt templates.

    Supports versioning, activation/deactivation, and A/B testing.
    """

    def __init__(self):
        self._prompts: dict[str, list[PromptVersion]] = {}
        self._active: dict[str, str] = {}  # name → active version
        self._register_defaults()

    def register(
        self,
        name: str,
        version: str,
        template: str,
        description: str = "",
        activate: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> PromptVersion:
        """Register a new prompt version."""
        prompt = PromptVersion(
            name=name,
            version=version,
            template=template,
            description=description,
            metadata=metadata or {},
            active=activate,
        )

        if name not in self._prompts:
            self._prompts[name] = []

        # Check for duplicate version — update in place
        for existing in self._prompts[name]:
            if existing.version == version:
                existing.template = template
                existing.description = description
                existing.metadata = metadata or {}
                logger.info("Updated prompt: %s v%s", name, version)
                if activate:
                    self._active[name] = version
                return existing

        self._prompts[name].append(prompt)

        if activate:
            self._active[name] = version

        logger.info("Registered prompt: %s v%s (active=%s)", name, version, activate)
        return prompt

    def get(self, name: str, version: str | None = None) -> str:
        """
        Get a prompt template by name.

        If version is None, returns the active version.
        """
        if name not in self._prompts:
            raise KeyError(f"Unknown prompt: {name}")

        target_version = version or self._active.get(name)
        if not target_version:
            raise KeyError(f"No active version for prompt: {name}")

        for prompt in self._prompts[name]:
            if prompt.version == target_version:
                return prompt.template

        raise KeyError(f"Version {target_version} not found for prompt: {name}")

    def get_info(self, name: str) -> dict:
        """Get metadata about a prompt and its versions."""
        if name not in self._prompts:
            raise KeyError(f"Unknown prompt: {name}")

        versions = self._prompts[name]
        active_version = self._active.get(name, "")

        return {
            "name": name,
            "active_version": active_version,
            "versions": [
                {
                    "version": v.version,
                    "description": v.description,
                    "active": v.version == active_version,
                    "created_at": v.created_at,
                    "template_length": len(v.template),
                }
                for v in versions
            ],
        }

    def activate(self, name: str, version: str) -> None:
        """Set a specific version as the active prompt."""
        if name not in self._prompts:
            raise KeyError(f"Unknown prompt: {name}")
        found = any(v.version == version for v in self._prompts[name])
        if not found:
            raise KeyError(f"Version {version} not found for prompt: {name}")
        self._active[name] = version
        logger.info("Activated prompt: %s v%s", name, version)

    def list_all(self) -> list[dict]:
        """List all registered prompts with their active versions."""
        return [
            {
                "name": name,
                "active_version": self._active.get(name, ""),
                "total_versions": len(versions),
            }
            for name, versions in self._prompts.items()
        ]

    def summary(self) -> dict:
        """Return a summary of the registry state."""
        return {
            "total_prompts": len(self._prompts),
            "total_versions": sum(len(v) for v in self._prompts.values()),
            "prompts": self.list_all(),
        }

    # ── Healthcare Domain Default Prompts ─────────────────────────────

    def _register_defaults(self) -> None:
        """Register the default healthcare system prompts."""

        self.register(
            "chat_system",
            version="1.0",
            template=(
                "You are an AI Medical Health Assistant for a healthcare platform.\n\n"
                "Patient Profile:\n{user_profile}\n\n"
                "Medical History:\n{medical_history}\n\n"
                "Past Interactions (RAG Memory):\n{rag_context}\n\n"
                "Web Research Context:\n{web_context}\n\n"
                "Instructions:\n"
                "- Engagement Style: {engagement_style}\n"
                "- Personalize responses using the patient's name and history.\n"
                "- Be supportive, empathetic, and pragmatic.\n"
                "- Suggest relevant health tips or follow-up actions.\n"
                "- SAFETY: If symptoms suggest emergency (chest pain, stroke signs, severe bleeding), "
                "advise calling emergency services immediately.\n"
                "- DISCLAIMER: Always clarify you are an AI assistant, not a licensed physician. "
                "Recommend consulting a healthcare professional for medical decisions.\n"
                "- Keep responses concise and readable.\n\n"
                "CRITICAL — DATA PRIVACY & MEMORY:\n"
                "- You HAVE access to this patient's secure medical records and past conversations "
                "(provided above).\n"
                "- If the patient asks if you 'remember' or 'store data', say: 'Yes, I can securely "
                "recall your past checkups and conversations to help you better.'\n"
                "- DO NOT give generic 'I am an AI who doesn't store data' responses."
            ),
            description="Main system prompt for the medical chatbot with full context injection",
        )

        self.register(
            "medical_qa",
            version="1.0",
            template=(
                "You are a knowledgeable medical information assistant.\n"
                "Answer the patient's question using ONLY the context provided below.\n"
                "If the context doesn't contain enough information, say so honestly.\n"
                "Cite sources by referencing record types in brackets like [Diabetes Checkup].\n\n"
                "IMPORTANT: Always include the disclaimer that this is AI-generated information "
                "and not a substitute for professional medical advice.\n\n"
                "--- MEDICAL CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
                "Question: {query}\n\n"
                "Answer:"
            ),
            description="RAG-grounded medical Q&A with citation requirements",
        )

        self.register(
            "symptom_analysis",
            version="1.0",
            template=(
                "You are a medical symptom analysis assistant.\n\n"
                "Patient Profile: {user_profile}\n"
                "Reported Symptoms: {symptoms}\n"
                "Medical History: {medical_history}\n\n"
                "Provide:\n"
                "1. A brief analysis of the reported symptoms\n"
                "2. Possible conditions to discuss with a doctor (NOT a diagnosis)\n"
                "3. Recommended next steps (lifestyle changes, tests, specialist referrals)\n"
                "4. Red flags that require immediate medical attention\n\n"
                "DISCLAIMER: This is AI-generated information for educational purposes only. "
                "It is NOT a medical diagnosis. Please consult a healthcare professional.\n\n"
                "Analysis:"
            ),
            description="Structured symptom analysis with safety disclaimers",
        )

        self.register(
            "report_summary",
            version="1.0",
            template=(
                "You are a medical report summarizer.\n\n"
                "Summarize the following health records for the patient in plain, "
                "easy-to-understand language.\n\n"
                "Patient: {patient_name}\n"
                "Records:\n{records}\n\n"
                "Provide:\n"
                "1. Overall health trend (improving, stable, declining)\n"
                "2. Key findings from recent checkups\n"
                "3. Areas of concern\n"
                "4. Positive indicators\n\n"
                "DISCLAIMER: This summary is AI-generated. Consult your doctor for "
                "authoritative interpretation of your medical records.\n\n"
                "Summary:"
            ),
            description="Health record summarization in plain language",
        )

        self.register(
            "risk_assessment",
            version="1.0",
            template=(
                "You are a health risk assessment assistant.\n\n"
                "Based on the following prediction results and patient data, provide a "
                "clear explanation of the risk assessment.\n\n"
                "Patient Profile: {user_profile}\n"
                "Prediction Type: {prediction_type}\n"
                "Prediction Result: {prediction}\n"
                "Confidence: {confidence}%\n"
                "Input Data: {input_data}\n\n"
                "Provide:\n"
                "1. What the prediction means in plain language\n"
                "2. Key risk factors identified from the input data\n"
                "3. Actionable lifestyle recommendations\n"
                "4. When to see a doctor\n\n"
                "DISCLAIMER: This AI risk assessment is for informational purposes only. "
                "It is not a medical diagnosis. Please consult a healthcare professional "
                "for personalized medical advice.\n\n"
                "Assessment:"
            ),
            description="Disease risk prediction explanation and recommendations",
        )

        self.register(
            "streaming_system",
            version="1.0",
            template=(
                "You are the AI Health Copilot for a healthcare platform. "
                "Answer concisely using only the medical data provided below.\n\n"
                "{context}"
            ),
            description="Compact system prompt for streaming chat (token-efficient)",
        )


# ── Global Singleton ──────────────────────────────────────────────────

_registry: PromptRegistry | None = None


def get_prompt_registry() -> PromptRegistry:
    """Get the global prompt registry."""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


def get_prompt(name: str, version: str | None = None) -> str:
    """Convenience: get a prompt template by name."""
    return get_prompt_registry().get(name, version)


def register_prompt(name: str, version: str, template: str, **kwargs) -> PromptVersion:
    """Convenience: register a new prompt version."""
    return get_prompt_registry().register(name, version, template, **kwargs)
#   i 1 8 n   p r o m p t   s u p p o r t   -   W I P  
 