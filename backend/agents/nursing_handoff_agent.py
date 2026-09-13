"""Inpatient Nursing & Care Transition Agent
===========================================
Generates structured Situation-Background-Assessment-Recommendation (SBAR) clinical handoffs,
evaluates longitudinal telemetry trends (arrhythmia burden, ST elevation/depression, MAP trajectories),
audits Medication Administration Record (MAR) schedules and Institute for Safe Medication Practices
(ISMP) high-alert double-checks (insulin, anticoagulants, opioids, concentrated electrolytes),
and tracks lines, drains, airways (LDA) and nursing risk scales (Braden, Morse, CAM-ICU).

Emits strongly-typed FHIR R4 action proposals (MedicationRequest, ServiceRequest, Flag)
and ClinicalAgentResponse.
"""

from __future__ import annotations

import datetime
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

# Ensure package directory is on sys.path if not installed in editable mode
_pkg_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "packages", "clinical-fhir-abdm", "src")
)
if _pkg_path not in sys.path and os.path.isdir(_pkg_path):
    sys.path.insert(0, _pkg_path)

try:
    from clinical_fhir_abdm.schemas import (
        ClinicalAgentResponse,
        FHIRFlagProposal,
        FHIRMedicationRequestProposal,
        FHIRServiceRequestProposal,
    )
