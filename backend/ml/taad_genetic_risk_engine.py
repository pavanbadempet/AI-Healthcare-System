"""
Thoracic Aortic Aneurysm & Dissection (TAAD) Genetic Risk Engine
================================================================
Evaluates pathogenic genetic variants (FBN1, TGFBR1/2, ACTA2, COL3A1), aortic root Z-score,
and family history to adjust surgical thresholds (42-50 mm) per ACC/AHA Aortic Guidelines.
"""

from typing import Dict, Optional


class TaadGeneticRiskEngine:
    """Evaluates genetic variants and calculates tailored surgical thresholds for TAAD."""

    def evaluate_taad_genetic_risk(
        self,
        aortic_root_max_diameter_mm: float,
        pathogenic_variant_gene: Optional[str] = None,  # FBN1, TGFBR1, TGFBR2, ACTA2, COL3A1
        aortic_root_z_score: float = 2.0,
        family_history_aortic_dissection: bool = False,
        rapid_growth_rate_over_5mm_yr: bool = False,
    ) -> Dict[str, any]:
        surgical_threshold_mm = 55.0

        if pathogenic_variant_gene in ["TGFBR1", "TGFBR2"]:
            surgical_threshold_mm = 42.0  # Loeys-Dietz syndrome
        elif pathogenic_variant_gene == "COL3A1":
            surgical_threshold_mm = 45.0  # Vascular Ehlers-Danlos
        elif pathogenic_variant_gene in ["FBN1", "ACTA2", "MYH11"]:
            surgical_threshold_mm = 45.0 if family_history_aortic_dissection or rapid_growth_rate_over_5mm_yr else 50.0

        surgery_indicated = aortic_root_max_diameter_mm >= surgical_threshold_mm or aortic_root_z_score >= 3.5

        syndrome_name = "SPORADIC_THORACIC_AORTIC_ANEURYSM"
        if pathogenic_variant_gene in ["TGFBR1", "TGFBR2"]:
            syndrome_name = "LOEYS_DIETZ_SYNDROME"
        elif pathogenic_variant_gene == "FBN1":
            syndrome_name = "MARFAN_SYNDROME"
        elif pathogenic_variant_gene == "COL3A1":
            syndrome_name = "VASCULAR_EHLERS_DANLOS_SYNDROME"
        elif pathogenic_variant_gene == "ACTA2":
            syndrome_name = "FAMILIAL_TAAD_ACTA2"

        recommendation = f"Aortic diameter {aortic_root_max_diameter_mm} mm below threshold ({surgical_threshold_mm} mm); continue annual CTA/MRI surveillance"
        if surgery_indicated:
            recommendation = f"SURGICAL REPAIR INDICATED ({syndrome_name}, Diameter {aortic_root_max_diameter_mm} mm >= {surgical_threshold_mm} mm threshold): Elective aortic root / ascending aorta replacement (David valve-sparing or Bentall procedure)"

        return {
            "aortic_root_max_diameter_mm": aortic_root_max_diameter_mm,
            "pathogenic_variant_gene": pathogenic_variant_gene,
            "syndrome_name": syndrome_name,
            "tailored_surgical_threshold_mm": surgical_threshold_mm,
            "surgery_indicated": surgery_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
taad_engine = TaadGeneticRiskEngine()
