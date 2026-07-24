"""
ALS SOD1 Gene Antisense Oligonucleotide Tofersen (Qalsody) & Biomarker Engine
=============================================================================
Evaluates SOD1 mutation positive ALS for intrathecal Tofersen ASO therapy (100 mg intrathecal)
and tracks plasma neurofilament light chain (NfL) reduction as a surrogate biomarker.
"""

from typing import Dict, Optional


class AlsRelyvrioTofersenBiomarkerEngine:
    """Evaluates Tofersen ASO eligibility and NfL biomarker monitoring for SOD1 ALS."""

    def evaluate_tofersen_eligibility(
        self,
        sod1_mutation_confirmed: bool = True,
        plasma_nfl_pg_mL: float = 65.0,  # Baseline NfL
        post_treatment_nfl_pg_mL: Optional[float] = None,
        intrathecal_administration_feasible: bool = True,
    ) -> Dict[str, any]:
        tofersen_indicated = sod1_mutation_confirmed and intrathecal_administration_feasible

        nfl_reduction_percent = 0.0
        nfl_response = "BASELINE_NOT_EVALUATED"

        if post_treatment_nfl_pg_mL is not None and plasma_nfl_pg_mL > 0:
            nfl_reduction_percent = round(((plasma_nfl_pg_mL - post_treatment_nfl_pg_mL) / plasma_nfl_pg_mL) * 100.0, 1)
            if nfl_reduction_percent >= 30.0:
                nfl_response = "SIGNIFICANT_BIOMARKER_RESPONSE"
            else:
                nfl_response = "MODEST_OR_STABLE_BIOMARKER_RESPONSE"

        recommendation = "Tofersen (Qalsody) NOT indicated (Requires confirmed pathogenic SOD1 gene mutation); evaluate multidisciplinary ALS care and Riluzole"
        if tofersen_indicated:
            recommendation = f"ELIGIBLE FOR TOFERSEN (Qalsody Intrathecal ASO): Administer Tofersen 100 mg intrathecal loading doses at Day 1, Day 15, Day 29, followed by maintenance 100 mg IT Q28D. Monitor plasma NfL every 3 months (Current NfL response: {nfl_response})"

        return {
            "sod1_mutation_confirmed": sod1_mutation_confirmed,
            "tofersen_indicated": tofersen_indicated,
            "dosing_route": "INTRATHECAL_100MG",
            "nfl_reduction_percent": nfl_reduction_percent,
            "nfl_response": nfl_response,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
tofersen_engine = AlsRelyvrioTofersenBiomarkerEngine()
