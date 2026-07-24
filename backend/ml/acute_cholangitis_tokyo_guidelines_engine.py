"""
Acute Cholangitis Tokyo Guidelines 2018 (TG18) Severity Staging Engine
========================================================================
Evaluates TG18 diagnostic criteria (Charcot's triad: fever, jaundice, RUQ pain)
and TG18 severity criteria (Grade III Severe, Grade II Moderate, Grade I Mild)
to trigger urgent ERCP biliary decompression within 12-24 hours.
"""

from typing import Dict


class AcuteCholangitisTokyoGuidelinesEngine:
    """Evaluates TG18 diagnosis and severity staging for acute cholangitis."""

    def evaluate_tg18_cholangitis(
        self,
        fever_temp_celsius: float,
        wbc_count_k_uL: float,
        total_bilirubin_mg_dL: float,
        ruq_abdominal_pain: bool = True,
        biliary_dilation_on_us_ct: bool = True,
        organ_dysfunction_shock_or_renal: bool = False,
        age_years: float = 60.0,
    ) -> Dict[str, any]:
        systemic_inflammation = fever_temp_celsius > 38.0 or wbc_count_k_uL > 10.0 or wbc_count_k_uL < 4.0
        cholestasis = total_bilirubin_mg_dL >= 2.0
        biliary_imaging = biliary_dilation_on_us_ct

        tg18_diagnosis_definite = systemic_inflammation and cholestasis and biliary_imaging

        severity_grade = "GRADE_I_MILD"
        ercp_drainage_timing = "ELECTIVE_OR_INPATIENT_ERCP_WITHIN_24_TO_48_HOURS"

        if tg18_diagnosis_definite:
            if organ_dysfunction_shock_or_renal:
                severity_grade = "GRADE_III_SEVERE"
                ercp_drainage_timing = "EMERGENT_ERCP_BILIARY_DRAINAGE_IMMEDIATELY_WITHIN_12_HOURS"
            elif (
                wbc_count_k_uL > 12.0
                or wbc_count_k_uL < 4.0
                or fever_temp_celsius >= 39.0
                or age_years >= 75.0
                or total_bilirubin_mg_dL >= 5.0
            ):
                severity_grade = "GRADE_II_MODERATE"
                ercp_drainage_timing = "URGENT_ERCP_BILIARY_DRAINAGE_WITHIN_24_HOURS"

        recommendation = "TG18 Definite Criteria NOT met; evaluate alternative causes of cholestasis / fever"
        if tg18_diagnosis_definite:
            if severity_grade == "GRADE_III_SEVERE":
                recommendation = f"CRITICAL TOKYO GRADE III SEVERE CHOLANGITIS (Organ Dysfunction): Perform {ercp_drainage_timing}; initiate IV Cefepime + Metronidazole + vasopressor ICU support"
            elif severity_grade == "GRADE_II_MODERATE":
                recommendation = f"TOKYO GRADE II MODERATE CHOLANGITIS: Perform {ercp_drainage_timing}; initiate IV Piperacillin-Tazobactam"
            else:
                recommendation = f"TOKYO GRADE I MILD CHOLANGITIS: Perform {ercp_drainage_timing}; initiate IV Ampicillin-Sulbactam"

        return {
            "tg18_diagnosis_definite": tg18_diagnosis_definite,
            "severity_grade": severity_grade,
            "recommended_ercp_timing": ercp_drainage_timing,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
cholangitis_engine = AcuteCholangitisTokyoGuidelinesEngine()
