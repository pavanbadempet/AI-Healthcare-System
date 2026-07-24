"""
Chronic Hepatitis B Phase 5 HBsAg Loss & Functional Cure Engine
================================================================
Evaluates HBsAg seroclearance (< 0.05 IU/mL), anti-HBs antibody seroconversion (>= 10 mIU/mL),
and undetectable HBV DNA (< 10 IU/mL) to confirm Phase 5 Functional Cure and evaluate safe NUC withdrawal.
"""

from typing import Dict


class HepatitisBFunctionalCureEngine:
    """Evaluates Phase 5 HBsAg Loss (Functional Cure) and antiviral discontinuation eligibility."""

    def evaluate_functional_cure(
        self,
        hbsag_quantitative_iu_mL: float,  # < 0.05 IU/mL considered seroclearance
        anti_hbs_mIU_mL: float,  # >= 10 mIU/mL seroconversion
        hbv_dna_iu_mL: float,  # < 10 IU/mL undetected
        cirrhosis_present: bool = False,
        months_of_sustained_hbsag_loss: float = 6.0,
    ) -> Dict[str, any]:
        hbsag_loss = hbsag_quantitative_iu_mL < 0.05
        anti_hbs_seroconversion = anti_hbs_mIU_mL >= 10.0
        hbv_dna_undetectable = hbv_dna_iu_mL < 10.0

        functional_cure_achieved = hbsag_loss and hbv_dna_undetectable and (months_of_sustained_hbsag_loss >= 6.0)

        safe_to_discontinue_antiviral = functional_cure_achieved and not cirrhosis_present

        recommendation = "Functional Cure NOT achieved; continue indefinite NUC antiviral therapy (TAF / Entecavir)"
        if functional_cure_achieved:
            if safe_to_discontinue_antiviral:
                recommendation = f"PHASE 5 FUNCTIONAL CURE ACHIEVED (HBsAg < 0.05 IU/mL, Anti-HBs {anti_hbs_mIU_mL} mIU/mL): Safe to discontinue NUC antiviral therapy; monitor HBsAg & HBV DNA Q3M to detect rare relapse"
            else:
                recommendation = "PHASE 5 FUNCTIONAL CURE ACHIEVED (HBsAg Loss): Continue NUC antiviral therapy due to underlying Cirrhosis to prevent decompensation flare"

        return {
            "hbsag_quantitative_iu_mL": hbsag_quantitative_iu_mL,
            "hbsag_loss": hbsag_loss,
            "anti_hbs_seroconversion": anti_hbs_seroconversion,
            "functional_cure_achieved": functional_cure_achieved,
            "safe_to_discontinue_antiviral": safe_to_discontinue_antiviral,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_cure_engine = HepatitisBFunctionalCureEngine()
