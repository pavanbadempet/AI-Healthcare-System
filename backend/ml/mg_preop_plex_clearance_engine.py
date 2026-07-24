"""
Myasthenia Gravis Surgical Risk & Pre-Operative PLEX Clearance Engine
====================================================================
Evaluates pre-operative risk for major elective surgery or thymectomy in Myasthenia Gravis patients.
Assesses Forced Vital Capacity (FVC < 80% or < 2.0 L), bulbar muscle weakness, and QMG score (> 10.5) to mandate
3-5 sessions of pre-operative Plasma Exchange (PLEX) or IVIG (2 g/kg) to prevent post-operative myasthenic crisis.
"""

from typing import Dict


class MgPreopPlexClearanceEngine:
    """Evaluates surgical clearance and pre-operative PLEX/IVIG optimization in MG patients."""

    def evaluate_preop_clearance(
        self,
        planned_procedure: str,  # THYMECTOMY, CARDIAC_SURGERY, ABDOMINAL_SURGERY, OTHER
        forced_vital_capacity_liters: float,  # FVC < 2.0 L is high risk for post-op respiratory failure
        fvc_percent_predicted: float,  # FVC < 80%
        bulbar_symptoms_present: bool,  # Dysphagia, dysarthria, impaired cough
        qmg_score: float,  # Quantitative Myasthenia Gravis score (> 10.5 = moderate-to-severe)
        on_high_dose_steroids: bool = False,  # Prednisone >= 30 mg/day
    ) -> Dict[str, any]:
        high_respiratory_risk = forced_vital_capacity_liters < 2.0 or fvc_percent_predicted < 80.0
        high_bulbar_risk = bulbar_symptoms_present
        severe_disease_activity = qmg_score >= 10.5

        plex_or_ivig_indicated = high_respiratory_risk or high_bulbar_risk or severe_disease_activity

        recommendation = "CLEARED FOR SURGERY: Patient has preserved respiratory mechanics (FVC >= 80%), mild symptoms, and low risk for post-operative crisis. Continue current oral Pyridostigmine regimen."
        if plex_or_ivig_indicated:
            reasons = []
            if high_respiratory_risk:
                reasons.append(f"Reduced FVC ({forced_vital_capacity_liters:.1f} L, {fvc_percent_predicted:.0f}% predicted)")
            if high_bulbar_risk:
                reasons.append("Active bulbar weakness / impaired airway protection")
            if severe_disease_activity:
                reasons.append(f"Elevated QMG score ({qmg_score:.1f} >= 10.5)")

            reason_str = ", ".join(reasons)
            recommendation = f"HIGH RISK FOR POST-OPERATIVE MYASTHENIC CRISIS ({reason_str}): MANDATE pre-operative optimization with 5 sessions of Plasma Exchange (PLEX) or IVIG (2 g/kg divided over 5 days) starting 7-10 days prior to surgery. Defer elective surgery until FVC > 80% and bulbar symptoms resolve."

        return {
            "planned_procedure": planned_procedure,
            "fvc_liters": forced_vital_capacity_liters,
            "fvc_percent_predicted": fvc_percent_predicted,
            "high_respiratory_risk": high_respiratory_risk,
            "high_bulbar_risk": high_bulbar_risk,
            "plex_or_ivig_indicated": plex_or_ivig_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mg_preop_plex_engine = MgPreopPlexClearanceEngine()
