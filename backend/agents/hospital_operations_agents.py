"""
AI Healthcare System — Essential Hospital Operations AI Agents.

Implements high-value, essential operational agents:
1. Agent Prior Auth — Automates insurance prior authorization & medical necessity justification
2. Agent Sepsis Deterioration — ICU real-time qSOFA & sepsis early warning detector
3. Agent Surgical OR — Operating room turnover, scheduling, and sterilization prep optimizer
"""

import uuid
from typing import Any, Dict, List

from pydantic import BaseModel

from backend.agents.reflective_memory import agent_reflective_memory
from backend.agents.supervisor_orchestrator import (
    AgentCapability,
    RegisteredAgent,
    supervisor_router,
)

# =====================================================================
# 1. Agent Prior Authorization (Insurance Pre-Approval Automation)
# =====================================================================

class PriorAuthResult(BaseModel):
    request_id: str
    patient_id: str
    procedure_code: str
    approval_status: str  # "AUTO_APPROVED", "PENDING_CLINICAL_REVIEW", "DENIED"
    clinical_justification: str
    missing_documentation: List[str]


class AgentPriorAuth:
    """
    Autonomous agent handling insurance prior authorization & medical necessity matching.
    """

    def process_prior_auth(self, request_data: Dict[str, Any]) -> PriorAuthResult:
        """Process a prior authorization request against payer guidelines."""
        patient_id = request_data.get("patient_id", "P-100")
        cpt = request_data.get("procedure_code", "CPT-70450")  # e.g., CT Head
        has_prior_xray = request_data.get("has_prior_xray", True)
        has_neurological_symptoms = request_data.get("has_neurological_symptoms", True)

        missing = []
        if not has_prior_xray:
            missing.append("Prior conservative treatment documentation (X-Ray / Conservative Therapy)")

        if has_neurological_symptoms:
            status = "AUTO_APPROVED"
            justification = f"Medical necessity established: Acute neurological symptoms present for procedure {cpt}."
        elif missing:
            status = "PENDING_CLINICAL_REVIEW"
            justification = "Requires secondary clinical review due to missing prior conservative therapy documentation."
        else:
            status = "DENIED"
            justification = "Does not meet payer medical necessity criteria for advanced imaging."

        # Log episode in reflective memory
        agent_reflective_memory.record_episode(
            episode_id=f"EP-AUTH-{uuid.uuid4().hex[:6]}",
            agent_name="AgentPriorAuth",
            action_taken=f"Evaluated Prior Auth for {patient_id} ({cpt})",
            outcome=f"Status: {status}",
            reward_signal=1.0 if status == "AUTO_APPROVED" else 0.5,
        )

        return PriorAuthResult(
            request_id=f"PA-{uuid.uuid4().hex[:6]}",
            patient_id=patient_id,
            procedure_code=cpt,
            approval_status=status,
            clinical_justification=justification,
            missing_documentation=missing,
        )


# =====================================================================
# 2. Agent Sepsis Deterioration (ICU Real-Time Deterioration Monitor)
# =====================================================================

class SepsisRiskResult(BaseModel):
    patient_id: str
    qsofa_score: int       # 0 to 3 (Quick SOFA score)
    sepsis_risk_level: str  # "NORMAL", "ELEVATED", "HIGH_ALERT", "SEPTIC_SHOCK_WARNING"
    triggered_criteria: List[str]
    immediate_interventions: List[str]


class AgentSepsisDeterioration:
    """
    Autonomous agent evaluating real-time vital signs for early sepsis shock detection.
    """

    def evaluate_sepsis_risk(self, vital_stream: Dict[str, Any]) -> SepsisRiskResult:
        """Evaluate qSOFA (Quick Sequential Organ Failure Assessment) score."""
        patient_id = vital_stream.get("patient_id", "P-ICU-01")
        rr = vital_stream.get("respiratory_rate", 18)   # >= 22 = 1 pt
        sbp = vital_stream.get("systolic_bp", 120)       # <= 100 = 1 pt
        gcs = vital_stream.get("gcs_score", 15)          # < 15 = 1 pt

        qsofa = 0
        criteria = []

        if rr >= 22:
            qsofa += 1
            criteria.append(f"Tachypnea: Respiratory Rate {rr} >= 22 bpm")

        if sbp <= 100:
            qsofa += 1
            criteria.append(f"Hypotension: Systolic BP {sbp} <= 100 mmHg")

        if gcs < 15:
            qsofa += 1
            criteria.append(f"Altered Mental Status: GCS {gcs} < 15")

        if qsofa >= 2:
            risk = "SEPTIC_SHOCK_WARNING"
            interventions = [
                "Draw Blood Cultures x2 before antibiotics",
                "Administer IV Broad-Spectrum Antibiotics within 1 Hour",
                "Measure Serum Lactate Level",
                "Administer 30 mL/kg Crystalloid Fluid Bolus for Hypotension",
            ]
        elif qsofa == 1:
            risk = "ELEVATED"
            interventions = ["Increase Vital Monitoring Frequency to q15m", "Notify Attending Physician"]
        else:
            risk = "NORMAL"
            interventions = ["Maintain Standard ICU Monitoring Protocol"]

        return SepsisRiskResult(
            patient_id=patient_id,
            qsofa_score=qsofa,
            sepsis_risk_level=risk,
            triggered_criteria=criteria,
            immediate_interventions=interventions,
        )


# =====================================================================
# 3. Agent Surgical OR (Operating Room Suite Optimizer)
# =====================================================================

class ORScheduleResult(BaseModel):
    or_room_id: str
    scheduled_case_id: str
    turnover_time_minutes: int
    sterilization_status: str  # "READY", "IN_PROGRESS", "DELAYED"
    optimization_recommendations: List[str]


class AgentSurgicalOR:
    """
    Autonomous agent optimizing surgical suite turnover and equipment sterilization prep.
    """

    def optimize_or_schedule(self, surgical_case: Dict[str, Any]) -> ORScheduleResult:
        """Optimize Operating Room allocation and turnover timing."""
        or_room_id = surgical_case.get("or_room_id", "OR-3")
        case_id = surgical_case.get("case_id", "SURG-101")
        case_type = surgical_case.get("case_type", "ORTHOPEDIC")

        turnover = 25 if case_type == "LAPAROSCOPIC" else 35
        recs = [
            f"Pre-stage specialized {case_type} surgical trays 20 mins prior to incision",
            "Coordinate anesthesia prep in holding bay to reduce room occupancy",
        ]

        return ORScheduleResult(
            or_room_id=or_room_id,
            scheduled_case_id=case_id,
            turnover_time_minutes=turnover,
            sterilization_status="READY",
            optimization_recommendations=recs,
        )


# =====================================================================
# Global Instances & Supervisor Registration
# =====================================================================

agent_prior_auth = AgentPriorAuth()
agent_sepsis_deterioration = AgentSepsisDeterioration()
agent_surgical_or = AgentSurgicalOR()

# Register essential operational agents with Supervisor Router
supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-PRIOR-AUTH",
    name="Autonomous Prior Authorization & Medical Necessity Agent",
    capabilities=[AgentCapability.PRIOR_AUTH, AgentCapability.BILLING],
    priority=10,
))

supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-ICU-SEPSIS",
    name="Real-Time ICU Sepsis & Clinical Deterioration Agent",
    capabilities=[AgentCapability.ICU_MONITOR, AgentCapability.SAFETY],
    priority=10,
))

supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-SURGICAL-OR",
    name="Surgical Suite & Operating Room Optimization Agent",
    capabilities=[AgentCapability.SURGICAL_OR, AgentCapability.SCHEDULING],
    priority=9,
))
