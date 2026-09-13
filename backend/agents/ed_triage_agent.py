"""Emergency Department (ED) Triage & Critical Care Clinical Reasoning Agent
==========================================================================
Calculates Emergency Severity Index (ESI Level 1-5), qSOFA, full SOFA (0-24),
NEWS2 scoring engine with dual SpO2 scales, physiological trajectory dynamics
(Shock Index, Modified Shock Index, delta trends), and Surviving Sepsis Campaign
(SSC) 1-Hour rapid resuscitation bundles.

Emits strongly-typed FHIR action proposals and ClinicalAgentResponse.
"""

from __future__ import annotations

import datetime
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

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
    import uuid
    from dataclasses import asdict

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


class EmergencyTriageAgent:
    """Production-grade Emergency & Critical Care specialist reasoning agent."""

    # ── 1. Dynamic ESI Triage Engine ──────────────────────────────────────────

    def evaluate_pediatric_vital_danger_zone(
        self,
        age_years: float,
        heart_rate: float,
        respiratory_rate: float,
        oxygen_sat: float,
    ) -> Tuple[bool, List[str]]:
        """Evaluates pediatric age-stratified physiological danger zones."""
        danger_flags = []

        if oxygen_sat < 92.0:
            danger_flags.append(f"Hypoxia: SpO2 {oxygen_sat:.1f}% (< 92%)")

        if age_years < (1.0 / 12.0):  # Neonate (< 1 month)
            if heart_rate > 180 or heart_rate < 100:
                danger_flags.append(f"Neonate abnormal HR: {heart_rate} bpm (safe: 100-180)")
            if respiratory_rate > 60 or respiratory_rate < 30:
                danger_flags.append(f"Neonate abnormal RR: {respiratory_rate}/min (safe: 30-60)")
        elif age_years < 1.0:  # Infant (1-12 months)
            if heart_rate > 160 or heart_rate < 90:
                danger_flags.append(f"Infant abnormal HR: {heart_rate} bpm (safe: 90-160)")
            if respiratory_rate > 50 or respiratory_rate < 25:
                danger_flags.append(f"Infant abnormal RR: {respiratory_rate}/min (safe: 25-50)")
        elif age_years < 3.0:  # Toddler (1-3 years)
            if heart_rate > 140 or heart_rate < 80:
                danger_flags.append(f"Toddler abnormal HR: {heart_rate} bpm (safe: 80-140)")
            if respiratory_rate > 40 or respiratory_rate < 20:
                danger_flags.append(f"Toddler abnormal RR: {respiratory_rate}/min (safe: 20-40)")
        elif age_years < 6.0:  # Preschool (3-5 years)
            if heart_rate > 120 or heart_rate < 70:
                danger_flags.append(f"Preschool abnormal HR: {heart_rate} bpm (safe: 70-120)")
            if respiratory_rate > 30 or respiratory_rate < 18:
                danger_flags.append(f"Preschool abnormal RR: {respiratory_rate}/min (safe: 18-30)")
        elif age_years < 12.0:  # School-age (6-11 years)
            if heart_rate > 110 or heart_rate < 60:
                danger_flags.append(f"School-age abnormal HR: {heart_rate} bpm (safe: 60-110)")
            if respiratory_rate > 25 or respiratory_rate < 14:
                danger_flags.append(f"School-age abnormal RR: {respiratory_rate}/min (safe: 14-25)")
        else:  # Adolescent (12-17 years)
            if heart_rate > 100 or heart_rate < 50:
                danger_flags.append(f"Adolescent abnormal HR: {heart_rate} bpm (safe: 50-100)")
            if respiratory_rate > 20 or respiratory_rate < 12:
                danger_flags.append(f"Adolescent abnormal RR: {respiratory_rate}/min (safe: 12-20)")

        return (len(danger_flags) > 0, danger_flags)

    def evaluate_adult_vital_danger_zone(
        self,
        heart_rate: float,
        systolic_bp: float,
        oxygen_sat: float,
        respiratory_rate: float,
        temperature_c: Optional[float] = None,
    ) -> Tuple[bool, List[str]]:
        """Evaluates adult vital sign danger zones under ESI triage guidelines."""
        danger_flags = []
        if heart_rate > 100 or heart_rate < 50:
            danger_flags.append(f"Adult abnormal HR: {heart_rate} bpm (safe: 50-100)")
        if systolic_bp < 90 or systolic_bp > 200:
            danger_flags.append(f"Adult abnormal SBP: {systolic_bp} mmHg (safe: 90-200)")
        if oxygen_sat < 92.0:
            danger_flags.append(f"Hypoxia: SpO2 {oxygen_sat:.1f}% (< 92%)")
        if respiratory_rate > 20 or respiratory_rate < 10:
            danger_flags.append(f"Adult abnormal RR: {respiratory_rate}/min (safe: 10-20)")
        if temperature_c is not None:
            if temperature_c < 36.0 or temperature_c > 38.3:
                danger_flags.append(f"Adult abnormal Temp: {temperature_c:.1f}°C (safe: 36.0-38.3)")
        return (len(danger_flags) > 0, danger_flags)

    def evaluate_esi_triage(
        self,
        chief_complaint: str,
        heart_rate: float,
        systolic_bp: float,
        oxygen_sat: float,
        respiratory_rate: float,
        is_unresponsive_or_dying: bool = False,
        is_high_risk_situation: bool = False,
        projected_resources_needed: int = 1,
        age_years: float = 35.0,
        temperature_c: Optional[float] = None,
        severe_pain_or_distress: bool = False,
        confused_lethargic_disoriented: bool = False,
        avpu: Optional[str] = None,
        gcs: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Calculates Emergency Severity Index (ESI Level 1-5)."""
        complaint_lower = (chief_complaint or "").lower()

        # Decision Point A: Immediate life-saving intervention required?
        is_esi_1 = False
        esi_1_reasons = []

        if is_unresponsive_or_dying:
            is_esi_1 = True
            esi_1_reasons.append("Clinical report: unresponsive or moribund")
        if avpu in ["P", "U"] or (gcs is not None and gcs < 9):
            is_esi_1 = True
            esi_1_reasons.append(f"Severe neurological depression (AVPU={avpu}, GCS={gcs})")

        # Vital sign thresholds for ESI 1 (adult vs pediatric)
        if age_years >= 18.0:
            if heart_rate > 150 or heart_rate < 35:
                is_esi_1 = True
                esi_1_reasons.append(f"Adult extreme heart rate: {heart_rate} bpm")
            if systolic_bp < 80:
                is_esi_1 = True
                esi_1_reasons.append(f"Adult profound hypotension: SBP {systolic_bp} mmHg")
            if respiratory_rate < 8 or respiratory_rate > 35:
                is_esi_1 = True
                esi_1_reasons.append(f"Adult severe respiratory compromise: RR {respiratory_rate}/min")
        else:
            # Pediatric ESI-1: cardiac arrest / severe apnea / profound bradycardia
            if heart_rate < 50 or (age_years < 1.0 and heart_rate > 220) or (age_years >= 1.0 and heart_rate > 200):
                is_esi_1 = True
                esi_1_reasons.append(f"Pediatric extreme heart rate: {heart_rate} bpm")
            if respiratory_rate < 6 or (age_years < 1.0 and respiratory_rate > 70) or (age_years >= 1.0 and respiratory_rate > 60):
                is_esi_1 = True
                esi_1_reasons.append(f"Pediatric severe respiratory compromise: RR {respiratory_rate}/min")
            if systolic_bp < (60 if age_years < 1.0 else (70 + 2 * age_years) - 20):
                is_esi_1 = True
                esi_1_reasons.append(f"Pediatric profound hypotension: SBP {systolic_bp} mmHg")

        if oxygen_sat < 85.0:
            is_esi_1 = True
            esi_1_reasons.append(f"Critical desaturation: SpO2 {oxygen_sat:.1f}%")

        if is_esi_1:
            return {
                "esi_level": 1,
                "acuity_category": "IMMEDIATE_RESUSCITATION",
                "target_time_to_physician_min": 0,
                "clinical_description": "Immediate life-saving intervention required (Resuscitation Area).",
                "recommended_area": "Trauma / Resuscitation Bay",
                "rationale": "; ".join(esi_1_reasons),
                "is_pediatric": age_years < 18.0,
            }

        # Decision Point B: High-risk situation / confused / severe pain / danger zone?
        is_esi_2 = False
        esi_2_reasons = []

        if is_high_risk_situation:
            is_esi_2 = True
            esi_2_reasons.append("High-risk clinical presentation flag active")
        if confused_lethargic_disoriented or avpu in ["C", "V"]:
            is_esi_2 = True
            esi_2_reasons.append("New onset confusion, lethargy, or acute disorientation")
        if severe_pain_or_distress:
            is_esi_2 = True
            esi_2_reasons.append("Severe acute pain or emotional distress (score >= 7/10)")

        # High-risk complaint keywords
        high_risk_keywords = [
            "chest pain", "stroke", "anaphylaxis", "stabbing", "gunshot",
            "overdose", "suicidal", "severe dyspnea", "syncope", "testicular torsion",
            "ectopic pregnancy", "sepsis"
        ]
        if any(kw in complaint_lower for kw in high_risk_keywords):
            is_esi_2 = True
            esi_2_reasons.append(f"High-risk chief complaint matching: '{chief_complaint}'")

        # Vital sign danger zones
        if age_years < 18.0:
            in_danger, ped_flags = self.evaluate_pediatric_vital_danger_zone(
                age_years, heart_rate, respiratory_rate, oxygen_sat
            )
            if in_danger:
                is_esi_2 = True
                esi_2_reasons.extend(ped_flags)
        else:
            in_danger, adult_flags = self.evaluate_adult_vital_danger_zone(
                heart_rate, systolic_bp, oxygen_sat, respiratory_rate, temperature_c
            )
            if in_danger:
                is_esi_2 = True
                esi_2_reasons.extend(adult_flags)

        # Explicit adult ESI 2 thresholds
        if oxygen_sat < 92.0 or systolic_bp > 200 or heart_rate > 130:
            is_esi_2 = True
            esi_2_reasons.append(
                f"Severe vital abnormality (HR={heart_rate}, SBP={systolic_bp}, SpO2={oxygen_sat})"
            )

        if is_esi_2:
            return {
                "esi_level": 2,
                "acuity_category": "EMERGENT",
                "target_time_to_physician_min": 10,
                "clinical_description": "High-risk situation or severe vital sign abnormality (Emergent).",
                "recommended_area": "Acute ED Care Bed",
                "rationale": "; ".join(esi_2_reasons),
                "is_pediatric": age_years < 18.0,
            }

        # Decision Point C: Resource needs (ESI 3, 4, 5)
        if projected_resources_needed >= 2:
            return {
                "esi_level": 3,
                "acuity_category": "URGENT",
                "target_time_to_physician_min": 30,
                "clinical_description": "Urgent presentation requiring multiple resources (labs, imaging, IV meds).",
                "recommended_area": "Main ED Treatment Area",
                "rationale": f"Stable vitals, projected resource count: {projected_resources_needed}",
                "is_pediatric": age_years < 18.0,
            }
        elif projected_resources_needed == 1:
            return {
                "esi_level": 4,
                "acuity_category": "LESS_URGENT",
                "target_time_to_physician_min": 60,
                "clinical_description": "Less urgent presentation requiring 1 resource (single X-ray or lab).",
                "recommended_area": "Fast Track / Express Care",
                "rationale": "Stable vitals, single resource needed",
                "is_pediatric": age_years < 18.0,
            }
        else:
            return {
                "esi_level": 5,
                "acuity_category": "NON_URGENT",
                "target_time_to_physician_min": 120,
                "clinical_description": "Non-urgent presentation requiring zero complex ED resources.",
                "recommended_area": "Outpatient Clinic / Fast Track",
                "rationale": "Stable vitals, zero resource requirement (exam/refill only)",
                "is_pediatric": age_years < 18.0,
            }

    # ── 2. Bedside qSOFA Scoring Engine ───────────────────────────────────────

    def calculate_qsofa(
        self,
        respiratory_rate: float,
        systolic_bp: float,
        gcs: Optional[int] = None,
        avpu: Optional[str] = None,
        altered_mentation: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Calculates bedside quick SOFA (qSOFA) score (0-3 points)."""
        score = 0
        criteria_met = []

        if respiratory_rate >= 22.0:
            score += 1
            criteria_met.append(f"Tachypnea (RR {respiratory_rate:.1f} >= 22)")

        if systolic_bp <= 100.0:
            score += 1
            criteria_met.append(f"Hypotension (SBP {systolic_bp:.1f} <= 100)")

        is_altered = False
        if altered_mentation is True:
            is_altered = True
        elif gcs is not None and gcs < 15:
            is_altered = True
        elif avpu is not None and avpu.upper() != "A":
            is_altered = True

        if is_altered:
            score += 1
            criteria_met.append("Altered mentation (GCS < 15 or non-Alert)")

        # In-hospital mortality risk estimation
        mortality_map = {0: 1.2, 1: 3.5, 2: 12.8, 3: 24.5}
        mortality_risk_pct = mortality_map.get(score, 25.0)
        high_risk = score >= 2

        recommendation = (
            "Positive qSOFA (>= 2): High risk of poor outcome / prolonged ICU stay. "
            "Immediately screen for organ dysfunction (full SOFA), draw serum lactate, "
            "obtain blood cultures, and initiate Sepsis resuscitation pathway."
            if high_risk
            else "Low qSOFA score (< 2). Re-evaluate if clinical condition deteriorates."
        )

        return {
            "qsofa_score": score,
            "criteria_met": criteria_met,
            "high_risk": high_risk,
            "estimated_mortality_risk_pct": mortality_risk_pct,
            "recommendation": recommendation,
        }

    # ── 3. Full SOFA Scoring Engine ───────────────────────────────────────────

    def calculate_full_sofa(
        self,
        pao2: Optional[float] = None,
        fio2: Optional[float] = None,
        spo2: Optional[float] = None,
        is_mechanically_ventilated: bool = False,
        platelets: Optional[float] = None,  # x10^3/uL
        bilirubin: Optional[float] = None,  # mg/dL
        mean_arterial_pressure: Optional[float] = None,  # mmHg
        systolic_bp: Optional[float] = None,
        diastolic_bp: Optional[float] = None,
        dopamine_dose: Optional[float] = None,  # ug/kg/min
        dobutamine_active: bool = False,
        epinephrine_dose: Optional[float] = None,  # ug/kg/min
        norepinephrine_dose: Optional[float] = None,  # ug/kg/min
        gcs: Optional[int] = None,
        creatinine: Optional[float] = None,  # mg/dL
        urine_output_ml_day: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculates full Sequential Organ Failure Assessment (SOFA) score (0-24 points)."""
        subscores: Dict[str, int] = {}
        findings: Dict[str, str] = {}

        # 1. Respiration
        resp_score = 0
        if pao2 is not None and fio2 is not None and fio2 > 0:
            pf_ratio = pao2 / fio2
            if pf_ratio < 100 and is_mechanically_ventilated:
                resp_score = 4
            elif pf_ratio < 200 and is_mechanically_ventilated:
                resp_score = 3
            elif pf_ratio < 300:
                resp_score = 2
            elif pf_ratio < 400:
                resp_score = 1
            findings["respiration"] = f"PaO2/FiO2 = {pf_ratio:.1f}"
        elif spo2 is not None and fio2 is not None and fio2 > 0:
            # SF ratio surrogate
            sf_ratio = spo2 / fio2
            if sf_ratio < 150 and is_mechanically_ventilated:
                resp_score = 4
            elif sf_ratio < 235:
                resp_score = 3
            elif sf_ratio < 315:
                resp_score = 2
            elif sf_ratio < 440:
                resp_score = 1
            findings["respiration"] = f"SpO2/FiO2 surrogate = {sf_ratio:.1f}"
        subscores["respiration"] = resp_score

        # 2. Coagulation (Platelets x10^3 / uL)
        coag_score = 0
        if platelets is not None:
            if platelets < 20.0:
                coag_score = 4
            elif platelets < 50.0:
                coag_score = 3
            elif platelets < 100.0:
                coag_score = 2
            elif platelets < 150.0:
                coag_score = 1
            findings["coagulation"] = f"Platelets: {platelets} x10^3/uL"
        subscores["coagulation"] = coag_score

        # 3. Liver (Bilirubin mg/dL)
        liver_score = 0
        if bilirubin is not None:
            if bilirubin >= 12.0:
                liver_score = 4
            elif bilirubin >= 6.0:
                liver_score = 3
            elif bilirubin >= 2.0:
                liver_score = 2
            elif bilirubin >= 1.2:
                liver_score = 1
            findings["liver"] = f"Bilirubin: {bilirubin} mg/dL"
        subscores["liver"] = liver_score

        # 4. Cardiovascular
        cv_score = 0
        map_val = mean_arterial_pressure
        if map_val is None and systolic_bp is not None and diastolic_bp is not None:
            map_val = (2 * diastolic_bp + systolic_bp) / 3.0

        if (dopamine_dose and dopamine_dose > 15) or (epinephrine_dose and epinephrine_dose > 0.1) or (norepinephrine_dose and norepinephrine_dose > 0.1):
            cv_score = 4
            findings["cardiovascular"] = "High-dose vasopressors active"
        elif (dopamine_dose and dopamine_dose > 5) or (epinephrine_dose and epinephrine_dose <= 0.1) or (norepinephrine_dose and norepinephrine_dose <= 0.1):
            cv_score = 3
            findings["cardiovascular"] = "Moderate vasopressors active"
        elif (dopamine_dose and dopamine_dose <= 5) or dobutamine_active:
            cv_score = 2
            findings["cardiovascular"] = "Low-dose inotropes active"
        elif map_val is not None and map_val < 70.0:
            cv_score = 1
            findings["cardiovascular"] = f"MAP {map_val:.1f} mmHg (< 70)"
        else:
            findings["cardiovascular"] = f"MAP {map_val:.1f} mmHg (>= 70)" if map_val else "Stable"
        subscores["cardiovascular"] = cv_score

        # 5. Neurological (GCS)
        neuro_score = 0
        if gcs is not None:
            if gcs < 6:
                neuro_score = 4
            elif gcs <= 9:
                neuro_score = 3
            elif gcs <= 12:
                neuro_score = 2
            elif gcs <= 14:
                neuro_score = 1
            findings["neurological"] = f"GCS: {gcs}"
        subscores["neurological"] = neuro_score

        # 6. Renal (Creatinine mg/dL or Urine Output)
        renal_score = 0
        if creatinine is not None:
            if creatinine >= 5.0 or (urine_output_ml_day is not None and urine_output_ml_day < 200):
                renal_score = 4
            elif creatinine >= 3.5 or (urine_output_ml_day is not None and urine_output_ml_day < 500):
                renal_score = 3
            elif creatinine >= 2.0:
                renal_score = 2
            elif creatinine >= 1.2:
                renal_score = 1
            findings["renal"] = f"Creatinine: {creatinine} mg/dL"
        subscores["renal"] = renal_score

        total_sofa = sum(subscores.values())
        organ_failures = sum(1 for v in subscores.values() if v >= 2)

        # Mortality risk curve
        if total_sofa <= 1:
            mortality_pct = 3.3
        elif total_sofa <= 3:
            mortality_pct = 8.5
        elif total_sofa <= 5:
            mortality_pct = 18.0
        elif total_sofa <= 7:
            mortality_pct = 25.5
        elif total_sofa <= 9:
            mortality_pct = 36.4
        elif total_sofa <= 11:
            mortality_pct = 48.0
        elif total_sofa <= 14:
            mortality_pct = 60.0
        else:
            mortality_pct = 85.0

        return {
            "total_sofa_score": total_sofa,
            "subscores": subscores,
            "organ_failures_count": organ_failures,
            "estimated_icu_mortality_pct": mortality_pct,
            "organ_system_findings": findings,
            "sepsis_organ_dysfunction_confirmed": total_sofa >= 2,
        }

    # ── 4. NEWS2 Scoring Engine ───────────────────────────────────────────────

    def calculate_news2(
        self,
        respiratory_rate: float,
        oxygen_sat: float,
        hypercapnic_respiratory_failure: bool = False,
        supplemental_oxygen: bool = False,
        systolic_bp: float = 120.0,
        heart_rate: float = 75.0,
        consciousness: str = "A",  # A, C, V, P, U
        temperature_c: float = 37.0,
    ) -> Dict[str, Any]:
        """Calculates National Early Warning Score 2 (NEWS2) across 7 parameters."""
        parameter_scores: Dict[str, int] = {}

        # 1. Respiratory Rate
        if respiratory_rate <= 8:
            rr_pts = 3
        elif 9 <= respiratory_rate <= 11:
            rr_pts = 1
        elif 12 <= respiratory_rate <= 20:
            rr_pts = 0
        elif 21 <= respiratory_rate <= 24:
            rr_pts = 2
        else:
            rr_pts = 3
        parameter_scores["respiratory_rate"] = rr_pts

        # 2. Oxygen Saturation (Scale 1 vs Scale 2 for hypercapnic failure)
        if not hypercapnic_respiratory_failure:
            if oxygen_sat <= 91:
                spo2_pts = 3
            elif oxygen_sat in [92, 93]:
                spo2_pts = 2
            elif oxygen_sat in [94, 95]:
                spo2_pts = 1
            else:
                spo2_pts = 0
        else:
            # Scale 2: Target 88-92%
            if oxygen_sat <= 83:
                spo2_pts = 3
            elif oxygen_sat in [84, 85]:
                spo2_pts = 2
            elif oxygen_sat in [86, 87]:
                spo2_pts = 1
            elif 88 <= oxygen_sat <= 92:
                spo2_pts = 0
            elif oxygen_sat in [93, 94] and supplemental_oxygen:
                spo2_pts = 1
            elif oxygen_sat in [95, 96] and supplemental_oxygen:
                spo2_pts = 2
            elif oxygen_sat >= 97 and supplemental_oxygen:
                spo2_pts = 3
            else:
                spo2_pts = 0
        parameter_scores["oxygen_saturation"] = spo2_pts

        # 3. Supplemental Oxygen
        parameter_scores["supplemental_oxygen"] = 2 if supplemental_oxygen else 0

        # 4. Systolic Blood Pressure
        if systolic_bp <= 90:
            sbp_pts = 3
        elif 91 <= systolic_bp <= 100:
            sbp_pts = 2
        elif 101 <= systolic_bp <= 110:
            sbp_pts = 1
        elif 111 <= systolic_bp <= 219:
            sbp_pts = 0
        else:
            sbp_pts = 3
        parameter_scores["systolic_bp"] = sbp_pts

        # 5. Heart Rate
        if heart_rate <= 40:
            hr_pts = 3
        elif 41 <= heart_rate <= 50:
            hr_pts = 1
        elif 51 <= heart_rate <= 90:
            hr_pts = 0
        elif 91 <= heart_rate <= 110:
            hr_pts = 1
        elif 111 <= heart_rate <= 130:
            hr_pts = 2
        else:
            hr_pts = 3
        parameter_scores["heart_rate"] = hr_pts

        # 6. Consciousness (ACVPU)
        c_code = consciousness.strip().upper()[:1] if consciousness else "A"
        parameter_scores["consciousness"] = 0 if c_code == "A" else 3

        # 7. Body Temperature
        if temperature_c <= 35.0:
            temp_pts = 3
        elif 35.1 <= temperature_c <= 36.0:
            temp_pts = 1
        elif 36.1 <= temperature_c <= 38.0:
            temp_pts = 0
        elif 38.1 <= temperature_c <= 39.0:
            temp_pts = 1
        else:
            temp_pts = 2
        parameter_scores["temperature"] = temp_pts

        total_score = sum(parameter_scores.values())
        has_single_3 = any(v >= 3 for v in parameter_scores.values())

        if total_score >= 7:
            clinical_risk = "HIGH"
            response_recommendation = (
                "Emergency response: Immediate assessment by clinical team with critical care "
                "competencies / ICU outreach team. Continuous monitoring."
            )
        elif 5 <= total_score <= 6 or has_single_3:
            clinical_risk = "MEDIUM" if total_score >= 5 else "LOW_MEDIUM"
            response_recommendation = (
                "Urgent response: Assessment by clinical team; minimum hourly monitoring; "
                "escalate care if not rapidly improving."
            )
        else:
            clinical_risk = "LOW"
            response_recommendation = "Routine ward monitoring: 4 to 12 hourly observations."

        return {
            "total_news2_score": total_score,
            "parameter_scores": parameter_scores,
            "clinical_risk_level": clinical_risk,
            "has_extreme_single_parameter": has_single_3,
            "clinical_escalation_recommendation": response_recommendation,
        }

    # ── 5. Physiological Trajectory Dynamics ──────────────────────────────────

    def evaluate_shock_indices(
        self,
        heart_rate: float,
        systolic_bp: float,
        diastolic_bp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculates Shock Index (SI) and Modified Shock Index (MSI)."""
        si = heart_rate / systolic_bp if systolic_bp > 0 else 9.99

        if diastolic_bp is not None:
            map_val = (2 * diastolic_bp + systolic_bp) / 3.0
            msi = heart_rate / map_val if map_val > 0 else 9.99
        else:
            map_val = None
            msi = None

        if si > 1.0:
            si_status = "CRITICAL_SHOCK"
        elif si >= 0.9:
            si_status = "OCCULT_SHOCK"
        elif si >= 0.7:
            si_status = "MILDLY_ELEVATED"
        else:
            si_status = "NORMAL"

        msi_status = None
        if msi is not None:
            if msi > 1.3:
                msi_status = "CRITICAL_HYPOPERFUSION"
            elif msi < 0.7:
                msi_status = "HYPERDYNAMIC_OR_HYPERTENSIVE"
            else:
                msi_status = "NORMAL"

        return {
            "shock_index": round(si, 3),
            "shock_index_status": si_status,
            "mean_arterial_pressure": round(map_val, 1) if map_val else None,
            "modified_shock_index": round(msi, 3) if msi else None,
            "modified_shock_index_status": msi_status,
            "hypoperfusion_detected": si >= 0.9 or (msi is not None and msi > 1.3),
        }

    def evaluate_trajectory_trend(
        self,
        vitals_history: List[Dict[str, float]],
    ) -> Dict[str, Any]:
        """Analyzes physiological trajectories over consecutive observation intervals."""
        if len(vitals_history) < 2:
            return {
                "trajectory_state": "STABLE",
                "trajectory_description": "Insufficient history for longitudinal trend evaluation",
                "delta_map": 0.0,
                "delta_hr": 0.0,
                "delta_shock_index": 0.0,
            }

        prev = vitals_history[-2]
        curr = vitals_history[-1]

        prev_map = (2 * prev.get("diastolic_bp", 80) + prev.get("systolic_bp", 120)) / 3.0
        curr_map = (2 * curr.get("diastolic_bp", 80) + curr.get("systolic_bp", 120)) / 3.0
        delta_map = curr_map - prev_map

        delta_hr = curr.get("heart_rate", 75) - prev.get("heart_rate", 75)
        prev_si = prev.get("heart_rate", 75) / prev.get("systolic_bp", 120)
        curr_si = curr.get("heart_rate", 75) / curr.get("systolic_bp", 120)
        delta_si = curr_si - prev_si

        if delta_map <= -10.0 and delta_hr >= 15.0:
            state = "CRITICAL_COLLAPSE"
            desc = "Rapid hemodynamic deterioration: declining MAP with compensatory tachycardia."
        elif delta_si >= 0.15 or delta_map <= -8.0:
            state = "DETERIORATING"
            desc = "Worsening physiological trajectory; intensifying occult shock."
        elif delta_map >= 10.0 and delta_hr <= -10.0:
            state = "IMPROVING"
            desc = "Hemodynamic stabilization: increasing MAP with declining heart rate."
        else:
            state = "STABLE"
            desc = "Hemodynamics within physiological tolerance bands."

        return {
            "trajectory_state": state,
            "trajectory_description": desc,
            "delta_map": round(delta_map, 2),
            "delta_hr": round(delta_hr, 2),
            "delta_shock_index": round(delta_si, 3),
        }

    # ── 6. Surviving Sepsis Campaign (SSC) 1-Hour Resuscitation Bundle ───────────

    def evaluate_ssc_bundle(
        self,
        suspected_infection: bool,
        qsofa_score: int,
        mean_arterial_pressure: float,
        serum_lactate: Optional[float] = None,
        patient_weight_kg: float = 70.0,
    ) -> Dict[str, Any]:
        """Evaluates Surviving Sepsis Campaign (SSC) 1-Hour rapid resuscitation bundle requirements."""
        bundle_activated = False
        triggers = []

        if suspected_infection:
            if qsofa_score >= 2:
                bundle_activated = True
                triggers.append("qSOFA >= 2 with suspected infection")
            if mean_arterial_pressure < 65.0:
                bundle_activated = True
                triggers.append(f"Refractory hypotension (MAP {mean_arterial_pressure:.1f} < 65 mmHg)")
            if serum_lactate is not None and serum_lactate >= 2.0:
                bundle_activated = True
                triggers.append(f"Hyperlactatemia ({serum_lactate:.1f} >= 2.0 mmol/L)")

        required_actions = []
        fluid_volume_ml = round(patient_weight_kg * 30.0)

        if bundle_activated:
            required_actions.append({
                "step": 1,
                "action": "MEASURE_LACTATE",
                "detail": "Measure blood lactate level STAT; remeasure within 2-4 hours if initial lactate > 2.0 mmol/L",
            })
            required_actions.append({
                "step": 2,
                "action": "OBTAIN_BLOOD_CULTURES",
                "detail": "Obtain two sets of blood cultures (aerobic/anaerobic) prior to initiating antimicrobial therapy",
            })
            required_actions.append({
                "step": 3,
                "action": "ADMINISTER_ANTIBIOTICS",
                "detail": "Administer empiric broad-spectrum IV antimicrobials within 1 hour (e.g. Cefepime + Vancomycin)",
            })
            if mean_arterial_pressure < 65.0 or (serum_lactate is not None and serum_lactate >= 4.0):
                required_actions.append({
                    "step": 4,
                    "action": "FLUID_RESUSCITATION",
                    "detail": f"Begin rapid IV administration of 30 mL/kg balanced crystalloids ({fluid_volume_ml} mL Lactated Ringer's)",
                })
                required_actions.append({
                    "step": 5,
                    "action": "VASOPRESSORS",
                    "detail": "Initiate IV Norepinephrine infusion to target MAP >= 65 mmHg if hypotensive during or after fluid loading",
                })

        return {
            "ssc_bundle_activated": bundle_activated,
            "activation_triggers": triggers,
            "crystalloid_volume_ml": fluid_volume_ml if bundle_activated else 0,
            "target_map_mmHg": 65.0,
            "bundle_actions": required_actions,
        }

    # ── 7. Comprehensive ClinicalAgentResponse Generator ───────────────────────

    def evaluate_emergency_patient(
        self,
        patient_id: str,
        chief_complaint: str,
        heart_rate: float,
        systolic_bp: float,
        oxygen_sat: float,
        respiratory_rate: float,
        diastolic_bp: float = 80.0,
        temperature_c: float = 37.0,
        age_years: float = 40.0,
        is_unresponsive_or_dying: bool = False,
        is_high_risk_situation: bool = False,
        severe_pain_or_distress: bool = False,
        confused_lethargic_disoriented: bool = False,
        avpu: str = "A",
        gcs: int = 15,
        projected_resources_needed: int = 1,
        suspected_infection: bool = False,
        serum_lactate: Optional[float] = None,
        platelets: Optional[float] = None,
        bilirubin: Optional[float] = None,
        creatinine: Optional[float] = None,
        fio2: float = 0.21,
        vitals_history: Optional[List[Dict[str, float]]] = None,
    ) -> ClinicalAgentResponse:
        """Executes deep emergency clinical reasoning, emitting structured ClinicalAgentResponse."""
        # 1. ESI triage
        esi_res = self.evaluate_esi_triage(
            chief_complaint=chief_complaint,
            heart_rate=heart_rate,
            systolic_bp=systolic_bp,
            oxygen_sat=oxygen_sat,
            respiratory_rate=respiratory_rate,
            is_unresponsive_or_dying=is_unresponsive_or_dying,
            is_high_risk_situation=is_high_risk_situation,
            projected_resources_needed=projected_resources_needed,
            age_years=age_years,
            temperature_c=temperature_c,
            severe_pain_or_distress=severe_pain_or_distress,
            confused_lethargic_disoriented=confused_lethargic_disoriented,
            avpu=avpu,
            gcs=gcs,
        )

        # 2. qSOFA
        qsofa_res = self.calculate_qsofa(
            respiratory_rate=respiratory_rate,
            systolic_bp=systolic_bp,
            gcs=gcs,
            avpu=avpu,
            altered_mentation=confused_lethargic_disoriented,
        )

        # 3. NEWS2
        news2_res = self.calculate_news2(
            respiratory_rate=respiratory_rate,
            oxygen_sat=oxygen_sat,
            hypercapnic_respiratory_failure=False,
            supplemental_oxygen=oxygen_sat < 94.0,
            systolic_bp=systolic_bp,
            heart_rate=heart_rate,
            consciousness=avpu,
            temperature_c=temperature_c,
        )

        # 4. Shock Indices & Trajectory
        si_res = self.evaluate_shock_indices(heart_rate, systolic_bp, diastolic_bp)
        history_list = vitals_history or [
            {"heart_rate": heart_rate, "systolic_bp": systolic_bp, "diastolic_bp": diastolic_bp}
        ]
        traj_res = self.evaluate_trajectory_trend(history_list)

        # 5. Full SOFA
        map_calc = (2 * diastolic_bp + systolic_bp) / 3.0
        sofa_res = self.calculate_full_sofa(
            spo2=oxygen_sat,
            fio2=fio2,
            platelets=platelets,
            bilirubin=bilirubin,
            mean_arterial_pressure=map_calc,
            gcs=gcs,
            creatinine=creatinine,
        )

        # 6. SSC Sepsis Bundle
        ssc_res = self.evaluate_ssc_bundle(
            suspected_infection=suspected_infection,
            qsofa_score=qsofa_res["qsofa_score"],
            mean_arterial_pressure=map_calc,
            serum_lactate=serum_lactate,
        )

        # Formulate FHIR Action Proposals
        proposals: List[Any] = []
        recommendations: List[Dict[str, Any]] = []

        # Triage Recommendation
        recommendations.append({
            "domain": "TRIAGE",
            "esi_level": esi_res["esi_level"],
            "acuity": esi_res["acuity_category"],
            "target_bed": esi_res["recommended_area"],
            "time_to_physician_min": esi_res["target_time_to_physician_min"],
        })

        if esi_res["esi_level"] == 1:
            proposals.append(
                FHIRFlagProposal(
                    patient_id=patient_id,
                    status="active",
                    category="clinical_alert",
                    severity="critical",
                    code="418138009",  # Resuscitation required
                    details=f"CRITICAL ESI-1: {esi_res['rationale']}. Immediate Resuscitation Bay activation.",
                    author="EmergencyTriageAgent",
                )
            )
            proposals.append(
                FHIRServiceRequestProposal(
                    patient_id=patient_id,
                    category="procedure",
                    code="305367005",  # Resuscitation
                    description="Immediate Emergency Resuscitation and Airway Team Evaluation",
                    urgency="stat",
                    indication=chief_complaint,
                )
            )

        # Sepsis & SSC Proposals
        if ssc_res["ssc_bundle_activated"]:
            recommendations.append({
                "domain": "CRITICAL_CARE_SEPSIS",
                "status": "SURVIVING_SEPSIS_BUNDLE_ACTIVATED",
                "bundle_actions": ssc_res["bundle_actions"],
            })
            proposals.append(
                FHIRFlagProposal(
                    patient_id=patient_id,
                    status="active",
                    category="clinical_alert",
                    severity="critical",
                    code="433324003",  # Sepsis
                    details="CODE SEPSIS: Surviving Sepsis Campaign 1-Hour Bundle activated.",
                    author="EmergencyTriageAgent",
                )
            )
            proposals.append(
                FHIRServiceRequestProposal(
                    patient_id=patient_id,
                    category="laboratory",
                    code="25802-4",  # LOINC: Blood culture
                    description="Blood Culture x2 sets (Aerobic/Anaerobic) STAT prior to antibiotics",
                    urgency="stat",
                    indication="Suspected Sepsis Resuscitation",
                )
            )
            proposals.append(
                FHIRServiceRequestProposal(
                    patient_id=patient_id,
                    category="laboratory",
                    code="2524-7",  # LOINC: Lactate [Moles/volume] in Serum or Plasma
                    description="Serum Lactate STAT",
                    urgency="stat",
                    indication="Sepsis Hypoperfusion Assessment",
                )
            )
            proposals.append(
                FHIRMedicationRequestProposal(
                    patient_id=patient_id,
                    medication_name="Cefepime 2g IV + Vancomycin 15-20mg/kg IV",
                    dosage="Broad spectrum empiric coverage",
                    route="intravenous",
                    frequency="STAT once",
                    indication="Empiric Sepsis Resuscitation Antimicrobial Therapy",
                    clinical_evidence=[
                        "Surviving Sepsis Campaign 2021 1-Hour Bundle",
                        f"qSOFA: {qsofa_res['qsofa_score']}",
                        f"SOFA: {sofa_res['total_sofa_score']}",
                    ],
                    priority="stat",
                )
            )
            if map_calc < 65.0:
                proposals.append(
                    FHIRMedicationRequestProposal(
                        patient_id=patient_id,
                        medication_name="Lactated Ringer's Solution",
                        dosage=f"{ssc_res['crystalloid_volume_ml']} mL (30 mL/kg)",
                        route="intravenous",
                        frequency="rapid infusion",
                        indication="Septic Shock Fluid Resuscitation",
                        clinical_evidence=["Hypotension MAP < 65 mmHg"],
                        priority="stat",
                    )
                )
                proposals.append(
                    FHIRMedicationRequestProposal(
                        patient_id=patient_id,
                        medication_name="Norepinephrine",
                        dosage="0.02 - 1.0 mcg/kg/min titrate to MAP >= 65",
                        route="intravenous continuous infusion",
                        frequency="continuous",
                        indication="Refractory Septic Shock Vasopressor Support",
                        clinical_evidence=["MAP < 65 despite fluid loading"],
                        priority="stat",
                    )
                )

        # High NEWS2 proposal
        if news2_res["total_news2_score"] >= 7:
            proposals.append(
                FHIRFlagProposal(
                    patient_id=patient_id,
                    status="active",
                    category="clinical_alert",
                    severity="high",
                    code="428800007",  # High early warning score
                    details=f"NEWS2 High Risk Score: {news2_res['total_news2_score']}. Rapid Response Outreach Alert.",
                    author="EmergencyTriageAgent",
                )
            )

        # Trajectory deterioration flag
        if traj_res["trajectory_state"] in ["DETERIORATING", "CRITICAL_COLLAPSE"]:
            proposals.append(
                FHIRFlagProposal(
                    patient_id=patient_id,
                    status="active",
                    category="safety_risk",
                    severity="critical" if traj_res["trajectory_state"] == "CRITICAL_COLLAPSE" else "high",
                    code="271594007",  # Syncope / shock
                    details=f"Physiological Deterioration: {traj_res['trajectory_description']} (Delta SI: {traj_res['delta_shock_index']})",
                    author="EmergencyTriageAgent",
                )
            )

        confidence = 0.95
        if not platelets or not bilirubin or not creatinine:
            confidence = 0.88  # Partial labs for full SOFA

        return ClinicalAgentResponse(
            agent_name="EmergencyTriageAgent",
            epistemic_confidence=confidence,
            recommendations=recommendations,
            proposed_fhir_actions=proposals,
            reasoning=(
                f"Assigned ESI {esi_res['esi_level']} ({esi_res['acuity_category']}). "
                f"NEWS2: {news2_res['total_news2_score']}. qSOFA: {qsofa_res['qsofa_score']}. "
                f"Full SOFA: {sofa_res['total_sofa_score']}. Shock Index: {si_res['shock_index']} ({si_res['shock_index_status']}). "
                f"Trajectory: {traj_res['trajectory_state']}."
            ),
            metadata={
                "esi": esi_res,
                "qsofa": qsofa_res,
                "full_sofa": sofa_res,
                "news2": news2_res,
                "shock_indices": si_res,
                "trajectory": traj_res,
                "ssc_bundle": ssc_res,
            },
        )


# Singleton triage agent instance
ed_triage_agent = EmergencyTriageAgent()
