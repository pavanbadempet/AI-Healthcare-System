"""
Normal Pressure Hydrocephalus (NPH) Evan's Index & Tap Test Engine
===================================================================
Evaluates Evan's Index (> 0.30), Hakim's Triad, CSF Tap Test (30-40 mL removal) gait improvement (>= 20%),
and DESH MRI features to predict response to Programmable VP Shunting.
"""

from typing import Dict


class NphEvansIndexTapTestEngine:
    """Evaluates Normal Pressure Hydrocephalus (NPH) diagnostic criteria and VP shunt candidacy."""

    def evaluate_nph_shunt_candidacy(
        self,
        evans_index: float,  # Frontal horn max width / internal skull max width (> 0.30)
        gait_ataxia_present: bool,
        cognitive_decline_present: bool,
        urinary_incontinence_present: bool,
        csf_tap_test_gait_speed_improvement_pct: float,  # >= 20%
        desh_mri_features_present: bool = True,  # Disproportionately Enlarged Subarachnoid Space Hydrocephalus
        lp_opening_pressure_mm_h2o: float = 140.0,  # 60-200 mm H2O normal pressure
    ) -> Dict[str, any]:
        ventriculomegaly = evans_index > 0.30
        normal_pressure = 60.0 <= lp_opening_pressure_mm_h2o <= 200.0

        hakim_triad_count = sum([gait_ataxia_present, cognitive_decline_present, urinary_incontinence_present])
        positive_tap_test = csf_tap_test_gait_speed_improvement_pct >= 20.0

        nph_confirmed = ventriculomegaly and normal_pressure and gait_ataxia_present and (positive_tap_test or desh_mri_features_present)

        shunt_candidacy = "INELIGIBLE"
        if nph_confirmed:
            if positive_tap_test:
                shunt_candidacy = "HIGH_PROBABILITY_VP_SHUNT_RESPONDER"
            else:
                shunt_candidacy = "MODERATE_PROBABILITY_VP_SHUNT_RESPONDER"

        recommendation = "Criteria for NPH not met; evaluate alternative causes of gait impairment / dementia (e.g. Vascular Dementia, Parkinsonism)"
        if nph_confirmed:
            recommendation = f"Confirmed iNPH (Evan's Index {evans_index}, Tap Test Gait Improvement {csf_tap_test_gait_speed_improvement_pct}%): Implantation of Programmable Ventriculoperitoneal (VP) Shunt indicated (initial setting 110 mm H2O with anti-siphon valve)"

        return {
            "evans_index": evans_index,
            "ventriculomegaly": ventriculomegaly,
            "hakim_triad_count": hakim_triad_count,
            "csf_tap_test_gait_speed_improvement_pct": csf_tap_test_gait_speed_improvement_pct,
            "positive_tap_test": positive_tap_test,
            "nph_confirmed": nph_confirmed,
            "shunt_candidacy": shunt_candidacy,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
nph_engine = NphEvansIndexTapTestEngine()
