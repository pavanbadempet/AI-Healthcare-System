"""
Child-Pugh Cirrhosis Liver Mortality Calculator
================================================
Calculates Child-Pugh Class (Class A, Class B, Class C) and estimated 1-year and 2-year survival.
"""

from typing import Dict


class ChildPughCalculator:
    """Calculates Child-Pugh score for hepatic cirrhosis mortality risk."""

    def calculate_child_pugh_score(
        self,
        bilirubin_mg_dL: float,
        albumin_g_dL: float,
        inr: float,
        ascites_severity: str,  # 'NONE', 'MILD_SLIGHT', 'MODERATE_SEVERE'
        encephalopathy_grade: int,  # 0, 1, 2, 3, 4
    ) -> Dict[str, any]:
        score = 0

        # Bilirubin
        if bilirubin_mg_dL > 3.0:
            score += 3
        elif bilirubin_mg_dL >= 2.0:
            score += 2
        else:
            score += 1

        # Albumin
        if albumin_g_dL < 2.8:
            score += 3
        elif albumin_g_dL <= 3.5:
            score += 2
        else:
            score += 1

        # INR
        if inr > 2.3:
            score += 3
        elif inr >= 1.7:
            score += 2
        else:
            score += 1

        # Ascites
        asc_upper = ascites_severity.upper()
        if "MODERATE" in asc_upper or "SEVERE" in asc_upper:
            score += 3
        elif "MILD" in asc_upper or "SLIGHT" in asc_upper:
            score += 2
        else:
            score += 1

        # Encephalopathy
        if encephalopathy_grade >= 3:
            score += 3
        elif encephalopathy_grade >= 1:
            score += 2
        else:
            score += 1

        child_class = "CLASS_A"
        one_year_survival = 100.0
        two_year_survival = 85.0

        if score >= 10:
            child_class = "CLASS_C"
            one_year_survival = 45.0
            two_year_survival = 35.0
        elif score >= 7:
            child_class = "CLASS_B"
            one_year_survival = 80.0
            two_year_survival = 60.0

        return {
            "child_pugh_score": score,
            "child_pugh_class": child_class,
            "one_year_survival_percent": one_year_survival,
            "two_year_survival_percent": two_year_survival,
            "liver_transplantation_eval_indicated": child_class in ["CLASS_B", "CLASS_C"],
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
child_pugh_calculator = ChildPughCalculator()
