"""
Chronic Hepatitis B NUC Antiviral Stopping Rules Engine
========================================================
Evaluates clinical criteria for safe NUC (TDF/TAF/Entecavir) withdrawal in non-cirrhotic HBV:
HBsAg loss (< 0.05 IU/mL) or HBeAg seroconversion with >= 12-36 months consolidation.
STRICTLY CONTRAINDICATED in patients with liver cirrhosis (F4 / Child-Pugh A-C).
"""

from typing import Dict


class HbvTreatmentStoppingRulesEngine:
    """Evaluates NUC antiviral cessation criteria in chronic hepatitis B."""

    def evaluate_nuc_withdrawal_safety(
        self,
        liver_cirrhosis_present: bool = False,
        hbsag_loss_achieved: bool = False,  # HBsAg < 0.05 IU/mL
        hbeag_seroconversion_achieved: bool = True,
        consolidation_therapy_months: float = 24.0,  # >= 12-36 months required
        hbv_dna_undetectable_months: float = 24.0,
    ) -> Dict[str, any]:
        if liver_cirrhosis_present:
            return {
                "safe_to_stop_nuc": False,
                "reason": "LIVER_CIRRHOSIS_STRICT_CONTRAINDICATION",
                "clinical_recommendation": "DO NOT DISCONTINUE NUC ANTIVIRAL THERAPY! Liver cirrhosis (F4) is a strict contraindication to stopping NUCs due to severe risk of fatal hepatic flare and liver failure; lifelong antiviral suppression required",
                "status": "EVALUATION_COMPLETE",
            }

        safe_to_stop = False
        reason = "INSUFFICIENT_CONSOLIDATION_OR_SEROCLEARANCE"

        if hbsag_loss_achieved:
            safe_to_stop = True
            reason = "FUNCTIONAL_CURE_HBSAG_LOSS_ACHIEVED"
        elif hbeag_seroconversion_achieved and consolidation_therapy_months >= 12.0 and hbv_dna_undetectable_months >= 12.0:
            safe_to_stop = True
            reason = "HBEAG_SEROCONVERSION_WITH_SUFFICIENT_CONSOLIDATION"

        recommendation = "Continue NUC antiviral therapy; stopping criteria not yet met (HBsAg loss or >= 12 months consolidation post-HBeAg seroconversion required)"
        if safe_to_stop:
            recommendation = f"SAFE TO CEASE NUC ANTIVIRAL THERAPY ({reason}): Cease TDF/TAF/Entecavir with mandatory close monitoring of ALT and HBV DNA every 1-3 months for at least 12 months to detect off-treatment relapse"

        return {
            "safe_to_stop_nuc": safe_to_stop,
            "reason": reason,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_stopping_engine = HbvTreatmentStoppingRulesEngine()
