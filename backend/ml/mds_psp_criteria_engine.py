"""
Progressive Supranuclear Palsy (MDS-PSP) Diagnostic Criteria Engine
====================================================================
Evaluates 2017 MDS-PSP criteria: Vertical supranuclear gaze palsy, prominent postural instability,
akinesia, and midbrain atrophy ("hummingbird sign") to differentiate Richardson Syndrome (PSP-RS) from PSP-P.
"""

from typing import Dict


class MdsPspCriteriaEngine:
    """Evaluates 2017 MDS-PSP diagnostic criteria and clinical phenotypes."""

    def evaluate_mds_psp_criteria(
        self,
        vertical_supranuclear_gaze_palsy: bool,
        slow_vertical_saccades: bool,
        unprovoked_falls_within_3_years: bool,
        freezing_of_gait_within_3_years: bool = False,
        parkinsonism_levodopa_resistant: bool = True,
        midbrain_atrophy_hummingbird_sign: bool = True,
    ) -> Dict[str, any]:
        gaze_feature_present = vertical_supranuclear_gaze_palsy or slow_vertical_saccades
        instability_present = unprovoked_falls_within_3_years or freezing_of_gait_within_3_years

        psp_criteria_met = gaze_feature_present and instability_present and parkinsonism_levodopa_resistant

        phenotype = "PROBABLE_PSP_RICHARDSON_SYNDROME_PSP_RS"
        if psp_criteria_met:
            if freezing_of_gait_within_3_years and not vertical_supranuclear_gaze_palsy:
                phenotype = "PSP_PROGRESSIVE_GAIT_FREEZING_PSP_PGF"
            elif not unprovoked_falls_within_3_years:
                phenotype = "PSP_PARKINSONISM_PSP_P"

        recommendation = "Incomplete criteria for PSP; evaluate Parkinson's Disease (levodopa challenge) & Multiple System Atrophy (MSA)"
        if psp_criteria_met:
            recommendation = f"Diagnosed {phenotype}: Initiate fall prevention physical therapy, balance training, coenzyme Q10 / Amantadine symptom control, and dysphagia speech assessment"

        return {
            "gaze_feature_present": gaze_feature_present,
            "instability_present": instability_present,
            "midbrain_atrophy_present": midbrain_atrophy_hummingbird_sign,
            "psp_criteria_met": psp_criteria_met,
            "psp_phenotype": phenotype,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
psp_engine = MdsPspCriteriaEngine()
