"""
Longitudinal Disease Progression Predictor
===========================================
Predicts 5-year chronic kidney disease (CKD stage 1-5) and diabetes HbA1c progression
curves based on historical lab trends over multi-year encounter records.
"""

from typing import Dict, List, Optional


class DiseaseProgressionPredictor:
    """Forecasts longitudinal clinical disease trajectories over 1-5 year horizons."""

    def predict_ckd_progression(
        self,
        historical_egfr: List[float],
        historical_years: List[int],
    ) -> Dict[str, any]:
        if not historical_egfr or len(historical_egfr) < 2:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": "At least 2 historical eGFR readings required to model trajectory.",
            }

        # Linear regression slope computation for eGFR decline rate
        n = len(historical_egfr)
        sum_x = sum(historical_years)
        sum_y = sum(historical_egfr)
        sum_xy = sum(x * y for x, y in zip(historical_years, historical_egfr))
        sum_xx = sum(x * x for x in historical_years)

        denominator = n * sum_xx - sum_x * sum_x
        slope = (n * sum_xy - sum_x * sum_y) / denominator if denominator != 0 else 0.0

        annual_decline_rate = round(-slope, 2)
        current_egfr = historical_egfr[-1]
        projected_3yr_egfr = max(5.0, round(current_egfr + (slope * 3), 1))
        projected_5yr_egfr = max(5.0, round(current_egfr + (slope * 5), 1))

        # Determine CKD Stage
        def get_ckd_stage(egfr_val: float) -> str:
            if egfr_val >= 90:
                return "Stage 1 (Normal/High)"
            elif egfr_val >= 60:
                return "Stage 2 (Mildly Decreased)"
            elif egfr_val >= 30:
                return "Stage 3 (Moderate)"
            elif egfr_val >= 15:
                return "Stage 4 (Severe)"
            else:
                return "Stage 5 (Kidney Failure)"

        return {
            "current_egfr": current_egfr,
            "annual_decline_rate_ml_min": annual_decline_rate,
            "current_ckd_stage": get_ckd_stage(current_egfr),
            "projected_3yr_egfr": projected_3yr_egfr,
            "projected_3yr_ckd_stage": get_ckd_stage(projected_3yr_egfr),
            "projected_5yr_egfr": projected_5yr_egfr,
            "projected_5yr_ckd_stage": get_ckd_stage(projected_5yr_egfr),
            "progression_risk": "RAPID_DECLINER" if annual_decline_rate >= 4.0 else "STABLE",
            "status": "SUCCESS",
        }


# Singleton predictor instance
progression_predictor = DiseaseProgressionPredictor()
