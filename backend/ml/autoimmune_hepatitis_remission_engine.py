"""
Autoimmune Hepatitis (AIH) Remission & Maintenance Discontinuation Engine
==========================================================================
Evaluates biochemical remission (normal ALT/AST and IgG sustained >= 24 months)
and histologic remission (Ishak HAI <= 3) to guide safe immunosuppression withdrawal.
"""

from typing import Dict, Optional


class AutoimmuneHepatitisRemissionEngine:
    """Evaluates AIH remission criteria and immunosuppression withdrawal safety."""

    def evaluate_remission_and_withdrawal(
        self,
        months_of_normal_alt_ast: float,  # >= 24 months required
        months_of_normal_serum_igg: float,  # >= 24 months required
        ishak_hepatitis_activity_index: Optional[int] = None,  # <= 3 = histologic remission
        cirrhosis_present: bool = False,
    ) -> Dict[str, any]:
        biochemical_remission = months_of_normal_alt_ast >= 24.0 and months_of_normal_serum_igg >= 24.0

        histologic_remission = ishak_hepatitis_activity_index is not None and ishak_hepatitis_activity_index <= 3

        safe_to_attempt_withdrawal = biochemical_remission and histologic_remission and not cirrhosis_present

        recommendation = "Continue Azathioprine / Low-dose Prednisolone maintenance therapy; biochemical or histologic remission criteria not fulfilled (requires 24 months normal ALT/IgG + biopsy Ishak score <= 3)"
        if safe_to_attempt_withdrawal:
            recommendation = "COMPLETE BIOCHEMICAL & HISTOLOGIC REMISSION ACHIEVED: Safe to attempt slow immunosuppression withdrawal (taper corticosteroid completely over 3-6 months, then gradually withdraw Azathioprine). Monitor LFTs monthly during withdrawal"
        elif biochemical_remission and cirrhosis_present:
            recommendation = "BIOCHEMICAL REMISSION IN CIRRHOSIS: Continue indefinite low-dose monotherapy (Azathioprine 1-2 mg/kg/day) due to high relapse risk (50-80%) and risk of hepatic decompensation"

        return {
            "biochemical_remission": biochemical_remission,
            "histologic_remission": histologic_remission,
            "safe_to_attempt_withdrawal": safe_to_attempt_withdrawal,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
aih_remission_engine = AutoimmuneHepatitisRemissionEngine()
