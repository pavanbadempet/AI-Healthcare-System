"""
Myasthenia Gravis Thymoma & Thymectomy Surgical Eligibility Engine
====================================================================
Evaluates MGTX trial surgical eligibility for thymectomy: Mandatory for all Thymoma-associated MG (Masaoka I-IV)
and recommended for non-thymomatous AChR+ generalized MG (Age 18-65, disease duration < 5 years).
"""

from typing import Dict


class MgThymectomyEligibilityEngine:
    """Evaluates thymectomy surgical indication according to MGTX trial guidelines."""

    def evaluate_thymectomy_eligibility(
        self,
        thymoma_present_on_ct_mri: bool = False,
        achr_antibody_positive: bool = True,
        generalized_mg_symptoms: bool = True,  # Class II-IV gMG
        patient_age_years: int = 35,  # MGTX range 18 to 65
        disease_duration_years: float = 2.5,  # MGTX <= 5 years
    ) -> Dict[str, any]:
        mandatory_for_thymoma = thymoma_present_on_ct_mri

        mgtx_eligible = (
            not thymoma_present_on_ct_mri
            and achr_antibody_positive
            and generalized_mg_symptoms
            and (18 <= patient_age_years <= 65)
            and disease_duration_years <= 5.0
        )

        thymectomy_indicated = mandatory_for_thymoma or mgtx_eligible

        surgical_approach = "EXTENDED_TRANSTERNAAL_OR_ROBOTIC_MINIMALLY_INVASIVE_THYMECTOMY"

        recommendation = "Thymectomy not routinely indicated (ocular MG only, MuSK+ MG without thymoma, age > 65 without thymoma, or duration > 5 years)"
        if mandatory_for_thymoma:
            recommendation = f"MANDATORY THYMECTOMY FOR THYMOMA (Masaoka stage I-IV resection): Perform surgical resection of mediastinal mass ({surgical_approach}) regardless of age or disease duration to treat thymoma and improve MG control"
        elif mgtx_eligible:
            recommendation = f"THYMECTOMY RECOMMENDED (MGTX Trial Criteria: AChR+ gMG, Age {patient_age_years}, Duration {disease_duration_years} yrs): Perform extended thymectomy ({surgical_approach}) to increase complete stable remission rate and reduce required prednisone dose"

        return {
            "mandatory_for_thymoma": mandatory_for_thymoma,
            "mgtx_eligible": mgtx_eligible,
            "thymectomy_indicated": thymectomy_indicated,
            "surgical_approach": surgical_approach if thymectomy_indicated else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mg_thymectomy_engine = MgThymectomyEligibilityEngine()
