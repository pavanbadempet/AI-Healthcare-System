"""
Acute Upper GI Bleed Rockall Risk Score Engine
===============================================
Calculates pre- and post-endoscopy Rockall score (0 to 11 points)
for rebleeding and mortality prediction in non-variceal upper GI bleeding.
"""

from typing import Dict


class RockallGiBleedEngine:
    """Calculates Rockall score for upper gastrointestinal hemorrhage risk stratification."""

    def calculate_rockall_score(
        self,
        age_years: int,
        shock_state: str,              # "NO_SHOCK", "TACHYCARDIA", "HYPOTENSION"
        comorbidities: str,            # "NONE", "MAJOR", "RENAL_LIVER_MALIGNANCY"
        endoscopic_diagnosis: str,     # "NO_LESION_MALORY_WEISS", "PEPTIC_ULCER", "GI_MALIGNANCY"
        stigmata_of_hemorrhage: str,   # "NONE", "BLOOD_IN_STOMACH_ADHERENT_CLOT", "ACTIVE_BLEEDING_SPURTING"
    ) -> Dict[str, any]:
        score = 0

        # Age
        if age_years >= 80:
            score += 2
        elif age_years >= 60:
            score += 1

        # Shock
        if shock_state == "HYPOTENSION":
            score += 2
        elif shock_state == "TACHYCARDIA":
            score += 1

        # Comorbidities
        if comorbidities == "RENAL_LIVER_MALIGNANCY":
            score += 3
        elif comorbidities == "MAJOR":
            score += 2

        # Endoscopic diagnosis
        if endoscopic_diagnosis == "GI_MALIGNANCY":
            score += 2
        elif endoscopic_diagnosis == "PEPTIC_ULCER":
            score += 1

        # Stigmata
        if stigmata_of_hemorrhage == "ACTIVE_BLEEDING_SPURTING":
            score += 2
        elif stigmata_of_hemorrhage == "BLOOD_IN_STOMACH_ADHERENT_CLOT":
            score += 2

        risk_tier = "LOW_RISK"
        mortality_pct = 0.5

        if score >= 5:
            risk_tier = "HIGH_RISK"
            mortality_pct = 25.0
        elif score >= 3:
            risk_tier = "INTERMEDIATE_RISK"
            mortality_pct = 5.6

        recommendation = "Low Rockall score (<3): Suitable for early outpatient discharge & oral PPI"
        if risk_tier == "HIGH_RISK":
            recommendation = "High Rockall score (>=5): Stat ICU admission, continuous IV Pantoprazole infusion (8mg/hr), & urgent dual endoscopic hemostasis (clip + epinephrine)"

        return {
            "rockall_total_score": score,
            "risk_tier": risk_tier,
            "estimated_mortality_percent": mortality_pct,
            "icu_admission_and_iv_ppi_indicated": risk_tier == "HIGH_RISK",
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
rockall_gi_engine = RockallGiBleedEngine()
