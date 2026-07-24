"""
Chronic Hepatitis B Co-Infection (HBV/HIV & HBV/HCV) Management Engine
========================================================================
Evaluates treatment strategies for HBV/HIV co-infection (mandates TDF/TAF + FTC/3TC backbone in ART)
and HBV/HCV co-infection (monitors HBV reactivation during HCV DAA therapy and mandates TDF/TAF prophylaxis).
"""

from typing import Dict


class HbvCoinfectionManagementEngine:
    """Evaluates management of HBV/HIV and HBV/HCV co-infected patients."""

    def evaluate_coinfection_strategy(
        self,
        hbsag_positive: bool = True,
        hiv_coinfected: bool = False,
        hcv_coinfected: bool = False,
        undergoing_hcv_daa_therapy: bool = False,
    ) -> Dict[str, any]:
        art_backbone_recommendation = "NONE"
        hbv_reactivation_warning = False

        if hiv_coinfected:
            art_backbone_recommendation = "TENOFVIR_TAF_OR_TDF_PLUS_EMTRICITABINE_FTC_OR_LAMIVUDINE_3TC_BACKBONE"

        if hcv_coinfected and undergoing_hcv_daa_therapy and hbsag_positive:
            hbv_reactivation_warning = True

        recommendation = "No co-infection management specific adjustments required"

        if hiv_coinfected and hcv_coinfected:
            recommendation = f"TRIPLE CO-INFECTION (HBV/HIV/HCV): Include {art_backbone_recommendation} in ART regimen. Initiate HCV DAAs with prophylactic TAF/TDF to prevent fatal HBV reactivation flare"
        elif hiv_coinfected:
            recommendation = f"HBV/HIV CO-INFECTION: ART regimen MUST contain two drugs active against both HIV and HBV -> {art_backbone_recommendation}. NEVER use Lamivudine monotherapy to avoid rapid HBV resistance"
        elif hcv_coinfected and undergoing_hcv_daa_therapy:
            recommendation = "HBV/HCV CO-INFECTION ON DAA THERAPY: HIGH RISK FOR HBV REACTIVATION FLARE! Initiate prophylactic Tenofovir (TAF 25 mg or TDF 300 mg daily) concurrently with HCV Direct-Acting Antivirals until 12 weeks post-DAA completion"

        return {
            "hiv_coinfected": hiv_coinfected,
            "hcv_coinfected": hcv_coinfected,
            "hbv_reactivation_warning": hbv_reactivation_warning,
            "art_backbone_recommendation": art_backbone_recommendation,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_coinfection_engine = HbvCoinfectionManagementEngine()
