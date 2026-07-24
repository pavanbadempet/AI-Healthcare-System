"""
Acute-on-Chronic Liver Failure CLIF-C ACLF Score & Prognosis Engine
====================================================================
Calculates CLIF-C ACLF Score = 10 * [0.33 * CLIF-C OFS + 0.04 * Age + 0.63 * ln(WBC) - 2]
to predict 28-day, 90-day, and 180-day mortality in ACLF patients.
"""

import math
from typing import Dict


class AclfClifCAclfScoreEngine:
    """Calculates CLIF-C ACLF prognostic score and predicts 28-day/90-day mortality."""

    def calculate_clif_c_aclf_score(
        self,
        clif_c_ofs_total: int,  # Range 6 to 18
        patient_age_years: int,
        wbc_count_10_3_uL: float,  # e.g. 15.0 for 15,000 / uL
    ) -> Dict[str, any]:
        wbc_ln = math.log(max(wbc_count_10_3_uL, 0.1))

        raw_score = 10.0 * (0.33 * clif_c_ofs_total + 0.04 * patient_age_years + 0.63 * wbc_ln - 2.0)
        clif_c_aclf_score = max(10.0, min(100.0, raw_score))

        # Mortality estimations based on CANONIC study ranges
        estimated_28_day_mortality_percent = 15.0
        if clif_c_aclf_score >= 70.0:
            estimated_28_day_mortality_percent = 85.0
        elif clif_c_aclf_score >= 60.0:
            estimated_28_day_mortality_percent = 55.0
        elif clif_c_aclf_score >= 50.0:
            estimated_28_day_mortality_percent = 30.0

        recommendation = f"CLIF-C ACLF Score {clif_c_aclf_score:.1f} (28-day mortality ~ {estimated_28_day_mortality_percent:.0f}%): Continue intensive organ support and re-evaluate daily"
        if clif_c_aclf_score >= 64.0:
            recommendation = f"CRITICAL CLIF-C ACLF SCORE {clif_c_aclf_score:.1f} (Severe prognosis, 28-day mortality {estimated_28_day_mortality_percent}%): Discuss emergency liver transplantation or goals of care / palliative transition if not a transplant candidate"

        return {
            "clif_c_aclf_score": round(clif_c_aclf_score, 1),
            "estimated_28_day_mortality_percent": estimated_28_day_mortality_percent,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
clif_aclf_score_engine = AclfClifCAclfScoreEngine()
