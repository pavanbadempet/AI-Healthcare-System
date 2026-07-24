"""
Arterial Blood Gas (ABG) Acid-Base & Oxygenation Calculator
============================================================
Interprets primary acid-base disorders (Metabolic Acidosis with Anion Gap calculation,
Respiratory Acidosis/Alkalosis) and calculates PaO2/FiO2 ratio for ARDS classification.
"""

from typing import Dict, Optional


class AbgAcidBaseCalculator:
    """Interprets ABG parameters and classifies ARDS oxygenation status."""

    def evaluate_abg(
        self,
        ph: float,
        paco2_mmHg: float,
        hco3_mEq_L: float,
        pao2_mmHg: float,
        fio2_decimal: float = 0.21,
        sodium_mEq_L: Optional[float] = None,
        chloride_mEq_L: Optional[float] = None,
    ) -> Dict[str, any]:
        primary_disorder = "NORMAL_ACID_BASE"
        if ph < 7.35:
            if hco3_mEq_L < 22.0:
                primary_disorder = "METABOLIC_ACIDOSIS"
            elif paco2_mmHg > 45.0:
                primary_disorder = "RESPIRATORY_ACIDOSIS"
        elif ph > 7.45:
            if hco3_mEq_L > 26.0:
                primary_disorder = "METABOLIC_ALKALOSIS"
            elif paco2_mmHg < 35.0:
                primary_disorder = "RESPIRATORY_ALKALOSIS"

        anion_gap = None
        is_high_anion_gap = False
        if sodium_mEq_L and chloride_mEq_L:
            anion_gap = round(sodium_mEq_L - (chloride_mEq_L + hco3_mEq_L), 1)
            is_high_anion_gap = anion_gap > 12.0

        pao2_fio2_ratio = round(pao2_mmHg / max(fio2_decimal, 0.21), 1)

        ards_category = "NO_ARDS"
        if pao2_fio2_ratio <= 100.0:
            ards_category = "SEVERE_ARDS"
        elif pao2_fio2_ratio <= 200.0:
            ards_category = "MODERATE_ARDS"
        elif pao2_fio2_ratio <= 300.0:
            ards_category = "MILD_ARDS"

        return {
            "ph": ph,
            "paco2": paco2_mmHg,
            "hco3": hco3_mEq_L,
            "primary_acid_base_disorder": primary_disorder,
            "anion_gap": anion_gap,
            "high_anion_gap_acidosis": is_high_anion_gap,
            "pao2_fio2_ratio": pao2_fio2_ratio,
            "ards_classification": ards_category,
            "status": "INTERPRETATION_COMPLETE",
        }


# Singleton calculator instance
abg_calculator = AbgAcidBaseCalculator()
