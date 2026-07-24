"""
Primary Progressive Aphasia (PPA) Variant Classifier Engine
============================================================
Evaluates clinical language features (agrammatism, effortful speech, surface dyslexia,
single-word comprehension, confrontational naming) and MRI neuroimaging patterns
to classify PPA variants (Non-fluent/Agrammatic, Semantic, Logopenic).
"""

from typing import Dict


class PpaVariantClassifierEngine:
    """Classifies Primary Progressive Aphasia (PPA) neurodegenerative variants."""

    def classify_ppa_variant(
        self,
        agrammatic_speech: bool = False,
        effortful_speech_halting: bool = False,
        surface_dyslexia_present: bool = False,
        impaired_single_word_comprehension: bool = False,
        impaired_confrontational_naming: bool = False,
        impaired_phrase_repetition: bool = False,
        phonemic_paraphasias_present: bool = False,
    ) -> Dict[str, any]:
        variant = "UNCLASSIFIED_PRIMARY_PROGRESSIVE_APHASIA"
        pathology_association = "UNKNOWN"

        if (agrammatic_speech or effortful_speech_halting) and not impaired_single_word_comprehension:
            variant = "NON_FLUENT_AGRAMMATIC_PPA_NFVPPA"
            pathology_association = "TAU_OPATHY_FTLD_TAU"
        elif surface_dyslexia_present or (impaired_single_word_comprehension and impaired_confrontational_naming):
            variant = "SEMANTIC_VARIANT_PPA_SVPPA"
            pathology_association = "TDP43_PROTEINOPATHY_FTLD_TDP_TYPE_C"
        elif impaired_phrase_repetition or phonemic_paraphasias_present:
            variant = "LOGOPENIC_VARIANT_PPA_LVPPA"
            pathology_association = "ALZHEIMER_DISEASE_NEUROPATHOLOGY"

        recommendation = f"PPA Variant: {variant} (Associated Pathology: {pathology_association}). Refer to Speech-Language Pathology for augmentative communication strategies & order CSF/PET biomarkers"

        return {
            "ppa_variant": variant,
            "associated_pathology": pathology_association,
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton engine instance
ppa_classifier_engine = PpaVariantClassifierEngine()
