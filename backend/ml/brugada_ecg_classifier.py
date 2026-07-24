"""
Brugada & Early Repolarization Syndrome ECG Classifier
======================================================
Analyzes V1-V3 ST-segment coved/saddleback elevations to classify Brugada Pattern Type 1 / Type 2
and evaluate sudden cardiac death risk.
"""

from typing import Dict


class BrugadaEcgClassifier:
    """Classifies Brugada ECG patterns and sudden cardiac death risk."""

    def classify_brugada_pattern(
        self,
        st_elevation_v1_v3_mm: float,
        pattern_morphology: str,  # 'COVED_TYPE_1', 'SADDLEBACK_TYPE_2', 'NORMAL'
        syncope_history: bool = False,
        family_history_sudden_cardiac_death: bool = False,
    ) -> Dict[str, any]:
        pattern_type = "NO_BRUGADA_PATTERN"
        risk_tier = "LOW_RISK"

        morphology_upper = pattern_morphology.upper()
        if morphology_upper == "COVED_TYPE_1" and st_elevation_v1_v3_mm >= 2.0:
            pattern_type = "BRUGADA_TYPE_1_COVED"
            risk_tier = "HIGH_RISK" if syncope_history or family_history_sudden_cardiac_death else "MODERATE_RISK"
        elif morphology_upper == "SADDLEBACK_TYPE_2" and st_elevation_v1_v3_mm >= 2.0:
            pattern_type = "BRUGADA_TYPE_2_SADDLEBACK"
            risk_tier = "MODERATE_RISK" if syncope_history else "LOW_RISK"

        icd_recommended = pattern_type == "BRUGADA_TYPE_1_COVED" and syncope_history

        return {
            "st_elevation_mm": st_elevation_v1_v3_mm,
            "brugada_pattern_type": pattern_type,
            "sudden_cardiac_death_risk_tier": risk_tier,
            "electrophysiology_consult_indicated": pattern_type != "NO_BRUGADA_PATTERN",
            "icd_implantation_recommended": icd_recommended,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton classifier instance
brugada_classifier = BrugadaEcgClassifier()
