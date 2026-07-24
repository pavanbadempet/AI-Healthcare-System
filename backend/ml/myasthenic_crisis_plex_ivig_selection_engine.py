"""
Myasthenic Crisis Plasma Exchange (PLEX) vs IVIG Selection Engine
===================================================================
Evaluates clinical parameters (renal impairment, IgA deficiency, hyperviscosity risk, vascular access)
in severe Myasthenic Crisis to recommend PLEX (5-6 exchanges) vs High-Dose IVIG (2 g/kg).
"""

from typing import Dict


class MyasthenicCrisisPlexIvigSelectionEngine:
    """Evaluates PLEX vs IVIG modality selection for Myasthenic Crisis."""

    def select_crisis_modality(
        self,
        respiratory_failure_intubated: bool = True,
        hyperviscosity_risk_or_thrombosis: bool = False,
        iga_deficiency_present: bool = False,
        acute_renal_failure_present: bool = False,
        difficult_central_venous_access: bool = False,
    ) -> Dict[str, any]:
        ivig_contraindicated = hyperviscosity_risk_or_thrombosis or iga_deficiency_present or acute_renal_failure_present
        plex_contraindicated = difficult_central_venous_access

        selected_modality = "HIGH_DOSE_IVIG"
        if ivig_contraindicated or (respiratory_failure_intubated and not plex_contraindicated):
            selected_modality = "PLASMA_EXCHANGE_PLEX"

        dosage = "2.0 g/kg divided over 2 to 5 days IV"
        if selected_modality == "PLASMA_EXCHANGE_PLEX":
            dosage = "5 to 6 plasma exchanges (1.0-1.5 plasma volumes each) over 10 to 14 days"

        recommendation = f"MYASTHENIC CRISIS SELECTION: Initiate {selected_modality} ({dosage}). Monitor FVC, NIF, vital capacity, and electrolyte levels continuously in Neuro-ICU"

        return {
            "selected_modality": selected_modality,
            "recommended_dosage_regimen": dosage,
            "ivig_contraindicated": ivig_contraindicated,
            "plex_contraindicated": plex_contraindicated,
            "clinical_recommendation": recommendation,
            "status": "SELECTION_COMPLETE",
        }


# Singleton engine instance
plex_ivig_engine = MyasthenicCrisisPlexIvigSelectionEngine()
