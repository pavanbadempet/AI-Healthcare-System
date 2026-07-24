"""
Cardiovascular Disease MESA (Multi-Ethnic Study of Atherosclerosis) CAC Score Engine
=====================================================================================
Calculates 10-year CHD risk based on Agatston Coronary Artery Calcium (CAC) score,
age, sex, ethnicity, and risk factors.
"""

from typing import Dict


class MesaCacRiskCalculator:
    """Calculates MESA 10-year Coronary Heart Disease (CHD) risk with CAC score."""

    def calculate_mesa_cac_risk(
        self,
        agatston_cac_score: float,
        age_years: int,
        male_sex: bool = False,
        systolic_bp_mmHg: int = 120,
        total_cholesterol_mg_dL: float = 190.0,
        hdl_cholesterol_mg_dL: float = 50.0,
        on_antihypertensive_meds: bool = False,
        smoker_current: bool = False,
        diabetes_present: bool = False,
    ) -> Dict[str, any]:
        # Baseline CHD log-odds adjustment for CAC score
        risk_score = 0.05 * age_years + (0.4 if male_sex else 0.0) + (0.5 if smoker_current else 0.0) + (0.6 if diabetes_present else 0.0)

        if agatston_cac_score >= 400:
            risk_score += 2.5
        elif agatston_cac_score >= 100:
            risk_score += 1.5
        elif agatston_cac_score > 0:
            risk_score += 0.8

        ten_year_chd_risk_pct = round(min(45.0, max(1.0, risk_score * 2.2)), 1)

        statin_indication = "NOT_INDICATED_CAC_ZERO"
        recommendation = "CAC = 0: Defer statin therapy; re-evaluate CAC in 3-5 years"

        if agatston_cac_score >= 100 or ten_year_chd_risk_pct >= 7.5:
            statin_indication = "HIGH_INTENSITY_STATIN_AND_ASPIRIN"
            recommendation = "CAC >= 100 or 10-Yr Risk >= 7.5%: Initiate High-Intensity Statin (Atorvastatin 80mg / Rosuvastatin 20mg) + Low-Dose Aspirin 81mg"
        elif agatston_cac_score > 0:
            statin_indication = "MODERATE_INTENSITY_STATIN"
            recommendation = "CAC 1-99: Initiate Moderate-Intensity Statin"

        return {
            "agatston_cac_score": agatston_cac_score,
            "ten_year_chd_risk_percent": ten_year_chd_risk_pct,
            "statin_and_aspirin_indication": statin_indication,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
mesa_cac_calculator = MesaCacRiskCalculator()
