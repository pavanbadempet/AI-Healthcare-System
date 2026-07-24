"""
Infrarenal Abdominal Aortic Aneurysm (AAA) EVAR Anatomical Feasibility Engine
=============================================================================
Evaluates CTA proximal neck length (>= 10 mm), neck angulation (<= 60 deg), iliac access (>= 6 mm),
and AAA sac max diameter (>= 55 mm males, >= 50 mm females) to select EVAR vs FEVAR vs Open Repair.
"""

from typing import Dict


class EvarAaaAnatomicalFeasibilityEngine:
    """Evaluates CTA anatomy for Endovascular Aneurysm Repair (EVAR) suitability."""

    def evaluate_evar_feasibility(
        self,
        aaa_max_sac_diameter_mm: float,
        proximal_neck_length_mm: float,
        proximal_neck_diameter_mm: float,
        proximal_neck_angulation_deg: float,
        min_iliac_access_diameter_mm: float,
        is_female: bool = False,
    ) -> Dict[str, any]:
        size_threshold = 50.0 if is_female else 55.0
        repair_indicated = aaa_max_sac_diameter_mm >= size_threshold

        favorable_neck = (proximal_neck_length_mm >= 10.0) and (proximal_neck_angulation_deg <= 60.0) and (18.0 <= proximal_neck_diameter_mm <= 32.0)
        adequate_access = min_iliac_access_diameter_mm >= 6.0

        standard_evar_eligible = repair_indicated and favorable_neck and adequate_access

        recommended_approach = "CONSERVATIVE_SURVEILLANCE_CTA_EVERY_6_MONTHS"
        if repair_indicated:
            if standard_evar_eligible:
                recommended_approach = "STANDARD_BIFURCATED_EVAR_STENT_GRAFT"
            elif not favorable_neck and adequate_access:
                recommended_approach = "FENESTRATED_OR_BRANCHED_EVAR_FEVAR_BEVAR"
            else:
                recommended_approach = "OPEN_SURGICAL_AAA_REPAIR_WITH_DACRON_GRAFT"

        recommendation = f"AAA Max Diameter {aaa_max_sac_diameter_mm} mm below repair threshold ({size_threshold} mm); continue annual/semiannual ultrasound/CTA surveillance"
        if repair_indicated:
            if standard_evar_eligible:
                recommendation = f"Candidate for Standard EVAR ({recommended_approach}): Proximal neck length {proximal_neck_length_mm} mm & angulation {proximal_neck_angulation_deg}° meet IFU instructions for use"
            elif recommended_approach == "FENESTRATED_OR_BRANCHED_EVAR_FEVAR_BEVAR":
                recommendation = f"Short / Hostile Proximal Neck ({proximal_neck_length_mm} mm): Standard EVAR contraindicated due to type 1A endoleak risk; proceed with FEVAR / BEVAR or Chimney EVAR (ChEVAR)"
            else:
                recommendation = f"Hostile Anatomy & Inadequate Iliac Access ({min_iliac_access_diameter_mm} mm): Proceed with Open Surgical AAA Repair"

        return {
            "aaa_max_sac_diameter_mm": aaa_max_sac_diameter_mm,
            "proximal_neck_length_mm": proximal_neck_length_mm,
            "repair_indicated": repair_indicated,
            "standard_evar_eligible": standard_evar_eligible,
            "recommended_approach": recommended_approach,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
evar_engine = EvarAaaAnatomicalFeasibilityEngine()
