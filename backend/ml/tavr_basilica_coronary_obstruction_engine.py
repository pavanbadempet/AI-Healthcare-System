"""
TAVR Coronary Obstruction Risk & BASILICA Technique Engine
===========================================================
Evaluates cardiac CT Virtual Valve-to-Coronary (VTC) distance (< 4 mm), coronary ostial height (< 10 mm),
and sinus of Valsalva width (< 30 mm) to recommend BASILICA leaflet laceration vs chimney stenting.
"""

from typing import Dict


class TavrBasilicaCoronaryObstructionEngine:
    """Evaluates coronary obstruction risk and BASILICA indication during TAVR."""

    def evaluate_coronary_obstruction_risk(
        self,
        vtc_distance_left_main_mm: float,  # < 4.0 mm = High Risk
        coronary_height_left_main_mm: float,  # < 10.0 mm = High Risk
        sinus_of_valsalva_width_mm: float = 32.0,  # < 30.0 mm = High Risk
        failed_bioprosthesis_present: bool = True,  # Valve-in-Valve TAVR
    ) -> Dict[str, any]:
        high_risk_left_main = vtc_distance_left_main_mm < 4.0 or (
            coronary_height_left_main_mm < 10.0 and sinus_of_valsalva_width_mm < 30.0
        )

        basilica_indicated = high_risk_left_main and failed_bioprosthesis_present

        recommended_prevention = "STANDARD_TAVR_NO_CORONARY_PROTECTION"
        if basilica_indicated:
            recommended_prevention = "BASILICA_LEAFLET_LACERATION"
        elif high_risk_left_main:
            recommended_prevention = "CHIMNEY_STENT_CORONARY_PROTECTION"

        recommendation = "Low risk for coronary obstruction (VTC >= 4 mm, Coronary height >= 10 mm); proceed with standard TAVR"
        if recommended_prevention == "BASILICA_LEAFLET_LACERATION":
            recommendation = f"HIGH RISK CORONARY OBSTRUCTION (VTC {vtc_distance_left_main_mm} mm < 4 mm in Valve-in-Valve TAVR): Perform BASILICA (electrosurgical leaflet laceration of left coronary cusp) immediately prior to TAVR deployment to maintain coronary perfusion"
        elif recommended_prevention == "CHIMNEY_STENT_CORONARY_PROTECTION":
            recommendation = f"HIGH RISK CORONARY OBSTRUCTION (VTC {vtc_distance_left_main_mm} mm < 4 mm): Place guide catheter & undeployed coronary stent in Left Main prior to TAVR deployment (Chimney/Snorkel stenting technique)"

        return {
            "vtc_distance_left_main_mm": vtc_distance_left_main_mm,
            "coronary_height_left_main_mm": coronary_height_left_main_mm,
            "high_risk_coronary_obstruction": high_risk_left_main,
            "recommended_prevention_technique": recommended_prevention,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
basilica_engine = TavrBasilicaCoronaryObstructionEngine()
