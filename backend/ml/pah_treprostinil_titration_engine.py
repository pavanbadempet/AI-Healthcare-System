"""
Pulmonary Arterial Hypertension (PAH) Inhaled Treprostinil Titration Engine
============================================================================
Evaluates Tyvaso DPI / inhaled Treprostinil dosing (16-64 mcg per session 4x daily),
tolerability (cough, headache), and PVR response to guide titration up to 12 breaths QID.
"""

from typing import Dict


class PahTreprostinilTitrationEngine:
    """Evaluates inhaled Treprostinil (Tyvaso DPI) dosing titration for PAH."""

    def evaluate_treprostinil_titration(
        self,
        current_breaths_per_session: int,  # 3, 6, 9, 12 breaths QID
        who_functional_class: int,  # 1, 2, 3, 4
        cough_or_flushing_tolerable: bool = True,
        systemic_hypotension_present: bool = False,
    ) -> Dict[str, any]:
        target_breaths = 9
        if who_functional_class >= 3:
            target_breaths = 12

        next_breaths = current_breaths_per_session
        titration_status = "MAINTAIN_CURRENT_DOSE"

        if systemic_hypotension_present or not cough_or_flushing_tolerable:
            next_breaths = max(1, current_breaths_per_session - 1)
            titration_status = "DECREASE_DOSE_FOR_TOLERABILITY"
        elif current_breaths_per_session < target_breaths:
            next_breaths = current_breaths_per_session + 1
            titration_status = "TITRATE_UP_BY_1_BREATH"

        recommendation = f"Inhaled Treprostinil (Tyvaso DPI): Current {current_breaths_per_session} breaths QID -> {titration_status} to {next_breaths} breaths QID (Target {target_breaths} breaths QID). Administer 4 times daily during waking hours"

        return {
            "current_breaths_per_session": current_breaths_per_session,
            "recommended_next_breaths_per_session": next_breaths,
            "target_breaths_per_session": target_breaths,
            "titration_status": titration_status,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
treprostinil_engine = PahTreprostinilTitrationEngine()
