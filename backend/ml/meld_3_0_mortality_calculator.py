"""
Chronic Liver Disease MELD 3.0 Mortality Predictor
==================================================
Calculates MELD 3.0 score incorporating female sex adjustment, bilirubin, INR,
sodium, creatinine, and albumin for 90-day liver transplant allocation.
"""

import math
from typing import Dict


class Meld30MortalityCalculator:
    """Calculates MELD 3.0 score for end-stage liver disease mortality & transplant priority."""

    def calculate_meld_3_0_score(
        self,
        female_sex: bool,
        serum_bilirubin_mg_dL: float,
        inr: float,
        serum_sodium_mEq_L: float,
        serum_creatinine_mg_dL: float,
        serum_albumin_g_dL: float,
        dialysis_twice_in_past_week: bool = False,
    ) -> Dict[str, any]:
        # Bound inputs per OPTN MELD 3.0 specification
        bili = max(1.0, serum_bilirubin_mg_dL)
        inr_val = max(1.0, inr)
        creat = 4.0 if dialysis_twice_in_past_week else min(4.0, max(1.0, serum_creatinine_mg_dL))
        sod = min(137.0, max(125.0, serum_sodium_mEq_L))
        alb = min(3.5, max(1.5, serum_albumin_g_dL))

        # MELD 3.0 formula
        meld = (
            1.33 * (1 if female_sex else 0)
            + 4.56 * math.log(bili)
            + 0.82 * (137.0 - sod)
            - 0.24 * (137.0 - sod) * math.log(bili)
            + 9.09 * math.log(inr_val)
            + 1.85 * (3.5 - alb)
            - 1.83 * (3.5 - alb) * math.log(inr_val)
            + 2.66 * math.log(creat)
            + 11.14
        )

        meld_3_0_score = int(round(min(40.0, max(6.0, meld))))

        ninety_day_mortality_pct = 2.0
        if meld_3_0_score >= 35:
            ninety_day_mortality_pct = 80.0
        elif meld_3_0_score >= 25:
            ninety_day_mortality_pct = 50.0
        elif meld_3_0_score >= 15:
            ninety_day_mortality_pct = 20.0

        transplant_listing = meld_3_0_score >= 15

        recommendation = "MELD 3.0 < 15: Routine hepatology follow-up & HCC surveillance Q6M"
        if meld_3_0_score >= 35:
            recommendation = "MELD 3.0 >= 35 (80% 90-Day Mortality): STAT Status 1A/High-Priority Liver Transplant UNOS listing & ICU care"
        elif transplant_listing:
            recommendation = "MELD 3.0 >= 15: Active UNOS Liver Transplant Listing indicated"

        return {
            "meld_3_0_score": meld_3_0_score,
            "ninety_day_mortality_risk_percent": ninety_day_mortality_pct,
            "transplant_listing_indicated": transplant_listing,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
meld_3_0_calculator = Meld30MortalityCalculator()
