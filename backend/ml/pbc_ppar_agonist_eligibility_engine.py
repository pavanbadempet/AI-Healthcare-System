"""
Primary Biliary Cholangitis (PBC) Seladelpar & Elafibranor PPAR Agonist Eligibility Engine
===========================================================================================
Evaluates 2024 FDA-approved second-line PPAR agonists (Seladelpar PPAR-delta, Elafibranor PPAR-alpha/delta)
for PBC patients with UDCA non-response (ALP >= 1.67x ULN) or UDCA intolerance.
"""

from typing import Dict


class PbcPparAgonistEligibilityEngine:
    """Evaluates second-line PPAR agonist (Seladelpar vs Elafibranor) eligibility for PBC."""

    def evaluate_pbc_ppar_eligibility(
        self,
        alkaline_phosphatase_u_L: float,
        alp_upper_limit_normal_u_L: float = 116.0,
        total_bilirubin_mg_dL: float = 1.0,
        udca_adequate_trial_12_months: bool = True,
        udca_intolerant: bool = False,
        pruritus_moderate_to_severe: bool = False,
    ) -> Dict[str, any]:
        alp_ratio = alkaline_phosphatase_u_L / alp_upper_limit_normal_u_L

        inadequate_response = alp_ratio >= 1.67 or total_bilirubin_mg_dL > 1.0
        eligible = (inadequate_response and udca_adequate_trial_12_months) or udca_intolerant

        decompensated_cirrhosis = total_bilirubin_mg_dL > 2.0  # Caution / contraindication for Obeticholic acid

        recommended_drug = "SELADELPAR_10MG_DAILY" if pruritus_moderate_to_severe else "ELAFIBRANOR_80MG_DAILY"

        recommendation = "PBC biochemical response adequate on UDCA (ALP < 1.67x ULN & normal Bilirubin); continue UDCA monotherapy"
        if eligible:
            if decompensated_cirrhosis:
                recommendation = "CAUTION: Elevated bilirubin > 2.0 mg/dL (Decompensated Cirrhosis risk). Obeticholic acid contraindicated; evaluate Seladelpar 10 mg daily under close liver monitoring or liver transplant evaluation"
            else:
                recommendation = f"ELIGIBLE FOR SECOND-LINE PPAR AGONIST (ALP {round(alp_ratio, 2)}x ULN): Initiate {recommended_drug} in combination with UDCA (or as monotherapy if UDCA intolerant). Monitor ALP, Bilirubin, and LFTs Q3M"

        return {
            "alp_to_uln_ratio": round(alp_ratio, 2),
            "inadequate_udca_response": inadequate_response,
            "eligible_for_ppar_agonist": eligible,
            "recommended_ppar_agent": recommended_drug if eligible else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
pbc_ppar_engine = PbcPparAgonistEligibilityEngine()
