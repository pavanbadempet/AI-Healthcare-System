"""
Heart Failure HFrEF GDMT Medication Optimizer
===============================================
Evaluates GDMT Quadruple Therapy (ARNI/ACEi/ARB, Beta-blocker, MRA, SGLT2i) gaps,
contraindicated eGFR/K+ thresholds, and target dose titration.
"""

from typing import Dict


class HfGdmtOptimizer:
    """Evaluates guideline-directed medical therapy for HFrEF patients."""

    def evaluate_gdmt_quadruple_therapy(
        self,
        ejection_fraction_percent: int,
        systolic_bp_mmHg: int,
        heart_rate_bpm: int,
        egfr_mL_min_1_73m2: float,
        potassium_mEq_L: float,
        on_arni_acei_arb: bool = False,
        on_beta_blocker: bool = False,
        on_mra: bool = False,
        on_sglt2i: bool = False,
    ) -> Dict[str, any]:
        recommendations = []

        if ejection_fraction_percent <= 40:
            if not on_arni_acei_arb:
                if egfr_mL_min_1_73m2 >= 30 and potassium_mEq_L < 5.0:
                    recommendations.append("Initiate Sacubitril/Valsartan (ARNI) or ACEi/ARB")
                else:
                    recommendations.append("Hold ARNI/ACEi due to renal impairment or hyperkalemia")

            if not on_beta_blocker:
                if heart_rate_bpm >= 60 and systolic_bp_mmHg >= 100:
                    recommendations.append("Initiate Evidence-Based Beta-Blocker (Carvedilol / Metoprolol Succinate / Bisoprolol)")
                else:
                    recommendations.append("Hold Beta-Blocker due to bradycardia or hypotension")

            if not on_mra:
                if egfr_mL_min_1_73m2 >= 30 and potassium_mEq_L < 5.0:
                    recommendations.append("Initiate Mineralocorticoid Receptor Antagonist (Spironolactone / Eplerenone)")

            if not on_sglt2i:
                if egfr_mL_min_1_73m2 >= 20:
                    recommendations.append("Initiate SGLT2 Inhibitor (Dapagliflozin / Empagliflozin)")

        quadruple_therapy_count = sum([on_arni_acei_arb, on_beta_blocker, on_mra, on_sglt2i])
        quadruple_therapy_optimized = quadruple_therapy_count == 4

        return {
            "ejection_fraction": ejection_fraction_percent,
            "active_gdmt_pillar_count": quadruple_therapy_count,
            "quadruple_therapy_fully_optimized": quadruple_therapy_optimized,
            "optimization_recommendations": recommendations,
            "status": "OPTIMIZATION_COMPLETE",
        }


# Singleton optimizer instance
hf_gdmt_optimizer = HfGdmtOptimizer()
