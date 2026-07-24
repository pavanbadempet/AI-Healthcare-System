"""
Pulmonary Arterial Hypertension (PAH) Right Heart Catheterization (RHC) Engine
================================================================================
Evaluates 2022 ESC/ERS RHC criteria: mPAP > 20 mmHg, PCWP <= 15 mmHg, and PVR > 2.0 Wood units
to differentiate Pre-capillary PAH (Group 1) from Post-capillary PH (Group 2 LHD).
"""

from typing import Dict


class PahRhcHemodynamicEngine:
    """Evaluates RHC hemodynamics for Pre-capillary vs Post-capillary Pulmonary Hypertension."""

    def evaluate_rhc_hemodynamics(
        self,
        mean_pap_mmHg: float,  # > 20 mmHg = PH definition
        pcwp_mmHg: float,  # <= 15 mmHg = Pre-capillary, > 15 mmHg = Post-capillary
        pvr_wood_units: float,  # > 2.0 Wood units = PAH
        cardiac_index_L_min_m2: float = 2.8,
    ) -> Dict[str, any]:
        ph_present = mean_pap_mmHg > 20.0
        pre_capillary = pcwp_mmHg <= 15.0 and pvr_wood_units > 2.0
        post_capillary = pcwp_mmHg > 15.0

        ph_classification = "NO_PULMONARY_HYPERTENSION"
        if ph_present:
            if pre_capillary:
                ph_classification = "GROUP_1_PRE_CAPILLARY_PAH"
            elif post_capillary:
                if pvr_wood_units > 2.0:
                    ph_classification = "COMBINED_POST_AND_PRE_CAPILLARY_PH_CMPC_PH"
                else:
                    ph_classification = "ISOLATED_POST_CAPILLARY_PH_IAPC_PH"

        recommendation = "Hemodynamics within normal limits (mPAP <= 20 mmHg)"
        if ph_classification == "GROUP_1_PRE_CAPILLARY_PAH":
            recommendation = f"PRE-CAPILLARY PAH DIAGNOSED (mPAP {mean_pap_mmHg} mmHg, PCWP {pcwp_mmHg} mmHg <= 15, PVR {pvr_wood_units} Wood units > 2.0): Initiate upfront dual oral combination PAH therapy (ERA + PDE5i)"
        elif ph_classification == "COMBINED_POST_AND_PRE_CAPILLARY_PH_CMPC_PH":
            recommendation = "COMBINED POST- AND PRE-CAPILLARY PH (Group 2 LHD + Vascular Remodeling): Optimize left heart failure therapy (GDMT); perform acute vasoreactivity testing"

        return {
            "mean_pap_mmHg": mean_pap_mmHg,
            "pcwp_mmHg": pcwp_mmHg,
            "pvr_wood_units": pvr_wood_units,
            "ph_classification": ph_classification,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
rhc_engine = PahRhcHemodynamicEngine()
