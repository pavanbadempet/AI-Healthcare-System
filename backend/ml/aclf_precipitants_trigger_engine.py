"""
Acute-on-Chronic Liver Failure (ACLF) Precipitants & Trigger Identification Engine
===================================================================================
Identifies major acute triggers causing ACLF (bacterial infection/SBP, acute alcoholic hepatitis, HBV flare, variceal bleeding)
and generates targeted antimicrobial (Ceftriaxone + Albumin 1.5g/kg) and immunosuppressive (Prednisolone) resuscitation protocols.
"""

from typing import Dict, List, Optional


class AclfPrecipitantsEngine:
    """Evaluates acute triggers causing ACLF and generates targeted resuscitation plans."""

    def evaluate_aclf_triggers(
        self,
        cirrhosis_confirmed: bool,
        ascites_polymorphonuclear_count_per_uL: float,  # PMN >= 250 = SBP
        fever_or_leukocytosis: bool,
        recent_heavy_alcohol_use: bool,
        maddrey_discriminant_function: Optional[float] = None,  # Maddrey DF >= 32 = Severe Alcoholic Hepatitis
        hbv_dna_iu_mL: float = 0.0,
        active_variceal_bleed: bool = False,
    ) -> Dict[str, any]:
        triggers: List[str] = []
        is_sbp = ascites_polymorphonuclear_count_per_uL >= 250.0
        if is_sbp:
            triggers.append("SPONTANEOUS_BACTERIAL_PERITONITIS")

        if fever_or_leukocytosis and not is_sbp:
            triggers.append("SYSTEMIC_BACTERIAL_INFECTION")

        is_severe_alcoholic_hepatitis = False
        if recent_heavy_alcohol_use and maddrey_discriminant_function and maddrey_discriminant_function >= 32.0:
            is_severe_alcoholic_hepatitis = True
            triggers.append("SEVERE_ACUTE_ALCOHOLIC_HEPATITIS")

        if hbv_dna_iu_mL >= 2000.0:
            triggers.append("HEPATITIS_B_REACTIVATION_FLARE")

        if active_variceal_bleed:
            triggers.append("ACUTE_GUT_VARICEAL_HEMORRHAGE")

        recommendation = "STABLE: Monitor closely for secondary infections, acute kidney injury (HRS-AKI), and organ failure progression."
        if "SPONTANEOUS_BACTERIAL_PERITONITIS" in triggers:
            recommendation = "ACLF TRIGGER IDENTIFIED (SBP - Ascitic PMN >= 250/uL): Initiate IV Ceftriaxone 2g daily + IV Albumin 1.5 g/kg on Day 1 and 1.0 g/kg on Day 3 to prevent hepatorenal syndrome and septic shock."
        elif "SEVERE_ACUTE_ALCOHOLIC_HEPATITIS" in triggers:
            recommendation = f"ACLF TRIGGER IDENTIFIED (Severe Alcoholic Hepatitis - Maddrey DF {maddrey_discriminant_function:.1f} >= 32): Initiate oral Prednisolone 40 mg daily for 28 days (if active infection excluded) and monitor Lille score on Day 7."
        elif "HEPATITIS_B_REACTIVATION_FLARE" in triggers:
            recommendation = f"ACLF TRIGGER IDENTIFIED (HBV Reactivation Flare - HBV DNA {hbv_dna_iu_mL} IU/mL): Immediately initiate high-potency oral antiviral therapy (Tenofovir Alafenamide 25 mg or Entecavir 1 mg daily)."

        return {
            "cirrhosis_confirmed": cirrhosis_confirmed,
            "ascitic_pmn_count": ascites_polymorphonuclear_count_per_uL,
            "identified_triggers": triggers,
            "sbp_confirmed": is_sbp,
            "severe_alcoholic_hepatitis": is_severe_alcoholic_hepatitis,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
aclf_precipitants_engine = AclfPrecipitantsEngine()
