"""
Wells' Criteria for Pulmonary Embolism (PE) Risk Calculator
=============================================================
Calculates pre-test probability score for PE and guides D-Dimer vs CT Pulmonary Angiography (CTPA) diagnostic pathways.
"""

from typing import Dict


class WellsPeCalculator:
    """Calculates Wells' score for Pulmonary Embolism risk estimation."""

    def calculate_wells_pe_score(
        self,
        clinical_signs_of_dvt: bool,
        pe_most_likely_diagnosis: bool,
        heart_rate_over_100: bool,
        immobilization_or_surgery_past_4wks: bool,
        prior_dvt_or_pe: bool,
        hemoptysis: bool,
        active_cancer: bool,
    ) -> Dict[str, any]:
        score = 0.0
        if clinical_signs_of_dvt:
            score += 3.0
        if pe_most_likely_diagnosis:
            score += 3.0
        if heart_rate_over_100:
            score += 1.5
        if immobilization_or_surgery_past_4wks:
            score += 1.5
        if prior_dvt_or_pe:
            score += 1.5
        if hemoptysis:
            score += 1.0
        if active_cancer:
            score += 1.0

        pe_likely = score > 4.0

        recommendation = "Stat CT Pulmonary Angiography (CTPA) & therapeutic anticoagulation evaluation" if pe_likely else "High-sensitivity D-Dimer assay (if negative, PE excluded without imaging)"

        return {
            "wells_score": score,
            "pe_likely": pe_likely,
            "risk_tier": "HIGH_PE_UNLIKELY" if not pe_likely else "HIGH_PE_LIKELY",
            "diagnostic_pathway_recommendation": recommendation,
            "order_ctpa_immediately": pe_likely,
            "status": "SCORING_COMPLETE",
        }


# Singleton calculator instance
wells_pe_calculator = WellsPeCalculator()
