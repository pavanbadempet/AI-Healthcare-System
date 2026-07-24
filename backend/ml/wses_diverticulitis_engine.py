"""
WSES Acute Diverticulitis Severity Score Engine
===============================================
Calculates WSES score (0 to 15) combining CT severity, ASA physical status, age, and immunocompromise
to predict 30-day emergency mortality and surgical strategy.
"""

from typing import Dict


class WsesDiverticulitisEngine:
    """Calculates World Society of Emergency Surgery (WSES) diverticulitis score."""

    def calculate_wses_score(
        self,
        ct_stage: str,               # "UNCOMPLICATED", "STAGE_1A_PERICOLIC_AIR", "STAGE_1B_ABSCESS_SMALL", "STAGE_2A_ABSCESS_LARGE", "STAGE_2B_DISTANT_AIR", "STAGE_3_PERITONITIS_FLUID", "STAGE_4_FECAL_PERITONITIS"
        asa_physical_status: int,     # 1 to 5
        age_years: int,
        immunocompromised_host: bool = False,
    ) -> Dict[str, any]:
        score = 0

        # CT Stage
        ct_map = {
            "UNCOMPLICATED": 0,
            "STAGE_1A_PERICOLIC_AIR": 1,
            "STAGE_1B_ABSCESS_SMALL": 2,
            "STAGE_2A_ABSCESS_LARGE": 3,
            "STAGE_2B_DISTANT_AIR": 4,
            "STAGE_3_PERITONITIS_FLUID": 6,
            "STAGE_4_FECAL_PERITONITIS": 8,
        }
        score += ct_map.get(ct_stage, 0)

        # ASA status
        if asa_physical_status >= 4:
            score += 3
        elif asa_physical_status == 3:
            score += 2

        # Age
        if age_years >= 70:
            score += 2

        # Immunocompromise
        if immunocompromised_host:
            score += 2

        mortality_pct = 1.0
        if score >= 9:
            mortality_pct = 35.0
        elif score >= 5:
            mortality_pct = 12.0

        emergency_surgery = ct_stage in ["STAGE_3_PERITONITIS_FLUID", "STAGE_4_FECAL_PERITONITIS"] or score >= 8

        recommendation = "Low WSES score: Non-operative conservative management or outpatient oral antibiotics"
        if emergency_surgery:
            recommendation = "High WSES score / Diffuse Peritonitis: Emergency Laparotomy with Hartmann's Procedure or Primary Resection + Ileostomy"

        return {
            "wses_total_score": score,
            "thirty_day_mortality_percent": mortality_pct,
            "emergency_laparotomy_indicated": emergency_surgery,
            "clinical_recommendation": recommendation,
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
wses_diverticulitis_engine = WsesDiverticulitisEngine()
