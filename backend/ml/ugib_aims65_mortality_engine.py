"""
Acute Upper Gastrointestinal Bleeding (UGIB) AIMS65 Mortality Score Engine
===========================================================================
Calculates AIMS65 mortality risk score (Albumin < 3.0 g/dL, INR > 1.5, Mental status alter, SBP <= 90, Age > 65)
to stratify ICU admission vs floor monitoring and urgent endoscopy timing (< 12-24 hours).
"""

from typing import Dict


class UgibAims65MortalityEngine:
    """Calculates AIMS65 mortality risk score for acute UGIB."""

    def calculate_aims65_score(
        self,
        serum_albumin_g_dL: float,  # < 3.0 g/dL = 1 pt
        inr: float,  # > 1.5 = 1 pt
        altered_mental_status: bool,  # GCS < 15 or lethargy = 1 pt
        systolic_bp_mmHg: float,  # <= 90 mmHg = 1 pt
        age_years: int,  # > 65 years = 1 pt
    ) -> Dict[str, any]:
        score = 0
        if serum_albumin_g_dL < 3.0:
            score += 1
        if inr > 1.5:
            score += 1
        if altered_mental_status:
            score += 1
        if systolic_bp_mmHg <= 90.0:
            score += 1
        if age_years > 65:
            score += 1

        in_hospital_mortality = "0.3%"
        risk_category = "LOW_RISK"
        icu_indicated = False

        if score >= 3:
            risk_category = "HIGH_RISK"
            in_hospital_mortality = "10.3% - 24.5%"
            icu_indicated = True
        elif score >= 2:
            risk_category = "INTERMEDIATE_RISK"
            in_hospital_mortality = "3.2%"

        recommendation = f"AIMS65 Score: {score} ({risk_category}, Mortality {in_hospital_mortality}): Floor monitoring; perform EGD within 24 hours of resuscitation"
        if icu_indicated:
            recommendation = f"CRITICAL AIMS65 SCORE: {score} ({risk_category}, Mortality {in_hospital_mortality}): Admit to ICU; urgent EGD within 12 hours following IV PPI bolus + infusion and endotracheal intubation for airway protection"

        return {
            "aims65_score": score,
            "risk_category": risk_category,
            "in_hospital_mortality_percent": in_hospital_mortality,
            "icu_admission_indicated": icu_indicated,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
aims65_engine = UgibAims65MortalityEngine()
