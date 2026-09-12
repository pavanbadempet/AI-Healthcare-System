"""Metacognitive Epistemic Calibrator & Autonomous Safety Yield.

Calculates model self-uncertainty (epistemic confidence bounds), identifies critical
diagnostic gaps, and enforces autonomous safety yielding to human attending physicians
whenever uncertainty exceeds clinical risk thresholds (U > tau_safe).
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, List, Optional


class MetacognitiveAssessment:
    """Evaluation of an agent's self-reflective uncertainty and human escalation requirements."""

    def __init__(
        self,
        assessment_id: str,
        clinical_claim: str,
        epistemic_uncertainty: float,
        safe_threshold: float,
        autonomous_execution_permitted: bool,
        yield_decision: str,
        identified_knowledge_gaps: List[str],
        clinician_escalation_brief: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime.datetime] = None,
    ) -> None:
        self.assessment_id = assessment_id
        self.clinical_claim = clinical_claim
        self.epistemic_uncertainty = epistemic_uncertainty
        self.safe_threshold = safe_threshold
        self.autonomous_execution_permitted = autonomous_execution_permitted
        self.yield_decision = yield_decision  # AUTONOMOUS_EXECUTION_SAFE, YIELD_TO_HUMAN_CLINICIAN
        self.identified_knowledge_gaps = identified_knowledge_gaps
        self.clinician_escalation_brief = clinician_escalation_brief
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "clinical_claim": self.clinical_claim,
            "epistemic_uncertainty": round(self.epistemic_uncertainty, 4),
            "safe_threshold": self.safe_threshold,
            "autonomous_execution_permitted": self.autonomous_execution_permitted,
            "yield_decision": self.yield_decision,
            "identified_knowledge_gaps": self.identified_knowledge_gaps,
            "clinician_escalation_brief": self.clinician_escalation_brief,
            "timestamp": self.timestamp.isoformat(),
        }


class MetacognitiveCalibrator:
    """Self-reflection engine evaluating confidence bounds and safety yields."""

    def __init__(self, default_safe_threshold: float = 0.35) -> None:
        self.default_safe_threshold = default_safe_threshold

    def evaluate_epistemic_confidence(
        self,
        clinical_claim: str,
        available_evidence: List[str],
        missing_observations: List[str],
        acuity_level: str = "HIGH",  # CRITICAL, HIGH, MODERATE, LOW
    ) -> MetacognitiveAssessment:
        """Compute epistemic uncertainty and determine if the agent must yield control to humans."""
        aid = str(uuid.uuid4())

        # Dynamic threshold based on patient clinical acuity
        threshold_map = {
            "CRITICAL": 0.20,
            "HIGH": 0.35,
            "MODERATE": 0.50,
            "LOW": 0.65,
        }
        threshold = threshold_map.get(acuity_level.upper(), self.default_safe_threshold)

        # Calculate Epistemic Uncertainty (U in [0.0, 1.0])
        # Penalty for missing diagnostic observations
        gap_penalty = min(len(missing_observations) * 0.15, 0.60)
        # Evidence sufficiency factor
        evidence_credit = min(len(available_evidence) * 0.10, 0.40)

        raw_uncertainty = 0.20 + gap_penalty - evidence_credit
        uncertainty = max(0.05, min(0.95, raw_uncertainty))

        should_yield = uncertainty > threshold
        yield_decision = "YIELD_TO_HUMAN_CLINICIAN" if should_yield else "AUTONOMOUS_EXECUTION_SAFE"

        escalation_brief = None
        if should_yield:
            escalation_brief = {
                "headline": f"AUTONOMOUS YIELD: Epistemic Uncertainty {round(uncertainty, 3)} exceeds safety floor {threshold}",
                "primary_clinical_concern": f"Unverified hypothesis: '{clinical_claim}'",
                "missing_critical_diagnostics": missing_observations,
                "recommended_physician_actions": [
                    f"Perform bedside physical examination to confirm '{clinical_claim}'",
                    f"Order targeted diagnostics: {', '.join(missing_observations)}",
                    "Sign or modify proposed intervention before execution",
                ],
            }

        return MetacognitiveAssessment(
            assessment_id=aid,
            clinical_claim=clinical_claim,
            epistemic_uncertainty=uncertainty,
            safe_threshold=threshold,
            autonomous_execution_permitted=(not should_yield),
            yield_decision=yield_decision,
            identified_knowledge_gaps=missing_observations,
            clinician_escalation_brief=escalation_brief,
        )
