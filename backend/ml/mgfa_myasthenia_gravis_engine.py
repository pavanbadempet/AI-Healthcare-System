"""
Myasthenia Gravis Foundation of America (MGFA) Clinical Classification Engine
=============================================================================
Stages Myasthenia Gravis severity from Class I (ocular) to Class V (myasthenic crisis / intubation).
"""

from typing import Dict


class MgfaMyastheniaGravisEngine:
    """Classifies Myasthenia Gravis clinical severity according to MGFA standards."""

    def classify_mgfa_grade(
        self,
        ocular_muscle_weakness_only: bool = False,
        generalized_mild_weakness: bool = False,
        generalized_moderate_weakness: bool = False,
        generalized_severe_weakness: bool = False,
        oropharyngeal_bulbar_predominant: bool = False,
        intubation_respiratory_failure: bool = False,
    ) -> Dict[str, any]:
        mgfa_class = "CLASS_I_OCULAR"

        if intubation_respiratory_failure:
            mgfa_class = "CLASS_V_MYASTHENIC_CRISIS"
        elif generalized_severe_weakness:
            mgfa_class = "CLASS_IVb_SEVERE_BULBAR" if oropharyngeal_bulbar_predominant else "CLASS_IVa_SEVERE_LIMB"
        elif generalized_moderate_weakness:
            mgfa_class = "CLASS_IIIb_MODERATE_BULBAR" if oropharyngeal_bulbar_predominant else "CLASS_IIIa_MODERATE_LIMB"
        elif generalized_mild_weakness:
            mgfa_class = "CLASS_IIb_MILD_BULBAR" if oropharyngeal_bulbar_predominant else "CLASS_IIa_MILD_LIMB"

        recommendation = "Pyridostigmine 60mg PO TID & thymectomy evaluation if AChR antibody positive"
        if mgfa_class == "CLASS_V_MYASTHENIC_CRISIS":
            recommendation = "Stat ICU Admission, Mechanical Ventilation, IVIG (2g/kg over 5d) OR Therapeutic Plasma Exchange (TPE/PLEX 5 sessions)"

        return {
            "mgfa_class": mgfa_class,
            "myasthenic_crisis_present": mgfa_class == "CLASS_V_MYASTHENIC_CRISIS",
            "plex_or_ivig_indicated": mgfa_class in ["CLASS_V_MYASTHENIC_CRISIS", "CLASS_IVa_SEVERE_LIMB", "CLASS_IVb_SEVERE_BULBAR"],
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton engine instance
mgfa_engine = MgfaMyastheniaGravisEngine()
