"""
Chronic Kidney Disease (CKD) KDIGO GFR/Albuminuria Risk Matrix Engine
======================================================================
Classifies CKD progression risk (Low, Moderate, High, Very High) based on eGFR Stages G1-G5
and Albuminuria Categories A1-A3.
"""

from typing import Dict


class CkdKdigoRiskMatrixEngine:
    """Classifies CKD progression and cardiovascular mortality risk using KDIGO matrix."""

    def evaluate_ckd_kdigo_stage(
        self,
        egfr_mL_min_1_73m2: float,
        urine_albumin_creatinine_ratio_mg_g: float,
    ) -> Dict[str, any]:
        # GFR Stage
        gfr_stage = "G1_NORMAL_OR_HIGH"
        if egfr_mL_min_1_73m2 < 15.0:
            gfr_stage = "G5_KIDNEY_FAILURE"
        elif egfr_mL_min_1_73m2 < 30.0:
            gfr_stage = "G4_SEVERELY_DECREASED"
        elif egfr_mL_min_1_73m2 < 45.0:
            gfr_stage = "G3b_MODERATELY_TO_SEVERELY_DECREASED"
        elif egfr_mL_min_1_73m2 < 60.0:
            gfr_stage = "G3a_MILDLY_TO_MODERATELY_DECREASED"
        elif egfr_mL_min_1_73m2 < 90.0:
            gfr_stage = "G2_MILDLY_DECREASED"

        # Albuminuria Category
        alb_category = "A1_NORMAL_TO_MILDLY_INCREASED"
        if urine_albumin_creatinine_ratio_mg_g > 300.0:
            alb_category = "A3_SEVERELY_INCREASED"
        elif urine_albumin_creatinine_ratio_mg_g >= 30.0:
            alb_category = "A2_MODERATELY_INCREASED"

        risk_tier = "LOW_RISK"
        if gfr_stage in ["G4_SEVERELY_DECREASED", "G5_KIDNEY_FAILURE"] or alb_category == "A3_SEVERELY_INCREASED":
            risk_tier = "VERY_HIGH_RISK"
        elif gfr_stage in ["G3a_MILDLY_TO_MODERATELY_DECREASED", "G3b_MODERATELY_TO_SEVERELY_DECREASED"] or alb_category == "A2_MODERATELY_INCREASED":
            risk_tier = "HIGH_RISK"

        recommendation = "Annual eGFR & ACR monitoring"
        if risk_tier == "VERY_HIGH_RISK":
            recommendation = "Nephrology consult, SGLT2i + RAS inhibitor, & evaluate dialysis access"
        elif risk_tier == "HIGH_RISK":
            recommendation = "Initiate SGLT2 inhibitor (Dapagliflozin/Empagliflozin) & ACEi/ARB titration"

        return {
            "egfr_stage": gfr_stage,
            "albuminuria_category": alb_category,
            "ckd_kdigo_risk_tier": risk_tier,
            "nephrology_referral_recommended": risk_tier == "VERY_HIGH_RISK",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
ckd_kdigo_engine = CkdKdigoRiskMatrixEngine()
