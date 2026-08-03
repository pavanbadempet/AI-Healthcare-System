"""
AI Healthcare System — Enterprise Autonomous Clinical Agents.

Implements specialized AI Agents:
1. Agent Fraud Detection — Identifies upcoding, phantom billing, and duplicate claims
2. Agent Entity Resolution — Resolves patient identities & deduplicates EMPI records
3. Agent Cost Analyzer — Analyzes DRG treatment costs, length-of-stay, and resource utilization
4. Agent Future Forecast — Forecasts ED surge, ICU bed demand, readmission risk, & trajectory
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
# 1. Agent Fraud Detection
# =====================================================================

class FraudAnalysisResult(BaseModel):
    claim_id: str
    fraud_score: float  # 0.0 to 1.0
    risk_level: str     # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    detected_anomalies: List[str]
    recommended_action: str


class AgentFraudDetection:
    """
    Autonomous agent detecting healthcare billing fraud, upcoding,
    phantom claims, and duplicate billing patterns.
    """

    def analyze_claim(self, claim_data: Dict[str, Any]) -> FraudAnalysisResult:
        """Analyze a medical claim for fraud indicators."""
        claim_id = claim_data.get("claim_id", f"CLM-{uuid.uuid4().hex[:6]}")
        amount = claim_data.get("amount", 0.0)
        cpt_codes = claim_data.get("cpt_codes", [])
        icd_codes = claim_data.get("icd_codes", [])
        is_duplicate = claim_data.get("is_duplicate", False)

        anomalies = []
        score = 0.0

        if is_duplicate:
            anomalies.append("DUPLICATE_CLAIM_SUBMISSION_DETECTED")
            score += 0.5

        if amount > 10000.0 and "CPT-99211" in cpt_codes:
            anomalies.append("UPCODING_MISMATCH: High billing amount for low-complexity code")
            score += 0.35

        if not icd_codes:
            anomalies.append("UNSUBSTANTIATED_CLAIM: Missing diagnostic ICD-10 justification")
            score += 0.25

        score = min(score, 1.0)
        risk = "CRITICAL" if score >= 0.7 else "HIGH" if score >= 0.4 else "MEDIUM" if score >= 0.2 else "LOW"
        action = "REJECT_AND_FLAG_FOR_AUDIT" if score >= 0.5 else "APPROVE_WITH_MONITORING"

        # Record in reflective memory
        agent_reflective_memory.record_episode(
            episode_id=f"EP-FRAUD-{claim_id}",
            agent_name="AgentFraudDetection",
            action_taken=f"Analyzed claim {claim_id}",
            outcome=f"Fraud Score: {score}, Risk: {risk}",
            reward_signal=1.0 if score > 0.0 else 0.5,
        )

        return FraudAnalysisResult(
            claim_id=claim_id,
            fraud_score=round(score, 2),
            risk_level=risk,
            detected_anomalies=anomalies,
            recommended_action=action,
        )


# =====================================================================
# 2. Agent Entity Resolution (Enterprise Master Patient Index - EMPI)
# =====================================================================

class EntityMatchResult(BaseModel):
    match_found: bool
    primary_patient_id: str
    matched_patient_ids: List[str]
    confidence_score: float
    field_similarities: Dict[str, float]


class AgentEntityResolution:
    """
    Autonomous agent performing deterministic & probabilistic patient entity resolution,
    record deduplication, and cross-system EMPI matching.
    """

    def resolve_entity(
        self,
        candidate: Dict[str, Any],
        master_records: List[Dict[str, Any]],
    ) -> EntityMatchResult:
        """Resolve a candidate patient record against master index records."""
        cand_ssn = candidate.get("ssn")
        cand_dob = candidate.get("dob")
        cand_name = candidate.get("name", "").lower()

        matched_ids = []
        best_score = 0.0

        for record in master_records:
            pid = record.get("patient_id")
            score = 0.0
            similarities = {}

            if cand_ssn and cand_ssn == record.get("ssn"):
                score += 0.6
                similarities["ssn"] = 1.0

            if cand_dob and cand_dob == record.get("dob"):
                score += 0.25
                similarities["dob"] = 1.0

            rec_name = record.get("name", "").lower()
            if cand_name and rec_name and (cand_name in rec_name or rec_name in cand_name):
                score += 0.15
                similarities["name"] = 0.9

            if score > best_score:
                best_score = score
                matched_ids = [pid]
            elif score == best_score and score > 0.5:
                matched_ids.append(pid)

        return EntityMatchResult(
            match_found=best_score >= 0.7,
            primary_patient_id=matched_ids[0] if matched_ids else candidate.get("patient_id", "P-NEW"),
            matched_patient_ids=matched_ids,
            confidence_score=round(best_score, 2),
            field_similarities={"overall": best_score},
        )


# =====================================================================
# 3. Agent Cost Analyzer
# =====================================================================

class CostAnalysisResult(BaseModel):
    patient_id: str
    estimated_total_cost: float
    drg_code: str
    expected_length_of_stay_days: int
    cost_saving_opportunities: List[str]


class AgentCostAnalyzer:
    """
    Autonomous agent analyzing clinical treatment costs, DRG Length-of-Stay,
    and resource allocation efficiency.
    """

    def analyze_cost(self, patient_case: Dict[str, Any]) -> CostAnalysisResult:
        """Analyze financial cost trajectory and optimization opportunities."""
        patient_id = patient_case.get("patient_id", "P-100")
        drg = patient_case.get("drg_code", "DRG-291")
        current_los = patient_case.get("length_of_stay_days", 5)

        base_cost = 2500.0 * current_los
        savings = []

        if current_los > 4:
            savings.append("EARLY_DISCHARGE_CARE_CONTINUITY: Transition to outpatient remote monitoring can save ~$3,500")

        if patient_case.get("has_generic_substitute"):
            savings.append("PHARMACY_GENERIC_SUBSTITUTION: Switch to generic equivalent can save ~$800")
            base_cost -= 800.0

        return CostAnalysisResult(
            patient_id=patient_id,
            estimated_total_cost=round(base_cost, 2),
            drg_code=drg,
            expected_length_of_stay_days=max(3, current_los - 1),
            cost_saving_opportunities=savings,
        )


# =====================================================================
# 4. Agent Future Forecast
# =====================================================================

class ForecastResult(BaseModel):
    forecast_type: str
    target_date: str
    predicted_metric_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    trajectory_trend: str  # "STABLE", "INCREASING", "DECREASING", "CRITICAL_SURGE"


class AgentFutureForecast:
    """
    Autonomous agent forecasting ED patient surge, ICU bed demand,
    readmission risks, and chronic disease progression trajectories.
    """

    def forecast_demand(
        self,
        historical_counts: List[float],
        forecast_horizon_days: int = 7,
    ) -> ForecastResult:
        """Forecast hospital capacity or patient surge trend."""
        if not historical_counts:
            historical_counts = [50.0, 55.0, 52.0, 58.0, 60.0]

        avg_val = sum(historical_counts) / len(historical_counts)
        trend_factor = 1.08  # 8% growth trend

        predicted = avg_val * (trend_factor ** (forecast_horizon_days / 7.0))
        lower = predicted * 0.90
        upper = predicted * 1.10

        trend = "CRITICAL_SURGE" if predicted > 80.0 else "INCREASING" if predicted > avg_val else "STABLE"

        return ForecastResult(
            forecast_type="ED_PATIENT_SURGE_FORECAST",
            target_date=f"+{forecast_horizon_days}d",
            predicted_metric_value=round(predicted, 1),
            confidence_interval_lower=round(lower, 1),
            confidence_interval_upper=round(upper, 1),
            trajectory_trend=trend,
        )


# =====================================================================
# Global Instances & Supervisor Registration
# =====================================================================

agent_fraud_detection = AgentFraudDetection()
agent_entity_resolution = AgentEntityResolution()
agent_cost_analyzer = AgentCostAnalyzer()
agent_future_forecast = AgentFutureForecast()

# Register new enterprise agents with Supervisor Router
supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-FRAUD-DETECTION",
    name="Autonomous Fraud & Billing Detection Agent",
    capabilities=[AgentCapability.BILLING, AgentCapability.SAFETY],
    priority=10,
))

supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-ENTITY-RESOLUTION",
    name="Enterprise Master Patient Index Entity Resolution Agent",
    capabilities=[AgentCapability.TRIAGE, AgentCapability.SAFETY],
    priority=9,
))

supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-COST-ANALYZER",
    name="Clinical Treatment Cost & DRG Optimization Agent",
    capabilities=[AgentCapability.BILLING, AgentCapability.DISCHARGE],
    priority=8,
))

supervisor_router.register_agent(RegisteredAgent(
    agent_id="AGENT-FUTURE-FORECAST",
    name="Hospital Surge & Disease Trajectory Forecast Agent",
    capabilities=[AgentCapability.TRIAGE, AgentCapability.SCHEDULING],
    priority=9,
))
