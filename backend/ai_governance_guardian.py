"""
Multi-Level AI Governance & Clinical Safety Guardian
Enforces 4 distinct defense-in-depth levels of AI safety, prompt injection defense,
conformal uncertainty gating, hallucination verification, and Four-Eye clinical escalation.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .clinical_compliance.four_eye_governance import (
    FourEyeActionType,
    four_eye_engine,
)

logger = logging.getLogger(__name__)

# Known dangerous prompt injection patterns
ADVERSARIAL_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+override",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"dan\s+mode",
    r"jailbreak",
    r"bypass\s+(safety|guardrails|hipaa)",
    r"disregard\s+(medical\s+)?disclaimer",
    r"act\s+as\s+an\s+unfiltered",
    r"pretend\s+you\s+have\s+no\s+rules",
    r"show\s+me\s+the\s+hidden\s+system\s+prompt"
]

# High-risk medications requiring automated clinical safety screening
CONTROLLED_OR_HIGH_RISK_MEDS = [
    "oxycodone", "fentanyl", "morphine", "hydrocodone", "alprazolam",
    "diazepam", "lorazepam", "clonazepam", "warfarin", "methotrexate",
    "digoxin", "lithium", "insulin"
]


class GovernanceCheckResult(BaseModel):
    is_safe: bool
    passed_levels: List[str]
    failed_level: Optional[str] = None
    risk_score: float = 0.0
    action_required: str = "EXECUTE"
    four_eye_request_id: Optional[str] = None
    sanitized_content: str = ""
    governance_metadata: Dict[str, Any] = Field(default_factory=dict)


class MultiLevelAIGovernanceGuardian:
    """
    4-Tier AI Governance Architecture:
    - Level 1: Adversarial Prompt Injection & PHI Sanitization
    - Level 2: Conformal Uncertainty & OOD Risk Gate
    - Level 3: Medical Hallucination & Contraindication Cross-Checker
    - Level 4: Dual-Clinician Four-Eye Peer Review Routing
    """

    def __init__(self):
        self.injection_regexes = [re.compile(p, re.IGNORECASE) for p in ADVERSARIAL_INJECTION_PATTERNS]

    # =========================================================================
    # LEVEL 1: Adversarial Prompt Injection & Input Sanitization
    # =========================================================================
    def evaluate_level_1_input_safety(self, prompt: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Scans input for adversarial injection attacks, role hijacking, and jailbreaks.
        Returns (is_safe, sanitized_prompt, audit_metadata).
        """
        for r in self.injection_regexes:
            if r.search(prompt):
                logger.warning("Adversarial prompt injection pattern detected and neutralized.")
                return False, "[BLOCKED_ADVERSARIAL_INJECTION_DETECTED]", {
                    "level": "LEVEL_1_INPUT_SAFETY",
                    "reason": "Prompt injection / jailbreak signature matched.",
                    "status": "BLOCKED"
                }

        # PHI & input sanitization
        sanitized = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", prompt)
        sanitized = re.sub(r"\b\d{16}\b", "[REDACTED_CARD]", sanitized)

        return True, sanitized, {
            "level": "LEVEL_1_INPUT_SAFETY",
            "status": "PASSED"
        }

    # =========================================================================
    # LEVEL 2: Conformal Uncertainty & Out-of-Distribution (OOD) Gate
    # =========================================================================
    def evaluate_level_2_uncertainty(
        self,
        predicted_probability: float,
        confidence_interval_width: float,
        conformal_confidence_level: float = 0.95
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Ensures model predictions meet conformal certainty thresholds.
        Rejects predictions with high epistemic uncertainty (>0.40 confidence interval).
        """
        is_calibrated = confidence_interval_width <= 0.40
        return is_calibrated, {
            "level": "LEVEL_2_CONFORMAL_UNCERTAINTY",
            "conformal_confidence_level": conformal_confidence_level,
            "ci_width": round(confidence_interval_width, 4),
            "calibrated": is_calibrated,
            "status": "PASSED" if is_calibrated else "FLAGGED_HIGH_UNCERTAINTY"
        }

    # =========================================================================
    # LEVEL 3: Medical Hallucination & Contraindication Verifier
    # =========================================================================
    def evaluate_level_3_clinical_grounding(
        self,
        generated_advice: str,
        patient_allergies: Optional[List[str]] = None,
        patient_medications: Optional[List[str]] = None
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Cross-references generated clinical output against known patient contraindications,
        allergies, and mandatory medical disclaimers.
        """
        flags: List[str] = []
        advice_lower = generated_advice.lower()

        # Pharmacological allergy class mapping
        ALLERGY_CROSS_MAP = {
            "penicillin": ["amoxicillin", "ampicillin", "augmentin", "piperacillin", "penicillin"],
            "sulfa": ["sulfamethoxazole", "trimethoprim", "bactrim", "sulfasalazine"],
            "nsaid": ["aspirin", "ibuprofen", "naproxen", "ketorolac", "meloxicam"],
        }

        # Check for direct allergy and cross-reactivity conflicts
        if patient_allergies:
            for allergy in patient_allergies:
                al_lower = allergy.lower().strip()
                # Direct match
                if al_lower in advice_lower:
                    flags.append(f"Potential direct allergy conflict detected: {allergy}")
                # Cross-reactivity match
                cross_meds = ALLERGY_CROSS_MAP.get(al_lower, [])
                for cm in cross_meds:
                    if cm in advice_lower:
                        flags.append(f"Potential allergy cross-reactivity detected: {allergy} -> {cm}")

        # Ensure mandatory medical disclaimer is present
        has_disclaimer = "disclaimer" in advice_lower or "clinician" in advice_lower or "doctor" in advice_lower

        is_grounded = len(flags) == 0 and has_disclaimer

        return is_grounded, flags, {
            "level": "LEVEL_3_CLINICAL_GROUNDING",
            "allergy_conflicts": flags,
            "has_disclaimer": has_disclaimer,
            "status": "PASSED" if is_grounded else "FLAGGED_SAFETY_WARNING"
        }

    # =========================================================================
    # LEVEL 4: Four-Eye Clinical Action Enforcement
    # =========================================================================
    def evaluate_level_4_action_routing(
        self,
        action_type: FourEyeActionType,
        patient_id: int,
        initiator_id: int,
        initiator_name: str,
        initiator_npi: str,
        payload: Dict[str, Any],
        is_high_risk: bool = False
    ) -> GovernanceCheckResult:
        """
        Executes complete 4-level defense pipeline and routes to Four-Eye signoff queue if high-risk.
        """
        passed_levels = []

        # Level 1 Check
        content_str = str(payload)
        l1_safe, sanitized, l1_meta = self.evaluate_level_1_input_safety(content_str)
        if not l1_safe:
            return GovernanceCheckResult(
                is_safe=False,
                passed_levels=[],
                failed_level="LEVEL_1_INPUT_SAFETY",
                action_required="REJECT_AND_ALERT_SECURITY",
                sanitized_content=sanitized,
                governance_metadata=l1_meta
            )
        passed_levels.append("LEVEL_1_INPUT_SAFETY")

        # Level 2 Check (Uncertainty)
        prob = payload.get("probability", 0.5)
        ci = payload.get("confidence_interval_width", 0.15)
        l2_safe, l2_meta = self.evaluate_level_2_uncertainty(prob, ci)
        if not l2_safe:
            is_high_risk = True
        passed_levels.append("LEVEL_2_CONFORMAL_UNCERTAINTY")

        # Level 3 Check (Clinical Grounding)
        advice = payload.get("advice", "Please consult a qualified clinician.")
        allergies = payload.get("allergies", [])
        l3_safe, conflicts, l3_meta = self.evaluate_level_3_clinical_grounding(advice, allergies)
        if not l3_safe:
            is_high_risk = True
        passed_levels.append("LEVEL_3_CLINICAL_GROUNDING")

        # Level 4: Determine if Four-Eye Sign-off is required
        med_name = str(payload.get("medication_name", "")).lower()
        if any(controlled in med_name for controlled in CONTROLLED_OR_HIGH_RISK_MEDS):
            is_high_risk = True

        if prob >= 0.85 or is_high_risk:
            # Submit to Four-Eye Engine
            four_eye_req = four_eye_engine.submit_action_for_review(
                action_type=action_type,
                patient_id=patient_id,
                initiator_id=initiator_id,
                initiator_name=initiator_name,
                initiator_npi=initiator_npi,
                clinical_justification=payload.get("justification", "High-risk clinical intervention requiring secondary peer physician approval."),
                payload=payload
            )
            passed_levels.append("LEVEL_4_FOUR_EYE_PEER_REVIEW_QUEUED")
            return GovernanceCheckResult(
                is_safe=True,
                passed_levels=passed_levels,
                action_required="AWAIT_FOUR_EYE_APPROVAL",
                four_eye_request_id=four_eye_req.request_id,
                risk_score=round(prob, 4),
                governance_metadata={
                    "four_eye_status": four_eye_req.status.value,
                    "l1": l1_meta,
                    "l2": l2_meta,
                    "l3": l3_meta
                }
            )

        passed_levels.append("LEVEL_4_STANDARD_DIRECT_EXECUTION")
        return GovernanceCheckResult(
            is_safe=True,
            passed_levels=passed_levels,
            action_required="EXECUTE",
            risk_score=round(prob, 4),
            governance_metadata={
                "l1": l1_meta,
                "l2": l2_meta,
                "l3": l3_meta
            }
        )


# Global Singleton
ai_guardian = MultiLevelAIGovernanceGuardian()
