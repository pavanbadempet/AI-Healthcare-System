"""Metacognitive Epistemic Calibrator & Autonomous Safety Yield.

Calculates model self-uncertainty (epistemic confidence bounds), identifies critical
diagnostic gaps, and enforces autonomous safety yielding to human attending physicians
whenever uncertainty exceeds clinical risk thresholds (U > tau_safe).
"""

from __future__ import annotations

import datetime
import math
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
        self.epistemic_uncertainty = float(epistemic_uncertainty)
        self.safe_threshold = float(safe_threshold)
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


class SwarmEpistemicAssessment:
    """Evaluation of epistemic uncertainty and consensus coherence across a clinical agent swarm."""

    def __init__(
        self,
        assessment_id: str,
        swarm_uncertainty: float,
        safe_threshold: float,
        autonomous_execution_permitted: bool,
        yield_decision: str,
        agent_uncertainties: Dict[str, float],
        confidence_dispersion: float,
        identified_conflicts: List[str],
        clinician_escalation_brief: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime.datetime] = None,
    ) -> None:
        self.assessment_id = assessment_id
        self.swarm_uncertainty = float(swarm_uncertainty)
        self.safe_threshold = float(safe_threshold)
        self.autonomous_execution_permitted = autonomous_execution_permitted
        self.yield_decision = yield_decision  # AUTONOMOUS_EXECUTION_SAFE, YIELD_TO_HUMAN_CLINICIAN
        self.agent_uncertainties = agent_uncertainties
        self.confidence_dispersion = float(confidence_dispersion)
        self.identified_conflicts = identified_conflicts
        self.clinician_escalation_brief = clinician_escalation_brief
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "swarm_uncertainty": round(self.swarm_uncertainty, 4),
            "safe_threshold": self.safe_threshold,
            "autonomous_execution_permitted": self.autonomous_execution_permitted,
            "yield_decision": self.yield_decision,
            "agent_uncertainties": {k: round(v, 4) for k, v in self.agent_uncertainties.items()},
            "confidence_dispersion": round(self.confidence_dispersion, 4),
            "identified_conflicts": self.identified_conflicts,
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

    def evaluate_swarm_proposals(
        self,
        proposals: List[Any],
        patient_context: Optional[Dict[str, Any]] = None,
        acuity_level: str = "HIGH",
        safe_threshold: Optional[float] = None,
    ) -> SwarmEpistemicAssessment:
        """Calculate epistemic uncertainty across swarm agent proposals and enforce safety yield."""
        aid = str(uuid.uuid4())

        threshold_map = {
            "CRITICAL": 0.20,
            "HIGH": 0.35,
            "MODERATE": 0.50,
            "LOW": 0.65,
        }
        threshold = safe_threshold if safe_threshold is not None else threshold_map.get(
            acuity_level.upper(), self.default_safe_threshold
        )

        if not proposals:
            return SwarmEpistemicAssessment(
                assessment_id=aid,
                swarm_uncertainty=0.95,
                safe_threshold=threshold,
                autonomous_execution_permitted=False,
                yield_decision="YIELD_TO_HUMAN_CLINICIAN",
                agent_uncertainties={},
                confidence_dispersion=0.0,
                identified_conflicts=["No agent proposals available for swarm deliberation"],
                clinician_escalation_brief={
                    "headline": "AUTONOMOUS YIELD: Empty swarm proposal set",
                    "primary_clinical_concern": "Clinical decision cannot proceed without specialist input",
                    "recommended_physician_actions": ["Evaluate patient directly"],
                },
            )

        agent_uncertainties: Dict[str, float] = {}
        confidences: List[float] = []
        identified_conflicts: List[str] = []

        all_actions: List[str] = []
        has_safety_hold = False

        for i, prop in enumerate(proposals):
            name = getattr(prop, "agent_name", None) or (
                prop.get("agent_name") if isinstance(prop, dict) else None
            ) or f"agent_{i+1}"

            conf = getattr(prop, "epistemic_confidence", None)
            if conf is None and isinstance(prop, dict):
                conf = prop.get("epistemic_confidence", 0.9)
            conf_val = float(conf if conf is not None else 0.9)
            conf_val = max(0.0, min(1.0, conf_val))

            confidences.append(conf_val)
            unc = 1.0 - conf_val
            agent_uncertainties[name] = unc

            # Extract actions / recommendations to detect divergence
            recs = getattr(prop, "recommendations", None) or (
                prop.get("recommendations") if isinstance(prop, dict) else []
            )
            for r in recs:
                r_str = str(r).lower()
                all_actions.append(r_str)
                if "hold" in r_str or "contraindicated" in r_str or "veto" in r_str or "refute" in r_str:
                    has_safety_hold = True

        n = len(confidences)
        mean_conf = sum(confidences) / n
        mean_uncertainty = sum(agent_uncertainties.values()) / n

        # Dispersion: sample standard deviation
        variance = sum((c - mean_conf) ** 2 for c in confidences) / n
        dispersion = math.sqrt(variance)

        # Conflict penalty: if an agent calls for hold/veto while others propose starting treatment
        conflict_penalty = 0.0
        has_active_treatment = any(
            any(kw in act for kw in ["prescribe", "initiate", "give", "administer", "infuse", "surgery", "resection"])
            for act in all_actions
        )
        if has_safety_hold and has_active_treatment:
            conflict_penalty += 0.25
            identified_conflicts.append("Specialist disagreement: active intervention proposed alongside safety hold / contraindication")

        # Disagreement penalty if confidence dispersion is high
        if dispersion > 0.20:
            conflict_penalty += min(0.15, dispersion * 0.5)
            identified_conflicts.append(f"High confidence variance across swarm specialists (dispersion: {round(dispersion, 3)})")

        # Missing observations in patient profile
        context = patient_context or {}
        gaps = context.get("missing_observations", [])
        gap_penalty = min(0.20, len(gaps) * 0.05)
        if gaps:
            identified_conflicts.append(f"Missing clinical observations: {', '.join(str(g) for g in gaps[:3])}")

        # Aggregate Swarm Epistemic Uncertainty U
        raw_swarm_u = mean_uncertainty + (1.5 * variance) + conflict_penalty + gap_penalty
        swarm_uncertainty = max(0.05, min(0.98, raw_swarm_u))

        should_yield = swarm_uncertainty > threshold
        yield_decision = "YIELD_TO_HUMAN_CLINICIAN" if should_yield else "AUTONOMOUS_EXECUTION_SAFE"

        escalation_brief = None
        if should_yield:
            escalation_brief = {
                "headline": f"AUTONOMOUS YIELD: Swarm Epistemic Uncertainty {round(swarm_uncertainty, 3)} exceeds safety floor {threshold}",
                "primary_clinical_concern": "Clinical disagreement or elevated epistemic uncertainty across specialist swarm",
                "participating_agents": list(agent_uncertainties.keys()),
                "highest_uncertainty_agent": max(agent_uncertainties.items(), key=lambda x: x[1])[0],
                "identified_conflicts": identified_conflicts,
                "recommended_physician_actions": [
                    "Review competing specialist proposals at multidisciplinary bedside round",
                    "Order resolving diagnostic tests or consult attending sub-specialist",
                    "Countersign or adjust treatment plan prior to administration",
                ],
            }

        return SwarmEpistemicAssessment(
            assessment_id=aid,
            swarm_uncertainty=swarm_uncertainty,
            safe_threshold=threshold,
            autonomous_execution_permitted=(not should_yield),
            yield_decision=yield_decision,
            agent_uncertainties=agent_uncertainties,
            confidence_dispersion=dispersion,
            identified_conflicts=identified_conflicts,
            clinician_escalation_brief=escalation_brief,
        )
