"""
Acute Fatty Liver of Pregnancy (AFLP) Swansea Criteria Engine
==============================================================
Evaluates Swansea Criteria (>= 6 of 14 features: vomiting, abdominal pain, polydipsia,
hypoglycemia < 4 mmol/L, elevated AST/ALT > 42 U/L, ammonia > 47 umol/L, microvesicular steatosis)
to trigger immediate delivery and maternal ICU stabilization.
"""

from typing import Dict


class AflpSwanseaCriteriaEngine:
    """Evaluates Swansea Criteria for Acute Fatty Liver of Pregnancy (AFLP)."""

    def evaluate_swansea_criteria(
        self,
        vomiting_present: bool = False,
        abdominal_pain_present: bool = False,
        polydipsia_polyuria_present: bool = False,
        encephalopathy_present: bool = False,
        hypoglycemia_less_than_4_mmol_L: bool = False,
        elevated_ast_or_alt_over_42_U_L: bool = False,
        elevated_bilirubin_over_14_umol_L: bool = False,
        elevated_uric_acid_over_340_umol_L: bool = False,
        elevated_ammonia_over_47_umol_L: bool = False,
        leukocytosis_over_11_x10_9_L: bool = False,
        renal_impairment_creatinine_over_150_umol_L: bool = False,
        coagulopathy_inr_over_1_4: bool = False,
        microvesicular_steatosis_on_biopsy_or_us: bool = False,
    ) -> Dict[str, any]:
        criteria_list = [
            vomiting_present,
            abdominal_pain_present,
            polydipsia_polyuria_present,
            encephalopathy_present,
            hypoglycemia_less_than_4_mmol_L,
            elevated_ast_or_alt_over_42_U_L,
            elevated_bilirubin_over_14_umol_L,
            elevated_uric_acid_over_340_umol_L,
            elevated_ammonia_over_47_umol_L,
            leukocytosis_over_11_x10_9_L,
            renal_impairment_creatinine_over_150_umol_L,
            coagulopathy_inr_over_1_4,
            microvesicular_steatosis_on_biopsy_or_us,
        ]

        criteria_count = sum(1 for c in criteria_list if c)
        aflp_diagnosed = criteria_count >= 6

        recommendation = f"Swansea Criteria {criteria_count}/14: AFLP not confirmed; evaluate preeclampsia / HELLP syndrome"
        if aflp_diagnosed:
            recommendation = f"CRITICAL OBSTETRIC EMERGENCY (Swansea Criteria MET: {criteria_count}/14 features): Initiate immediate delivery regardless of gestational age; transfer to Obstetric ICU; correct hypoglycemia (IV Dextrose 10%) & coagulopathy (FFP / Cryoprecipitate)"

        return {
            "swansea_criteria_count": criteria_count,
            "aflp_diagnosed": aflp_diagnosed,
            "immediate_delivery_indicated": aflp_diagnosed,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
aflp_engine = AflpSwanseaCriteriaEngine()
