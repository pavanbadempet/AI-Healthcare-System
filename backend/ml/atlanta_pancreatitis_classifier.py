"""
Acute Pancreatitis Atlanta Classification & Organ Failure Engine
=================================================================
Classifies acute pancreatitis severity into Mild, Moderately Severe, or Severe (persistent organ failure > 48h)
according to the Revised Atlanta Classification.
"""

from typing import Dict


class AtlantaPancreatitisClassifier:
    """Classifies acute pancreatitis severity using Revised Atlanta Classification."""

    def classify_pancreatitis_severity(
        self,
        transient_organ_failure_under_48h: bool,
        persistent_organ_failure_over_48h: bool,
        local_complications_necrosis_fluid_collection: bool = False,
    ) -> Dict[str, any]:
        severity = "MILD_ACUTE_PANCREATITIS"
        icu_transfer = False

        if persistent_organ_failure_over_48h:
            severity = "SEVERE_ACUTE_PANCREATITIS"
            icu_transfer = True
        elif transient_organ_failure_under_48h or local_complications_necrosis_fluid_collection:
            severity = "MODERATELY_SEVERE_ACUTE_PANCREATITIS"

        recommendation = "Standard ward admission, oral refeeding as tolerated, & IV crystalloids"
        if severity == "SEVERE_ACUTE_PANCREATITIS":
            recommendation = "Stat ICU transfer, invasive hemodynamic monitoring, & Surgical Gastroenterology consult"
        elif severity == "MODERATELY_SEVERE_ACUTE_PANCREATITIS":
            recommendation = "High-dependency unit monitoring & repeat contrast CT abdomen at 72h"

        return {
            "atlanta_severity_grade": severity,
            "persistent_organ_failure_present": persistent_organ_failure_over_48h,
            "icu_transfer_indicated": icu_transfer,
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton classifier instance
atlanta_classifier = AtlantaPancreatitisClassifier()
