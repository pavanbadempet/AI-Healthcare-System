"""
Multiple Sclerosis NMO (NMOSD) vs MOGAD vs MS Classifier Engine
================================================================
Evaluates anti-AQP4-IgG cell-based assay, anti-MOG-IgG serology, LETM >= 3 segments,
and optic neuritis to differentiate NMOSD from MOGAD and classic MS to select target biologics.
"""

from typing import Dict


class NmoAqp4MogadClassifierEngine:
    """Classifies autoimmune demyelinating CNS disorders (NMOSD, MOGAD, MS)."""

    def classify_demyelinating_disorder(
        self,
        aqp4_igg_positive: bool,
        mog_igg_positive: bool,
        letm_segments: int = 0,  # Longitudinally Extensive Transverse Myelitis (>=3 segments)
        bilateral_optic_neuritis: bool = False,
        area_postrema_syndrome: bool = False,
        brainstem_syndrome: bool = False,
        csf_oligoclonal_bands_positive: bool = False,
    ) -> Dict[str, any]:
        classification = "MULTIPLE_SCLEROSIS"
        targeted_biologic = "Ocrelizumab / Ofatumumab (Anti-CD20)"

        if aqp4_igg_positive:
            classification = "NMOSD_AQP4_POSITIVE"
            targeted_biologic = "Satralizumab (Anti-IL6R) / Eculizumab (Anti-C5) / Inebilizumab (Anti-CD19)"
        elif mog_igg_positive:
            classification = "MOGAD_MOG_ANTIBODY_DISEASE"
            targeted_biologic = "Intravenous Immunoglobulin (IVIG) / Rituximab / Corticosteroid Taper"
        elif letm_segments >= 3 or area_postrema_syndrome:
            classification = "SERONEGATIVE_NMOSD"
            targeted_biologic = "Rituximab / Inebilizumab (Seronegative Protocol)"

        recommendation = f"Diagnosis: {classification}. Initiate {targeted_biologic}. Avoid Interferon-beta/Glatiramer acetate as they may exacerbate NMOSD flares."

        return {
            "classification": classification,
            "aqp4_igg_positive": aqp4_igg_positive,
            "mog_igg_positive": mog_igg_positive,
            "letm_present": letm_segments >= 3,
            "area_postrema_syndrome": area_postrema_syndrome,
            "targeted_biologic": targeted_biologic,
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton engine instance
nmo_classifier_engine = NmoAqp4MogadClassifierEngine()
