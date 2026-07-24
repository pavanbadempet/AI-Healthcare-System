"""
Chronic Hepatitis B Perinatal Transmission Prophylaxis Engine
============================================================
Evaluates pregnant HBsAg+ mothers at 28 weeks gestation with high HBV DNA (>= 200,000 IU/mL)
or HBeAg positivity to guide maternal Tenofovir (TDF) and infant HBIG + HBV vaccine active-passive immunoprophylaxis.
"""

from typing import Dict


class HbvPerinatalProphylaxisEngine:
    """Evaluates maternal and infant prophylaxis to prevent mother-to-child HBV transmission."""

    def evaluate_perinatal_prophylaxis(
        self,
        maternal_hbsag_positive: bool = True,
        gestational_age_weeks: int = 28,
        maternal_hbv_dna_iu_mL: float = 500000.0,  # >= 200,000 IU/mL (5.3 log10) threshold
        maternal_hbeag_positive: bool = True,
    ) -> Dict[str, any]:
        high_viral_load = maternal_hbv_dna_iu_mL >= 200000.0 or maternal_hbeag_positive

        maternal_tdf_indicated = maternal_hbsag_positive and gestational_age_weeks >= 28 and high_viral_load

        maternal_recommendation = "Maternal TDF antiviral prophylaxis NOT indicated (HBV DNA < 200,000 IU/mL and HBeAg negative)"
        if maternal_tdf_indicated:
            maternal_recommendation = f"INITIATE MATERNAL TDF PROPHYLAXIS (Gestation {gestational_age_weeks} wks, HBV DNA {maternal_hbv_dna_iu_mL} IU/mL): Start Tenofovir Disoproxil Fumarate (TDF) 300 mg orally daily to suppress maternal viral load prior to delivery"

        infant_immunoprophylaxis = "INFANT HBIG (100-200 IU IM) + FIRST DOSE HBV VACCINE IM WITHIN 12 HOURS OF BIRTH AT SEPARATE INJECTION SITES"

        return {
            "maternal_tdf_indicated": maternal_tdf_indicated,
            "maternal_recommendation": maternal_recommendation,
            "infant_immunoprophylaxis": infant_immunoprophylaxis,
            "clinical_recommendation": f"{maternal_recommendation}. ALL INFANTS MUST RECEIVE: {infant_immunoprophylaxis}",
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_perinatal_engine = HbvPerinatalProphylaxisEngine()
