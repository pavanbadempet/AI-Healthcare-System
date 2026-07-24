"""
Pericarditis vs STEMI ECG Differential Classifier
=================================================
Differentiates Acute Pericarditis (concave diffuse ST elevation, PR depression, Spodick sign)
from Acute STEMI (convex localized ST elevation, reciprocal ST depression).
"""

from typing import Dict


class PericarditisStemiEcgClassifier:
    """Classifies ECG signals between Acute Pericarditis and Acute STEMI."""

    def classify_ecg_differential(
        self,
        diffuse_concave_st_elevation: bool,
        pr_segment_depression_lead_ii: bool,
        st_elevation_is_localized_contiguous_leads: bool,
        reciprocal_st_depression_present: bool,
        troponin_level_ng_mL: float,
    ) -> Dict[str, any]:
        classification = "NORMAL_OR_NON_SPECIFIC"
        urgency = "ROUTINE"

        if st_elevation_is_localized_contiguous_leads and reciprocal_st_depression_present:
            classification = "ACUTE_STEMI_MYOCARDIAL_INFARCTION"
            urgency = "STAT_CATH_LAB_ACTIVATION"
        elif diffuse_concave_st_elevation or pr_segment_depression_lead_ii:
            classification = "ACUTE_PERICARDITIS"
            urgency = "HIGH_PRIORITY"

        recommendation = "Maintain routine ECG monitoring"
        if classification == "ACUTE_STEMI_MYOCARDIAL_INFARCTION":
            recommendation = "Activate Cath Lab stat for Primary PCI (Door-to-Balloon < 90 min) & aspirin + P2Y12 inhibitor"
        elif classification == "ACUTE_PERICARDITIS":
            recommendation = "High-dose NSAID / Aspirin + Colchicine for 3 months & restrict strenuous physical activity"

        return {
            "ecg_classification": classification,
            "urgency_tier": urgency,
            "cath_lab_activation_required": classification == "ACUTE_STEMI_MYOCARDIAL_INFARCTION",
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton classifier instance
pericarditis_stemi_classifier = PericarditisStemiEcgClassifier()
