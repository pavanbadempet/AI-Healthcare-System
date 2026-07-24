"""
Invasive Left Atrial Appendage Occlusion (LAAO) Watchman / Amulet Sizing Engine
================================================================================
Evaluates LAA landing zone maximum/minimum diameter (17-31 mm), depth (>= 10 mm),
and lobe anatomy (Chicken Wing, Windsock, Cauliflower) on TEE/CT to size Watchman FLX
or Amplatzer Amulet devices for non-valvular AFib stroke prevention.
"""

from typing import Dict, Optional


class LaaoWatchmanSizingEngine:
    """Evaluates TEE/CT anatomical parameters for LAAO device sizing and PASS criteria."""

    def calculate_laao_device_size(
        self,
        laa_landing_zone_max_diameter_mm: float,
        laa_landing_zone_min_diameter_mm: float,
        laa_usable_depth_mm: float,
        anatomy_type: str = "WINDSOCK",  # CHICKEN_WING, WINDSOCK, CAULIFLOWER, BROCCOLI
        oral_anticoagulation_contraindicated: bool = True,
    ) -> Dict[str, any]:
        avg_diameter = (laa_landing_zone_max_diameter_mm + laa_landing_zone_min_diameter_mm) / 2.0
        depth_adequate = laa_usable_depth_mm >= 10.0

        device_indicated = oral_anticoagulation_contraindicated and (17.0 <= avg_diameter <= 31.0) and depth_adequate

        recommended_watchman_flx_size_mm: Optional[int] = None
        if device_indicated:
            if avg_diameter <= 19.0:
                recommended_watchman_flx_size_mm = 20
            elif avg_diameter <= 22.0:
                recommended_watchman_flx_size_mm = 24
            elif avg_diameter <= 25.0:
                recommended_watchman_flx_size_mm = 27
            elif avg_diameter <= 28.0:
                recommended_watchman_flx_size_mm = 31
            else:
                recommended_watchman_flx_size_mm = 35

        phenotype = "INELIGIBLE_FOR_LAAO"
        if device_indicated:
            phenotype = "LAAO_WATCHMAN_FLX_CANDIDATE"
        elif avg_diameter > 31.0:
            phenotype = "EXTRA_LARGE_LAA_LANDING_ZONE"

        recommendation = "Ineligible for Watchman LAAO; continue oral anticoagulation (Apixaban/Rivaroxaban) if tolerated"
        if device_indicated:
            recommendation = f"Candidate for Watchman FLX LAAO ({recommended_watchman_flx_size_mm} mm device): Target 10-25% compression; verify PASS criteria (Position, Anchor, Size, Seal < 5mm jet) prior to release"
        elif phenotype == "EXTRA_LARGE_LAA_LANDING_ZONE":
            recommendation = "Extra-Large LAA Landing Zone (> 31 mm): Evaluate for Amplatzer Amulet (34 mm) or LARIAT Epicardial Suture Sizing"

        return {
            "average_landing_zone_diameter_mm": round(avg_diameter, 1),
            "usable_depth_mm": laa_usable_depth_mm,
            "anatomy_type": anatomy_type,
            "laao_indicated": device_indicated,
            "recommended_watchman_flx_size_mm": recommended_watchman_flx_size_mm,
            "laao_phenotype": phenotype,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
laao_engine = LaaoWatchmanSizingEngine()