except ImportError:
    @dataclass
    class FHIRMedicationRequestProposal:
        patient_id: str
        medication_name: str
        dosage: str
        route: str = "oral"
        frequency: str = "once daily"
        indication: str = ""
        clinical_evidence: Optional[List[str]] = None
        requester: Optional[str] = None
        intent: str = "order"
        priority: str = "routine"
        id: Optional[str] = None
        created_at: Optional[datetime.datetime] = None

        def __post_init__(self) -> None:
            if self.id is None:
                self.id = f"medreq-{uuid.uuid4().hex[:10]}"
            if self.created_at is None:
                self.created_at = datetime.datetime.now(datetime.timezone.utc)
            if self.clinical_evidence is None:
                self.clinical_evidence = []

        def to_dict(self) -> Dict[str, Any]:
            data = asdict(self)
            if self.created_at:
                data["created_at"] = self.created_at.isoformat()
            return data

    @dataclass
    class FHIRServiceRequestProposal:
        patient_id: str
        category: str
        code: str
        description: str
        urgency: str = "routine"
        indication: str = ""
        requester: Optional[str] = None
        supporting_info: Optional[List[str]] = None
        id: Optional[str] = None
        created_at: Optional[datetime.datetime] = None

        def __post_init__(self) -> None:
            if self.id is None:
                self.id = f"sr-{uuid.uuid4().hex[:10]}"
            if self.created_at is None:
                self.created_at = datetime.datetime.now(datetime.timezone.utc)
            if self.supporting_info is None:
                self.supporting_info = []

        def to_dict(self) -> Dict[str, Any]:
            data = asdict(self)
            if self.created_at:
                data["created_at"] = self.created_at.isoformat()
            return data

    @dataclass
    class FHIRFlagProposal:
        patient_id: str
        status: str = "active"
        category: str = "clinical_alert"
        severity: str = "warning"
        code: str = ""
        details: str = ""
        author: Optional[str] = None
        id: Optional[str] = None
        created_at: Optional[datetime.datetime] = None

        def __post_init__(self) -> None:
            if self.id is None:
                self.id = f"flag-{uuid.uuid4().hex[:10]}"
            if self.created_at is None:
                self.created_at = datetime.datetime.now(datetime.timezone.utc)

        def to_dict(self) -> Dict[str, Any]:
            data = asdict(self)
            if self.created_at:
                data["created_at"] = self.created_at.isoformat()
            return data

    @dataclass
    class ClinicalAgentResponse:
        recommendations: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
        proposed_fhir_actions: List[Any] = field(default_factory=list)
        epistemic_confidence: float = 1.0
        agent_name: Optional[str] = None
        reasoning: Optional[str] = None
        metadata: Dict[str, Any] = field(default_factory=dict)
        timestamp: datetime.datetime = field(
            default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

        def to_dict(self) -> Dict[str, Any]:
            return {
                "agent_name": self.agent_name,
                "epistemic_confidence": round(self.epistemic_confidence, 4),
                "recommendations": self.recommendations,
                "proposed_fhir_actions": [
                    a.to_dict() if hasattr(a, "to_dict") else a for a in self.proposed_fhir_actions
                ],
                "reasoning": self.reasoning,
                "metadata": self.metadata,
                "timestamp": self.timestamp.isoformat(),
            }


# ISMP High-Alert Medication Categories and Dual-Verification Requirements
ISMP_HIGH_ALERT_DRUGS: Dict[str, Dict[str, Any]] = {
    "insulin": {
        "pattern": r"(insulin|glargine|lispro|aspart|regular\s*insulin|nph|detemir|degludec)",
        "alert_type": "ISMP_HIGH_ALERT_INSULIN",
        "requires_independent_double_check": True,
        "vital_prerequisite": "Point-of-Care Blood Glucose verified within 1 hour",
        "toxicity_risk": "Severe hypoglycemic encephalopathy, seizure, or coma",
    },
    "anticoagulant": {
        "pattern": r"(heparin|enoxaparin|warfarin|apixaban|rivaroxaban|dabigatran|bivalirudin|argatroban)",
        "alert_type": "ISMP_HIGH_ALERT_ANTICOAGULANT",
        "requires_independent_double_check": True,
        "vital_prerequisite": "Recent baseline coagulation panel (aPTT, PT/INR, or anti-Xa) and platelet count",
        "toxicity_risk": "Catastrophic internal or intracranial hemorrhage; HIT",
    },
    "opioid": {
        "pattern": r"(morphine|hydromorphone|dilaudid|fentanyl|oxycodone|methadone|oxymorphone)",
        "alert_type": "ISMP_HIGH_ALERT_OPIOID",
        "requires_independent_double_check": True,
        "vital_prerequisite": "Baseline sedation score (POSS/RASS) and continuous SpO2 / respiratory rate monitoring",
        "toxicity_risk": "Fatal respiratory depression and apnea",
    },
    "concentrated_electrolyte": {
        "pattern": r"(potassium\s*chloride|kcl\s*concentrate|hypertonic\s*saline|3%\s*nacl|magnesium\s*sulfate)",
        "alert_type": "ISMP_HIGH_ALERT_CONCENTRATED_ELECTROLYTE",
        "requires_independent_double_check": True,
        "vital_prerequisite": "Dedicated IV infusion pump with guardrails limits; verified central access for KCl >20mEq/h",
        "toxicity_risk": "Lethal ventricular dysrhythmia or central pontine myelinolysis",
    },
    "neuromuscular_blocker": {
        "pattern": r"(rocuronium|vecuronium|cisatracurium|succinylcholine)",
        "alert_type": "ISMP_HIGH_ALERT_PARALYTIC",
        "requires_independent_double_check": True,
        "vital_prerequisite": "Secured mechanical airway and continuous deep sedation confirmed",
        "toxicity_risk": "Awake paralysis and asphyxiation",
    },
}


class NursingHandoffAgent:
    """Inpatient Nursing Coordinator & Care Transition Reasoning Agent."""

    def __init__(self) -> None:
        self.agent_name = "InpatientNursing_HandoffAgent"

    def analyze_telemetry_trends(
        self,
        telemetry_records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluates longitudinal telemetry trends, arrhythmia burden, and ST-segment / MAP trajectories."""
        if not telemetry_records:
            return {
                "status": "NO_TELEMETRY_DATA",
                "arrhythmia_burden_pct": 0.0,
                "st_elevation_detected": False,
                "st_depression_detected": False,
                "map_trajectory": "STABLE",
                "mean_map": None,
                "alarms": [],
            }

        alarms: List[str] = []
        abnormal_rhythms = 0
        st_elev_count = 0
        st_dep_count = 0
        map_values: List[float] = []

        for rec in telemetry_records:
            rhythm = str(rec.get("rhythm", "NSR")).upper()
            if rhythm not in ["NSR", "SINUS_RHYTHM", "NORMAL"]:
                abnormal_rhythms += 1
                if rhythm in ["VFIB", "VTACH", "ASYSTOLE", "3RD_DEGREE_AVB"]:
                    alarms.append(f"LETHAL DYSRHYTHMIA DETECTED: {rhythm}")
                elif rhythm in ["AFIB_RVR", "SVT"] and rec.get("heart_rate", 0) > 130:
                    alarms.append(f"RAPID VENTRICULAR RESPONSE: {rhythm} at HR {rec.get('heart_rate')}")

            # ST segment shift in mm
            st_delta = float(rec.get("st_segment_delta_mm", 0.0))
            if st_delta >= 1.0:
                st_elev_count += 1
                alarms.append(f"ST Elevation delta +{st_delta} mm (Potential acute transmural ischemia/STEMI)")
            elif st_delta <= -1.0:
                st_dep_count += 1
                alarms.append(f"ST Depression delta {st_delta} mm (Subendocardial ischemia/strain)")

            # MAP tracking
            sbp = rec.get("systolic_bp")
            dbp = rec.get("diastolic_bp")
            if sbp is not None and dbp is not None:
                map_val = (sbp + 2 * dbp) / 3.0
                map_values.append(map_val)
            elif "map" in rec:
                map_values.append(float(rec["map"]))

        total_records = len(telemetry_records)
        arrhythmia_burden = round((abnormal_rhythms / total_records) * 100.0, 1)

        # MAP trajectory delta
        map_trajectory = "STABLE"
        mean_map = round(sum(map_values) / len(map_values), 1) if map_values else None
        if len(map_values) >= 2:
            first_map = map_values[0]
            last_map = map_values[-1]
            map_diff = last_map - first_map
            if map_diff <= -15.0 or (mean_map is not None and mean_map < 65.0):
                map_trajectory = "DOWNWARD_HYPOTENSIVE"
                alarms.append(f"Hypotensive MAP drift detected (Latest MAP: {round(last_map, 1)} mmHg, delta {round(map_diff, 1)})")
            elif map_diff >= 20.0 or (mean_map is not None and mean_map > 110.0):
                map_trajectory = "UPWARD_HYPERTENSIVE"

        return {
            "status": "TELEMETRY_ANALYZED",
            "arrhythmia_burden_pct": arrhythmia_burden,
            "st_elevation_detected": st_elev_count > 0,
            "st_depression_detected": st_dep_count > 0,
            "map_trajectory": map_trajectory,
            "mean_map": mean_map,
            "alarms": list(set(alarms)),
        }

    def audit_mar_schedule(
        self,
        mar_schedule: List[Dict[str, Any]],
        patient_vitals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Audits MAR administration schedule for overdue meds and ISMP high-alert double-checks."""
        patient_vitals = patient_vitals or {}
        overdue_medications: List[Dict[str, Any]] = []
        high_alert_checks: List[Dict[str, Any]] = []
        general_safety_flags: List[str] = []

        now = datetime.datetime.now(datetime.timezone.utc)

        for item in mar_schedule:
            med_name = item.get("medication_name", "")
            dose = item.get("dose", "")
            route = item.get("route", "oral")
            scheduled_time_str = item.get("scheduled_time")
            status = item.get("status", "SCHEDULED").upper()

            # 1. Overdue check
            if status == "SCHEDULED" and scheduled_time_str:
                try:
                    sched_dt = datetime.datetime.fromisoformat(scheduled_time_str)
                    if sched_dt.tzinfo is None:
                        sched_dt = sched_dt.replace(tzinfo=datetime.timezone.utc)
                    if (now - sched_dt).total_seconds() > 3600:  # > 60 mins late
                        overdue_medications.append({
                            "medication": med_name,
                            "dose": dose,
                            "scheduled_time": scheduled_time_str,
                            "minutes_overdue": int((now - sched_dt).total_seconds() // 60),
                        })
                except Exception:
                    pass

            # 2. ISMP High-Alert Identification
            med_lower = med_name.lower()
            for drug_class, rule in ISMP_HIGH_ALERT_DRUGS.items():
                if re.search(rule["pattern"], med_lower):
                    is_verified = item.get("independent_double_check_completed", False)
                    verifier = item.get("verified_by_rn")

                    high_alert_entry = {
                        "medication": med_name,
                        "drug_class": drug_class,
                        "dose": dose,
                        "route": route,
                        "alert_type": rule["alert_type"],
                        "requires_double_check": rule["requires_independent_double_check"],
                        "double_check_completed": is_verified,
                        "verified_by_rn": verifier,
                        "vital_prerequisite": rule["vital_prerequisite"],
                        "toxicity_risk": rule["toxicity_risk"],
                        "compliance_status": "COMPLIANT" if is_verified else "REQUIRES_SECOND_RN_SIGN_OFF",
                    }
                    high_alert_checks.append(high_alert_entry)

                    if not is_verified:
                        general_safety_flags.append(
                            f"MANDATORY ISMP SAFETY GATE: {med_name} ({dose}) requires independent 2nd RN double-check prior to administration."
                        )

                    # Clinical condition checks (e.g. insulin with low glucose)
                    if drug_class == "insulin":
                        glucose = patient_vitals.get("blood_glucose_mg_dl")
                        if glucose is not None and glucose < 70:
                            general_safety_flags.append(
                                f"HYPOGLYCEMIA WARNING: Blood glucose is {glucose} mg/dL. HOLD INSULIN and initiate hypoglycemia rescue protocol."
                            )
                    elif drug_class == "opioid":
                        resp_rate = patient_vitals.get("respiratory_rate")
                        if resp_rate is not None and resp_rate < 10:
                            general_safety_flags.append(
                                f"RESPIRATORY DEPRESSION: Respiratory rate is {resp_rate}/min. HOLD OPIOID and assess for Naloxone administration."
                            )

        return {
            "total_scheduled": len(mar_schedule),
            "overdue_medications": overdue_medications,
            "high_alert_checks": high_alert_checks,
            "safety_flags": general_safety_flags,
            "all_high_alert_verified": all(h["double_check_completed"] for h in high_alert_checks),
        }

    def evaluate_clinical_risk_scales(
        self,
        braden_score: Optional[int] = None,
        morse_score: Optional[int] = None,
        cam_icu_positive: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Interprets validated nursing assessment risk scales (Braden, Morse Fall, CAM-ICU)."""
        interpretations: List[str] = []
        protocols: List[str] = []

        # Braden Scale (Pressure Injury Risk, 6-23; <=12 high/very high risk)
        braden_risk = "NORMAL"
        if braden_score is not None:
            if braden_score <= 9:
                braden_risk = "VERY_HIGH_RISK"
                interpretations.append(f"Braden {braden_score}: Very High Risk for Pressure Injury.")
                protocols.append("Initiate Q2H repositioning, low-air-loss mattress, barrier cream, barrier heel offloading boots.")
            elif braden_score <= 12:
                braden_risk = "HIGH_RISK"
                interpretations.append(f"Braden {braden_score}: High Risk for Pressure Injury.")
                protocols.append("Initiate Q2H repositioning schedule, pressure-relieving foam mattress, skin assessment Q-shift.")
            elif braden_score <= 14:
                braden_risk = "MODERATE_RISK"
                interpretations.append(f"Braden {braden_score}: Moderate Risk for Pressure Injury.")
                protocols.append("Moisture management and scheduled turning.")
            else:
                braden_risk = "MILD_OR_NO_RISK"

        # Morse Fall Scale (0-125; >=45 high fall risk)
        morse_risk = "LOW_RISK"
        if morse_score is not None:
            if morse_score >= 45:
                morse_risk = "HIGH_FALL_RISK"
                interpretations.append(f"Morse Fall Score {morse_score}: High Fall Risk.")
                protocols.append("Yellow fall wristband, bed alarm active, non-skid socks, 1-to-1 assisted ambulation, low bed position.")
            elif morse_score >= 25:
                morse_risk = "MODERATE_FALL_RISK"
                interpretations.append(f"Morse Fall Score {morse_score}: Moderate Fall Risk.")
                protocols.append("Standard fall prevention, bed rails up x2, call light within reach.")
            else:
                morse_risk = "LOW_FALL_RISK"

        # CAM-ICU (Confusion Assessment Method for the ICU - Delirium)
        delirium_status = "NEGATIVE"
        if cam_icu_positive is True:
            delirium_status = "POSITIVE"
            interpretations.append("CAM-ICU POSITIVE: Acute Delirium Present.")
            protocols.append("Delirium bundle: day/night light cycle, sleep hygiene, early mobilization, reorientation, minimize sedation.")
        elif cam_icu_positive is False:
            delirium_status = "NEGATIVE"

        return {
            "braden_risk": braden_risk,
            "braden_score": braden_score,
            "morse_risk": morse_risk,
            "morse_score": morse_score,
            "delirium_status": delirium_status,
            "interpretations": interpretations,
            "nursing_protocols_triggered": protocols,
        }

    def generate_sbar_handoff(
        self,
        patient_id: int,
        patient_name: str,
        room_number: str,
        chief_complaint: str,
        recent_vitals_summary: str,
        active_iv_lines: List[str],
        pending_labs: List[str],
        nurse_notes: Optional[str] = None,
        # Enhanced clinical fields
        telemetry_records: Optional[List[Dict[str, Any]]] = None,
        mar_schedule: Optional[List[Dict[str, Any]]] = None,
        drains: Optional[List[str]] = None,
        airways: Optional[List[str]] = None,
        braden_score: Optional[int] = None,
        morse_score: Optional[int] = None,
        cam_icu_positive: Optional[bool] = None,
        code_status: str = "FULL_CODE",
    ) -> Dict[str, Any]:
        """Backward-compatible method returning comprehensive SBAR package with telemetry, MAR, LDA, and risk scales."""
        pid_str = str(patient_id)
        drains = drains or []
        airways = airways or ["Room Air / Unassisted"]

        # 1. Telemetry trends
        telem_analysis = self.analyze_telemetry_trends(telemetry_records or [])

        # 2. MAR safety audit
        mar_audit = self.audit_mar_schedule(mar_schedule or [])

        # 3. Clinical risk scales
        risk_scales = self.evaluate_clinical_risk_scales(
            braden_score=braden_score,
            morse_score=morse_score,
            cam_icu_positive=cam_icu_positive,
        )

        # Lines, Drains, Airways (LDA) summary
        lda_summary = (
            f"Lines: {', '.join(active_iv_lines) or 'None'}\n"
            f"Drains: {', '.join(drains) or 'None'}\n"
            f"Airways/Oxygen: {', '.join(airways)}"
        )

        # Compile SBAR Sections
        situation = (
            f"Patient {patient_name} (ID #{patient_id}), Room {room_number}, Code Status: {code_status}. "
            f"Chief Complaint: {chief_complaint}."
        )

        telem_str = (
            f"Telemetry: Arrhythmia burden {telem_analysis['arrhythmia_burden_pct']}%, MAP trend {telem_analysis['map_trajectory']}."
            if telemetry_records else "Telemetry: Not continuously monitored."
        )
        background = (
            f"Admitted for clinical monitoring. {lda_summary.replace(chr(10), '; ')}. "
            f"Fall Risk: {risk_scales['morse_risk']} | Skin Integrity: {risk_scales['braden_risk']}."
        )

        assessment = (
            f"Recent vitals: {recent_vitals_summary}. {telem_str} "
            f"Delirium (CAM-ICU): {risk_scales['delirium_status']}. "
            f"{' '.join(telem_analysis['alarms'])}"
        ).strip()

        rec_parts = []
        if pending_labs:
            rec_parts.append(f"Pending labs to follow up: {', '.join(pending_labs)}.")
        if mar_audit["safety_flags"]:
            rec_parts.append(f"MAR Alerts: {' '.join(mar_audit['safety_flags'])}.")
        if risk_scales["nursing_protocols_triggered"]:
            rec_parts.append(f"Protocols: {' '.join(risk_scales['nursing_protocols_triggered'])}.")
        if nurse_notes:
            rec_parts.append(f"Nurse Notes: {nurse_notes}")
        else:
            rec_parts.append("Continue standard Q4H neuro/vital checks.")

        recommendation = " ".join(rec_parts)

        # Generate FHIR action proposals
        proposed_actions: List[Any] = []
        if telem_analysis["st_elevation_detected"] or telem_analysis["map_trajectory"] == "DOWNWARD_HYPOTENSIVE":
            flag = FHIRFlagProposal(
                patient_id=pid_str,
                status="active",
                category="clinical_alert",
                severity="critical",
                code="HEMODYNAMIC_INSTABILITY",
                details=f"TELEMETRY ALERT: {'; '.join(telem_analysis['alarms'])}",
            )
            proposed_actions.append(flag)

        if risk_scales["morse_risk"] == "HIGH_FALL_RISK":
            flag = FHIRFlagProposal(
                patient_id=pid_str,
                status="active",
                category="safety_risk",
                severity="high",
                code="FALL_RISK_HIGH",
                details=f"High Fall Risk (Morse {morse_score}). Bed alarm and assisted transfer mandated.",
            )
            proposed_actions.append(flag)

        if not mar_audit["all_high_alert_verified"] and mar_audit["high_alert_checks"]:
            flag = FHIRFlagProposal(
                patient_id=pid_str,
                status="active",
                category="safety_risk",
                severity="warning",
                code="ISMP_VERIFICATION_PENDING",
                details="Pending independent second-RN sign-off on high-alert medication administration.",
            )
            proposed_actions.append(flag)

        # Fall prevention / skin care service requests if high risk
        if risk_scales["braden_risk"] in ["HIGH_RISK", "VERY_HIGH_RISK"]:
            sr_wound = FHIRServiceRequestProposal(
                patient_id=pid_str,
                category="procedure",
                code="225358003",  # Wound care
                description="Wound Care / Pressure Injury Prevention Protocol: Low-air-loss mattress & barrier offloading",
                urgency="urgent",
                indication=f"High skin injury risk (Braden {braden_score})",
            )
            proposed_actions.append(sr_wound)

        clinical_response = ClinicalAgentResponse(
            recommendations=[
                {"section": "SBAR", "sbar": {"situation": situation, "background": background, "assessment": assessment, "recommendation": recommendation}},
                {"section": "TELEMETRY", "data": telem_analysis},
                {"section": "MAR_AUDIT", "data": mar_audit},
                {"section": "RISK_SCALES", "data": risk_scales},
            ],
            proposed_fhir_actions=proposed_actions,
            epistemic_confidence=0.96,
            agent_name=self.agent_name,
            reasoning=f"Compiled structured SBAR transition for {patient_name}. Assessed {len(telemetry_records or [])} telemetry epochs and {len(mar_schedule or [])} MAR entries.",
            metadata={
                "room_number": room_number,
                "code_status": code_status,
                "lines_drains_airways": {"lines": active_iv_lines, "drains": drains, "airways": airways},
            },
        )

        return {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "room_number": room_number,
            "code_status": code_status,
            "sbar": {
                "situation": situation,
                "background": background,
                "assessment": assessment,
                "recommendation": recommendation,
            },
            "active_iv_lines": active_iv_lines,
            "drains": drains,
            "airways": airways,
            "pending_labs": pending_labs,
            "telemetry_analysis": telem_analysis,
            "mar_audit": mar_audit,
            "risk_scales": risk_scales,
            "proposed_fhir_actions": [a.to_dict() for a in proposed_actions],
            "clinical_response": clinical_response.to_dict(),
            "status": "HANDOFF_READY",
        }


# Singleton agent instance
nursing_handoff_agent = NursingHandoffAgent()

