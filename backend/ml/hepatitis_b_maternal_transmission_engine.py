"""
Chronic Hepatitis B Maternal-Fetal Transmission Prevention Engine
===================================================================
Evaluates pregnant HBsAg+ women at 24-28 weeks gestation: serum HBV DNA > 200,000 IU/mL (> 5.3 log10)
or HBeAg positivity to initiate TDF (300 mg daily) / TAF (25 mg daily) prophylaxis + infant HBIG/vaccine.
"""

from typing import Dict


class HepatitisBMaternalTransmissionEngine:
    """Evaluates maternal HBV PMTCT prophylaxis indications and infant birth dose strategy."""

    def evaluate_maternal_hbv_pmtct(
        self,
        gestational_age_weeks: float,  # 24 to 28 weeks screening window
        hbv_dna_iu_mL: float,  # > 200,000 IU/mL indicates antiviral prophylaxis
        hbeag_positive: bool = True,
        hbsag_positive: bool = True,
        maternal_egfr_mL_min: float = 90.0,
    ) -> Dict[str, any]:
        pmtct_antiviral_indicated = (
            hbsag_positive
            and gestational_age_weeks >= 24.0
            and (hbv_dna_iu_mL >= 200000.0 or hbeag_positive)
        )

        recommended_antiviral = "TDF_300MG_DAILY"
        if maternal_egfr_mL_min < 60.0:
            recommended_antiviral = "TAF_25MG_DAILY"

        recommendation = "Antiviral prophylaxis NOT indicated (HBV DNA < 200,000 IU/mL and HBeAg negative); administer Hepatitis B Vaccine + HBIG to newborn within 12 hours of birth"
        if pmtct_antiviral_indicated:
            recommendation = f"MATERNAL HBV PROPHYLAXIS INDICATED (HBV DNA {hbv_dna_iu_mL} IU/mL >= 200,000 IU/mL): Initiate {recommended_antiviral} at 28 weeks gestation; continue through 2 to 12 weeks postpartum. Administer Infant HBIG (0.5 mL IM) + HBV Vaccine within 12 hours of delivery"

        return {
            "hbsag_positive": hbsag_positive,
            "gestational_age_weeks": gestational_age_weeks,
            "hbv_dna_iu_mL": hbv_dna_iu_mL,
            "pmtct_antiviral_indicated": pmtct_antiviral_indicated,
            "recommended_antiviral": recommended_antiviral if pmtct_antiviral_indicated else "NONE",
            "infant_birth_protocol": "HBIG_100IU_IM_PLUS_HBV_VACCINE_WITHIN_12H",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_maternal_engine = HepatitisBMaternalTransmissionEngine()
