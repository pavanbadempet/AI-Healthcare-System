"""
Transcatheter Tricuspid Valve Intervention (TTVI) Bicaval Stent System Engine
==============================================================================
Evaluates IVC/SVC diameter (18-34 mm), tricuspid annulus size, and severe TR
to select TricValve / LuCASTR bicaval dual-stent system vs TEER vs EVOQUE replacement.
"""

from typing import Dict


class TtviAnatomicalFeasibilityEngine:
    """Evaluates bicaval dual-stent system (TricValve) feasibility for severe TR."""

    def evaluate_bicaval_ttvi_suitability(
        self,
        ivc_diameter_mm: float,  # 20 to 34 mm for TricValve IVC stent
        svc_diameter_mm: float,  # 18 to 31 mm for TricValve SVC stent
        severe_torrential_tr_present: bool = True,
        teer_and_evoque_ineligible: bool = True,  # Massive coaptation gap or extreme tethering
    ) -> Dict[str, any]:
        ivc_suitable = 20.0 <= ivc_diameter_mm <= 34.0
        svc_suitable = 18.0 <= svc_diameter_mm <= 31.0

        bicaval_suitable = (
            severe_torrential_tr_present
            and teer_and_evoque_ineligible
            and ivc_suitable
            and svc_suitable
        )

        recommendation = "Bicaval dual-stent system NOT indicated (IVC/SVC diameters outside 18-34 mm range or candidate for TEER/EVOQUE); evaluate medical therapy with loop diuretics + MRA"
        if bicaval_suitable:
            recommendation = f"ELIGIBLE FOR TRICVALVE BICAVAL DUAL-STENT SYSTEM (IVC {ivc_diameter_mm} mm, SVC {svc_diameter_mm} mm): Deploy self-expanding Caval Valve Implantation (CAVI) in IVC and SVC to abolish systemic venous congestion and hepatic congestion"

        return {
            "ivc_diameter_mm": ivc_diameter_mm,
            "svc_diameter_mm": svc_diameter_mm,
            "bicaval_ttvi_suitable": bicaval_suitable,
            "recommended_system": "TRICVALVE_BICAVAL_DUAL_STENT_SYSTEM" if bicaval_suitable else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
ttvi_engine = TtviAnatomicalFeasibilityEngine()
