"""
Chronic Hepatitis Delta (HDV) High-Dose Bulevirtide & Triple Combination Engine
================================================================================
Evaluates high viral load HDV, compensated cirrhosis, and prior treatment failure
to select Bulevirtide 2 mg vs 10 mg SC daily + PegIFN-alpha + TAF/TDF triple combination therapy.
"""

from typing import Dict


class HdvTripleCombinationBulevirtideEngine:
    """Evaluates high-dose Bulevirtide and triple combination regimens for Chronic HDV."""

    def evaluate_hdv_triple_therapy(
        self,
        hdv_rna_iu_mL: float,
        compensated_cirrhosis_present: bool = False,
        prior_bulevirtide_2mg_partial_response: bool = False,
        hbv_dna_iu_mL: float = 50.0,
    ) -> Dict[str, any]:
        bulevirtide_dose_mg = 2.0
        if prior_bulevirtide_2mg_partial_response or hdv_rna_iu_mL >= 1000000.0:
            bulevirtide_dose_mg = 10.0

        triple_combination_indicated = compensated_cirrhosis_present or hdv_rna_iu_mL >= 500000.0

        regimen = f"Bulevirtide {int(bulevirtide_dose_mg)} mg SC daily + Tenofovir (TAF/TDF)"
        if triple_combination_indicated:
            regimen = f"TRIPLE THERAPY: Bulevirtide {int(bulevirtide_dose_mg)} mg SC daily + PegIFN-alpha 180 mcg SC weekly + TAF 25 mg daily"

        recommendation = f"RECOMMENDED HDV REGIMEN: {regimen}. Monitor serum bile acids monthly (Bulevirtide causes asymptomatic elevation of total bile salts due to NTCP inhibition)"

        return {
            "hdv_rna_iu_mL": hdv_rna_iu_mL,
            "bulevirtide_daily_dose_mg": bulevirtide_dose_mg,
            "triple_combination_indicated": triple_combination_indicated,
            "recommended_regimen": regimen,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hdv_triple_engine = HdvTripleCombinationBulevirtideEngine()
