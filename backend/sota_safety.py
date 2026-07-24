"""
AI Healthcare System — SOTA Clinical Safety & Guardrails Engine
================================================================
Provides state-of-the-art AI safety, adversarial jailbreak protection,
PHI redaction, and clinical disclaimer injection.
"""

import re
from typing import Tuple

ADVERSARIAL_PATTERNS = [
    r"ignore previous instructions",
    r"disregard all prior rules",
    r"system prompt leakage",
    r"jailbreak",
    r"dan mode",
]

MEDICAL_DISCLAIMER = (
    "\n\n[MEDICAL DISCLAIMER: This AI system provides information for educational "
    "and clinical decision-support purposes only. It is not a substitute for professional medical "
    "advice, diagnosis, or treatment. Always consult a qualified clinician for emergencies.]"
)


class SOTASafetyEngine:
    """Clinical Safety & Prompt Guardrails Processor."""

    def sanitize_user_prompt(self, prompt: str) -> Tuple[bool, str]:
        """
        Scans for adversarial jailbreak payloads.
        Returns (is_safe, sanitized_prompt_or_error).
        """
        lowered = prompt.lower()
        for pattern in ADVERSARIAL_PATTERNS:
            if re.search(pattern, lowered):
                return False, "Security Alert: Adversarial prompt injection detected and blocked."
        return True, prompt

    def redact_phi(self, text: str) -> str:
        """
        Redacts SSNs, phone numbers, and email patterns to protect PHI.
        """
        # Redact SSN
        text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", text)
        # Redact Phone
        text = re.sub(r"\b\d{3}-\d{3}-\d{4}\b", "[REDACTED_PHONE]", text)
        # Redact Email
        text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]", text)
        return text

    def apply_clinical_guardrails(self, response_text: str) -> str:
        """
        Applies automatic PII redaction and clinical disclaimer injection.
        """
        clean_text = self.redact_phi(response_text)
        if "[MEDICAL DISCLAIMER:" not in clean_text:
            clean_text += MEDICAL_DISCLAIMER
        return clean_text


sota_safety_engine = SOTASafetyEngine()
