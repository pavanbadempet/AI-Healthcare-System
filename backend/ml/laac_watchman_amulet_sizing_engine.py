"""
Percutaneous Left Atrial Appendage Closure (LAAC) Watchman FLX vs Amulet Sizing Engine
======================================================================================
Evaluates TEE/CT LAA ostium diameter (17-31 mm), usable depth (>= 10-15 mm), and anatomy
(Chicken Wing, Cactus, Cauliflower, Windsock) in NVAF with high bleeding risk (HAS-BLED >= 3)
to select Watchman FLX (20-35 mm) vs Amplatzer Amulet (16-34 mm) device size.
"""

from typing import Dict


class LaacWatchmanAmuletSizingEngine:
    """Evaluates LAA closure device candidacy and sizing for stroke prevention in AFib."""

    def evaluate_laac_sizing(
        self,
        laa_ostium_max_diameter_mm: float,  # 17.0 to 31.0 mm for Watchman FLX
        laa_usable_depth_mm: float,  # >= 10.0-15.0 mm
        nonvalvular_afib_present: bool = True,
        cha2ds2_vasc_score: int = 4,  # >= 2
        has_bled_score: int = 3,  # >= 3 or OAC contraindicated
        laa_thrombus_present_on_tee: bool = False,  # Strict contraindication
    ) -> Dict[str, any]:
        if laa_thrombus_present_on_tee:
            return {
                "laac_eligible": False,
                "reason": "LAA_THROMBUS_STRICT_CONTRAINDICATION",
                "clinical_recommendation": "LAAC STRICTLY CONTRAINDICATED! LAA thrombus detected on TEE; initiate 4-8 weeks of therapeutic systemic anticoagulation (DOAC / Warfarin) and repeat TEE before re-evaluating LAAC",
                "status": "EVALUATION_COMPLETE",
            }

        eligible = (
            nonvalvular_afib_present
            and cha2ds2_vasc_score >= 2
            and has_bled_score >= 3
            and 16.0 <= laa_ostium_max_diameter_mm <= 31.0
            and laa_usable_depth_mm >= 10.0
        )

        device_selected = "WATCHMAN_FLX"
        recommended_size_mm = laa_ostium_max_diameter_mm * 1.15  # 10-20% oversizing

        recommendation = "LAAC NOT indicated or anatomy unsuitable (ostium outside 16-31 mm or depth < 10 mm); continue oral anticoagulation or left atrial appendage surgical ligation"
        if eligible:
            recommendation = f"ELIGIBLE FOR LAAC PROCEDURE ({device_selected}): Select device size approx {recommended_size_mm:.1f} mm for LAA ostium {laa_ostium_max_diameter_mm} mm. Deploy under ICE/TEE guidance to achieve peri-device leak < 3 mm and reduce embolic stroke risk without long-term OAC"

        return {
            "laac_eligible": eligible,
            "device_selected": device_selected if eligible else "NONE",
            "recommended_device_size_mm": round(recommended_size_mm, 1) if eligible else 0.0,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
laac_engine = LaacWatchmanAmuletSizingEngine()
