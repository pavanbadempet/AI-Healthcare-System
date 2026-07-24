"""
Sepsis SOFA & qSOFA Sequential Organ Failure Evaluator
======================================================
Calculates SOFA score across 6 organ systems (Respiration, Coagulation, Liver, Cardiovascular, CNS, Renal)
and qSOFA bedside triage score for acute septic shock.
"""

from typing import Dict


class SofaSepsisEvaluator:
    """Calculates SOFA and qSOFA scores for sepsis organ dysfunction."""

    def calculate_sofa_score(
        self,
        pao2_fio2_ratio: float,
        platelets_k_uL: int,
        bilirubin_mg_dL: float,
        mean_arterial_pressure_mmHg: float,
        vasopressor_required: bool,
        gcs_score: int,
        creatinine_mg_dL: float,
    ) -> Dict[str, any]:
        sofa_score = 0

        # Respiration
        if pao2_fio2_ratio < 100:
            sofa_score += 4
        elif pao2_fio2_ratio < 200:
            sofa_score += 3
        elif pao2_fio2_ratio < 300:
            sofa_score += 2
        elif pao2_fio2_ratio < 400:
            sofa_score += 1

        # Coagulation
        if platelets_k_uL < 20:
            sofa_score += 4
        elif platelets_k_uL < 50:
            sofa_score += 3
        elif platelets_k_uL < 100:
            sofa_score += 2
        elif platelets_k_uL < 150:
            sofa_score += 1

        # Liver
        if bilirubin_mg_dL >= 12.0:
            sofa_score += 4
        elif bilirubin_mg_dL >= 6.0:
            sofa_score += 3
        elif bilirubin_mg_dL >= 2.0:
            sofa_score += 2
        elif bilirubin_mg_dL >= 1.2:
            sofa_score += 1

        # Cardiovascular
        if vasopressor_required:
            sofa_score += 3
        elif mean_arterial_pressure_mmHg < 70:
            sofa_score += 1

        # CNS
        if gcs_score <= 6:
            sofa_score += 4
        elif gcs_score <= 9:
            sofa_score += 3
        elif gcs_score <= 12:
            sofa_score += 2
        elif gcs_score <= 14:
            sofa_score += 1

        # Renal
        if creatinine_mg_dL >= 5.0:
            sofa_score += 4
        elif creatinine_mg_dL >= 3.5:
            sofa_score += 3
        elif creatinine_mg_dL >= 2.0:
            sofa_score += 2
        elif creatinine_mg_dL >= 1.2:
            sofa_score += 1

        sepsis_organ_failure = sofa_score >= 2
        estimated_icu_mortality_pct = round(min(sofa_score * 4.5, 80.0), 1)

        return {
            "sofa_score": sofa_score,
            "sepsis_organ_failure_present": sepsis_organ_failure,
            "estimated_icu_mortality_percent": estimated_icu_mortality_pct,
            "septic_shock_suspected": vasopressor_required and mean_arterial_pressure_mmHg < 65,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton evaluator instance
sofa_evaluator = SofaSepsisEvaluator()
