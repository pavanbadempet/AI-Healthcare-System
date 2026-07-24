"""
Light's Criteria Pleural Effusion Exudate vs Transudate Classifier
====================================================================
Evaluates pleural fluid protein/LDH ratios against serum values to differentiate Exudative vs Transudative effusions.
"""

from typing import Dict


class LightsCriteriaClassifier:
    """Classifies pleural effusions using Light's criteria."""

    def classify_pleural_effusion(
        self,
        pleural_fluid_protein_g_dL: float,
        serum_protein_g_dL: float,
        pleural_fluid_ldh_IU_L: float,
        serum_ldh_IU_L: float,
        upper_limit_normal_serum_ldh: float = 200.0,
    ) -> Dict[str, any]:
        protein_ratio = round(pleural_fluid_protein_g_dL / max(serum_protein_g_dL, 0.1), 2)
        ldh_ratio = round(pleural_fluid_ldh_IU_L / max(serum_ldh_IU_L, 0.1), 2)
        ldh_uln_threshold = round((2.0 / 3.0) * upper_limit_normal_serum_ldh, 1)

        criteria_1_met = protein_ratio > 0.5
        criteria_2_met = ldh_ratio > 0.6
        criteria_3_met = pleural_fluid_ldh_IU_L > ldh_uln_threshold

        is_exudate = criteria_1_met or criteria_2_met or criteria_3_met

        etiology = "EXUDATIVE_EFFUSION (Infection, Malignancy, Pulmonary Embolism, Autoimmune)" if is_exudate else "TRANSUDATIVE_EFFUSION (Heart Failure, Cirrhosis, Nephrotic Syndrome)"

        return {
            "pleural_serum_protein_ratio": protein_ratio,
            "pleural_serum_ldh_ratio": ldh_ratio,
            "effusion_type": "EXUDATE" if is_exudate else "TRANSUDATE",
            "suspected_etiology_categories": etiology,
            "further_workup": "Pleural fluid cytology, Gram stain, culture, cell count & differential" if is_exudate else "Optimize fluid management & treat underlying systemic condition",
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton classifier instance
lights_classifier = LightsCriteriaClassifier()
