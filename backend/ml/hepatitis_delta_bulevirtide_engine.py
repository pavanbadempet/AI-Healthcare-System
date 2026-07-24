"""
Chronic Hepatitis Delta (HDV) Bulevirtide Entry Inhibitor Engine
==================================================================
Evaluates HDV RNA viral load, HBsAg positivity, ALT levels, and fibrosis stage (F0-F4)
to stage HDV superinfection and direct Bulevirtide 2mg daily SC (NTCP entry inhibitor) therapy.
"""

from typing import Dict


class HepatitisDeltaBulevirtideEngine:
    """Evaluates Chronic Hepatitis Delta infection and Bulevirtide therapy indication."""

    def evaluate_hdv_bulevirtide_indication(
        self,
        hbsag_positive: bool,
        hdv_rna_detected: bool,
        hdv_rna_iu_mL: float,
        alt_u_L: float,
        fibrosis_stage_f0_f4: int = 2,  # F0 to F4
        decompensated_cirrhosis: bool = False,
    ) -> Dict[str, any]:
        bulevirtide_indicated = (
            hbsag_positive
            and hdv_rna_detected
            and hdv_rna_iu_mL > 100.0
            and not decompensated_cirrhosis
            and fibrosis_stage_f0_f4 >= 2
        )

        regimen = "OBSERVATION_OR_PEG_IFN_ALPHA"
        if bulevirtide_indicated:
            regimen = "BULEVIR TIDE_2MG_DAILY_SUBCUTANEOUS_INJECTION"

        recommendation = "Bulevirtide not indicated; monitor HDV RNA and ALT every 6 months"
        if bulevirtide_indicated:
            recommendation = f"Active Chronic HDV Superinfection (HDV RNA {hdv_rna_iu_mL} IU/mL, Fibrosis F{fibrosis_stage_f0_f4}): Initiate Bulevirtide 2 mg daily SC (NTCP receptor inhibitor) for at least 48 weeks + co-administer TAF/TDF for HBV DNA suppression"
        elif decompensated_cirrhosis:
            recommendation = "Decompensated HDV Cirrhosis: Bulevirtide safety in Child-Pugh B/C not established; refer for Liver Transplantation evaluation"

        return {
            "hbsag_positive": hbsag_positive,
            "hdv_rna_detected": hdv_rna_detected,
            "hdv_rna_iu_mL": hdv_rna_iu_mL,
            "fibrosis_stage": fibrosis_stage_f0_f4,
            "bulevirtide_indicated": bulevirtide_indicated,
            "recommended_regimen": regimen,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hdv_engine = HepatitisDeltaBulevirtideEngine()
