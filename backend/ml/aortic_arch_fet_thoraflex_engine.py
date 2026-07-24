"""
Aortic Arch Aneurysm Frozen Elephant Trunk (FET) Thoraflex Hybrid Engine
========================================================================
Evaluates aortic arch aneurysm diameter (>= 55 mm), Ishimaru zone of proximal anchoring (Zone 0-2),
and descending aorta landing zone diameter (24-40 mm) to size Thoraflex Hybrid FET prostheses.
"""

from typing import Dict, Optional


class AorticArchFetThoraflexEngine:
    """Evaluates anatomical feasibility and sizing for Frozen Elephant Trunk (FET) arch repair."""

    def evaluate_fet_eligibility(
        self,
        arch_aneurysm_max_diameter_mm: float,
        descending_aorta_landing_diameter_mm: float,
        ishimaru_landing_zone: int = 0,  # 0, 1, 2
        acute_type_a_dissection: bool = False,
    ) -> Dict[str, any]:
        size_threshold = 50.0 if acute_type_a_dissection else 55.0
        aneurysm_indicated = arch_aneurysm_max_diameter_mm >= size_threshold

        landing_zone_eligible = 24.0 <= descending_aorta_landing_diameter_mm <= 40.0
        eligible = (aneurysm_indicated or acute_type_a_dissection) and landing_zone_eligible

        recommended_fet_size_mm: Optional[int] = None
        if eligible:
            if descending_aorta_landing_diameter_mm <= 28.0:
                recommended_fet_size_mm = 28
            elif descending_aorta_landing_diameter_mm <= 32.0:
                recommended_fet_size_mm = 32
            elif descending_aorta_landing_diameter_mm <= 36.0:
                recommended_fet_size_mm = 36
            else:
                recommended_fet_size_mm = 40

        recommendation = "Ineligible for FET repair; monitor aortic diameter with CTA every 6 months"
        if eligible:
            recommendation = f"Candidate for Frozen Elephant Trunk (Thoraflex Hybrid {recommended_fet_size_mm} mm Stent-Graft): Hypothermic circulatory arrest (28°C) + Antegrade Selective Cerebral Perfusion (ASCP) indicated for Ishimaru Zone {ishimaru_landing_zone} arch reconstruction"

        return {
            "arch_aneurysm_max_diameter_mm": arch_aneurysm_max_diameter_mm,
            "descending_aorta_landing_diameter_mm": descending_aorta_landing_diameter_mm,
            "fet_eligible": eligible,
            "recommended_fet_size_mm": recommended_fet_size_mm,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
fet_engine = AorticArchFetThoraflexEngine()
