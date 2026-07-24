"""
Myasthenia Gravis (MG) Thymectomy Eligibility Engine
====================================================
Evaluates MGTX trial criteria (AChR+ non-thymomatous gMG, age 18-65, duration < 5 years, MGFA II-IV)
and presence of Thymoma on CT/MRI to recommend transsternal or robotic video-assisted thymectomy (RATS).
"""

from typing import Dict


class MgThymectomyEligibilityEngine:
    """Evaluates thymectomy indication (MGTX trial criteria or Thymoma) in Myasthenia Gravis."""

    def evaluate_thymectomy_eligibility(
        self,
        achr_antibody_positive: bool = True,
        thymoma_present_on_imaging: bool = False,
        age_years: int = 35,
        disease_duration_years: float = 2.0,
        mgfa_class: str = "CLASS_II_MODERATE",  # CLASS_I_OCULAR, CLASS_II, CLASS_III, CLASS_IV, CLASS_V
    ) -> Dict[str, any]:
        mgtx_eligible = (
            achr_antibody_positive
            and not thymoma_present_on_imaging
            and 18 <= age_years <= 65
            and disease_duration_years <= 5.0
            and mgfa_class in ["CLASS_II_MODERATE", "CLASS_III_SEVERE", "CLASS_IV_VERY_SEVERE"]
        )

        thymoma_indication = thymoma_present_on_imaging

        surgery_indicated = mgtx_eligible or thymoma_indication

        surgical_approach = "ROBOTIC_THYMECTOMY_RATS_OR_VATS"
        if thymoma_indication:
            surgical_approach = "EXTENDED_TRANSSTERNAL_THYMECTOMY"

        recommendation = "Thymectomy NOT indicated (Pure ocular MGFA Class I, seronegative non-thymomatous MG, or age > 65); continue medical immunosuppression"
        if surgery_indicated:
            if thymoma_indication:
                recommendation = "THYMOMA DETECTED ON CHEST CT: Perform complete surgical thymectomy (extended transsternal approach) regardless of MG antibody status to prevent local tumor invasion"
            else:
                recommendation = f"ELIGIBLE FOR MGTX THYMECTOMY (AChR+ gMG, Age {age_years}, Duration {disease_duration_years}y): Recommend {surgical_approach} to increase rate of clinical remission and reduce corticosteroid requirements"

        return {
            "mgtx_trial_eligible": mgtx_eligible,
            "thymoma_indication": thymoma_indication,
            "thymectomy_indicated": surgery_indicated,
            "recommended_surgical_approach": surgical_approach if surgery_indicated else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mg_thymectomy_engine = MgThymectomyEligibilityEngine()
