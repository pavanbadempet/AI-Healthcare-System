"""
TTVR EVOQUE Valve Replacement vs Tricuspid TEER Decision Engine
================================================================
Evaluates tricuspid coaptation gap (> 7-10 mm), tethering height, and annulus perimeter
to select TTVR (EVOQUE replacement 44/48/52 mm) vs Tricuspid TEER (TriClip / PASCAL).
"""

from typing import Dict, Optional


class TtvrEvoqueVsTeerDecisionEngine:
    """Evaluates TTVR vs TEER strategy for severe tricuspid regurgitation."""

    def evaluate_ttvr_vs_teer(
        self,
        tricuspid_coaptation_gap_mm: float,  # > 7.0 mm unsuitable for TEER
        leaflet_tethering_height_mm: float,  # > 8.0 mm unsuitable for TEER
        annulus_perimeter_derived_diameter_mm: float,  # 38-52 mm for EVOQUE
        severe_or_torrential_tr: bool = True,
        rv_ejection_fraction_percent: float = 45.0,  # RVEF >= 30% required
    ) -> Dict[str, any]:
        teer_unsuitable = tricuspid_coaptation_gap_mm > 7.0 or leaflet_tethering_height_mm > 8.0

        evoque_suitable = (
            severe_or_torrential_tr
            and 38.0 <= annulus_perimeter_derived_diameter_mm <= 52.0
            and rv_ejection_fraction_percent >= 30.0
        )

        recommended_strategy = "TRICUSPID_TEER_TRICLIP_PASCAL"
        evoque_size_mm: Optional[int] = None

        if teer_unsuitable and evoque_suitable:
            recommended_strategy = "TTVR_EVOQUE_VALVE_REPLACEMENT"
            if annulus_perimeter_derived_diameter_mm <= 42.0:
                evoque_size_mm = 44
            elif annulus_perimeter_derived_diameter_mm <= 46.0:
                evoque_size_mm = 48
            else:
                evoque_size_mm = 52

        recommendation = f"Tricuspid TEER (TriClip/PASCAL) Indicated: Coaptation gap {tricuspid_coaptation_gap_mm} mm <= 7.0 mm suitable for edge-to-edge repair"
        if recommended_strategy == "TTVR_EVOQUE_VALVE_REPLACEMENT":
            recommendation = f"TRANSCATHETER TRICUSPID VALVE REPLACEMENT (TTVR) INDICATED (Coaptation gap {tricuspid_coaptation_gap_mm} mm > 7 mm unsuitable for TEER): Perform TTVR with EVOQUE {evoque_size_mm} mm system via transfemoral access"

        return {
            "tricuspid_coaptation_gap_mm": tricuspid_coaptation_gap_mm,
            "teer_unsuitable": teer_unsuitable,
            "recommended_strategy": recommended_strategy,
            "evoque_size_mm": evoque_size_mm,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
ttvr_teer_engine = TtvrEvoqueVsTeerDecisionEngine()
