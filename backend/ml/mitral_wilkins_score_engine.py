"""
Mitral Stenosis Wilkins Echocardiographic Score Engine
======================================================
Scores 4 echocardiographic features (leaflet mobility, thickness, calcification, subvalvular thickening)
from 1 to 4 to guide Percutaneous Transvenous Mitral Commissurotomy (PTMC) candidacy.
"""

from typing import Dict


class MitralWilkinsScoreEngine:
    """Calculates Wilkins Echo Score (4-16) for Mitral Valve Stenosis."""

    def calculate_wilkins_score(
        self,
        leaflet_mobility_score: int,       # 1 to 4
        valvular_thickness_score: int,     # 1 to 4
        valvular_calcification_score: int, # 1 to 4
        subvalvular_thickening_score: int, # 1 to 4
        mitral_valve_area_cm2: float = 1.0,
    ) -> Dict[str, any]:
        total_score = leaflet_mobility_score + valvular_thickness_score + valvular_calcification_score + subvalvular_thickening_score

        ptmc_candidacy = total_score <= 8
        intervention = "CONSERVATIVE_OR_SURGICAL_MVR"

        recommendation = "Score > 8: Favorable for Surgical Mitral Valve Replacement (MVR) due to severe subvalvular/calcific distortion"
        if ptmc_candidacy:
            intervention = "PERCUTANEOUS_BALLOON_VALVULOPLASTY_PTMC"
            recommendation = "Score <= 8: Highly favorable anatomy for Percutaneous Transvenous Mitral Commissurotomy (PTMC)"

        return {
            "wilkins_total_score": total_score,
            "ptmc_balloon_valvuloplasty_eligible": ptmc_candidacy,
            "recommended_intervention": intervention,
            "clinical_recommendation": recommendation,
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
mitral_wilkins_engine = MitralWilkinsScoreEngine()
