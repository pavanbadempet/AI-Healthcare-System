"""
PAH Prostacyclin (IP) Receptor Pathway Optimization Engine
===========================================================
Evaluates oral Selexipag (200-1600 mcg BID) vs inhaled Iloprost (2.5-5 mcg 6-9x daily)
in WHO FC II-III PAH patients in COMPERA 2.0 intermediate risk strata.
"""

from typing import Dict


class PahProstacyclinPathwayEngine:
    """Evaluates Prostacyclin IP receptor agonist therapy for PAH."""

    def evaluate_prostacyclin_pathway(
        self,
        who_functional_class: int,  # 2, 3, 4
        current_oral_selexipag_dose_mcg_bid: float = 0.0,
        prostacyclin_intolerant_diarrhea_jaw_pain: bool = False,
        parenteral_prostacyclin_indicated: bool = False,
    ) -> Dict[str, any]:
        target_selexipag_mcg_bid = 1600.0

        recommended_agent = "ORAL_SELEXIPAG"
        if parenteral_prostacyclin_indicated or who_functional_class == 4:
            recommended_agent = "PARENTERAL_EPOPROSTENOL_OR_TREPROSTINIL"
        elif prostacyclin_intolerant_diarrhea_jaw_pain:
            recommended_agent = "INHALED_ILOPROST_OR_TYVASO"

        next_selexipag_dose = current_oral_selexipag_dose_mcg_bid
        if recommended_agent == "ORAL_SELEXIPAG" and current_oral_selexipag_dose_mcg_bid < target_selexipag_mcg_bid:
            next_selexipag_dose = min(target_selexipag_mcg_bid, current_oral_selexipag_dose_mcg_bid + 200.0)

        recommendation = f"PROSTACYCLIN PATHWAY OPTIMIZATION: Recommended modality {recommended_agent}. Titrate oral Selexipag by 200 mcg BID weekly to maximum tolerated dose up to 1600 mcg BID"

        return {
            "recommended_prostacyclin_agent": recommended_agent,
            "current_selexipag_dose_mcg_bid": current_oral_selexipag_dose_mcg_bid,
            "recommended_next_selexipag_dose_mcg_bid": next_selexipag_dose,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
prostacyclin_engine = PahProstacyclinPathwayEngine()
