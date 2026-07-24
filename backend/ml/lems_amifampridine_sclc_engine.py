"""
Lambert-Eaton Myasthenic Syndrome (LEMS) Amifampridine & SCLC Screening Engine
================================================================================
Evaluates LEMS clinical presentation (proximal muscle weakness with post-exercise facilitation, autonomic dry mouth),
P/Q-type VGCC antibodies, and DELTA-P score to recommend 3,4-Diaminopyridine (Amifampridine 15-60 mg/day)
and mandate chest CT / PET-CT for Small Cell Lung Cancer (SCLC) screening.
"""

from typing import Dict


class LemsAmifampridineSclcEngine:
    """Evaluates LEMS diagnosis, Amifampridine therapy eligibility, and SCLC screening protocol."""

    def evaluate_lems_management(
        self,
        proximal_muscle_weakness_present: bool,
        post_exercise_facilitation_present: bool,  # Brief strength recovery after 10s maximum voluntary contraction
        autonomic_dysfunction_dry_mouth: bool,  # Dry mouth, constipation, erectile dysfunction
        vgcc_antibody_positive: bool,  # Voltage-gated calcium channel antibodies positive
        smoking_history_pack_years: float = 0.0,
        age_years: float = 55.0,
    ) -> Dict[str, any]:
        lems_confirmed = (
            proximal_muscle_weakness_present
            and post_exercise_facilitation_present
            and (vgcc_antibody_positive or autonomic_dysfunction_dry_mouth)
        )

        amifampridine_indicated = lems_confirmed

        # Calculate DELTA-P score for SCLC risk: Age >= 50, smoking history, autonomic dysfunction, weight loss
        sclc_risk_score = 0
        if age_years >= 50:
            sclc_risk_score += 1
        if smoking_history_pack_years >= 10.0:
            sclc_risk_score += 2
        if autonomic_dysfunction_dry_mouth:
            sclc_risk_score += 1

        high_sclc_risk = sclc_risk_score >= 2 or smoking_history_pack_years > 0

        recommendation = "EVALUATION INCOMPLETE: Patient does not meet full diagnostic criteria for LEMS. Obtain electrodiagnostic repetitive nerve stimulation (RNS) demonstrating > 100% incremental compound muscle action potential (CMAP) response."
        if lems_confirmed:
            recommendation = f"LAMBERT-EATON MYASTHENIC SYNDROME CONFIRMED: Initiate 3,4-Diaminopyridine (Amifampridine 15-60 mg daily in divided doses) for symptomatic neuromuscular enhancement. MANDATE Chest CT with IV contrast and PET-CT scan every 6 months for 2 years to screen for underlying Small Cell Lung Cancer (SCLC, High Risk DELTA-P score {sclc_risk_score})."

        return {
            "lems_confirmed": lems_confirmed,
            "amifampridine_indicated": amifampridine_indicated,
            "sclc_risk_score": sclc_risk_score,
            "high_sclc_risk": high_sclc_risk,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
lems_engine = LemsAmifampridineSclcEngine()
