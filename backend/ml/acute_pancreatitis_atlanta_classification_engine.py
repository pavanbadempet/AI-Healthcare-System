"""
Acute Pancreatitis Revised Atlanta Classification & Organ Failure Engine
========================================================================
Classifies Acute Pancreatitis (Mild, Moderately Severe, Severe) based on Revised Atlanta Classification
and Marshall Scoring (transient organ failure < 48h vs persistent organ failure > 48h).
"""

from typing import Dict


class AcutePancreatitisAtlantaClassificationEngine:
    """Evaluates Revised Atlanta Classification for Acute Pancreatitis severity."""

    def classify_atlanta_pancreatitis(
        self,
        organ_failure_duration_hours: float = 0.0,  # 0, < 48h (transient), > 48h (persistent)
        respiratory_pao2_fio2_ratio: float = 350.0,  # <= 300 organ failure
        renal_serum_creatinine_mg_dL: float = 1.0,  # >= 1.9 organ failure
        cardiovascular_sbp_mmHg: float = 120.0,  # < 90 mmHg (fluid refractory) organ failure
        pancreatic_necrosis_present: bool = False,
        acute_fluid_collection_present: bool = False,
    ) -> Dict[str, any]:
        organ_failure_present = (
            respiratory_pao2_fio2_ratio <= 300.0
            or renal_serum_creatinine_mg_dL >= 1.9
            or cardiovascular_sbp_mmHg < 90.0
        )

        local_complications = pancreatic_necrosis_present or acute_fluid_collection_present

        atlanta_severity = "MILD_ACUTE_PANCREATITIS"
        icu_admission_indicated = False

        if organ_failure_present:
            if organ_failure_duration_hours > 48.0:
                atlanta_severity = "SEVERE_ACUTE_PANCREATITIS"
                icu_admission_indicated = True
            else:
                atlanta_severity = "MODERATELY_SEVERE_ACUTE_PANCREATITIS"
        elif local_complications:
            atlanta_severity = "MODERATELY_SEVERE_ACUTE_PANCREATITIS"

        recommendation = "Mild Acute Pancreatitis: Floor admission; early oral refeeding as tolerated + goal-directed IV crystalloid resuscitation (Ringer's lactate 200-250 mL/h)"
        if atlanta_severity == "SEVERE_ACUTE_PANCREATITIS":
            recommendation = "CRITICAL SEVERE PANCREATITIS (Persistent Organ Failure > 48h): Admit to ICU; initiate aggressive goal-directed fluid resuscitation & enteric nutrition via NJ tube; delay necrosectomy > 4 weeks if possible"
        elif atlanta_severity == "MODERATELY_SEVERE_ACUTE_PANCREATITIS":
            recommendation = "Moderately Severe Pancreatitis (Transient Organ Failure / Local Complication): High-dependency unit monitoring; repeat contrast-enhanced CT in 72 hours if unresolving"

        return {
            "organ_failure_present": organ_failure_present,
            "organ_failure_duration_hours": organ_failure_duration_hours,
            "local_complications_present": local_complications,
            "atlanta_severity": atlanta_severity,
            "icu_admission_indicated": icu_admission_indicated,
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton engine instance
pancreatitis_atlanta_engine = AcutePancreatitisAtlantaClassificationEngine()
