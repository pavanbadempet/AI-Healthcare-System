"""
Eosinophilic Esophagitis (EoE) EREFS Endoscopic Severity Score Engine
========================================================================
Evaluates EREFS endoscopic criteria (Edema, Rings, Exudates, Furrows, Strictures: 0 to 9 points)
to grade esophageal remodeling, guide Dupilumab / Swallowed Steroids, and trigger Balloon Dilatation.
"""

from typing import Dict


class EoeErefsScoreEngine:
    """Evaluates EREFS endoscopic score for Eosinophilic Esophagitis."""

    def calculate_erefs_score(
        self,
        edema_score_0_to_1: int,
        rings_trachealisation_score_0_to_3: int,
        exudates_score_0_to_2: int,
        furrows_score_0_to_2: int,
        stricture_diameter_score_0_to_1: int,
    ) -> Dict[str, any]:
        total_erefs_score = (
            edema_score_0_to_1
            + rings_trachealisation_score_0_to_3
            + exudates_score_0_to_2
            + furrows_score_0_to_2
            + stricture_diameter_score_0_to_1
        )

        remodeling_stage = "MILD_INFLAMMATORY_EOE"
        dilatation_indicated = stricture_diameter_score_0_to_1 > 0 or rings_trachealisation_score_0_to_3 >= 2
        dupilumab_indicated = False

        if total_erefs_score >= 5 or stricture_diameter_score_0_to_1 > 0:
            remodeling_stage = "SEVERE_FIBROSTENOTIC_EOE"
            dupilumab_indicated = True
        elif total_erefs_score >= 3:
            remodeling_stage = "MODERATE_INFLAMMATORY_EOE"

        recommendation = "Mild EoE: Initiate High-Dose PPI (Omeprazole 20-40 mg BID) or 6-Food Elimination Diet (6FED)"
        if remodeling_stage == "SEVERE_FIBROSTENOTIC_EOE":
            recommendation = "Severe Fibrostenotic EoE (EREFS >= 5 / Stricture): Initiate Dupilumab (300 mg QW SC) or Swallowed Topical Steroids (Budesonide 1 mg BID slurry); perform Careful Esophageal Balloon Dilatation if caliber < 13mm"
        elif remodeling_stage == "MODERATE_INFLAMMATORY_EOE":
            recommendation = "Moderate Inflammatory EoE: Initiate Swallowed Viscous Budesonide (1 mg BID) & repeat EGD biopsy in 8-12 weeks to assess histologic response (< 15 eos/hpf)"

        return {
            "total_erefs_score": total_erefs_score,
            "remodeling_stage": remodeling_stage,
            "dupilumab_biologic_indicated": dupilumab_indicated,
            "esophageal_balloon_dilatation_indicated": dilatation_indicated,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
eoe_erefs_engine = EoeErefsScoreEngine()
