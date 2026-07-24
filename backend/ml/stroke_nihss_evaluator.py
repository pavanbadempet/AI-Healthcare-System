"""
Ischemic Stroke NIHSS Severity & Thrombolysis Eligibility Calculator
======================================================================
Calculates NIH Stroke Scale (NIHSS) score, evaluates tPA (Alteplase/Tenecteplase)
4.5-hour window contraindications, and flags mechanical thrombectomy eligibility.
"""

from typing import Dict


class StrokeNihssEvaluator:
    """Evaluates acute ischemic stroke severity and thrombolysis/thrombectomy eligibility."""

    def evaluate_stroke_tpa_eligibility(
        self,
        nihss_score: int,  # 0 to 42
        symptom_onset_hours_ago: float,
        has_intracranial_hemorrhage_on_ct: bool = False,
        systolic_bp_mmHg: int = 150,
        platelet_count_k_uL: int = 200,
    ) -> Dict[str, any]:
        severity = "MINOR_STROKE"
        if nihss_score >= 21:
            severity = "SEVERE_STROKE"
        elif nihss_score >= 16:
            severity = "MODERATE_TO_SEVERE_STROKE"
        elif nihss_score >= 5:
            severity = "MODERATE_STROKE"

        tpa_eligible = True
        contraindication_reasons = []

        if symptom_onset_hours_ago > 4.5:
            tpa_eligible = False
            contraindication_reasons.append("Symptom onset > 4.5 hours ago")

        if has_intracranial_hemorrhage_on_ct:
            tpa_eligible = False
            contraindication_reasons.append("Intracranial hemorrhage detected on non-contrast CT")

        if systolic_bp_mmHg > 185:
            tpa_eligible = False
            contraindication_reasons.append("BP > 185/110 mmHg (requires IV Labetalol/Nicardipine first)")

        if platelet_count_k_uL < 100:
            tpa_eligible = False
            contraindication_reasons.append("Thrombocytopenia (platelets < 100,000/uL)")

        thrombectomy_eligible = nihss_score >= 6 and symptom_onset_hours_ago <= 24.0 and not has_intracranial_hemorrhage_on_ct

        return {
            "nihss_score": nihss_score,
            "stroke_severity_tier": severity,
            "tpa_thrombolysis_eligible": tpa_eligible,
            "tpa_contraindications": contraindication_reasons,
            "mechanical_thrombectomy_eligible": thrombectomy_eligible,
            "recommended_action": "Stat IV Alteplase/Tenecteplase & Neurovascular Transfer" if tpa_eligible else "Endovascular Thrombectomy Evaluation / Medical Management",
            "status": "EVALUATION_COMPLETE",
        }


# Singleton evaluator instance
stroke_evaluator = StrokeNihssEvaluator()
