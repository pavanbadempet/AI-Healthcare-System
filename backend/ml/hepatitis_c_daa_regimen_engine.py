"""
Chronic Hepatitis C Direct-Acting Antiviral (DAA) Regimen Engine
================================================================
Evaluates HCV Genotype (1-6), Child-Pugh Score (A vs B/C), and DAA treatment history
to select pangenotypic DAA regimens (Sofosbuvir/Velpatasvir 12w vs Glecaprevir/Pibrentasvir 8w).
"""

from typing import Dict


class HepatitisCDaaRegimenEngine:
    """Selects pangenotypic DAA regimens for Hepatitis C treatment."""

    def select_daa_regimen(
        self,
        hcv_genotype: str,  # 1A, 1B, 2, 3, 4, 5, 6
        compensated_cirrhosis: bool = False,
        decompensated_cirrhosis_child_pugh_b_c: bool = False,
        prior_daa_treatment_failure: bool = False,
    ) -> Dict[str, any]:
        regimen = "GLECAPREVIR_PIBRENTASVIR_8_WEEKS"
        duration_weeks = 8

        if decompensated_cirrhosis_child_pugh_b_c:
            regimen = "SOFOSBUVIR_VELPATASVIR_12_WEEKS_PLUS_RIBAVIRIN"
            duration_weeks = 12
        elif prior_daa_treatment_failure:
            regimen = "SOFOSBUVIR_VELPATASVIR_VOXILAPREVIR_12_WEEKS"
            duration_weeks = 12
        elif compensated_cirrhosis:
            if hcv_genotype == "3":
                regimen = "SOFOSBUVIR_VELPATASVIR_12_WEEKS"
                duration_weeks = 12
            else:
                regimen = "GLECAPREVIR_PIBRENTASVIR_8_WEEKS"
                duration_weeks = 8

        recommendation = f"Recommended DAA Regimen: {regimen} (Duration {duration_weeks} weeks). Verify SVR12 (HCV RNA undetected 12 weeks post-therapy)"
        if decompensated_cirrhosis_child_pugh_b_c:
            recommendation += " (CONTRAINDICATION: Protease inhibitors Glecaprevir and Voxilaprevir are strictly contraindicated in Child-Pugh B/C)"

        return {
            "hcv_genotype": hcv_genotype,
            "compensated_cirrhosis": compensated_cirrhosis,
            "decompensated_cirrhosis": decompensated_cirrhosis_child_pugh_b_c,
            "recommended_regimen": regimen,
            "duration_weeks": duration_weeks,
            "clinical_recommendation": recommendation,
            "status": "SELECTION_COMPLETE",
        }


# Singleton engine instance
hcv_engine = HepatitisCDaaRegimenEngine()
