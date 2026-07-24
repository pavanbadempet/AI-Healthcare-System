"""
Invasive Coronary Myocardial Bridging Index Engine
==================================================
Evaluates dynamic systolic compression ("milking effect") of the left anterior descending (LAD) coronary artery,
diastolic hyperemic FFR (dFFR <= 0.76), and inotropic Dobutamine provocation.
"""

from typing import Dict, Optional


class MyocardialBridgingIndexEngine:
    """Evaluates invasive angiography and intravascular ultrasound (IVUS) for Myocardial Bridging."""

    def evaluate_myocardial_bridging(
        self,
        systolic_diameter_compression_percent: float,
        diastolic_ffr_hyperemic: Optional[float] = None,
        dobutamine_provocation_st_shift: bool = False,
        ivus_half_moon_sign_present: bool = False,
    ) -> Dict[str, any]:
        significant_bridging = (
            systolic_diameter_compression_percent >= 50.0
            and (
                (diastolic_ffr_hyperemic is not None and diastolic_ffr_hyperemic <= 0.76)
                or dobutamine_provocation_st_shift
                or ivus_half_moon_sign_present
            )
        )

        phenotype = "NON_SIGNIFICANT_BRIDGING"
        beta_blockers_indicated = False
        surgery_indicated = False

        if significant_bridging:
            phenotype = "HEMODYNAMICALLY_SIGNIFICANT_MYOCARDIAL_BRIDGING"
            beta_blockers_indicated = True
            if diastolic_ffr_hyperemic is not None and diastolic_ffr_hyperemic <= 0.70:
                surgery_indicated = True

        recommendation = "Benign myocardial bridging; no specific anti-anginal therapy required"
        if surgery_indicated:
            recommendation = "Severe Ischemic Myocardial Bridging (dFFR <= 0.70): Initiate High-Dose Beta-Blocker & Surgical Unroofing (Surgical Myotomy) evaluation; avoid Nitrates & Stents"
        elif beta_blockers_indicated:
            recommendation = "Symptomatic Myocardial Bridging: Initiate Non-dihydropyridine CCB or Beta-Blocker (Metoprolol/Nadolol); strictly avoid Nitrates (worsens systolic compression)"

        return {
            "systolic_diameter_compression_percent": systolic_diameter_compression_percent,
            "diastolic_ffr_hyperemic": diastolic_ffr_hyperemic,
            "hemodynamically_significant": significant_bridging,
            "bridging_phenotype": phenotype,
            "beta_blocker_or_ccb_indicated": beta_blockers_indicated,
            "surgical_unroofing_myotomy_indicated": surgery_indicated,
            "avoid_nitrates_and_stents": significant_bridging,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
myocardial_bridging_engine = MyocardialBridgingIndexEngine()
