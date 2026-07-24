"""
Acute Variceal Bleeding Baveno VII Pre-emptive TIPS Engine
===========================================================
Evaluates Baveno VII criteria for Early Pre-emptive TIPS (within 24-72 hours):
Child-Pugh C (10-13 pts) or Child-Pugh B (> 7 pts with active bleeding) following EBL + vasoactive drugs.
"""

from typing import Dict


class VaricealBleedingBaveno7TipsEngine:
    """Evaluates Baveno VII early pre-emptive TIPS indications in acute variceal hemorrhage."""

    def evaluate_baveno7_preemptive_tips(
        self,
        child_pugh_score_points: int,  # 5 to 15
        active_bleeding_on_endoscopy: bool = True,
        initial_ebl_successful: bool = True,
        vasoactive_drug_started: bool = True,  # Terlipressin / Octreotide
    ) -> Dict[str, any]:
        child_c = child_pugh_score_points >= 10 and child_pugh_score_points <= 13
        child_b_active = child_pugh_score_points >= 8 and active_bleeding_on_endoscopy

        preemptive_tips_indicated = (child_c or child_b_active) and initial_ebl_successful and vasoactive_drug_started

        recommendation = "Standard management: Continue vasoactive therapy (Terlipressin/Octreotide) for 2-5 days + IV Ceftriaxone 1g daily + secondary prophylaxis (NSBB + EBL)"
        if preemptive_tips_indicated:
            recommendation = f"Baveno VII PRE-EMPTIVE TIPS INDICATED (Child-Pugh Score {child_pugh_score_points}): Perform early PTFE-covered TIPS within 24 to 72 hours of endoscopic band ligation to improve 1-year survival"

        return {
            "child_pugh_score_points": child_pugh_score_points,
            "preemptive_tips_indicated": preemptive_tips_indicated,
            "recommended_timing_window": "WITHIN_24_TO_72_HOURS" if preemptive_tips_indicated else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
baveno7_tips_engine = VaricealBleedingBaveno7TipsEngine()
