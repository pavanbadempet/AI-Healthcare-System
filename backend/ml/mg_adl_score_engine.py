"""
Myasthenia Gravis MG-ADL (Activities of Daily Living) Rating Engine
====================================================================
Scores 8 MG-ADL items (0 to 24 points) to evaluate targeted biologics:
FcRn receptor inhibitors (Efgartigimod / Rozanolixizumab) vs Complement inhibitors (Eculizumab / Ravulizumab).
"""

from typing import Dict


class MgAdlScoreEngine:
    """Calculates MG-ADL score for Myasthenia Gravis targeted therapy eligibility."""

    def calculate_mg_adl_score(
        self,
        talking_score_0_to_3: int,
        chewing_score_0_to_3: int,
        swallowing_score_0_to_3: int,
        breathing_score_0_to_3: int,
        impairment_brushing_teeth_combing_hair_0_to_3: int,
        arising_from_chair_0_to_3: int,
        double_vision_diplopia_0_to_3: int,
        eyelid_droop_ptosis_0_to_3: int,
        achr_antibody_positive: bool = True,
    ) -> Dict[str, any]:
        total_mg_adl_score = (
            talking_score_0_to_3
            + chewing_score_0_to_3
            + swallowing_score_0_to_3
            + breathing_score_0_to_3
            + impairment_brushing_teeth_combing_hair_0_to_3
            + arising_from_chair_0_to_3
            + double_vision_diplopia_0_to_3
            + eyelid_droop_ptosis_0_to_3
        )

        bulbar_respiratory_impairment = (swallowing_score_0_to_3 + breathing_score_0_to_3) >= 3
        fcrn_inhibitor_indicated = False
        complement_inhibitor_indicated = False

        if total_mg_adl_score >= 6:
            fcrn_inhibitor_indicated = True
            if total_mg_adl_score >= 8 and achr_antibody_positive:
                complement_inhibitor_indicated = True

        recommendation = "Mild MG-ADL impairment (< 6): Maintain oral Pyridostigmine (60 mg TID-QID) & oral prednisone"
        if complement_inhibitor_indicated and bulbar_respiratory_impairment:
            recommendation = "Severe Refractory gMG (MG-ADL >= 8, AChR+): Indication for Complement C5 Inhibitor (Eculizumab / Ravulizumab) or FcRn Blocker (Efgartigimod); ensure Meningococcal Vaccination"
        elif fcrn_inhibitor_indicated:
            recommendation = "Moderate-to-Severe gMG (MG-ADL >= 6): Initiate FcRn Receptor Blocker (Efgartigimod alfa - 10 mg/kg IV weekly for 4 weeks)"

        return {
            "total_mg_adl_score": total_mg_adl_score,
            "achr_antibody_positive": achr_antibody_positive,
            "fcrn_blocker_efgartigimod_indicated": fcrn_inhibitor_indicated,
            "c5_complement_inhibitor_eculizumab_indicated": complement_inhibitor_indicated,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
mg_adl_engine = MgAdlScoreEngine()
