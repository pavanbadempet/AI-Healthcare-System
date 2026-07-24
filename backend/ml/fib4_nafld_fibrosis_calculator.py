"""
Hepatic Steatosis Fibrosis-4 (FIB-4) Calculator
================================================
Calculates FIB-4 index to stratify liver fibrosis risk in MASLD / MASH / HCV.
"""

import math
from typing import Dict


class Fib4NafldFibrosisCalculator:
    """Calculates FIB-4 score for non-invasive liver fibrosis staging."""

    def calculate_fib4_score(
        self,
        age_years: int,
        ast_u_l: float,
        alt_u_l: float,
        platelet_count_10_3_ul: float,
    ) -> Dict[str, any]:
        # FIB-4 = (Age * AST) / (Platelets * sqrt(ALT))
        fib4 = round((age_years * ast_u_l) / (platelet_count_10_3_ul * math.sqrt(max(alt_u_l, 1.0))), 2)

        risk_tier = "LOW_RISK_F0_F1"
        fibroscan_indicated = False

        if fib4 > 2.67:
            risk_tier = "HIGH_RISK_ADVANCED_FIBROSIS_F3_F4"
            fibroscan_indicated = True
        elif fib4 >= 1.30:
            risk_tier = "INDETERMINATE_RISK_F2"
            fibroscan_indicated = True

        recommendation = "FIB-4 < 1.30: Low risk of advanced fibrosis; repeat FIB-4 in 1-2 years"
        if fib4 > 2.67:
            recommendation = "FIB-4 > 2.67: High risk of F3-F4 fibrosis/cirrhosis; Stat Hepatology referral & Transient Elastography (FibroScan)"
        elif fib4 >= 1.30:
            recommendation = "FIB-4 1.30-2.67: Indeterminate risk; Order Transient Elastography (FibroScan) or ELF test"

        return {
            "fib4_score": fib4,
            "fibrosis_risk_tier": risk_tier,
            "transient_elastography_fibroscan_indicated": fibroscan_indicated,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
fib4_calculator = Fib4NafldFibrosisCalculator()
