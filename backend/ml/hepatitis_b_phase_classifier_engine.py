"""
Chronic Hepatitis B Phase Classification & Antiviral Indication Engine
========================================================================
Classifies Chronic HBV into 4 phases (HBeAg-Pos Infection, HBeAg-Pos Hepatitis,
HBeAg-Neg Infection, HBeAg-Neg Hepatitis) based on HBeAg, HBV DNA (IU/mL), ALT (U/L),
and Fibrosis stage (F0-F4) to direct Tenofovir Alafenamide (TAF) / Entecavir therapy.
"""

from typing import Dict, Optional


class HepatitisBPhaseClassifierEngine:
    """Classifies Chronic Hepatitis B phases and evaluates antiviral indication."""

    def classify_hbv_phase(
        self,
        hbeag_positive: bool,
        hbv_dna_iu_mL: float,
        alt_u_L: float,
        upper_limit_normal_alt: float = 35.0,  # 35 U/L males, 25 U/L females
        fibrosis_stage_f0_f4: Optional[int] = None,  # 0, 1, 2, 3, 4
        cirrhosis_present: bool = False,
    ) -> Dict[str, any]:
        alt_elevated = alt_u_L > upper_limit_normal_alt
        alt_2x_uln = alt_u_L >= (2.0 * upper_limit_normal_alt)

        phase = "HBEAG_NEGATIVE_CHRONIC_INFECTION_INACTIVE_CARRIER"
        antiviral_indicated = False

        if hbeag_positive:
            if hbv_dna_iu_mL > 10_000_000 and not alt_elevated:
                phase = "HBEAG_POSITIVE_CHRONIC_HBV_INFECTION_IMMUNE_TOLERANT"
            else:
                phase = "HBEAG_POSITIVE_CHRONIC_HBV_HEPATITIS_IMMUNE_ACTIVE"
                if hbv_dna_iu_mL > 20_000 or alt_2x_uln or (fibrosis_stage_f0_f4 is not None and fibrosis_stage_f0_f4 >= 2):
                    antiviral_indicated = True
        else:
            if hbv_dna_iu_mL >= 2000 and alt_elevated:
                phase = "HBEAG_NEGATIVE_CHRONIC_HBV_HEPATITIS"
                antiviral_indicated = True
            elif hbv_dna_iu_mL < 2000 and not alt_elevated:
                phase = "HBEAG_NEGATIVE_CHRONIC_HBV_INFECTION_INACTIVE_CARRIER"

        if cirrhosis_present:
            antiviral_indicated = True

        first_line_agent = "MONITORING_HBV_DNA_AND_ALT_EVERY_6_MONTHS"
        if antiviral_indicated:
            first_line_agent = "TENOFOVIR_ALAFENAMIDE_TAF_25MG_OR_ENTECAVIR_0_5MG"

        recommendation = f"HBV Phase: {phase}. Antiviral Therapy: {first_line_agent}"
        if cirrhosis_present:
            recommendation += " (Indefinite Antiviral Suppression + HCC Surveillance Ultrasonography every 6 months)"

        return {
            "hbv_phase": phase,
            "antiviral_indicated": antiviral_indicated,
            "recommended_antiviral": first_line_agent,
            "cirrhosis_present": cirrhosis_present,
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton engine instance
hbv_engine = HepatitisBPhaseClassifierEngine()
