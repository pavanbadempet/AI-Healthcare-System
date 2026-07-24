"""
Acute Stroke Extended Window Mechanical Thrombectomy (DAWN / DEFUSE 3) Engine
==============================================================================
Evaluates DAWN (6-24h) & DEFUSE 3 (6-16h) mismatch criteria: Core infarct volume (<= 50-70 mL),
penumbra volume (>= 15 mL), mismatch ratio (>= 1.8), and NIHSS to direct endovascular thrombectomy (EVT).
"""

from typing import Dict


class StrokeThrombectomyExtendedWindowEngine:
    """Evaluates 6-24 hour extended window Endovascular Thrombectomy (EVT) eligibility."""

    def evaluate_extended_window_evt(
        self,
        time_last_known_well_hours: float,  # 6.0 to 24.0
        core_infarct_volume_mL: float,  # CTP / MRI DWI core
        ischemic_penumbra_volume_mL: float,  # Tmax > 6s perfusion deficit
        nihss_score: int,  # Baseline NIHSS
        lvo_location: str = "ICA_OR_M1",  # ICA_OR_M1, M2, OTHER
        age_years: float = 65.0,
    ) -> Dict[str, any]:
        mismatch_ratio = (
            (ischemic_penumbra_volume_mL / max(core_infarct_volume_mL, 1.0))
            if core_infarct_volume_mL > 0
            else 2.0
        )
        mismatch_volume_mL = max(ischemic_penumbra_volume_mL - core_infarct_volume_mL, 0.0)

        dawn_eligible = False
        defuse3_eligible = False

        if 6.0 <= time_last_known_well_hours <= 24.0 and lvo_location == "ICA_OR_M1":
            # DAWN Criteria (6-24h)
            if age_years >= 80:
                if nihss_score >= 10 and core_infarct_volume_mL < 21.0:
                    dawn_eligible = True
            else:
                if nihss_score >= 10 and core_infarct_volume_mL < 31.0:
                    dawn_eligible = True
                elif nihss_score >= 20 and core_infarct_volume_mL < 51.0:
                    dawn_eligible = True

            # DEFUSE 3 Criteria (6-16h)
            if 6.0 <= time_last_known_well_hours <= 16.0:
                if core_infarct_volume_mL < 70.0 and mismatch_volume_mL >= 15.0 and mismatch_ratio >= 1.8 and nihss_score >= 6:
                    defuse3_eligible = True

        evt_indicated = dawn_eligible or defuse3_eligible

        trial_criteria = "INELIGIBLE"
        if dawn_eligible and defuse3_eligible:
            trial_criteria = "DAWN_AND_DEFUSE_3_ELIGIBLE"
        elif dawn_eligible:
            trial_criteria = "DAWN_ELIGIBLE_6_TO_24_HOURS"
        elif defuse3_eligible:
            trial_criteria = "DEFUSE_3_ELIGIBLE_6_TO_16_HOURS"

        recommendation = "Ineligible for extended window EVT; proceed with best medical management & permissive hypertension"
        if evt_indicated:
            recommendation = f"Candidate for Extended Window Mechanical Thrombectomy ({trial_criteria}): Core {core_infarct_volume_mL} mL, Mismatch Ratio {round(mismatch_ratio, 1)}; perform urgent stent-retriever / aspiration catheter EVT"

        return {
            "time_last_known_well_hours": time_last_known_well_hours,
            "core_infarct_volume_mL": core_infarct_volume_mL,
            "mismatch_ratio": round(mismatch_ratio, 2),
            "dawn_eligible": dawn_eligible,
            "defuse3_eligible": defuse3_eligible,
            "evt_indicated": evt_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
stroke_evt_engine = StrokeThrombectomyExtendedWindowEngine()
