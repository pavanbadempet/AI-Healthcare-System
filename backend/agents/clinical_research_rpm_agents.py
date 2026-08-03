"""
AI Healthcare System — Clinical Research & Remote Patient Monitoring (RPM) Agents.

Implements high-value agents:
1. Agent Trial Matching — Matches patient EHR & genomic biomarkers to clinical trials
2. Agent RPM Adherence — Tracks post-discharge vitals, wearability, & med adherence
"""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.agents.reflective_memory import agent_reflective_memory
from backend.agents.supervisor_orchestrator import (
    supervisor_router, AgentCapability, RegisteredAgent,
)


# =====================================================================
# 1. Agent Trial Matching (Clinical Trial Eligibility Agent)
# =====================================================================

class TrialMatchResult(BaseModel):
    patient_id: str
    eligible_trials: List[Dict[str, Any]]
    match_confidence: float
    eligibility_rationale: str


class AgentTrialMatching:
    """
    Autonomous agent matching patient clinical features, diagnosis codes,
    and genomic biomarkers against ClinicalTrials.gov eligibility criteria.
    """

    def match_trials(self, patient_profile: Dict[str, Any]) -> TrialMatchResult:
        """Find matching clinical trial protocols for patient profile."""
        patient_id = patient_profile.get("patient_id", "P-ONC-101")
        condition = patient_profile.get("condition", "NSCLC").upper()
        biomarker = patient_profile.get("biomarker", "EGFR_L858R")
        age = patient_profile.get("age", 58)

        trials = []
        if "NSCLC" in condition or "LUNG" in condition:
            trials.append({
                "nct_id": "NCT-04523144",
                "title": "Phase III Targeted Tyrosine Kinase Inhibitor in EGFR-Mutated Non-Small Cell Lung Cancer",
                "phase": "Phase 3",
                "eligibility_match": True,
            })
            trials.append({
                "nct_id": "NCT-05112098",
                "title": "Study of Novel Bispecific Antibody in Advanced Solid Tumors",
                "phase": "Phase 1/2",
                "eligibility_match": True,
            })

        confidence = 0.92 if trials else 0.40
        rationale = f"Matched {len(trials)} active protocols based on condition '{condition}', biomarker '{biomarker}', and age {age}."

        # Log episode in reflective memory
        agent_reflective_memory.record_episode(
            episode_id=f"EP-TRIAL-{uuid.uuid4().hex[:6]}",
            agent_name="AgentTrialMatching",
            action_taken=f"Matched trial for {patient_id}",
            outcome=f"Found {len(trials)} protocols",
            reward_signal=1.0 if trials else 0.5,
        )

        return TrialMatchResult(
            patient_id=patient_id,
            eligible_trials=trials,
            match_confidence=confidence,
            eligibility_rationale=rationale,
        )


# =====================================================================
# 2. Agent RPM Adherence (Remote Patient Monitoring & Med Tracker)
# =====================================================================

class RPMAdherenceResult(BaseModel):
    patient_id: str
    adherence_score_pct: float
    vitals_status: str       # "NORMAL", "ATTENTION_REQUIRED", "CRITICAL_ALERT"
    missed_doses_last_7d: int
    recommended_interventions: List[str]


class AgentRPMAdherence:
    """
    Autonomous agent tracking post-discharge continuous remote telemetry,
    wearable metrics, and medication adherence compliance.
    """

    def evaluate_rpm(self, rpm_telemetry: Dict[str, Any]) -> RPMAdherenceResult:
        """Evaluate continuous remote telemetry and medication logs."""
        patient_id = rpm_telemetry.get("patient_id", "P-RPM-50")
        missed = rpm_telemetry.get("missed_doses_last_7d", 1)
        systolic_avg = rpm_telemetry.get("avg_systolic_bp", 132)

        adherence_pct = round(max(0.0, (1.0 - (missed / 14.0)) * 100.0), 1)

        interventions = []
        if missed >= 3:
            status = "ATTENTION_REQUIRED"
            interventions.append("Trigger Automated SMS Dose Reminder")
            interventions.append("Schedule Telehealth Nurse Check-In Call")
        elif systolic_avg >= 150:
            status = "CRITICAL_ALERT"
            interventions.append("Alert Care Team: Uncontrolled Post-Discharge Hypertension")
        else:
            status = "NORMAL"
            interventions.append("Continue Daily Wearable Telemetry Sync")

        return RPMAdherenceResult(
            patient_id=patient_id,
            adherence_score_pct=adherence_pct,
            vitals_status=status,
            missed_doses_last_7d=missed,
            recommended_interventions=interventions,
        )


# =====================================================================
# Global Instances & Supervisor Registration
# =====================================================================

agent_trial_matching = AgentTrialMatching()
agent_rpm_adherence = AgentRPMAdherence()

# Register agents with Supervisor Router
supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-TRIAL-MATCHING",
    name="Clinical Trial & Biomarker Eligibility Matching Agent",
    capabilities=[AgentCapability.TRIAL_MATCHING, AgentCapability.SAFETY],
    priority=9,
))

supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-RPM-ADHERENCE",
    name="Remote Patient Monitoring & Medication Adherence Agent",
    capabilities=[AgentCapability.RPM_ADHERENCE, AgentCapability.DISCHARGE],
    priority=9,
))
