"""
QTc Interval Prolongation & Torsades de Pointes Risk Calculator
===============================================================
Calculates QTc using Bazett & Fridericia formulas, evaluates drug-induced QTc prolongation,
and triggers Torsades de Pointes (TdP) risk alerts (QTc > 500 ms).
"""

import math
from typing import Dict


class QtcProlongationCalculator:
    """Calculates corrected QTc intervals and Torsades de Pointes risk."""

    def calculate_qtc(
        self,
        qt_interval_ms: float,
        heart_rate_bpm: int,
        female_sex: bool = False,
        on_qt_prolonging_meds: bool = False,
    ) -> Dict[str, any]:
        rr_sec = 60.0 / max(heart_rate_bpm, 20)

        # Bazett's Formula: QTc = QT / sqrt(RR)
        qtc_bazett_ms = round(qt_interval_ms / math.sqrt(rr_sec), 1)

        # Fridericia's Formula: QTc = QT / (RR^(1/3))
        qtc_fridericia_ms = round(qt_interval_ms / (rr_sec ** (1.0 / 3.0)), 1)

        normal_cutoff = 470.0 if female_sex else 450.0
        is_prolonged = qtc_bazett_ms > normal_cutoff
        tdp_high_risk = qtc_bazett_ms >= 500.0 or (is_prolonged and on_qt_prolonging_meds)

        recommendation = "Maintain standard ECG monitoring"
        if tdp_high_risk:
            recommendation = "Stat Discontinue QT-prolonging drugs, check serum K+/Mg2+, & telemetry monitoring"
        elif is_prolonged:
            recommendation = "Monitor serum electrolytes & avoid adding additional QT-prolonging agents"

        return {
            "qt_raw_ms": qt_interval_ms,
            "heart_rate_bpm": heart_rate_bpm,
            "qtc_bazett_ms": qtc_bazett_ms,
            "qtc_fridericia_ms": qtc_fridericia_ms,
            "qtc_prolonged": is_prolonged,
            "torsades_de_pointes_high_risk": tdp_high_risk,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
qtc_calculator = QtcProlongationCalculator()
